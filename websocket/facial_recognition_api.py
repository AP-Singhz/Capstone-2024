
from flask import Flask, request, jsonify
import cv2
import numpy as np
import face_recognition
import json

app = Flask(__name__)

#File to save registered users
USER_DATA_FILE = "registered_users.json"

# Known face encodings and names
known_face_encodings = []
known_face_names = []

def load_known_faces():
    """Load known face encodings and names from a file."""
    global known_face_encodings, known_face_names
    try:
        with open(USER_DATA_FILE, "r") as file:
            data = json.load(file)
            known_face_encodings = [np.array(encoding) for encoding in data["encodings"]]
            known_face_names = data["names"]
            print("Loaded {} known faces.".format(len(known_face_names)))
    except FileNotFoundError:
        print("No registered users found. Starting with an empty file.")
    except Exception as e:
        print("Error loading known faces:", e)

def save_known_faces():
    """Save known face encodings and names to a file."""
    try:
        data = {
            "encodings": [encoding.tolist() for encoding in known_face_encodings],
            "names": known_face_names,
        }
        with open(USER_DATA_FILE, "w") as file:
            json.dump(data, file)
        print("Known faces saved.")
    except Exception as e:
        print("Error saving known faces:", e)


# @app.route("/recognize", methods=["POST"])
# def recognize_faces():
#     try:
#         # Decode the received frame
#         file = request.files["frame"]
#         np_frame = np.frombuffer(file.read(), np.uint8)
#         frame = cv2.imdecode(np_frame, cv2.IMREAD_COLOR)

#         # Detect faces
#         face_locations = face_recognition.face_locations(frame)
#         face_encodings = face_recognition.face_encodings(frame, face_locations)
        
#         recognition_results = []
#         for face_encoding in face_encodings:
#             matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
#             name = "Unknown"
#             if True in matches:
#                 first_match_index = matches.index(True)
#                 name = known_face_names[first_match_index]

#             recognition_results.append(name)

#         return jsonify({"recognized_faces": recognition_results})

#     except Exception as e:
#         print("Error:", e)
#         return jsonify({"error": str(e)}), 500


@app.route("/recognize", methods=["POST"])
def recognize_faces():
    """Recognize faces and return their locations and names."""
    try:
        # Decode the received frame
        file = request.files["frame"]
        np_frame = np.frombuffer(file.read(), np.uint8)
        frame = cv2.imdecode(np_frame, cv2.IMREAD_COLOR)

        # Detect faces
        face_locations = face_recognition.face_locations(frame)
        face_encodings = face_recognition.face_encodings(frame, face_locations)

        results = []
        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            name = "Unknown"
            if True in matches:
                first_match_index = matches.index(True)
                name = known_face_names[first_match_index]

            # Add face location and name to results
            results.append({
                "name": name,
                "location": [top, right, bottom, left]
            })

        return jsonify({"faces": results})

    except Exception as e:
        print("Error:", e)
        return jsonify({"error": str(e)}), 500
    

@app.route("/register", methods=["POST"])
def register_face():
    """Register a new face with a name."""
    try:
        name = request.form.get("name")
        file = request.files["frame"]
        np_frame = np.frombuffer(file.read(), np.uint8)
        frame = cv2.imdecode(np_frame, cv2.IMREAD_COLOR)

        # Detect a single face
        face_locations = face_recognition.face_locations(frame)
        if len(face_locations) != 1:
            return jsonify({"error": "Please ensure the image contains exactly one face."}), 400

        face_encoding = face_recognition.face_encodings(frame, face_locations)[0]

        # Add the new face encoding and name
        known_face_encodings.append(face_encoding)
        known_face_names.append(name)
        save_known_faces()

        return jsonify({"message": "User '{}' registered successfully.".format(name)})

    except Exception as e:
        print("Error during registration:", e)
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    load_known_faces()
    app.run(host="0.0.0.0", port=5000)
