from naoqi import ALProxy
import cv2
import numpy as np

ROBOT_IP = "192.168.1.10"  # Replace with your NAO robot's IP
ROBOT_PORT = 9559

def show_camera_feed():
    video_proxy = ALProxy("ALVideoDevice", ROBOT_IP, ROBOT_PORT)
    resolution = 2    # VGA
    color_space = 11  # RGB

    capture_device = video_proxy.subscribe("camera_feed", resolution, color_space, 30)

    try:
        while True:
            nao_image = video_proxy.getImageRemote(capture_device)
            if nao_image is None:
                continue

            image_width = nao_image[0]
            image_height = nao_image[1]
            array = nao_image[6]

            image = np.frombuffer(array, dtype=np.uint8).reshape((image_height, image_width, 3))
            cv2.imshow("NAO Camera Feed", image)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        video_proxy.unsubscribe(capture_device)
        cv2.destroyAllWindows()

if __name__ == "__main__":
    show_camera_feed()