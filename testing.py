from naoqi import ALProxy, ALBroker, ALModule
import sys

NAO_IP = "192.168.1.53"  # Change to your NAO's IP address
NAO_PORT = 9559

class WordRecognizerModule(ALModule):
    """
    A simple module to demonstrate basic speech recognition with NAO.
    """
    
    def __init__(self, name):
        ALModule.__init__(self, name)
        self.name = name
        self.tts = ALProxy("ALTextToSpeech")
        self.memory = ALProxy("ALMemory")
        self.speech_recognition = ALProxy("ALSpeechRecognition")
        
        # Setup speech recognition
        self.speech_recognition.setLanguage("English")
        words = ["hello", "goodbye", "yes", "no"]
        self.speech_recognition.setVocabulary(words, False)
        
        # Subscribe to the WordRecognized event
        self.memory.subscribeToEvent("WordRecognized", self.name, "onWordRecognized")

    def onWordRecognized(self, key, value, message):
        """
        This method will be called each time a word is recognized.
        """
        # value is a list containing the recognized word and the confidence level
        if value and len(value) > 1 and value[1] >= 0.4:  # Check confidence level
            word = value[0]
            print(f"Recognized word: {word}")
            self.tts.say(f"I heard: {word}")
            
    def stop(self):
        """
        Unsubscribe from the event when done.
        """
        self.memory.unsubscribeToEvent("WordRecognized", self.name)