# app.py — correct ordering for gevent + Flask-SocketIO

from gevent import monkey
monkey.patch_all()  # <-- must come first, before any other imports

from flask import Flask, request, jsonify, send_from_directory, render_template_string
import os, time, threading, tempfile, subprocess, sys
from flask_socketio import SocketIO, emit

# === timestamped printing ===
from datetime import datetime

def tprint(*args, **kwargs):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}]", *args, **kwargs)

# === faster-whisper ===
from faster_whisper import WhisperModel

WHISPER_MODEL   = os.environ.get("WHISPER_MODEL", "small")
WHISPER_DEVICE  = os.environ.get("WHISPER_DEVICE", "cpu")
WHISPER_COMPUTE = os.environ.get("WHISPER_COMPUTE", "int8")

# Load model silently at startup
whisper_model = WhisperModel(
    WHISPER_MODEL,
    device=WHISPER_DEVICE,
    compute_type=WHISPER_COMPUTE
)

def _transcribe_path(audio_path: str) -> str:
    segments, info = whisper_model.transcribe(
        audio_path,
        language=None,
        vad_filter=True,
        beam_size=1
    )
    return " ".join(seg.text.strip() for seg in segments if seg.text).strip()

def _to_wav_16k_mono(src_path: str, dst_path: str):
    subprocess.run(
        ["ffmpeg", "-y", "-i", src_path, "-ac", "1", "-ar", "16000", dst_path],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

AUDIO_UPLOAD_FOLDER = "audio_uploads"
os.makedirs(AUDIO_UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config["SECRET_KEY"] = "dev"

socketio = SocketIO(app, cors_allowed_origins="*", async_mode="gevent")

# ---------------------------
# Image routes (unchanged)
# ---------------------------

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

    tprint(f"[IMAGE UPLOADED] {filepath}")
    return "2"

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

# ---------------------------
# Text route (unchanged)
# ---------------------------

@app.route("/stt", methods=["POST"])
def receive_text():
    text = request.form.get("text", "")
    tprint(f"Received text: {text}")

    with open("received_texts.txt", "a", encoding="utf-8") as f:
        f.write(text + "\n")

    return jsonify({"received": text})

# ---------------------------
# Audio transcription
# ---------------------------

@app.route("/stt_audio", methods=["GET"])
def stt_audio_status():
    return jsonify({
        "ok": True,
        "backend": "faster-whisper",
        "model": WHISPER_MODEL,
        "device": WHISPER_DEVICE,
        "compute_type": WHISPER_COMPUTE
    })

import multiprocessing as mp

def _worker_tprint(*args, **kwargs):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}]", *args, **kwargs)

def _transcribe_process_entry(audio_path: str):
    try:
        local_model = WhisperModel(
            WHISPER_MODEL,
            device=WHISPER_DEVICE,
            compute_type=WHISPER_COMPUTE
        )

        try:
            segments, info = local_model.transcribe(
                audio_path,
                language=None,
                vad_filter=True,
                beam_size=1
            )
            text = " ".join(seg.text.strip() for seg in segments if seg.text).strip()
        except Exception:
            with tempfile.TemporaryDirectory() as td:
                wav_path = os.path.join(td, "audio_16k.wav")
                _to_wav_16k_mono(audio_path, wav_path)
                segments, info = local_model.transcribe(
                    wav_path,
                    language=None,
                    vad_filter=True,
                    beam_size=1
                )
                text = " ".join(seg.text.strip() for seg in segments if seg.text).strip()

        # ✅ ONLY transcribed text is printed
        _worker_tprint(f"[STT_AUDIO] {text}", flush=True)

    finally:
        try:
            os.remove(audio_path)
        except Exception:
            pass

@app.route("/stt_audio", methods=["POST"])
def stt_audio():
    f = request.files.get("audio")
    if not f:
        return jsonify({"error": "no file 'audio' provided"}), 400

    safe_name = os.path.basename(f.filename or "in_audio")
    base, ext = os.path.splitext(safe_name)
    if not ext:
        ext = ".m4a"

    uniq = str(int(time.time() * 1000))
    src_path = os.path.join(AUDIO_UPLOAD_FOLDER, f"{base}_{uniq}{ext}")
    f.save(src_path)

    # ✅ SINGLE print when audio is received
    tprint("[AUDIO RECEIVED]")

    p = mp.Process(
        target=_transcribe_process_entry,
        args=(src_path,),
        daemon=True
    )
    p.start()

    return jsonify({"queued": True})

# ---------------------------
# Socket.IO (unchanged)
# ---------------------------

_broadcast_thread = None
_stop_flag = False

def broadcaster():
    while not _stop_flag:
        socketio.emit("instruction", {"code": "2"})
        time.sleep(1)

@socketio.on("connect")
def on_connect():
    tprint("Client connected!")
    emit("instruction", {"code": "1"})
    global _broadcast_thread
    if _broadcast_thread is None:
        _broadcast_thread = threading.Thread(target=broadcaster, daemon=True)
        _broadcast_thread.start()

@socketio.on("disconnect")
def on_disconnect():
    tprint("Client disconnected.")

if __name__ == "__main__":
    try:
        mp.set_start_method("spawn", force=True)
    except Exception:
        pass

    tprint("Starting Flask-SocketIO server with gevent WebSocket support...")
    socketio.run(app, host="0.0.0.0", port=5000, debug=False, use_reloader=False)
