from naoqi import ALProxy, ALBroker, ALModule
from robot_move import MotionHandler
import time, sys, re

class LandmarkHandler(ALModule):
    def __init__(self, name, ip, port):
        self.ip = ip
        self.port = port
        self.name = name
        ALModule.__init__(self, name)
        self.memoryProxy = ALProxy("ALMemory", self.ip, self.port) 
        self.landmark_detection = ALProxy("ALLandMarkDetection", self.ip, self.port)
        self.motion_instance = MotionHandler("motion_handler", self.ip, self.port)
        print(" ------ LandmarkHandler __init__")


    def initialize_landmark_handler(self):
        self.memoryProxy.subscribeToEvent("LandmarkDetected", self.name, "onLandmarkDetected")
        self.landmark_location_angle = None
        print(" ------ initialize_landmark_handler")

    def onLandmarkDetected(self, key, value, message):
        print(" ------ onLandmarkDetected")
        self.landmark_location_angle = (self.motion_instance.motionProxy.getAngles("HeadYaw", True)[0])
        print(self.landmark_location_angle)
        self.memoryProxy.unsubscribeToEvent("LandmarkDetected", self.name)
