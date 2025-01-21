
from naoqi import ALProxy
#from nao_transcribe import detect_and_record_speech, transcribe_audio, send_to_flask_api ,speak_response , transfer_file
from nao_transcribe import (
    detect_and_record_speech,
    transcribe_audio,
    send_to_flask_api,
    speak_response,
    transfer_file,
)
import threading
from chat import detect_wake_word
import time
from nao_facial_recog import stream_frames_and_recognize, handle_recognition_results, register_user

# Configuration
ROBOT_IP = "172.20.10.6"  # Replace with your NAO robot's IP
ROBOT_PORT = 9559
LOCAL_FILE = "./speech.wav"

wake_word_detected = threading.Event()


def listen_for_wake_word():

    audio_recorder = ALProxy("ALAudioRecorder", ROBOT_IP, ROBOT_PORT)
    audio_device = ALProxy("ALAudioDevice",ROBOT_IP,ROBOT_PORT)
    audio_tts = ALProxy("ALTextToSpeech", ROBOT_IP, ROBOT_PORT)
    audio_tts.setParameter("blockUntilSayFinished", True) # Ensure TTS(NAO) is finsihed speaking before proceding
    while True:
        # Step 1: Detect wake word
        if detect_wake_word():
            print("Wake word detected!")
            wake_word_detected.set()  # Set the flag to indicate wake word detected
            audio_tts.say("How can I help you?")

            # Step 2: Record audio
            # print("Recording question...")
            # audio_recorder.startMicrophonesRecording(
            #     "./speech.wav", "wav", 16000, [0, 0, 1, 0]
            # )
            #time.sleep(5)  # Record for 5 seconds
            #audio_recorder.stopMicrophonesRecording()
            #print("Recording complete.")

            # Step 2: Record Speech dynamically
            print("Listening for you question")
            detect_and_record_speech(audio_recorder, audio_device)
            print("Recording complete. File saved: {} " .format(LOCAL_FILE))

            # Step 3: Transfer file from NAO to local system
            print("Transferring file from NAO to local system...")
            transfer_file()  # Call the existing function directly
            print("File transfer complete.")
            
            # Step 4: Transcribe audio
            question = transcribe_audio()
            if question:
                print("User asked:{}" .format(question))

                # Step 5: Send transcription to GPT and get a response
                response = send_to_flask_api(question)
                if response:
                    print("GPT Response: {}".format(response))
                    # Step6: Speak the GPT response
                    speak_response(audio_tts, response)
                else:
                    audio_tts.say("I couldn't get a response.")
            else:
                audio_tts.say("I couldn't understand you. Please try again.")
            
            wake_word_detected.clear() # reset the flag after the task
        
        else:
            threading.Event().wait(0.1)  # Wait for 0.1 seconds before checking again, short delay prevent CPU overuse


def run_facial_recognition():
    while True:
        if not wake_word_detected.is_set():
            stream_frames_and_recognize() #Run facial recog logic
        else:
            print("Pausing facial recognition...")
            threading.Event().wait(0.1) # Wait for 100ms to allow wake word to take priority

def main():
    print("Nao ready and listening...")

    #create threads for the two main processes word detection and facial recognition
    wake_word_thread = threading.Thread(target=listen_for_wake_word) # daemon thread runs in the background and does not block the program from exiting
    recognition_thread = threading.Thread(target=run_facial_recognition)

     # Set threads as daemon
    wake_word_thread.daemon = True
    recognition_thread.daemon = True

    #start the threads
    wake_word_thread.start()
    recognition_thread.start()

    #Keep the main thread alive. using join(), you ensure a synchronized and orderly shutdown of the program, 
    # where all threads have the opportunity to complete their tasks properly before the program exits.
    wake_word_thread.join()
    recognition_thread.join()


if __name__ == "__main__":
    main()























# from naoqi import ALProxy
# from nao_transcribe import detect_and_record_speech, transcribe_audio, send_to_flask_api ,speak_response , transfer_file
# from chat import detect_wake_word
# import time


# # Configuration
# ROBOT_IP = "172.20.10.6"  # Replace with your NAO robot's IP
# ROBOT_PORT = 9559
# LOCAL_FILE = "./speech.wav"
# def main():
#     print("NAO is ready and listening...")
#     audio_recorder = ALProxy("ALAudioRecorder", ROBOT_IP, ROBOT_PORT)
#     audio_device = ALProxy("ALAudioDevice",ROBOT_IP,ROBOT_PORT)
#     audio_tts = ALProxy("ALTextToSpeech", ROBOT_IP, ROBOT_PORT)
#     audio_tts.setParameter("blockUntilSayFinished", True) # Ensure TTS(NAO) is finsihed speaking before proceding
#     while True:
#         # Step 1: Detect wake word
#         if detect_wake_word():
#             print("Wake word detected!")
#             audio_tts.say("How can I help you?")

#             # Step 2: Record audio
#             # print("Recording question...")
#             # audio_recorder.startMicrophonesRecording(
#             #     "./speech.wav", "wav", 16000, [0, 0, 1, 0]
#             # )
#             #time.sleep(5)  # Record for 5 seconds
#             #audio_recorder.stopMicrophonesRecording()
#             #print("Recording complete.")

#             # Step 2: Record Speech dynamically
#             print("Listening for you question")
#             detect_and_record_speech(audio_recorder, audio_device)
#             print("Recording complete. File saved: {} " .format(LOCAL_FILE))

#             # Step 3: Transfer file from NAO to local system
#             print("Transferring file from NAO to local system...")
#             transfer_file()  # Call the existing function directly
#             print("File transfer complete.")
            
#             # Step 4: Transcribe audio
#             question = transcribe_audio()
#             if question:
#                 print("User asked:{}" .format(question))

#                 # Step 5: Send transcription to GPT and get a response
#                 response = send_to_flask_api(question)
#                 if response:
#                     print("GPT Response: {}".format(response))
#                     # Step6: Speak the GPT response
#                     speak_response(audio_tts, response)
#                 else:
#                     audio_tts.say("I couldn't get a response.")
#             else:
#                 audio_tts.say("I couldn't understand you. Please try again.")

# if __name__ == "__main__":
#     main()




