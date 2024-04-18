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
robot_move_instance = None
face_detection_instance = None
look_for_face_instance = None
words1_recognition_instance  = None
scan_handler_instance = None
landmark_detection_instance = None
robot_move_instance = None

nao_ip = "192.168.1.53"
nao_port = 9559
MyBroker = None

next_state = None

left_landmark_location = None
right_landmark_location = None

name_talking_to = None

names_of_employees = ["Eli"] #, "Ziyi", "Silas"]
yes_or_no = ["yes", "no"]

hello_words = ["hello"]

guest_possible_questions = [
"business hours",
"restroom",
"Wi-Fi password",
"mechanical engineering department",
"where can I park",
"restaurants or hotels",
"professor availability",
"appointment with admissions services",
"application process",
"services offered by UVA School of Engineering",
"promotions or discounts",
"upcoming events",
"professor's email",
"event today",
"emergency procedures",
"nearest emergency exits",
"Chinese language assistance",
"other languages",
# "Time",
"where is the phone",
"visitor passes"
]

responses_to_guests = {
"business hours": "Our business hours today is twelve thirty PM to two PM.",
"restroom": "The restroom is located down the hall to your left, next to the elevators.",
"Wi-Fi password": "Yes, we provide complimentary Wi-Fi access. Please use UVA Guest Wifi.",
"mechanical engineering department": "The marketing department is located in the mechanical engineering building. The mechanical engineering building is further down Engineers Way. Take a left when exiting Rice Hall.",
"where can I park": "The closest visitor parking is available in the lot next to the football stadium.",
"restaurants or hotels": "Yes, there are several restaurants within walking distance. I recommend you try restaurants on the Corner, near the Rotunda.",
"professor availability": "Yes, he should be walking around the room.",
"appointment with admissions services": "Of course. Please see the UVA Engineering School website for more information.",
"application process": "You can apply to be an undergraduate student here between 1 August and 31 October through the Common Application, an online college application service.",
"services offered by UVA School of Engineering": "UVA School of Engineering is a center for undergraduate and graduate education as well as high-class education.",
"promotions or discounts": "No.",
"upcoming events": "For the most up-to-date information, please visit the UVA Engineering School website as well as one of the information booths regarding todays event.",
"professor's email": "Professor Iqbals email address is tiqbal@virginia.edu.",
"event today": "Yes, today is the UVA School of Engineering open house.",
"emergency procedures": "In case of an emergency, please evacuate the building immediately using the nearest exit and assemble at the designated meeting point in the parking lot.",
"nearest emergency exits": "The nearest emergency exits are located towards the long side of the room. We also have exit signs posted throughout the building for your convenience.",
"Chinese language assistance": "Ni hao. Yes, we have staff members who speak Chinese. Would you like me to find someone to assist you?",
"other languages": "No, I am sorry, just English.",
# "Time": "The current time is " + datetime.now().time().strftime("%I:%M %p"),
"where is the phone": "The phone is right here, one of my assistants can direct a call after our conversation",
"visitor passes": "the visitor passes are right here, please fill one out"}

employee_possible_questions = ["going home",
                               "lunch",
                               "Have you seen Ziyi",
                               "Have you seen Silas",
                               "Have you seen Eli",
                               "I will be leaving",
                               ]

employee_responses_to_question = {"going home" : "Okay, see you tomorrow",
                                  "lunch" : "We are providing lunch today at 11",
                                 "Have you seen Ziyi" : "I saw Ziyi earlier, he should be around here somewhere",
                                 "Have you seen Silas" : "I saw Silas earlier, he should be around here somewhere",
                                 "Have you seen Eli" : "I saw Eli earlier, he should be around here somewhere",
                                 "I will be leaving": "Okay, see you later!",
                                }

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
        self.states = ['initialize', 'idle', 'conversation',]
        self.transitions = {
            'initialize': {'idle' : 'idle'},
            'idle': {'conversation' : 'conversation',
                     'idle' : 'idle'},
            'conversation': {'idle' : 'idle'}
        }
        self.current_state = 'initialize'
        self.transition_needed = False
    
    def transition(self):
        print("Transitioning from " +str(self.current_state) + " to " + str(self.transitions[self.current_state][next_state]))
        self.current_state = self.transitions[self.current_state][next_state]
        self.transition_needed = False


    def currentState(self):
        print("The current state is " + str(self.current_state))
        if self.current_state == 'initialize':
            set_up_experiment()
            self.transition_needed = True
        elif self.current_state == 'idle':
            wait_for_person_or_phone()
            self.transition_needed = True
        elif self.current_state == 'conversation':
            conversation_handler()
            self.transition_needed = True


def wait_for_person_or_phone():
    robot_move_instance.movesProxy.setExpressiveListeningEnabled(False)
    robot_move_instance.motionProxy.setAngles("HeadPitch", -0.4, .4)
    robot_move_instance.motionProxy.setAngles("HeadYaw", 0, .4)
    robot_move_instance.lifeProxy.setState("solitary")

    time.sleep(5)

    look_for_faces_code(30)
    global next_state
    if look_for_face_instance.face_detected:
        # robot_move_instance.lifeProxy.setState("disabled")
        next_state = "conversation"
    else:
        next_state = 'idle'
        scan_environment_functionality()


    
def conversation_handler():
    ############################# DIALOGUE HERE ##############################
    robot_move_instance.movesProxy.setExpressiveListeningEnabled(True)
    greet_person_code()
    if name_talking_to == "Visitor":
        robot_speak_instance.say_words("What is the reason for your visit?")
        guest_conversation()
    elif name_talking_to:
        robot_speak_instance.say_words("What can I help you with?")
        employee_conversation()
    time.sleep(3)
    global next_state
    next_state = "idle"

def employee_conversation():
    listen_for_words(employee_possible_questions, 20)
    if words1_recognition_instance.recognized_a_word:
        pass
    else:
        robot_speak_instance.say_words("If you need any more help, please come back in about 30 seconds")
        return
    
    robot_speak_instance.say_words(employee_responses_to_question[words1_recognition_instance.matched_word])

    look_for_faces_code(5)
    if look_for_face_instance.face_detected:
        # robot_speak_instance.say_words("Is there anything else you need?")
        employee_conversation()
    else:
        robot_speak_instance.say_words("okay, see you later.")
        return

def guest_conversation():
    listen_for_words(guest_possible_questions, 5)
    if words1_recognition_instance.recognized_a_word:
        pass
    else:
        counter = 0
        while counter < 2:
            robot_speak_instance.say_words("I could not understand, can you please repeat?")
            listen_for_words(guest_possible_questions, 10)
            if words1_recognition_instance.recognized_a_word:
                break
            
            look_for_faces_code(5)
            if look_for_face_instance.face_detected:
                counter += 1
            else:
                counter = 2
        if counter >= 2:
                robot_speak_instance.say_words("I'm sorry I could not help you, if you need any more assistance please come back in about 30 seconds")
                return
    robot_speak_instance.say_words(responses_to_guests[words1_recognition_instance.matched_word])
    if words1_recognition_instance.matched_word == "phone":
        point_to_phone()
    elif words1_recognition_instance.matched_word == "visitor passes":
        point_to_passes()

    # time.sleep(1)

    look_for_faces_code(5)
    if look_for_face_instance.face_detected:
        robot_speak_instance.say_words("Is there anything else you need?")
        guest_conversation()
    else:
        robot_speak_instance.say_words("See you later, have a good day.")
        return
    


def listen_for_words(words_to_listen_for, timeout):
    global words1_recognition_instance 
    if words1_recognition_instance:
        pass
    else:
        words1_recognition_instance = WordRecognizer("words1_recognition_instance", nao_ip, nao_port)
    words1_recognition_instance.start_listening_for_words(words_to_listen_for)

    start_time = time.time()

    try:
        while True:
            if words1_recognition_instance.recognized_a_word:
                words1_recognition_instance.stop_listening_for_words()
                break
            if (time.time() - start_time) > timeout:
                words1_recognition_instance.stop_listening_for_words()
                break
    except KeyboardInterrupt:
        print("Interrupted by user, shutting down")
        words1_recognition_instance.stop_listening_for_words()
        MyBroker.shutdown()
        sys.exit(0)




def point_to_phone():
    if left_landmark_location:
        point_to_location_code(left_landmark_location, "LArm")
        time.sleep(1)

def point_to_passes():
    if right_landmark_location:
        point_to_location_code(right_landmark_location, "RArm")
        time.sleep(1)

def set_up_experiment():
    robot_stand_up()
    time.sleep(1)
    set_up_robot_speaking()
    robot_move_instance.motionProxy.setAngles("HeadYaw", 0, 0.4)
    time.sleep(1)
    robot_move_instance.motionProxy.setAngles("HeadPitch", -.8, 0.4)
    time.sleep(1)
    learn_face_code()
    scan_environment_functionality()
    while (left_landmark_location == None or right_landmark_location == None):
        scan_environment_functionality()
    global next_state
    next_state = "idle"

def robot_stand_up():
    global robot_move_instance
    if robot_move_instance:
        pass
    else:
        robot_move_instance = MotionHandler("robot_move_instance", nao_ip, nao_port)

    if str(robot_move_instance.lifeProxy.getState()) == "disabled":
        pass
    else:
        robot_move_instance.lifeProxy.setState("disabled")
    print("Autonomous mode: "+str(robot_move_instance.lifeProxy.getState()))
    robot_move_instance.stand_up()
    robot_move_instance.start_head_movement()





def set_up_robot_speaking():
    global robot_speak_instance
    robot_speak_instance = RobotSpeak("robot_speak_instance", nao_ip, nao_port)

def learn_face_code():
    global face_detection_instance
    global names_of_employees
    face_detection_instance = FaceRecognition("face_detection_instance", nao_ip, nao_port)
    face_detection_instance.clear_face_database()
    # done_vocab = ["Done"]
    # global done_recognition_instance
    # done_recognition_instance = WordRecognizer("done_recognition_instance", nao_ip, nao_port)
    global name_recognition_instance
    name_recognition_instance = WordRecognizer("name_recognition_instance", nao_ip, nao_port)
    for i in range(len(names_of_employees)):
        # done_recognition_instance.start_listening_for_words(done_vocab)

        try:
            robot_speak_instance.say_words("Please present a new face for me to learn")
            time.sleep(1)
            face_detection_instance.start_looking_for_face()
            while True:
                time.sleep(1)
                if face_detection_instance.face_detected: 
                    print("there is a face")
                    break
        except KeyboardInterrupt:
            print("Interrupted by user, shutting down")
            # done_recognition_instance.stop_listening_for_words()
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

def look_for_faces_code(timeout):
    global look_for_face_instance 
    if look_for_face_instance:
        pass
    else:
        look_for_face_instance = FaceRecognition("look_for_face_instance", nao_ip, nao_port)
    
    start_time = time.time()
    
    look_for_face_instance.start_looking_for_face()

    try:
        while True:
            time.sleep(1)
            if look_for_face_instance.face_detected:
                look_for_face_instance.stop_looking_for_face()
                break
            if (time.time() - start_time) > timeout:
                # robot_speak_instance.say_words("I have timed out of the loop")
                break
    except KeyboardInterrupt:
        print("Interrupted by user, shutting down")
        look_for_face_instance.stop_looking_for_face()
        MyBroker.shutdown()
        sys.exit(0)

    time.sleep(1)

def greet_person_code():
    global name_talking_to
    if look_for_face_instance.face_recognized and look_for_face_instance.recognized_name:
        robot_speak_instance.say_words("Hello " + look_for_face_instance.recognized_name)
        name_talking_to = look_for_face_instance.recognized_name
    else:
        robot_speak_instance.say_words("Hello")
        name_talking_to = "Visitor"


def scan_environment_functionality():
    global scan_handler_instance
    if scan_handler_instance:
        pass
    else:
        scan_handler_instance = MotionHandler("scan_handler_instance", nao_ip, nao_port)
    
    global landmark_detection_instance
    if landmark_detection_instance:
        pass
    else:
        landmark_detection_instance = LandmarkHandler("landmark_detection_instance", nao_ip, nao_port)


    ################# Move head to the left #################
    time.sleep(1)
    scan_handler_instance.motionProxy.setAngles("HeadYaw", 0, .5)
    time.sleep(1)
    scan_handler_instance.motionProxy.setAngles("HeadPitch", .35, .3)
    time.sleep(1)
    scan_handler_instance.motionProxy.setAngles("HeadYaw", 1, .05)

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
    time.sleep(1)

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
        point_to_phone()
    else:
        robot_speak_instance.say_words("I could not find the phone")
    
    robot_move_instance.motionProxy.setAngles("HeadYaw", 0, 0.4)
    time.sleep(1)

    if right_landmark_location:
        robot_speak_instance.say_words("There are the passes")
        point_to_passes()
    else:
        robot_speak_instance.say_words("I could not find the passes")

    time.sleep(1)
    scan_handler_instance.motionProxy.setAngles("HeadYaw", 0, .5)
    time.sleep(1)



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
    point_speed = 0.3

    point_head_instance.motionProxy.setAngles("HeadYaw", location_angle, point_speed)
    point_head_instance.motionProxy.setAngles("HeadPitch", 0.4, 0.4)
    point_to_instance.trackerProxy.pointAt(arm, target_position, point_speed)

    robot_move_instance.stand_up()


if __name__ == "__main__":
    main()