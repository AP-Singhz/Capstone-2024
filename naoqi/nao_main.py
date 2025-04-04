
from naoqi import ALProxy
#from nao_transcribe import detect_and_record_speech, transcribe_audio, send_to_flask_api ,speak_response , transfer_file
from nao_transcribe import (
    detect_and_record_speech,
    transcribe_audio,
    send_to_flask_api,
    speak_response,
    transfer_file,
    wait_for_speech_to_finish
)
import threading
#from chat import detect_wake_word
from speech import detect_wake_word_speech

import time
#from nao_facial_recog import stream_frames_and_recognize, handle_recognition_results, register_user
from nao_facial_recog import stream_frames_and_recognize, handle_recognition_results, register_user, GREETED_USERS, GREETED_USERS_LOCK

# Configuration
ROBOT_IP = "172.20.10.2"  # Replace with your NAO robot's IP
ROBOT_PORT = 9559
LOCAL_FILE = "./speech.wav"

wake_word_detected = threading.Event()
# Global lock for audio operations
audio_lock = threading.Lock()
gpt_response_done = threading.Event()
facial_recog_done = threading.Event()

gpt_response_done.set()  # Initially, no GPT response is in progress.
facial_recog_done.set()  


def do_song_and_dance_GPT(audio_tts, question):
    """
    Have NAO sing the GPT-generated song while dancing concurrently.
    The dance routine (boogie) will stop when the singing is complete.
    """

    song = send_to_flask_api(question)
    if not song:
        audio_tts.say("I couldn't get a song response.")
        wait_for_speech_to_finish(audio_tts)
        return

    print("\n Song and dance working!:", song)
    
    # Create an event to signal when dancing should stop.
    dance_stop = threading.Event()
    
    # Define a function to run the dance routine which supports interruption.
    def dance_routine():
        from Dance1 import boogie
        boogie(stop_event=dance_stop)
    
    # Start the dance routine concurrently.
    dance_thread = threading.Thread(target=dance_routine)
    dance_thread.start()
    
    # NAO sings the song.
    speak_response(audio_tts, song)
    wait_for_speech_to_finish(audio_tts)
    
    # Signal the dance routine to stop.
    dance_stop.set()
    dance_thread.join()

# aaron needs to change a song 

def play_RPS(audio_tts, response):
    print("\n Rock Paper Scissors working!")
    import betterRPS
    betterRPS.main()
def play_boogie(audio_tts, response):
    print("\n Boogie working!")
    from Dance1 import boogie
    boogie()
def play_macarena(audio_tts, response):
    print("\n Macarena working!")
    from Dance2 import macarena
    macarena()
def play_gangname_style(audio_tts, response):
    print("\n Gangnam Style working!")
    from Dance2 import gangnam_style
    gangnam_style()

gpt_command_functions = {
    "song and dance": do_song_and_dance_GPT,
    "rock paper scissors": play_RPS,
    "boogie": play_boogie,
    "macarena": play_macarena,
    "gangnam style": play_gangname_style,

}

def listen_for_wake_word():

    audio_recorder = ALProxy("ALAudioRecorder", ROBOT_IP, ROBOT_PORT)
    audio_device = ALProxy("ALAudioDevice",ROBOT_IP,ROBOT_PORT)
    audio_tts = ALProxy("ALTextToSpeech", ROBOT_IP, ROBOT_PORT)
    
    while True:
        # Step 1: Detect wake word
        if detect_wake_word_speech():
            with audio_lock:
                print("Wake word detected!\n")
                wake_word_detected.set()  # Set the flag to indicate wake word detected
                gpt_response_done.clear()  # Mark that we're processing a GPT response.
                audio_tts.say("How can I help you?")
                wait_for_speech_to_finish(audio_tts)
                
                # Step 2: Record Speech dynamically
                print("Listening for you question\n")
                detect_and_record_speech(audio_recorder, audio_device)
                print("Recording complete. File saved: {} " .format(LOCAL_FILE) + "\n")

                # Step 3: Transfer file from NAO to local system
                print("Transferring file from NAO to local system...\n")
                transfer_file()  # Call the existing function directly
                print("File transfer complete.\n")
                
                # Step 4: Transcribe audio
                question = transcribe_audio()
                if question:
                    print("User asked:{}" .format(question) + "\n")
                    found_command = False

                    for command, func in gpt_command_functions.items():
                        if command in question.lower():
                            # Now pass the full question to the function.
                            func(audio_tts, question)
                            found_command = True
                            break
                    if not found_command:
                        response = send_to_flask_api(question)
                        if response:
                            print("GPT response: {}" .format(response) + "\n")
                            speak_response(audio_tts, response)
                            wait_for_speech_to_finish(audio_tts)
                        else:
                            audio_tts.say("I couldn't get a response.")
                            wait_for_speech_to_finish(audio_tts)
                else:
                    audio_tts.say("I couldn't understand you. Please try again.")
                    wait_for_speech_to_finish(audio_tts)
                
                # Mark GPT response as complete and allow facial recognition to resume.
                gpt_response_done.set()
                wake_word_detected.clear() # reset the flag after the task
        
        else:
            threading.Event().wait(2)  # Wait for 0.1 seconds before checking again, short delay prevent CPU overuse


def run_facial_recognition():
    while True:
        if (not wake_word_detected.is_set() and gpt_response_done.is_set() and  facial_recog_done.is_set()):
            stream_frames_and_recognize(facial_recog_done) #Run facial recog logic
        else:
            print("Pausing facial recognition...\n")
            threading.Event().wait(2) # Wait for 100ms to allow wake word to take priority

def main():
    print("Nao ready and listening...\n")

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

