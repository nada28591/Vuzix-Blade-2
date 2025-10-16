# app.py — correct ordering for gevent + Flask-SocketIO

from gevent import monkey
monkey.patch_all()  # <-- must come first, before any other imports

from flask import Flask, request, jsonify, send_from_directory, render_template_string
import os, time, threading
from flask_socketio import SocketIO, emit

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config["SECRET_KEY"] = "dev"

# Use gevent async mode
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="gevent")

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
    return "2"

@app.route('/Server', methods=["GET"])
def list_images():
    files = os.listdir(UPLOAD_FOLDER)
    html = "<h1>Uploaded Images</h1>"
    for f in files:
        html += f'<div><img src="/uploads/{f}" style="max-width:300px;"><p>{f}</p></div>'
    return render_template_string(html)

@app.route("/stt", methods=["POST"])
def receive_text():
    text = request.form.get("text", "")
    print(f"Received text: {text}")

    # --- Save to a file ---
    with open("received_texts.txt", "a", encoding="utf-8") as f:
        f.write(text + "\n")

    return jsonify({"received": text})

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

_broadcast_thread = None
_stop_flag = False

def broadcaster():
    while not _stop_flag:
        socketio.emit("instruction", {"code": "2"})
        time.sleep(1)

@socketio.on("connect")
def on_connect():
    print("Client connected!")
    emit("instruction", {"code": "1"})
    global _broadcast_thread
    if _broadcast_thread is None:
        _broadcast_thread = threading.Thread(target=broadcaster, daemon=True)
        _broadcast_thread.start()

@socketio.on("disconnect")
def on_disconnect():
    print("Client disconnected.")

if __name__ == "__main__":
    print("Starting Flask-SocketIO server with gevent WebSocket support...")
    socketio.run(app, host="0.0.0.0", port=5000, debug=False, use_reloader=False)
