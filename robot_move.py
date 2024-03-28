from naoqi import ALProxy, ALBroker, ALModule
import time, sys, re

class MotionHandler(ALModule):
    def __init__(self, name, ip, port):
        self.ip = ip
        self.port = port
        ALModule.__init__(self, name)
        self.motionProxy = ALProxy("ALMotion", self.ip, self.port)
        self.postureProxy = ALProxy("ALRobotPosture", self.ip, self.port)
        self.memoryProxy = ALProxy("ALMemory", self.ip, self.port)

        print(" ------ MotionHandler __init__")

    def start_head_movement(self):
        self.motionProxy.setStiffnesses("Head", 1.0)  # Enable head motors
        self.pitch_angle = 0.0  # Adjust as necessary for the robot to look straight ahead
        self.yaw_angle = 0.0    # Center the head
        self.motionProxy.setAngles(["HeadPitch", "HeadYaw"], [self.pitch_angle, self.yaw_angle], 0.1)  # Adjust speed as needed
        print(" ------ start_head_movement")

    def stand_up(self):
        self.postureProxy.goToPosture("Stand", 0.5)
        self.motionProxy.wakeUp()
        self.motionProxy.setAngles("HeadYaw", 0, .5)

        print(" ------ stand_up")

    def onMotionCompleted(self, name, value, subscriberIdentifier):
        self.motion_has_been_completed = [subscriberIdentifier, True]
        print(" -------- OnMotionCompleted")
