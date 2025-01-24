import requests
from naoqi import ALProxy
import paramiko
from scp import SCPClient
import speech_recognition as sr
import wave
import time
from pydub import AudioSegment

ROBOT_IP = "172.20.10.6"
ROBOT_PORT = 9559
USERNAME = "nao"
PASSWORD = "1234"

REMOTE_FILE = "/home/nao/recordings/audio/speech.wav"
CLEANED_FILE = "./cleaned_speech.wav"
LOCAL_FILE = "./speech.wav"

API_URL = "http://127.0.0.1:5000/chat" 

RMS_THRESHOLD = 700  
SILENCE_THRESHOLD = 5 


def wait_for_speech_to_finish(tts):
    """
    Dynamically wait for the NAO robot to finish speaking using ALTextToSpeech/TextDone event.
    """
    memory = ALProxy("ALMemory", ROBOT_IP, ROBOT_PORT)
    event_name = "ALTextToSpeech/TextDone"

    # Wait until the TextDone event is triggered
    print("Waiting for TextDone event...\n")
    while True:
        try:
            if memory.getData(event_name, 0):  # Check event data
                print("Speech finished.\n")
                break
        except RuntimeError as e:
            print("Error checking TextDone event:".format(e) + "\n")
            break

def detect_and_record_speech(audio_recorder, audio_device):
    
    try:
        print("Listening for speech...\n")
        silent_time = 0
        is_recording = False

        while True:
            rms = audio_device.getFrontMicEnergy()
            # if rms > RMS_THRESHOLD and not is_recording:
            print("Speech detected! Starting recording...\n")
            try:
                audio_recorder.startMicrophonesRecording(
                    REMOTE_FILE, "wav", 16000, [0, 0, 1, 0]
                )
                is_recording = True
            except RuntimeError as e:
                print("Error starting recording: {}".format(e) + "\n")
                return 

            while is_recording:
                rms = audio_device.getFrontMicEnergy()
                if rms < RMS_THRESHOLD:
                    silent_time += 1  # increment silence timer
                else:
                    silent_time = 0  

                if silent_time >= SILENCE_THRESHOLD:  # stops after silence threshold
                    print("Silence detected, stopping recording...\n")
                    audio_recorder.stopMicrophonesRecording()
                    is_recording = False
                    return

                    time.sleep(1)  # check the mic energy every second
    except Exception as e:
        print("Error during recording:{}".format(e) + "\n")


def transfer_file():
 
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ROBOT_IP, username=USERNAME, password=PASSWORD)

        with SCPClient(ssh.get_transport()) as scp:
            scp.get(REMOTE_FILE, LOCAL_FILE)
        print("File transferred successfully to:{}" .format(LOCAL_FILE))
    except Exception as e:
        print("Error during file transfer:{}".format(e) + "\n")


def preprocess_audio(input_file, output_file):
    """Reduce noise and normalize the audio file."""
    try:
        print("Preprocessing audio...\n")
        audio = AudioSegment.from_file(input_file)
        audio = audio.set_frame_rate(16000).set_channels(1)  # Mono, 16kHz
        audio.export(output_file, format="wav")
        print("Preprocessed audio saved to:{}" .format(output_file) + "\n")
        return output_file
    except Exception as e:
        print("Error preprocessing audio: {}".format(e) + "\n")
        return None


# def transcribe_audio():
 
#     try:
#         recognizer = sr.Recognizer()

#         with sr.AudioFile(LOCAL_FILE) as source:
#             audio_data = recognizer.record(source)

#         print("Transcribing audio...")
#         transcription = recognizer.recognize_google(audio_data)
#         print("Transcription:", transcription)
#         return transcription

#     except sr.UnknownValueError:
#         print("Could not understand the audio.")
#         return None
#     except sr.RequestError as e:
#         print("Error with the speech recognition service:", e)
#         return None


# def transcribe_audio():
#     recognizer = sr.Recognizer()
#     preprocessed_file = preprocess_audio(LOCAL_FILE, CLEANED_FILE)
#     if not preprocessed_file:
#         return None
#     try:
#         with sr.AudioFile(preprocessed_file) as source:
#             recognizer.adjust_for_ambient_noise(source)
#             audio_data = recognizer.record(source)
#         return recognizer.recognize_google(audio_data)
#     except Exception as e:
#         print(f"Error transcribing audio: {e}")
#         return None


def transcribe_audio():
    """Transcribe the audio file located at LOCAL_FILE."""
    recognizer = sr.Recognizer()

    # Preprocess the audio file
    preprocessed_file = preprocess_audio(LOCAL_FILE, CLEANED_FILE)
    if not preprocessed_file:
        print("Error preprocessing the audio file.\n")
        return None

    try:
        with sr.AudioFile(preprocessed_file) as source:
            recognizer.adjust_for_ambient_noise(source)  # Adjust threshold for ambient noise
            audio_data = recognizer.record(source)
        print("Transcribing audio...\n")
        text = recognizer.recognize_google(audio_data)
        print("Transcription:{}" .format(text) + "\n")
        return text
    except sr.UnknownValueError:
        print("Speech recognition could not understand the audio.\n")
        return None
    except sr.RequestError as e:
        print("Error with the speech recognition service:{}" .format(e) + "\n")
        return None
    except Exception as e:
        print("Unexpected error during transcription:{}" .format(e) + "\n")
        return None


def send_to_flask_api(user_input):

    try:
        response = requests.post(API_URL, json={"input": user_input})
        if response.status_code == 200:
            openai_response = response.json().get("response")
            print("OpenAI Response:{}".format(openai_response) + "\n")
            return openai_response
        else:
            print("Error with Flask API: {}, {}".format(response.status_code, response.text))
            return None
    except requests.RequestException as e:
        print("Error connecting to Flask API:{}".format(e) + "\n")
        return None


def speak_response(audio_tts, response):

    try:
        print("Speaking response...\n")
        audio_tts.say(str(response))
    except Exception as e:
        print("Error during text-to-speech: {}".format(e))


def main():
    try:

        audio_recorder = ALProxy("ALAudioRecorder", ROBOT_IP, ROBOT_PORT)
        audio_device = ALProxy("ALAudioDevice", ROBOT_IP, ROBOT_PORT)
        audio_tts = ALProxy("ALTextToSpeech", ROBOT_IP, ROBOT_PORT)

        audio_recorder.stopMicrophonesRecording()

        while True:

            detect_and_record_speech(audio_recorder, audio_device)

            transfer_file()
            transcription = transcribe_audio()

            if transcription:

                response = send_to_flask_api(transcription)

                if response:
                    speak_response(audio_tts, response)

            print("\nRestarting detection...\n")

    except KeyboardInterrupt:
        print("Program terminated by user.\n")


if __name__ == "__main__":
    main()
