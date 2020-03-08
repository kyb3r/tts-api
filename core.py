from sys import platform
import pyttsx3
from pydantic import BaseModel

class DanielVoice:
    def __init__(self, speed=180):
        self.engine = pyttsx3.init()
        self.speed = speed
        self.setup()
    
    def setup(self):
        self.engine.setProperty("rate", self.speed)
        self.engine.setProperty("rate", self.speed)
        voices = self.engine.getProperty("voices")

        if platform == "darwin":
            voice = "Daniel"
        elif platform == "win32":
            voice = "Vocalizer Expressive Daniel Harpo 22kHz"
        try:
            voice = [v for v in voices if v.name == voice][0]
        except IndexError:
            pass
        else:
            self.engine.setProperty("voice", voice.id)
    
    def await_synthesis(self):
        self.engine.runAndWait()
        print('Finished synthesis')
    
    def stop(self):
        self.engine.stop()

    def save_to_file(self, text, file):
        self.engine.save_to_file(text, str(file))
        print(f'Generating: {text}')

class Speech(BaseModel):
    speed: int = 180
    text: str

class BulkSpeech(Speech):
    text: list