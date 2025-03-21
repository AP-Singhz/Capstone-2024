#!/usr/bin/env python3

import random                           # For NAO’s random choice
import time                             # For pauses between speech/motions
import cv2                              # OpenCV for image capture & processing
import numpy as np                      # Numeric operations on image arrays
from naoqi import ALProxy               # NAOqi API proxy to control NAO

# ——— Configure NAO’s network address ———
ROBOT_IP = "172.20.10.6"                # Replace with your robot’s IP
PORT     = 9559                         # Default NAOqi port

# Create proxies to NAO services
motion = ALProxy("ALMotion", ROBOT_IP, PORT)            # Movement
tts    = ALProxy("ALTextToSpeech", ROBOT_IP, PORT)      # Speech
video  = ALProxy("ALVideoDevice", ROBOT_IP, PORT)       # Camera

def detect_gesture(frame):
    """Analyze a BGR image and return 'rock', 'paper', or 'scissors'."""
    blur = cv2.GaussianBlur(frame, (7,7), 0)             # Smooth image
    hsv = cv2.cvtColor(blur, cv2.COLOR_BGR2HSV)           # Convert to HSV for skin detection
    mask = cv2.inRange(hsv, np.array([0,30,60]), np.array([20,150,255]))  # Skin color threshold
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, None, iterations=2)     # Clean noise

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)  
    if not contours or cv2.contourArea(max(contours, key=cv2.contourArea)) < 2000:
        return None                                       # No valid hand detected

    cnt = max(contours, key=cv2.contourArea)             # Largest contour = hand
    hull = cv2.convexHull(cnt, returnPoints=False)       
    defects = cv2.convexityDefects(cnt, hull)            # Finger gaps
    fingers = 0 if defects is None else sum(
        1 for i in range(defects.shape[0]) if defects[i,0,3] > 10000
    )

    if fingers >= 3:
        return "paper"
    if fingers >= 1:
        return "scissors"
    return "rock"

def capture_user_choice(timeout=5):
    """Stream from NAO camera for up to `timeout` seconds, return detected gesture."""
    cam = video.subscribe("rpsCam", 2, 13, 30)           # Subscribe at VGA resolution, RGB, 30FPS
    start = time.time()
    choice = None

    while time.time() - start < timeout:                 # Loop until timeout
        img = video.getImageRemote(cam)                  # Grab one frame
        if img:
            frame = np.frombuffer(img[6], dtype=np.uint8).reshape((img[1], img[0], 3))
            choice = detect_gesture(frame)               # Detect gesture
            cv2.imshow("Show your gesture", frame)       # Display for debugging
            if choice:
                break                                   # Stop once gesture recognized
            cv2.waitKey(1)

    video.unsubscribe(cam)                               # Stop camera streaming
    cv2.destroyAllWindows()                              # Close display window
    return choice

def show_nao_choice(choice):
    """Move NAO’s hands into rock, paper, or scissors pose."""
    if choice == "rock":
        motion.closeHand("RHand"); motion.closeHand("LHand")
    elif choice == "paper":
        motion.openHand("RHand"); motion.openHand("LHand")
    else:  # scissors
        motion.openHand("RHand"); motion.openHand("LHand")
        motion.setAngles(["RShoulderRoll","LShoulderRoll"], [-0.5,0.5], 0.2)
    motion.waitUntilMoveIsFinished()                      # Wait until motion completes

def decide_winner(nao, user):
    """Return result string based on NAO vs user gesture."""
    if nao == user:
        return "It's a tie!"
    wins = {"rock":"scissors", "scissors":"paper", "paper":"rock"}
    return "NAO wins!" if wins[nao] == user else "You win!"

def play_round():
    """Perform one round: countdown, capture user, show NAO, announce winner."""
    motion.setStiffnesses("Body", 1.0)                    # Enable motors
    motion.closeHand("RHand"); motion.closeHand("LHand") # Start with fists
    motion.waitUntilMoveIsFinished()

    for word in ("Rock","Paper","Scissors"):
        tts.say(word)                                     # Speak countdown
        motion.setAngles(["LShoulderPitch","RShoulderPitch"], [0.3,0.3], 0.3)
        time.sleep(0.6)

    tts.say("Shoot")                                      # Reveal cue
    user_choice = capture_user_choice()                   # Detect user gesture
    nao_choice = random.choice(["rock","paper","scissors"])
    show_nao_choice(nao_choice)                           # Reveal NAO gesture

    if user_choice:
        tts.say(f"You showed {user_choice}. {decide_winner(nao_choice,user_choice)}")
    else:
        tts.say("I couldn't see your gesture.")

def main():
    """Loop rounds until user types 'no'."""
    while True:
        play_round()
        if input("Play again? (yes/no): ").strip().lower() != "yes":
            motion.rest()                                 # Return to rest pose
            break

if __name__ == "__main__":
    main()
