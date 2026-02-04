# Vuzix Blade 2 - Assistive Navigation

An assistive navigation application for Vuzix Blade 2 smart glasses that captures images, processes them through machine learning models, and provides audio navigation instructions to users.

## Repository Structure

```
Vuzix-Blade-2/
├─ my-application/   # Android Studio project (Vuzix/Android app)
├─ flask/            # Python Flask server code
└─ .gitignore
```

## Usage / Workflow

1. Image Capture: The Android app continuously captures camera images when streaming is enabled
2. Image Upload: Captured frames are converted to PNG format and sent to the Flask server via HTTP POST
3. Server Processing: The server receives images and processes them through machine learning models (integration in progress)
4. Navigation Instructions: The server sends real-time navigation instructions via WebSocket (Socket.IO)
5. Audio Output: The Android app plays pre-recorded MP3 instruction files through the device speakers (6 instructions: Stop, Straight, Right, Right-Right, Left, Left-Left)
6. Voice Input: Users can record voice commands via gesture controls, which are uploaded to the server for speech-to-text transcription

## Gesture Controls

| Gesture | Action |
|---------|--------|
| Tap touchpad | Toggle frame streaming on/off |
| Left swipe (1st) | Start audio recording |
| Left swipe (2nd) | Stop recording and upload to server |
| Right swipe | Send test text message |

## Requirements

### Server Requirements

#### Python Environment
- Python 3.8 or higher
- pip (latest version)

#### Python Dependencies
```bash
pip install flask
pip install flask-socketio
pip install gevent
pip install gevent-websocket
pip install faster-whisper
pip install python-socketio
```

#### System Dependencies
- ffmpeg (required for audio processing; must be on PATH)
  - Ubuntu/Debian: sudo apt install ffmpeg
  - macOS: brew install ffmpeg
  - Windows: Download from https://ffmpeg.org

Important (Gevent ordering)
- This server uses gevent + Flask-SocketIO.
- In app.py, `from gevent import monkey; monkey.patch_all()` MUST come first (before any other imports).

## Setup Instructions

### 1) Flask Server Setup

```bash
cd flask/
python app.py
```

The server runs on:
- http://0.0.0.0:5000

#### Whisper STT Configuration (Optional)
```bash
export WHISPER_MODEL=small      # tiny, base, small, medium, large
export WHISPER_DEVICE=cpu       # cpu, cuda
export WHISPER_COMPUTE=int8     # int8, int16, float16, float32
python app.py
```

#### Audio Transcription Behavior (Updated)
- POST /stt_audio queues transcription in a separate process (multiprocessing with spawn)
- The main server remains responsive while Whisper transcribes
- Minimal logs by design:
  - When audio arrives: [AUDIO RECEIVED]
  - When transcription finishes: [STT_AUDIO] <transcript>
- If direct transcription fails, the server auto-converts using ffmpeg to 16kHz mono WAV and retries

### 2) Android App Setup

1. Open Android Studio
2. Open the project in my-application/
3. In MainActivity.java locate SERVER_IP (around line 58)
4. Update SERVER_IP:
   - Emulator: 10.0.2.2
   - Physical device / Vuzix Blade 2: your computer's LAN IP
5. Build and run the application

## Testing Instructions

### Android Emulator
1. Start an emulator
2. Run the app
3. Ensure Flask server is running
4. App connects to http://10.0.2.2:5000

### Android Phone/Tablet
1. Enable Developer Options + USB Debugging
2. Connect via USB OR same WiFi network
3. Run the app
4. Set SERVER_IP to your computer's LAN IP
5. Grant Camera + Microphone permissions

### Vuzix Blade 2 Glasses
1. Enable Developer Mode on Vuzix Blade 2
2. Connect via USB or WiFi
3. Install APK via ADB or Android Studio
4. Configure SERVER_IP for your network
5. Test image capture, audio output, and voice recording

### Finding Your Computer's IP Address
- Windows: ipconfig
- macOS/Linux: ifconfig or ip addr

## Server Endpoints

### Image
- POST /Server — Upload PNG image frames
- GET /Server — View uploaded images (web interface)
- GET /uploads/<filename> — Serve uploaded images

### Text
- POST /stt — Receive text messages

### Audio (Speech-to-Text)
- GET /stt_audio — Check STT system status (backend/model/device/compute)
- POST /stt_audio — Upload audio for transcription (async)

### WebSocket (Socket.IO)
- WebSocket on `/` (Socket.IO)
- Server emits: "instruction" with payload like {"code": "1"}

## Features

- Real-time Image Streaming (~5 fps)
- WebSocket Communication (Socket.IO)
- Pre-recorded MP3 Instructions (Stop/Straight/Right/Right-Right/Left/Left-Left)
- Voice Recording + Upload via gestures
- Server-side Speech-to-Text using faster-whisper
- Gesture Controls via touchpad input

## Current Status

- ✅ Image capture and PNG upload
- ✅ WebSocket-based real-time instructions
- ✅ Audio instruction playback (MP3)
- ✅ Voice recording and STT integration

## Troubleshooting

- Connection Issues: verify Flask server is running and SERVER_IP is correct
- Audio Upload Fails: ensure ffmpeg is installed and microphone permission is granted
- No Camera Preview: check camera permission and ensure no other app is using the camera
- WebSocket Not Connecting: check server logs and firewall settings for port 5000

