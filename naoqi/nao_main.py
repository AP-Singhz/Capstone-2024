
from naoqi import ALProxy
from nao_transcribe import detect_and_record_speech, transcribe_audio, send_to_flask_api ,speak_response , transfer_file
from chat import detect_wake_word
import time


# Configuration
ROBOT_IP = "192.168.1.10"  # Replace with your NAO robot's IP
ROBOT_PORT = 9559
LOCAL_FILE = "./speech.wav"
def main():
    print("NAO is ready and listening...")
    audio_recorder = ALProxy("ALAudioRecorder", ROBOT_IP, ROBOT_PORT)
    audio_device = ALProxy("ALAudioDevice",ROBOT_IP,ROBOT_PORT)
    audio_tts = ALProxy("ALTextToSpeech", ROBOT_IP, ROBOT_PORT)

    while True:
        # Step 1: Detect wake word
        if detect_wake_word():
            print("Wake word detected!")
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

if __name__ == "__main__":
    main()
