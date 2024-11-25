import requests
import json
from naoqi import ALProxy

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

    NAO_IP = "172.20.10.6"

    tts = ALProxy("ALTextToSpeech", NAO_IP, 9559)

    print("ChatGPT Terminal Interface")
    print("Type your question below. Type 'exit' to quit.")
    
    while True:
        user_input = raw_input("You: ") 
        if user_input.lower() == "exit":
            print("Goodbye!")
            break
        
        response = get_response_from_chatgpt(user_input)
        print("ChatGPT: {}".format(response))
        tts("{}".format(response))

if __name__ == "__main__":
    main()