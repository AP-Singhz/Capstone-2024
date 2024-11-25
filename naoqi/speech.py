from naoqi import ALProxy
import time

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
    listen_and_repeat(ROBOT_IP)