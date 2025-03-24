from naoqi import ALProxy
import time

# List of wake words
WAKE_WORDS = ["hey nao", "hello nao", "hey now", "hello now", "hello no", "hey no"]

ROBOT_IP = "172.20.10.6"  # Your constant robot IP

def detect_wake_word_speech(robot_ip=ROBOT_IP, robot_port=9559, wake_words=None):
    """
    Listens for one of the specified wake words using ALSpeechRecognition.
    Returns True as soon as a wake word is detected.
    """
    if wake_words is None:
        wake_words = WAKE_WORDS

    try:
        # Create proxies for speech recognition, memory, and text-to-speech
        speech_rec = ALProxy("ALSpeechRecognition", robot_ip, robot_port)
        memory = ALProxy("ALMemory", robot_ip, robot_port)
        tts = ALProxy("ALTextToSpeech", robot_ip, robot_port)

        # Pause recognition to configure settings
        speech_rec.pause(True)
        speech_rec.setLanguage("English")
        # Set vocabulary to the list of wake words
        speech_rec.setVocabulary(wake_words, False)
        speech_rec.setParameter("Sensitivity", 0.8)
        speech_rec.pause(False)

        # Subscribe to the recognition service with a custom subscription name
        subscription_name = "WakeWordDetection"
        speech_rec.subscribe(subscription_name)

        print("Listening for wake words: {}".format(", ".join(wake_words)))
        while True:
            word_data = memory.getData("WordRecognized")
            if word_data and len(word_data) >= 2:
                word = word_data[0]
                confidence = word_data[1]
                if word:
                    word = word.lower().strip()
                    # Check if the recognized word is one of the wake words and meets the confidence threshold
                    if word in [w.lower() for w in wake_words] and confidence > 0.3:
                        print("Detected wake word '{}' with confidence {}.".format(word, confidence))
                        tts.say("Yes?")
                        speech_rec.pause(True)
                        speech_rec.unsubscribe(subscription_name)
                        return True
            time.sleep(0.1)
    except Exception as e:
        print("Error in wake word detection: {}".format(e))
        return False

# Optional: Original listen_and_repeat function (for testing or alternative use)
def listen_and_repeat(robot_ip, robot_port=9559):
    try:
        speech_rec = ALProxy("ALSpeechRecognition", robot_ip, robot_port)
        memory = ALProxy("ALMemory", robot_ip, robot_port)
        tts = ALProxy("ALTextToSpeech", robot_ip, robot_port)
        
        speech_rec.pause(True)
        speech_rec.setLanguage("English")
        vocabulary = ["hello", "hi", "goodbye", "how are you"]
        speech_rec.setVocabulary(vocabulary, False)
        speech_rec.setParameter("Sensitivity", 0.8)
        speech_rec.pause(False)
        
        tts.say("Hello, I'm ready to listen!")
        speech_rec.subscribe("Test_ASR")
        
        last_word = ""
        while True:
            word_data = memory.getData("WordRecognized")
            if word_data and len(word_data) >= 2:
                word = word_data[0]
                confidence = word_data[1]
                if word != '' and word != last_word and confidence > 0.3:
                    speech_rec.pause(True)
                    tts.say("I heard you say " + word)
                    last_word = word
                    time.sleep(1)
                    speech_rec.pause(False)
            time.sleep(0.5)
    except Exception as e:
        print("Error occurred: %s" % str(e))

if __name__ == "__main__":
    ROBOT_IP = "172.20.10.6"
    
    # Test the new wake word detection function
    if detect_wake_word_speech(ROBOT_IP):
        print("Wake word detected!")
    else:
        print("Wake word not detected.")
