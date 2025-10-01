# Server.py
from flask import Flask, request, jsonify, send_from_directory, render_template_string
from flask_socketio import SocketIO, emit
import os, time, threading

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev'

# IMPORTANT: use threading mode on Windows/Python 3.13
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# ---------------- HTTP routes (your existing ones) ----------------
@app.route('/Server', methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    base_name = os.path.splitext(file.filename)[0]
    filepath = os.path.join(UPLOAD_FOLDER, base_name + ".png")
    file.save(filepath)
    return "2"  # numeric response (your app maps this to audio)

@app.route('/Server', methods=["GET"])
def list_images():
    files = os.listdir(UPLOAD_FOLDER)
    html = "<h1>Uploaded Images</h1>"
    for f in files:
        html += f'<div><img src="/uploads/{f}" style="max-width:300px;"><p>{f}</p></div>'
    return render_template_string(html)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)
# -----------------------------------------------------------------

# ---- Socket.IO: push "1" every second to all connected clients ----
_broadcast_started = False

def broadcaster():
    while True:
        socketio.emit("instruction", {"code": "10"})
        # time.sleep(1)

@socketio.on("connect")
def on_connect():
    print("Client connected")
    emit("instruction", {"code": "1"})  # immediate push on connect
    global _broadcast_started
    if not _broadcast_started:
        threading.Thread(target=broadcaster, daemon=True).start()
        _broadcast_started = True

@socketio.on("disconnect")
def on_disconnect():
    print("Client disconnected")

@app.route("/")
def index():
    return "OK (HTTP is alive)"

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)

