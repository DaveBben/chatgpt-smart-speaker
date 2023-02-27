from chatgpt_wrapper import ChatGPT
import speech_recognition as sr
import json
import time
from rpi_ws281x import PixelStrip, Color
from google.cloud import texttospeech
import os
import subprocess

# LED strip configuration:
LED_COUNT = 12        # Number of LED pixels.
LED_PIN = 18          # GPIO pin connected to the pixels (18 uses PWM!).
# LED_PIN = 10        # GPIO pin connected to the pixels (10 uses SPI /dev/spidev0.0).
LED_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA = 10          # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 255  # Set to 0 for darkest and 255 for brightest
LED_INVERT = False    # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53


# Credentials for Google Speech to Text
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/home/pi/project_keys.json'

TRIGGER_PHRASE = "computer"


DIR_PATH = os.path.dirname(os.path.realpath(__file__))


bot = ChatGPT()
r = sr.Recognizer()
client = texttospeech.TextToSpeechClient()
strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)




def listen_for_audio(offline: bool = True, listen_seconds: int = 10) -> str:
    """Listens for audio from the microphone

    Returns:
        str: The recognized speech from the audio
    """
    try:
        with sr.Microphone() as audio_source:
            r.adjust_for_ambient_noise(audio_source, duration=0.2)
            audio2 = r.listen(audio_source, timeout=3, phrase_time_limit=listen_seconds)
            if offline:
                text = json.loads(r.recognize_vosk(audio2).lower())
                return text['text']
            else:
                text = r.recognize_google(audio2).lower()

                return text

    except sr.RequestError as e:
        print("Could not request results; {0}".format(e))
    except sr.UnknownValueError:
        print("unknown error occurred")
    except sr.WaitTimeoutError:
        print("No voice detected")


def colorWipe(strip, color, wait_ms=50):
    """Wipe color across display a pixel at a time."""
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color)
        strip.show()
        time.sleep(wait_ms / 1000.0)

def send_statement(voice_request: str) -> str:
    """Sends a statement to ChatGPT for Processing

    Args:
        voice_request (str): The requests to send

    Returns:
        str: The response from ChatGPT
    """
    response = bot.ask(voice_request)
    return response

def say_out_loud(response: str) -> None:
    """Convert the text to speech

    Args:
        response (str): Text to read out loud
    """
    synthesis_input = texttospeech.SynthesisInput(text=response)
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US", ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )
    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )
    file_path = os.path.join(DIR_PATH, "output.mp3")
    try:
        os.remove(file_path)
    except FileNotFoundError:
        pass

    with open(file_path, "wb") as out:
        # Write the response to the output file.
        out.write(response.audio_content)
        subprocess.run(['mpg123', file_path])

def play_beep():
    file_path = os.path.join(DIR_PATH, "beep.mp3")
    subprocess.run(['mpg123', file_path])


def main():
    triggered = False
    strip.begin()
    colorWipe(strip, Color(0, 0, 255))  # Blue wipe

    while True:
        if not triggered:
            colorWipe(strip, Color(0, 0, 0), 10)
            voice_request = listen_for_audio(offline=True, listen_seconds=2)
            if voice_request == TRIGGER_PHRASE:
                triggered = True
        else:
            play_beep()
            colorWipe(strip, Color(0, 0, 255))  # Blue wipe
           # set_led_status()
            triggered = False
            voice_request = listen_for_audio(offline=False)
            if voice_request:
                colorWipe(strip, Color(255, 0, 0))  # Red wipe
                chat_gpt_response = send_statement(voice_request)
                colorWipe(strip, Color(0, 255, 0))  # Green wipe
                if chat_gpt_response:
                    say_out_loud(chat_gpt_response)
           # set_led_status()
        time.sleep(2)


if __name__ == "__main__":
    main()
