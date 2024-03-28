from naoqi import ALProxy, ALBroker, ALModule
import time, sys, re


word_pattern =  re.compile(">\s*(.+?)\s*<")

class WordRecognizer(ALModule):
    def __init__(self, name, ip, port):
        self.ip = ip
        self.port = port
        self.name = name
        ALModule.__init__(self, name)
        self.memoryProxy = ALProxy("ALMemory", self.ip, self.port)
        self.listenProxy = ALProxy("ALSpeechRecognition", self.ip, self.port)

        print(" ------ WordRecognizer __init__")      

    def start_listening_for_words(self, words):
        self.vocabulary = words
        self.memoryProxy.subscribeToEvent("WordRecognized", self.name, "onWordRecognized")
        self.recognized_a_word = False
        self.matched_word = None
        self.listenProxy.pause(True)
        self.listenProxy.setLanguage("English")
        self.listenProxy.setVocabulary(words, True)

        self.listenProxy.subscribe(self.name)
        self.listenProxy.pause(False)
        print(" ------ Start Listening for Words")
       
    def stop_listening_for_words(self):
        self.listenProxy.unsubscribe(self.name)  # Ensure we unsubscribe to clean up
        self.memoryProxy.unsubscribeToEvent("WordRecognized", self.name) #, "onWordRecognized")
        self.listenProxy.pause(True)


    def onWordRecognized(self, key, value, message):
        print(" ------ on_name_recognized")
        print(value)
        string_match = word_pattern.search(str(value[0])).group(1)
        if value and string_match in self.vocabulary and value[1] >= 0.5:
            self.matched_word = string_match
            self.recognized_a_word = True
