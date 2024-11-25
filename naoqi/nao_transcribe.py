import requests
from naoqi import ALProxy
import paramiko
from scp import SCPClient
import speech_recognition as sr
import wave
import time

ROBOT_IP = "172.20.10.6"
ROBOT_PORT = 9559
USERNAME = "nao"
PASSWORD = "1234"

REMOTE_FILE = "/home/nao/recordings/audio/speech.wav"
LOCAL_FILE = "./speech.wav"

API_URL = "http://127.0.0.1:5000/chat" 

RMS_THRESHOLD = 700  
SILENCE_THRESHOLD = 3 


def detect_and_record_speech(audio_recorder, audio_device):
    
    try:
        print("Listening for speech...")
        silent_time = 0
        is_recording = False

        while True:
            rms = audio_device.getFrontMicEnergy()
            if rms > RMS_THRESHOLD and not is_recording:
                print("Speech detected! Starting recording...")
                try:
                    audio_recorder.startMicrophonesRecording(
                        REMOTE_FILE, "wav", 16000, [0, 0, 1, 0]
                    )
                    is_recording = True
                except RuntimeError as e:
                    print("Error starting recording: {}".format(e))
                    return 

                while is_recording:
                    rms = audio_device.getFrontMicEnergy()
                    if rms < RMS_THRESHOLD:
                        silent_time += 1
                    else:
                        silent_time = 0  

                    if silent_time >= SILENCE_THRESHOLD:
                        print("Silence detected, stopping recording...")
                        audio_recorder.stopMicrophonesRecording()
                        is_recording = False
                        return  

                    time.sleep(1)  

    except Exception as e:
        print("Error during recording:", e)


def transfer_file():
 
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ROBOT_IP, username=USERNAME, password=PASSWORD)

        with SCPClient(ssh.get_transport()) as scp:
            scp.get(REMOTE_FILE, LOCAL_FILE)
        print("File transferred successfully to:", LOCAL_FILE)

    except Exception as e:
        print("Error during file transfer:", e)


def transcribe_audio():
 
    try:
        recognizer = sr.Recognizer()

        with sr.AudioFile(LOCAL_FILE) as source:
            audio_data = recognizer.record(source)

        print("Transcribing audio...")
        transcription = recognizer.recognize_google(audio_data)
        print("Transcription:", transcription)
        return transcription

    except sr.UnknownValueError:
        print("Could not understand the audio.")
        return None
    except sr.RequestError as e:
        print("Error with the speech recognition service:", e)
        return None


def send_to_flask_api(user_input):

    try:
        response = requests.post(API_URL, json={"input": user_input})
        if response.status_code == 200:
            openai_response = response.json().get("response")
            print("OpenAI Response:", openai_response)
            return openai_response
        else:
            print("Error with Flask API:", response.status_code, response.text)
            return None
    except requests.RequestException as e:
        print("Error connecting to Flask API:", e)
        return None


def speak_response(audio_tts, response):

    try:
        print("Speaking response...")
        audio_tts.say(str(response))
    except Exception as e:
        print("Error during text-to-speech:", e)


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
        print("Program terminated by user.")


if __name__ == "__main__":
    main()
