from naoqi import ALProxy
import time
import speech_recognition as sr
from pydub import AudioSegment

def record_audio(ip, port, file_path, duration):
    """
    Records audio on the NAO robot for a specified duration.
    :param ip: NAO robot's IP address
    :param port: NAO robot's port number
    :param file_path: Path to save the recorded audio file
    :param duration: Duration of the recording in seconds
    """
    try:
        # Create a proxy for the audio recorder
        audio_recorder = ALProxy("ALAudioRecorder", ip, port)

        # Set the audio configuration
        channels = [0, 0, 1, 0]  # Record from the microphone on the front
        audio_format = "wav"  # Use WAV format

        # Start recording
        print("Recording audio...")
        audio_recorder.startMicrophonesRecording(file_path, audio_format, 16000, channels)

        # Wait for the specified duration
        time.sleep(duration)

        # Stop recording
        audio_recorder.stopMicrophonesRecording()
        print("Recording stopped. Audio saved to:", file_path)

    except Exception as e:
        print("Error during recording:", e)


def preprocess_audio(input_path, output_path):
    """
    Converts the audio file to a compatible format for transcription.
    :param input_path: Path to the original audio file
    :param output_path: Path to save the converted audio file
    """
    try:
        # Load the audio file with pydub
        print("Preprocessing audio...")
        audio = AudioSegment.from_file(input_path)
        
        # Set audio to mono channel and 16kHz sampling rate
        audio = audio.set_frame_rate(16000).set_channels(1)
        
        # Export the processed audio file
        audio.export(output_path, format="wav")
        print("Audio preprocessed and saved to:", output_path)
        return output_path
    except Exception as e:
        print("Error during audio preprocessing:", e)
        return None


def transcribe_audio(file_path):
    """
    Transcribes the audio file to text using SpeechRecognition.
    :param file_path: Path to the recorded audio file
    :return: Transcribed text
    """
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(file_path) as source:
            print("Transcribing audio...")
            audio = recognizer.record(source)
            text = recognizer.recognize_google(audio)
            print("Transcription: ", text)
            return text
    except Exception as e:
        print("Error during transcription:", e)
        return None


def speak_text(ip, port, text):
    """
    Makes the NAO robot speak the provided text.
    :param ip: NAO robot's IP address
    :param port: NAO robot's port number
    :param text: Text to be spoken by the robot
    """
    try:
        tts = ALProxy("ALTextToSpeech", ip, port)
        tts.say(text)
    except Exception as e:
        print("Error during text-to-speech:", e)


if __name__ == "__main__":
    # NAO robot IP and port
    nao_ip = "172.20.10.6"  # Replace with your NAO's IP
    nao_port = 9559

    # File path to save the audio
    raw_audio_file_path = "recorded_audio.wav"  # Adjust the path as needed
    processed_audio_file_path = "processed_audio.wav"  # Adjust the path as needed

    # Duration of the recording (in seconds)
    recording_duration = 5

    # Record audio
    record_audio(nao_ip, nao_port, raw_audio_file_path, recording_duration)

    # Preprocess audio
    processed_file_path = preprocess_audio(raw_audio_file_path, processed_audio_file_path)

    # Transcribe audio
    if processed_file_path:
        transcribed_text = transcribe_audio(processed_file_path)

        # Speak the transcribed text
        if transcribed_text:
            speak_text(nao_ip, nao_port, transcribed_text)
