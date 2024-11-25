import cv2
import numpy as np
import pymongo
import base64
from naoqi import ALProxy
import time
import datetime

NAO_IP = "172.20.10.6"

try:
    client = pymongo.MongoClient("mongodb+srv://rrsarker:<bizpoints>@cluster0.lcc7etx.mongodb.net/")
    print("Connected to MongoDB Atlas successfully!")
    db = client["nao_faces_db"]
    collection = db["faces"]
except Exception as e:
    print("Could not connect to MongoDB Atlas: {}".format(str(e)))
    exit(1)

video_proxy = ALProxy("ALVideoDevice", NAO_IP, 9559)
tts_proxy = ALProxy("ALTextToSpeech", NAO_IP, 9559)
asr_proxy = ALProxy("ALSpeechRecognition", NAO_IP, 9559)

resolution = 2
colorSpace = 20
fps = 30
camera_name = video_proxy.subscribe("python_cv_camera", resolution, colorSpace, fps)

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter('nao_camera_feed.mp4', fourcc, 20.0, (640, 480))

def encode_face_image(image):
    try:
        _, encoded_image = cv2.imencode('.jpg', image)
        return base64.b64encode(encoded_image.tobytes()).decode('utf-8')
    except Exception as e:
        print("Error encoding face image: {}".format(str(e)))
        return None

def is_face_in_db(face_encoding):
    try:
        result = collection.find_one({"encoding": face_encoding})
        return bool(result)
    except Exception as e:
        print("Error checking face in database: {}".format(str(e)))
        return False

def store_face_in_db(name, face_image):
    try:
        encoded_image = encode_face_image(face_image)
        if encoded_image is None:
            return
            
        face_encoding = base64.b64encode(face_image.tobytes()).decode('utf-8')
        user_data = {
            "name": name,
            "face_image": encoded_image,
            "encoding": face_encoding,
            "timestamp": datetime.datetime.now()
        }
        result = collection.insert_one(user_data)
        print("Stored face in database with ID: {}".format(result.inserted_id))
    except Exception as e:
        print("Error storing face in database: {}".format(str(e)))

def get_user_name():
    try:
        tts_proxy.say("What is your name?")
        
        asr_proxy.setLanguage("English")
        asr_proxy.subscribe("name_recognition")
        
        response = None
        attempts = 0
        max_attempts = 3
        
        while response is None and attempts < max_attempts:
            result = asr_proxy.getResult()
            if result and result[0]:
                response = result[0][0]
            attempts += 1
            time.sleep(1)
        
        asr_proxy.unsubscribe("name_recognition")
        
        return response
    except Exception as e:
        print("Error getting user name: {}".format(str(e)))
        return None

try:
    while True:
        image = video_proxy.getImageRemote(camera_name)
        if not image:
            print("Failed to get image from NAO")
            continue
            
        width = image[0]
        height = image[1]
        array = np.frombuffer(image[6], dtype=np.uint8).reshape(height, width, 2)
        
        rgb_image = cv2.cvtColor(array, cv2.COLOR_YUV2BGR_YUYV)
        resized = cv2.resize(rgb_image, (640, 480), interpolation=cv2.INTER_AREA)
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        for (x, y, w, h) in faces:
            cv2.rectangle(resized, (x, y), (x + w, y + h), (0, 255, 0), 2)

            face_image = resized[y:y + h, x:x + w]
            face_encoding = base64.b64encode(face_image.tobytes()).decode('utf-8')

            if not is_face_in_db(face_encoding):
                name = get_user_name()
                if name:
                    store_face_in_db(name, face_image)
                    tts_proxy.say("Hello, {}! Nice to meet you.".format(name))
                else:
                    tts_proxy.say("Sorry, I couldn't hear your name.")
            else:
                stored_face = collection.find_one({"encoding": face_encoding})
                if stored_face:
                    tts_proxy.say("Welcome back, {}!".format(stored_face['name']))

        cv2.imshow("Nao Camera Feed", resized)
        out.write(resized)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except Exception as e:
    print("An error occurred: {}".format(str(e)))

finally:
    video_proxy.unsubscribe(camera_name)
    out.release()
    cv2.destroyAllWindows()
    client.close()