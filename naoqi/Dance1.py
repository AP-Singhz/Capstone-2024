from naoqi import ALProxy
import time

ROBOT_IP = "172.20.10.6"  # Update the robot's IP address
PORT = 9559

# Initialize proxies
motion = ALProxy("ALMotion", ROBOT_IP, PORT)
posture = ALProxy("ALRobotPosture", ROBOT_IP, PORT)
audio = ALProxy("ALAudioPlayer", ROBOT_IP, PORT)

# Define the path to the audio file
AUDIO_FILE_PATH = "/home/nao/audio/dance1.mp3"  # Replace with the actual path on NAO

motion.wakeUp()
posture.goToPosture("StandInit", 0.5)

# Function to set joint angles
def set_joint_angles(joint_names, angles, duration):
    motion.angleInterpolation(joint_names, angles, [duration] * len(joint_names), True)

# Boogie dance function
def boogie():
    # Play the audio file
    file_id = audio.post.playFile(AUDIO_FILE_PATH)

    for _ in range(6):  # Repeat 6 times
        set_joint_angles(
            ["RShoulderPitch", "LShoulderPitch", "HeadYaw"],
            [-0.5, 1.0, -0.3],  # Raise right arm, lower left arm, head tilts left
            0.5
        )
        time.sleep(0.5)

        set_joint_angles(
            ["RShoulderPitch", "LShoulderPitch", "HeadYaw"],
            [1.0, -0.5, 0.3],  # Lower right arm, raise left arm, head tilts right
            0.5
        )
        time.sleep(0.5)

        set_joint_angles(
            ["HeadPitch"],
            [-0.2],  # Head nod forward
            0.5
        )
        time.sleep(0.5)

        set_joint_angles(
            ["HeadPitch"],
            [0.0],  # Head back to neutral
            0.5
        )
        time.sleep(0.5)

    # Wait for the audio file to finish (optional)
    audio.wait(file_id, 0)

# Execute the dance routine
try:
    boogie()
finally:
    posture.goToPosture("Crouch", 0.5)
    motion.rest()
