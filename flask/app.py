from flask import Flask, request, jsonify, send_from_directory, render_template_string
import os
from PIL import Image

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)

@app.route('/Server', methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    # Save directly as PNG
    base_name = os.path.splitext(file.filename)[0]
    filepath = os.path.join(UPLOAD_FOLDER, base_name + ".png")
    file.save(filepath)

    return "2"


# Serve a page that lists all images
@app.route('/Server', methods=["GET"])
def list_images():
    files = os.listdir(UPLOAD_FOLDER)
    html = "<h1>Uploaded Images</h1>"
    for f in files:
        html += f'<div><img src="/uploads/{f}" style="max-width:300px;"><p>{f}</p></div>'
    return render_template_string(html)

# Serve files from uploads folder
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0")
