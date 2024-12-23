import cv2
import numpy as np
from naoqi import ALProxy
import requests

# NAO Configuration
ROBOT_IP = "192.168.1.10"  # Replace with your NAO robot's IP
ROBOT_PORT = 9559
RESOLUTION = 2  # 640x480 resolution
FRAME_RATE = 30
PYTHON3_API_URL = "http://127.0.0.1:5000/recognize"  # Python 3 Flask API URL

# def stream_frames_and_recognize():
#     """
#     Stream frames from NAO's camera and send to Python 3 API for recognition.
#     """
#     video_proxy = ALProxy("ALVideoDevice", ROBOT_IP, ROBOT_PORT)
#     video_client = video_proxy.subscribeCamera(
#         "python_client", 0, RESOLUTION, 11, FRAME_RATE
#     )

#     try:
#         print("Streaming frames to Python 3 API for recognition... Press 'Ctrl+C' to stop.")
#         while True:
#             frame_data = video_proxy.getImageRemote(video_client)
#             if frame_data is None:
#                 continue

#             # Extract image properties
#             width = frame_data[0]
#             height = frame_data[1]
#             array = frame_data[6]
#             frame = np.frombuffer(array, dtype=np.uint8).reshape((height, width, 3))

#             # Convert to JPEG for transmission
#             _, encoded_frame = cv2.imencode(".jpg", frame)
#             response = requests.post(PYTHON3_API_URL, files={"frame": encoded_frame.tobytes()})

#             if response.status_code == 200:
#                 result = response.json()
#                 recognized_faces = result.get("recognized_faces", [])
#                 handle_recognition_results(recognized_faces)
#             else:
#                 print("Error in recognition response:", response.text)

#     except Exception as e:
#         print("Error during frame streaming:", e)

#     finally:
#         video_proxy.unsubscribe(video_client)

def stream_frames_and_recognize():
    video_proxy = ALProxy("ALVideoDevice", ROBOT_IP, ROBOT_PORT)
    video_client = video_proxy.subscribeCamera(
        "python_client", 0, RESOLUTION, 11, FRAME_RATE
    )

    try:
        print("Streaming frames to Python 3 API... Press 'q' to exit.")
        while True:
            frame_data = video_proxy.getImageRemote(video_client)
            if frame_data is None:
                continue

            # Extract and process the frame
            width = frame_data[0]
            height = frame_data[1]
            array = frame_data[6]
            frame = np.frombuffer(array, dtype=np.uint8).reshape((height, width, 3))

            # Send frame to Flask API
            _, encoded_frame = cv2.imencode(".jpg", frame)
            response = requests.post(PYTHON3_API_URL, files={"frame": encoded_frame.tobytes()})

            if response.status_code == 200:
                recognized_faces = response.json().get("faces", [])
                for face in recognized_faces:
                    name = face["name"]
                    top, right, bottom, left = face["location"]

                    # Draw rectangle and label
                    cv2.rectangle(frame, (left, top), (right, bottom), (255, 0, 0), 2)
                    cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

                # Robot interaction
                handle_recognition_results([face["name"] for face in recognized_faces])
            else:
                print("Error in recognition response:", response.text)

            # Display the frame
            cv2.imshow("NAO Camera - Facial Recognition", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except Exception as e:
        print("Error during frame streaming:", e)

    finally:
        video_proxy.unsubscribe(video_client)
        cv2.destroyAllWindows()


def handle_recognition_results(results):
    """
    Process recognition results and interact with the user.
    """
    tts = ALProxy("ALTextToSpeech", ROBOT_IP, ROBOT_PORT)
    if "Unknown" in results:
        tts.say("Hello! I don't recognize you. Would you like to register?")
    else:
        for name in results:
            tts.say("Hello, {}! Welcome back.".format(name))

if __name__ == "__main__":
    stream_frames_and_recognize()
