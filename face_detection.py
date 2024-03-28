from naoqi import ALProxy, ALBroker, ALModule
import time

class FaceRecognition(ALModule):
    def __init__(self, name, ip, port):
        ALModule.__init__(self, name)
        print(" ------ FaceRecognition __init__")
        self.name = name
        self.ip = ip
        self.port = port
        self.face_detection = ALProxy("ALFaceDetection", self.ip, self.port)
        self.memoryProxy = ALProxy("ALMemory", self.ip, self.port)
    
    def start_looking_for_face(self):
        self.face_recognized = False
        self.face_detected = False
        self.recognized_name = None
        self.face_detection.setTrackingEnabled(True)
        self.face_detection.subscribe(self.name, 100, 0.0)  # Adjust parameters as needed
        print(self.face_detection.isRecognitionEnabled())
        self.face_detection.setRecognitionEnabled(True)
        self.memoryProxy.subscribeToEvent("FaceDetected", self.name, "onFaceDetected")

        print(" ------ start_looking_for_face")

    def stop_looking_for_face(self):
        print(" ------ stop_looking_for_face")
        self.face_detection.unsubscribe(self.name)
        self.face_detection.setTrackingEnabled(False)

    def clear_face_database(self):
        print(" ------ clear_face_database")
        self.face_detection.clearDatabase()


    def learn_face(self, person_name):
        print(" ------ learn_face")
        self.face_detection.setRecognitionEnabled(True)
        
        try:
            while True:
                time.sleep(1)
                learned_face_successfully = self.face_detection.learnFace(person_name)
                if learned_face_successfully:
                    print("learned face successfully")
                    self.face_detection.setRecognitionEnabled(False)
                    break
                else:
                    print("could not learn face")
                    self.face_detection.setRecognitionEnabled(False)
                    break
        except KeyboardInterrupt:
            print("Interrupted by user, returning to main loop")
            self.face_detection.setRecognitionEnabled(False)

    def retrieve_learned_faces(self):
        print(" ------ retrieve_learned_faces")
        self.learned_faces = self.face_detection.getLearnedFacesList()
        print("Learned faces:", self.learned_faces)

    def onFaceDetected(self, key, value, subscriber_id):
        print("--------- onFaceDetected")
        # detected_faces = self.memoryProxy.getData("FaceDetected")
        # if detected_faces and detected_faces[1]:  # Adjust based on the structure
        #     self.face_detected = True
        #     print("I see a face")
        self.memoryProxy.unsubscribeToEvent("FaceDetected", self.name)
        self.face_detected = True
        
        if value and len(value) > 1:
            detected_faces_info = value[1]
            for face_info in detected_faces_info:
                face_id = face_info[0]  # The ID of the detected face
                face_label_info = face_info[1]  # Information including the label (name) if recognized
                if face_label_info and len(face_label_info) > 1:
                    self.recognized_name = face_label_info[2]
                    print("Recognized face name: " + str(self.recognized_name))
                    self.face_recognized = True
        else:
            print("No recognizable face detected.")
            self.face_recognized = False

