import requests
import json
import speech_recognition as sr

def transcribe_audio(file_path):
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(file_path) as source:
            print("Transcribing audio...")
            audio = recognizer.record(source)
            text = recognizer.recognize_google(audio)
            print("Transcription completed: {}".format(text))
            return text
    except Exception as e:
        print("Error: Unable to transcribe audio. Details: {}".format(e))
        return None

def get_response_from_chatgpt(user_input):
    url = "http://127.0.0.1:5000/chat"
    headers = {'Content-Type': 'application/json'}
    payload = {"input": user_input}

    try:
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        if response.status_code == 200:
            return response.json().get("response", "No response from server.")
        else:
            return "Error: Server returned status code {}".format(response.status_code)
    except Exception as e:
        return "Error: Could not connect to the server. Details: {}".format(e)

def main():
    print("Processing audio file: barbie.wav")

    # Transcribe the audio file
    transcription = transcribe_audio("barbie.wav")
    
    if transcription:
        # Send the transcription to ChatGPT server
        print("Sending transcription to ChatGPT...")
        response = get_response_from_chatgpt(transcription)
        print("ChatGPT Response: {}".format(response))
    else:
        print("No transcription available to send.")

if __name__ == "__main__":
    main()
