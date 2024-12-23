from flask import Flask, request, jsonify
import openai

app = Flask(__name__)

openai.api_key = ""
@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get("input")
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": user_input}]
    )
    return jsonify({"response": response['choices'][0]['message']['content']})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)




# from flask import Flask, request, jsonify
# import openai

# app = Flask(__name__)

# # Replace this with your actual OpenAI API key
# openai.api_key = ""

# @app.route('/chat', methods=['POST'])
# def chat():
#     user_input = request.json.get("input")
    
#     # Updated API call for openai>=1.0.0
#     try:
#         response = openai.ChatCompletion.create(
#             model="gpt-3.5-turbo",
#             messages=[{"role": "user", "content": user_input}]
#         )
        
#         # Accessing the response correctly in v1.x
#         reply = response['choices'][0]['message']['content']
#         return jsonify({"response": reply})
    
#     except Exception as e:
#         print("Error:", e)
#         traceback.print_exc()  # Print detailed error t
#         return jsonify({"error": str(e)}), 500

# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=5000)







# from flask import Flask, request, jsonify
# import openai
# import traceback  # For error logging

# app = Flask(__name__)

# # Replace this with your OpenAI API key
# openai.api_key = ""

# @app.route('/chat', methods=['POST'])
# def chat():
#     user_input = request.json.get("input")
#     try:
#         # Updated method for openai>=1.0.0
#         response = openai.ChatCompletion.create(
#             model="gpt-3.5-turbo",
#             messages=[{"role": "user", "content": user_input}]
#         )
#         # Accessing the response message in the updated version
#         reply = response.choices[0].message.content
#         return jsonify({"response": reply})

#     except Exception as e:
#         print("Error:", e)
#         traceback.print_exc()
#         return jsonify({"error": str(e)}), 500

# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=5000)
