#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import random
import time
import cv2
import numpy as np
from naoqi import ALProxy

# NAO Robot IP and Port
ROBOT_IP = "172.20.10.6"
PORT = 9559

# NAOqi Proxies
motion = ALProxy("ALMotion", ROBOT_IP, PORT)
tts = ALProxy("ALTextToSpeech", ROBOT_IP, PORT)
video = ALProxy("ALVideoDevice", ROBOT_IP, PORT)
speech_recognition = ALProxy("ALSpeechRecognition", ROBOT_IP, PORT)

# Gesture detection constants
FINGER_THRESHOLD = 10000

def detect_gesture(frame):
    """Detects if the user's gesture is rock, paper, or scissors."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blur, 60, 255, cv2.THRESH_BINARY_INV)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    cnt = max(contours, key=cv2.contourArea)
    hull = cv2.convexHull(cnt, returnPoints=False)
    defects = cv2.convexityDefects(cnt, hull)

    if defects is None:
        return "rock"

    fingers = sum(1 for i in range(defects.shape[0]) if defects[i, 0, 3] > FINGER_THRESHOLD)

    if fingers >= 4:
        return "paper"
    elif fingers == 1 or fingers == 2:
        return "scissors"
    return "rock"

def capture_user_choice(timeout=5):
    """Captures an image from NAO’s camera and detects hand gesture."""
    cam = video.subscribe("rpsCam", 2, 13, 30)
    start_time = time.time()
    user_choice = None

    while time.time() - start_time < timeout:
        img = video.getImageRemote(cam)
        if img:
            frame = np.frombuffer(img[6], dtype=np.uint8).reshape((img[1], img[0], 3))
            user_choice = detect_gesture(frame)
            cv2.imshow("Gesture", frame)
            if user_choice:
                break
            cv2.waitKey(1)

    video.unsubscribe(cam)
    cv2.destroyAllWindows()
    return user_choice

def show_nao_choice(choice):
    """Moves NAO’s hand to represent rock, paper, or scissors."""
    motion.setStiffnesses("Body", 1.0)
    if choice == "rock":
        motion.closeHand("RHand")
    elif choice == "paper":
        motion.openHand("RHand")
    elif choice == "scissors":
        motion.openHand("RHand")
        motion.setAngles("RShoulderRoll", -0.5, 0.2)  # Adjust angle for scissors gesture
    motion.waitUntilMoveIsFinished()

def move_hand_up():
    """Move hand halfway up for visual feedback after each gesture."""
    motion.setStiffnesses("Body", 1.0)
    motion.setAngles("RShoulderPitch", 0.5, 0.3)  # Adjust for hand halfway up position
    motion.waitUntilMoveIsFinished()

def decide_winner(nao, user):
    """Determines the winner between NAO and the user."""
    if nao == user:
        return "It's a tie!"
    wins = {"rock": "scissors", "scissors": "paper", "paper": "rock"}
    return "NAO wins!" if wins[nao] == user else "You win!"

def on_word_recognition(value, key):
    """Callback function to handle recognized speech (yes or no)."""
    print("Recognized word: ", key)
    if key == "yes":
        return True
    elif key == "no":
        return False
    return None

def listen_for_play_again():
    """Listen for a voice input to decide if the user wants to play again."""
    speech_recognition.setLanguage("English")
    speech_recognition.setVocabulary(["yes", "no"], False)

    # Subscribe to the speech recognition event
    speech_recognition.subscribe("SpeechRecognition")

    # Wait for the speech recognition to recognize a word
    while True:
        # Check if a word has been recognized
        result = speech_recognition.getData()
        if result:
            if result[0][0] == "yes":
                return True
            elif result[0][0] == "no":
                return False
            else:
                continue

    # Unsubscribe after the response has been received
    speech_recognition.unsubscribe("SpeechRecognition")

def play_round():
    """Plays a single round of Rock-Paper-Scissors."""
    motion.setStiffnesses("Body", 1.0)
    motion.closeHand("RHand")
    motion.waitUntilMoveIsFinished()

    # Announce each round
    for word in ("Rock", "Paper", "Scissors"):
        tts.say(word)
        time.sleep(0.6)
        move_hand_up()  # Move hand halfway up after each gesture

    tts.say("Shoot!")
    user_choice = capture_user_choice()
    nao_choice = random.choice(["rock", "paper", "scissors"])
    show_nao_choice(nao_choice)

    if user_choice:
        tts.say("You showed {}. {}".format(user_choice, decide_winner(nao_choice, user_choice)))
    else:
        tts.say("I couldn't detect your gesture.")

def main():
    """Main game loop."""
    while True:
        play_round()
        if not listen_for_play_again():
            motion.rest()
            break

if __name__ == "__main__":
    main()