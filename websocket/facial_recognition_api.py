from flask import Flask, request, jsonify
import cv2
import numpy as np
import face_recognition
import json
import spotipy
from spotipy.oauth2 import SpotifyOAuth

app = Flask(__name__)

# File to save registered users
USER_DATA_FILE = "registered_users.json"
users = []  # Global list to store user data


def load_known_faces():
    """Load known face encodings and names from a file."""
    global users
    try:
        with open(USER_DATA_FILE, "r") as file:
            data = json.load(file)
            # Convert face encodings back to NumPy arrays
            users = [{"name": user["name"], "encoding": np.array(user["encoding"])} for user in data]
            print("Loaded {} known faces.".format(len(users)))
    except FileNotFoundError:
        print("No registered users found. Starting with an empty file.")
        users = []
    except json.JSONDecodeError:
        print("Error: Invalid JSON format in {}. Starting with an empty list.".format(USER_DATA_FILE))
        users = []
    except Exception as e:
        print("Error loading known faces:", e)
        users = []


def save_known_faces():
    """Save known face encodings and names to a file."""
    try:
        # Convert NumPy arrays to lists for JSON serialization
        data = [{"name": user["name"], "encoding": user["encoding"].tolist()} for user in users]
        with open(USER_DATA_FILE, "w") as file:
            json.dump(data, file)
        print("Known faces saved.")
    except Exception as e:
        print("Error saving known faces:", e)


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
            name = "Unknown"
            # Compare face encodings with a stricter tolerance
            matches = [
                face_recognition.compare_faces([user["encoding"]], face_encoding, tolerance=0.4)
                for user in users
            ]

            # Find the first match
            for i, match in enumerate(matches):
                if True in match:
                    name = users[i]["name"]
                    break

            # Add face location and name to results
            results.append({"name": name, "location": [top, right, bottom, left]})

        return jsonify({"faces": results})

    except Exception as e:
        print("Error during face recognition:", e)
        return jsonify({"error": str(e)}), 500


@app.route("/register", methods=["POST"])
def register_face():
    """Register a new face with a name."""
    try:
        name = request.form.get("name")
        if not name:
            return jsonify({"error": "Name is required for registration."}), 400

        file = request.files["frame"]
        np_frame = np.frombuffer(file.read(), np.uint8)
        frame = cv2.imdecode(np_frame, cv2.IMREAD_COLOR)

        # Detect a single face
        face_locations = face_recognition.face_locations(frame)
        if len(face_locations) != 1:
            return jsonify({"error": "Please ensure the image contains exactly one face."}), 400

        face_encoding = face_recognition.face_encodings(frame, face_locations)[0]

        # Check for duplicate names
        if any(user["name"] == name for user in users):
            return jsonify({"error": "A user with this name already exists."}), 400

        # Add the new face encoding and name
        users.append({"name": name, "encoding": face_encoding})
        save_known_faces()

        return jsonify({"message": "User '{}' registered successfully.".format(name)})

    except Exception as e:
        print("Error during registration:", e)
        return jsonify({"error": str(e)}), 500

# Configure your Spotify credentials (make sure to set environment variables or hard-code for testing)
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id="YOUR_CLIENT_ID",
                                               client_secret="YOUR_CLIENT_SECRET",
                                               redirect_uri="YOUR_REDIRECT_URI",
                                               scope="user-read-playback-state"))

@app.route('/spotify',methods=["POST"])
def spotify_command():
    data = request.get_json()
    command = data.get('command', '').lower()
    
    # Example: if the command includes a song search request.
    if "search" in command:
        # Extract the search query (e.g., "spotify search Imagine")
        query = command.replace("spotify search", "").strip()
        results = sp.search(q=query, type='track', limit=1)
        if results and results['tracks']['items']:
            track = results['tracks']['items'][0]
            result_text = f"Found: {track['name']} by {track['artists'][0]['name']}"
        else:
            result_text = "No results found."
    else:
        result_text = "Spotify command not recognized."
    
    return jsonify({'result': result_text})




if __name__ == "__main__":
    load_known_faces()
    app.run(host="0.0.0.0", port=5000)
