# Flask GUI Face Recognition App with Client-Side Camera Access
from flask import Flask, render_template, request, jsonify
import cv2
import os
import face_recognition
import pickle
import numpy as np
import base64
from datetime import datetime
import re
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)

DATASET_DIR = "dataset"
ENCODINGS_PATH = "encodings.pkl"
SIMILARITY_THRESHOLD = 0.6

if not os.path.exists(DATASET_DIR):
    os.makedirs(DATASET_DIR)

# ========== Utility Functions ==========
def train_model():
    encodings_dict = {}
    for user_folder in os.listdir(DATASET_DIR):
        path = os.path.join(DATASET_DIR, user_folder)
        for img_name in os.listdir(path):
            img_path = os.path.join(path, img_name)
            image = face_recognition.load_image_file(img_path)
            encodings = face_recognition.face_encodings(image)
            if encodings:
                encodings_dict.setdefault(user_folder, []).append(encodings[0])
    with open(ENCODINGS_PATH, "wb") as f:
        pickle.dump(encodings_dict, f)


def process_image(image_data):
    # Decode base64 image
    if "," in image_data:
        _, encoded = image_data.split(",", 1)
        img_data = base64.b64decode(encoded)
        
        # Convert to OpenCV format
        nparr = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Convert to RGB for face_recognition
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Detect faces
        faces = face_recognition.face_locations(rgb)
        encodings = face_recognition.face_encodings(rgb, faces)
        
        results = []
        
        # If we have encodings saved, compare with known faces
        if os.path.exists(ENCODINGS_PATH):
            with open(ENCODINGS_PATH, "rb") as f:
                encodings_dict = pickle.load(f)
                
            for (top, right, bottom, left), encoding in zip(faces, encodings):
                best_match = None
                best_score = 0.0
                
                for name, known_encs in encodings_dict.items():
                    for known_enc in known_encs:
                        score = cosine_similarity([encoding], [known_enc])[0][0]
                        if score > best_score:
                            best_score = score
                            best_match = name
                
                label = best_match if best_score > SIMILARITY_THRESHOLD else "Unknown"
                results.append({
                    "label": label,
                    "confidence": float(best_score),
                    "bbox": [left, top, right, bottom]
                })
        else:
            # If no encodings file, just return "Unknown" for all faces
            for (top, right, bottom, left) in faces:
                results.append({
                    "label": "Unknown",
                    "confidence": 0.0,
                    "bbox": [left, top, right, bottom]
                })
        
        return {"faces": results}
    
    return {"faces": []}


# ========== Flask Routes ==========
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        images = request.form.getlist("images[]")

        if not name or not images:
            return "❌ Name or images missing", 400

        user_dir = os.path.join(DATASET_DIR, name)
        os.makedirs(user_dir, exist_ok=True)

        for idx, data_url in enumerate(images):
            try:
                if "," not in data_url:
                    print(f"⚠️ Skipping invalid image at index {idx}")
                    continue
                header, encoded = data_url.split(",", 1)
                img_data = base64.b64decode(encoded)
                img_path = os.path.join(user_dir, f"img_{idx}.png")
                with open(img_path, "wb") as f:
                    f.write(img_data)
            except Exception as e:
                print(f"❌ Error saving image {idx}: {e}")

        train_model()
        return jsonify({"success": True})

    return render_template("register.html")


@app.route("/recognize")
def recognize():
    return render_template("recognize_web.html")


@app.route("/process_frame", methods=["POST"])
def process_frame():
    data = request.json
    if not data or "image" not in data:
        return jsonify({"error": "No image data provided"}), 400
    
    result = process_image(data["image"])
    return jsonify(result)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/developer")
def developer():
    return render_template("developer.html")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)