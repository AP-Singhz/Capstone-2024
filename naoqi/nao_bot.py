import cv2
import numpy as np
from naoqi import ALProxy

NAO_IP = "172.20.10.6"

video_proxy = ALProxy("ALVideoDevice", NAO_IP, 9559)

resolution = 2
colorSpace = 20
fps = 30
camera_name = video_proxy.subscribe("python_cv_camera", resolution, colorSpace, fps)

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter('nao_camera_feed.mp4', fourcc, 20.0, (640, 480))

tts_proxy = ALProxy("ALTextToSpeech", NAO_IP, 9559)

while True:

    image = video_proxy.getImageRemote(camera_name)
    width = image[0]
    height = image[1]
    array = np.frombuffer(image[6], dtype=np.uint8).reshape(height, width, 2)

    rgb_image = cv2.cvtColor(array, cv2.COLOR_YUV2BGR_YUYV)

    resized = cv2.resize(rgb_image, (640, 480), interpolation=cv2.INTER_AREA)

    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

    for (x, y, w, h) in faces:
        cv2.rectangle(resized, (x, y), (x + w, y + h), (0, 255, 0), 2)

    cv2.imshow("Nao Camera Feed", resized)

    out.write(resized)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

video_proxy.unsubscribe(camera_name)
out.release()
cv2.destroyAllWindows()