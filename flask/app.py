# app.py — correct ordering for gevent + Flask-SocketIO

from gevent import monkey
monkey.patch_all()  # <-- must come first, before any other imports

from flask import Flask, request, jsonify, send_from_directory, render_template_string
import os, time, threading, tempfile, subprocess, sys
from flask_socketio import SocketIO, emit

# === NEW: faster-whisper init (loads once) ===
# pip install faster-whisper
from faster_whisper import WhisperModel

# Tunables via env (optional)
WHISPER_MODEL   = os.environ.get("WHISPER_MODEL", "small")  # e.g., "base", "small", "medium"
WHISPER_DEVICE  = os.environ.get("WHISPER_DEVICE", "cpu")   # "cpu" or "cuda"
WHISPER_COMPUTE = os.environ.get("WHISPER_COMPUTE", "int8") # "int8","int16","float16","float32"

print(f"[WHISPER] loading model='{WHISPER_MODEL}' device='{WHISPER_DEVICE}' compute='{WHISPER_COMPUTE}'")
whisper_model = WhisperModel(WHISPER_MODEL, device=WHISPER_DEVICE, compute_type=WHISPER_COMPUTE)
print("[WHISPER] ready")

def _transcribe_path(audio_path: str) -> str:
    """
    Try to transcribe an audio file directly with faster-whisper.
    (This usually works on MP3/M4A/WAV if ffmpeg is available.)
    """
    segments, info = whisper_model.transcribe(
        audio_path,
        language=None,    # auto-detect; set "en" to force English
        vad_filter=True,  # trim leading/trailing silence
        beam_size=1       # faster; raise for slightly better accuracy
    )
    return " ".join(seg.text.strip() for seg in segments if seg.text).strip()

def _to_wav_16k_mono(src_path: str, dst_path: str):
    """
    Fallback: Convert arbitrary audio to mono 16 kHz WAV via ffmpeg
    (Requires ffmpeg installed and on PATH.)
    """
    subprocess.run(
        ["ffmpeg", "-y", "-i", src_path, "-ac", "1", "-ar", "16000", dst_path],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config["SECRET_KEY"] = "dev"

# Use gevent async mode
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="gevent")

# ---------------------------
# Existing routes (unchanged)
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

# ---------------------------
# NEW: Audio transcription API (faster-whisper)
# ---------------------------

@app.route("/stt_audio", methods=["GET"])
def stt_audio_status():
    """Simple status/health endpoint."""
    return jsonify({
        "ok": True,
        "backend": "faster-whisper",
        "model": WHISPER_MODEL,
        "device": WHISPER_DEVICE,
        "compute_type": WHISPER_COMPUTE,
        "usage": "POST an MP3/M4A/WAV as form field 'audio' to /stt_audio"
    })

@app.route("/stt_audio", methods=["POST"])
def stt_audio():
    """
    Accepts an audio file (preferably MP3) in form field 'audio'.
    Tries direct transcription with faster-whisper; if it fails,
    converts to 16 kHz mono WAV via ffmpeg and retries.
    Prints the recognized text to terminal and returns JSON.
    """
    f = request.files.get("audio")
    if not f:
        return jsonify({"error": "no file 'audio' provided"}), 400

    with tempfile.TemporaryDirectory() as td:
        src_path = os.path.join(td, f.filename or "in_audio")
        f.save(src_path)

        # 1) Try direct transcription (works for MP3/M4A/WAV if ffmpeg is available)
        try:
            text = _transcribe_path(src_path)
        except Exception as e:
            print(f"[STT] direct decode failed: {e}", file=sys.stderr)
            # 2) Fallback: convert to WAV and retry
            try:
                wav_path = os.path.join(td, "audio_16k.wav")
                _to_wav_16k_mono(src_path, wav_path)
                text = _transcribe_path(wav_path)
            except subprocess.CalledProcessError:
                return jsonify({"error": "ffmpeg conversion failed. Is ffmpeg installed on PATH?"}), 500
            except Exception as e2:
                print(f"[STT] fallback transcription error: {e2}", file=sys.stderr)
                return jsonify({"error": "transcription failed"}), 500

    print(f"[STT_AUDIO] {text}", flush=True)  # <-- prints to your terminal
    return jsonify({"text": text})

# ---------------------------
# Socket.IO broadcaster (unchanged)
# ---------------------------

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
