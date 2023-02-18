from chatgpt_wrapper import ChatGPT
import speech_recognition as sr
import pyttsx3
from enum import Enum, auto


TRIGGER_PHRASE = "hey chat gpt"


class LED_STATUS(Enum):
    ON = auto
    OFF = auto


bot = ChatGPT()
r = sr.Recognizer()


def listen_for_audio() -> str:
    """Listens for audio from the microphone

    Returns:
        str: The recognized speech from the audio
    """
    try:
        with sr.Microphone() as audio_source:
            r.adjust_for_ambient_noise(audio_source, duration=0.2)
            audio2 = r.listen(audio_source)
            text = r.recognize_google(audio2).lower()
            return text

    except sr.RequestError as e:
        print("Could not request results; {0}".format(e))

    except sr.UnknownValueError:
        print("unknown error occurred")


def set_led_status(status: LED_STATUS) -> None:
    pass


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
    engine = pyttsx3.init()
    engine.setProperty("rate", 90)  # setting up new voice rate
    engine.say(response)
    engine.runAndWait()
    engine.stop()


def main():
    triggered = False
    while True:
        if not triggered:
            voice_request = listen_for_audio()
            if voice_request == TRIGGER_PHRASE:
                triggered = True
        else:
            set_led_status()
            triggered = False
            voice_request = listen_for_audio()
            if voice_request:
                chat_gpt_response = send_statement(voice_request)
                if chat_gpt_response:
                    say_out_loud(chat_gpt_response)
            set_led_status()


if __name__ == "__main__":
    main()
