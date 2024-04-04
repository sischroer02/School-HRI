from naoqi import ALProxy, ALBroker, ALModule
from word_recognition import WordRecognizer
from face_detection import FaceRecognition
from robot_move import MotionHandler
from robot_speak import RobotSpeak
# from robot_localization import LocalizationHandler
from landmark_detection import LandmarkHandler
from robot_tracker import TrackerHandler
from datetime import datetime
import time, sys, re, math

point_head_instance = None
point_to_instance = None
robot_speak_instance = None
reset_movement_instance = None
stand_up_instance = None
face_detection_instance = None
look_for_face_instance = None
words1_recognition_instance  = None


nao_ip = "192.168.1.53"
nao_port = 9559
MyBroker = None

next_state = None

left_landmark_location = None
right_landmark_location = None

name_talking_to = None

names_of_employees = ["Silas"]

guest_response_to_visitor_passes = ["yes", "no"]
guest_response_to_questions = ["yes", "no"]
guest_possible_questions = ["bathroom","entrance", "time", "Silas", "package", "lunch", "wifi password", "visitor passes", "phone"]
responses_to_guests = {"bathroom": "the bathroom is around the corner",
                       "entrance": "the entrance is behind you",
                       "time": "the time is" + str(datetime.now().time()),
                       "Silas": "Silas's office is around the corner",
                       "package": "I can sign for your package here",
                       "lunch": "lunch will be provided at 12:30",
                       "wifi password": "the wifi password is I L O V E F R I E N D L Y", 
                       "visitor passes" : "the visitor passes are right there",
                       "phone": "the phone is over there"
}

employee_responses_to_question = ["yes" "no"]

def main():
    global MyBroker
    MyBroker = ALBroker("myBroker", "0.0.0.0", 0, nao_ip, nao_port)
    global reset_movement_instance
    reset_movement_instance = MotionHandler("reset_movement_instance", nao_ip, nao_port)

    global fsm
    fsm = FSMHandler()

    try:
        print("entering fsm")
        while True:
            if fsm.transition_needed:
                fsm.transition()
            else:
                fsm.currentState()
    except KeyboardInterrupt:
        print("Interrupted by user, shutting down")
        MyBroker.shutdown()
        sys.exit(0)
    

class FSMHandler:
    def __init__(self):
        self.states = ['initialize', 'idle', 'conversation', 'phone', 'visitor_pases', 'pencils']
        self.transitions = {
            'initialize': {'idle' : 'idle'},
            'idle': {'conversation' : 'conversation',
                     'phone' : 'phone'},
            'conversation': {'idle' : 'idle', 
                             'phone' : 'phone', 
                             'visitor_passes' : 'visitor_passes', 
                             'pencils' : 'pencils'},
            'phone': {'idle' : 'idle', 
                      'conversation' : 'conversation'},
            'pencils': {'conversation' : 'conversation'},
            'visitor_passes': {'pencils' : 'pencils'}
        }
        self.current_state = 'initialize'
        self.transition_needed = False
    
    def transition(self):
        print("Transitioning from " +str(self.current_state) + "to " + str(self.transitions[self.current_state][next_state]))
        self.current_state = self.transitions[self.current_state][next_state]
        self.transition_needed = False


    def currentState(self):
        print("The current light is " + str(self.current_state))
        if self.current_state == 'initialize':
            set_up_experiment()
            self.transition_needed = True
        elif self.current_state == 'idle':
            wait_for_person_or_phone()
            self.transition_needed = True
        elif self.current_state == 'conversation':
            conversation_handler()
            self.transition_needed = True
        elif self.current_state == 'phone':
            point_to_phone()
            self.transition_needed = True
        elif self.current_state == 'visitor_passes':
            point_to_passes()
            self.transition_needed = True

def wait_for_person_or_phone():
    look_for_faces_code()
    global next_state
    if look_for_face_instance.face_detected:
        # next_state = 'conversation'
        next_state = "conversation"
    else:
        next_state = 'phone'

def conversation_handler():
    ############################# DIALOGUE HERE ##############################
    robot_speak_instance.say_words("This is where I would start a dialogue")
    time.sleep(1)

    if name_talking_to == "Visitor":
        guest_conversation()
    elif name_talking_to:
        employee_conversation()
    global next_state
    next_state = "idle"

    time.sleep(5)
    robot_speak_instance.say_words("Haven't heard from you for a while. Do you want to ask anything?")               # Prompt user after 5s of quietness

    face_recognition = FaceRecognition("FaceRecognition", "192.168.1.53", 9559)  
    face_recognition.start_looking_for_face()
    if not face_recognition.face_detected:
        robot_speak_instance.say_words("I can't detect a face. Could you please reposition your face in fornt of me?")     # Prompt user when lost face

def employee_conversation():
    robot_speak_instance.say_words("I know you are an employee this is where I would talk to you")

def guest_conversation():
    robot_speak_instance.say_words("Hello, what is the reason for your visit?")
    robot_speak_instance.say_words("Would you like something?")
    listen_for_words(guest_response_to_questions)
    robot_speak_instance.say_words("What would you like?")
    listen_for_words(guest_possible_questions)
    robot_speak_instance.say_words(responses_to_guests[words1_recognition_instance.matched_word])
    if words1_recognition_instance.matched_word == "phone":
        point_to_phone()
    elif words1_recognition_instance.matched_word == "visitor passes":
        point_to_passes()

def listen_for_words(words_to_listen_for):
    global words1_recognition_instance 
    if words1_recognition_instance:
        pass
    else:
        words1_recognition_instance = WordRecognizer("words1_recognition_instance", nao_ip, nao_port)
    words1_recognition_instance.start_listening_for_words(words_to_listen_for)
    try:
        while True:
            if words1_recognition_instance.recognized_a_word:
                words1_recognition_instance.stop_listening_for_words()
                break
    except KeyboardInterrupt:
        print("Interrupted by user, shutting down")
        words1_recognition_instance.stop_listening_for_words()
        MyBroker.shutdown()
        sys.exit(0)

def point_to_phone():
    point_to_location_code(left_landmark_location, "LArm")
    time.sleep(1)
    reset_movement_instance.stand_up()

def point_to_passes():
    point_to_location_code(right_landmark_location, "RArm")
    time.sleep(1)
    reset_movement_instance.stand_up()

def set_up_experiment():
    robot_stand_up()
    time.sleep(1)
    set_up_robot_speaking()
    learn_face_code()
    scan_environment_functionality()
    while (left_landmark_location == None or right_landmark_location == None):
        scan_environment_functionality()
    global next_state
    next_state = "idle"

def robot_stand_up():
    global stand_up_instance
    stand_up_instance = MotionHandler("stand_up_instance", nao_ip, nao_port)
    stand_up_instance.stand_up()
    stand_up_instance.start_head_movement()

def set_up_robot_speaking():
    global robot_speak_instance
    robot_speak_instance = RobotSpeak("robot_speak_instance", nao_ip, nao_port)

def learn_face_code():
    global face_detection_instance
    global names_of_employees
    face_detection_instance = FaceRecognition("face_detection_instance", nao_ip, nao_port)
    face_detection_instance.clear_face_database()
    done_vocab = ["Done"]
    global done_recognition_instance
    done_recognition_instance = WordRecognizer("done_recognition_instance", nao_ip, nao_port)
    global name_recognition_instance
    name_recognition_instance = WordRecognizer("name_recognition_instance", nao_ip, nao_port)
    for i in range(len(names_of_employees)):
        done_recognition_instance.start_listening_for_words(done_vocab)

        try:
            robot_speak_instance.say_words("Please present a new face for me to learn")
            while True:
                if done_recognition_instance.recognized_a_word:
                    done_recognition_instance.recognized_a_word = False
                    done_recognition_instance.stop_listening_for_words()
                    break
            face_detection_instance.start_looking_for_face()
            while True:
                time.sleep(1)
                if face_detection_instance.face_detected: 
                    print("there is a face")
                    break
        except KeyboardInterrupt:
            print("Interrupted by user, shutting down")
            done_recognition_instance.stop_listening_for_words()
            MyBroker.shutdown()
            sys.exit(0)

        name_recognition_instance.start_listening_for_words(names_of_employees)
        robot_speak_instance.say_words("What is your name?")

        try:
            while True:
                time.sleep(1)
                if name_recognition_instance.recognized_a_word:
                    name_recognition_instance.recognized_a_word = False
                    break
        except KeyboardInterrupt:
            print("Interrupted by user, shutting down")
            name_recognition_instance.stop_listening_for_words()
            MyBroker.shutdown()
            sys.exit(0)
        
        name_recognition_instance.stop_listening_for_words()
        face_detection_instance.learn_face(name_recognition_instance.matched_word)
        face_detection_instance.retrieve_learned_faces()
        robot_speak_instance.say_words("I learned the face of" + str(face_detection_instance.learned_faces))

def look_for_faces_code():
    global look_for_face_instance 
    if look_for_face_instance:
        pass
    else:
        look_for_face_instance = FaceRecognition("look_for_face_instance", nao_ip, nao_port)
    
    look_for_face_instance.start_looking_for_face()

    try:
        while True:
            time.sleep(1)
            if look_for_face_instance.face_detected:
                look_for_face_instance.stop_looking_for_face()
                break
    except KeyboardInterrupt:
        print("Interrupted by user, shutting down")
        look_for_face_instance.stop_looking_for_face()
        MyBroker.shutdown()
        sys.exit(0)

    time.sleep(1)
    global name_talking_to
    if look_for_face_instance.face_recognized and look_for_face_instance.recognized_name:
        robot_speak_instance.say_words("Hello " + look_for_face_instance.recognized_name)
        name_talking_to = look_for_face_instance.recognized_name
    else:
        robot_speak_instance.say_words("Hello, why are you visiting the office?")
        name_talking_to = "Visitor"


def scan_environment_functionality():
    global scan_handler_instance
    scan_handler_instance = MotionHandler("scan_handler_instance", nao_ip, nao_port)

    ################# Move head to the left #################
    scan_handler_instance.motionProxy.setAngles("HeadYaw", 0, .5)
    scan_handler_instance.motionProxy.setAngles("HeadYaw", 1, .05)

    global landmark_detection_instance
    landmark_detection_instance = LandmarkHandler("landmark_detection_instance", nao_ip, nao_port)
    landmark_detection_instance.initialize_landmark_handler()
    try:
        while True:
            if landmark_detection_instance.landmark_location_angle > 0 and landmark_detection_instance.landmark_location_angle < 1:
                global left_landmark_location
                left_landmark_location = landmark_detection_instance.landmark_location_angle + .15
                scan_handler_instance.motionProxy.killMove()
                scan_handler_instance.motionProxy.setAngles("HeadYaw", left_landmark_location, .5)
                break
            elif landmark_detection_instance.motion_instance.motionProxy.getAngles("HeadYaw", True)[0] > .9:
                print("motion Finished")
                break
    except KeyboardInterrupt:
        print("Interrupted by user, shutting down")
        MyBroker.shutdown()
        sys.exit(0)

    time.sleep(1)
    scan_handler_instance.motionProxy.setAngles("HeadYaw", 0, .5)
    time.sleep(2)

    ################# Move head to the Right #################
    scan_handler_instance.motionProxy.setAngles("HeadYaw", -1, .05)

    landmark_detection_instance.initialize_landmark_handler()
    try:
        while True:
            if landmark_detection_instance.landmark_location_angle < 0 and landmark_detection_instance.landmark_location_angle > -1:
                global right_landmark_location
                right_landmark_location = landmark_detection_instance.landmark_location_angle - .15
                scan_handler_instance.motionProxy.killMove()
                scan_handler_instance.motionProxy.setAngles("HeadYaw", right_landmark_location, .5)
                break
            elif landmark_detection_instance.motion_instance.motionProxy.getAngles("HeadYaw", True)[0] < -.9:
                print("motion Finished")
                break
    except KeyboardInterrupt:
        print("Interrupted by user, shutting down")
        MyBroker.shutdown()
        sys.exit(0)

    scan_handler_instance.motionProxy.setAngles("HeadYaw", 0, .5)


    if left_landmark_location:
        robot_speak_instance.say_words("There is the phone")
        scan_handler_instance.motionProxy.setAngles("HeadYaw", left_landmark_location, .5)
        time.sleep(1)
    else:
        robot_speak_instance.say_words("I could not find the phone")
    if right_landmark_location:
        robot_speak_instance.say_words("There are the passes")
        scan_handler_instance.motionProxy.setAngles("HeadYaw", right_landmark_location, .5)
    else:
        robot_speak_instance.say_words("I could not find the passes")

    time.sleep(2)
    scan_handler_instance.motionProxy.setAngles("HeadYaw", 0, .5)


def point_to_location_code(location_angle, arm):
    global point_to_instance 
    global point_head_instance 
    if point_to_instance:
        pass
    else:
        point_to_instance = TrackerHandler("point_to_instance", nao_ip, nao_port)
    if point_head_instance:
        pass
    else:
        point_head_instance = MotionHandler("point_head_instance", nao_ip, nao_port)

    distance = 1.0  # meters
    yaw_angle = location_angle  # Convert 30 degrees to radians
    pitch_angle = 0  # Convert 15 degrees to radians

    # Calculate target position in robot's frame
    target_x = distance * math.cos(pitch_angle) * math.cos(yaw_angle)
    target_y = distance * math.cos(pitch_angle) * math.sin(yaw_angle)
    target_z = distance * math.sin(pitch_angle)

    target_position = [target_x, target_y, target_z]
    point_speed = 0.2

    point_head_instance.motionProxy.setAngles("HeadYaw", location_angle, point_speed)
    point_to_instance.trackerProxy.pointAt(arm, target_position, point_speed)


if __name__ == "__main__":
    main()
