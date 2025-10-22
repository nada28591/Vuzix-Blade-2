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

The application follows this workflow:

1. **Image Capture**: The Android app continuously captures camera images when streaming is enabled
2. **Image Upload**: Captured frames are converted to PNG format and sent to the Flask server via HTTP POST
3. **Server Processing**: The server receives images and processes them through machine learning models (integration in progress)
4. **Navigation Instructions**: The server sends real-time navigation instructions via WebSocket (Socket.IO)
5. **Audio Output**: The Android app plays pre-recorded MP3 instruction files through the device speakers
6. **Voice Input**: Users can record voice commands via gesture controls, which are uploaded to the server for speech-to-text transcription

## Gesture Controls

| Gesture | Action |
|---------|--------|
| **Tap touchpad** | Toggle frame streaming on/off |
| **Left swipe (1st)** | Start audio recording |
| **Left swipe (2nd)** | Stop recording and upload to server |
| **Right swipe** | Send test text message |

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
- **ffmpeg**: Required for audio processing (must be on PATH)
  - Ubuntu/Debian: `sudo apt install ffmpeg`
  - macOS: `brew install ffmpeg`
  - Windows: Download from https://ffmpeg.org

### Android Development Requirements

- Latest version of Android Studio
- Android SDK with minimum API level 30 (Android 11)
- Gradle 7.0 or higher

#### Key Android Dependencies
- CameraX for camera functionality
- OkHttp for HTTP requests
- Socket.IO client for WebSocket communication
- MediaRecorder for audio capture

### Testing Devices

The application can be tested on:
- Any Android device (phone/tablet) running Android 11+
- Android Studio emulator
- Actual Vuzix Blade 2 smart glasses

## Setup Instructions

### 1. Flask Server Setup

Navigate to the `flask/` directory and start the Flask server:

```bash
cd flask/
python app.py
```

The server will start running on `http://0.0.0.0:5000` by default.

#### Optional: Configure Whisper STT Model
```bash
export WHISPER_MODEL=small      # Options: tiny, base, small, medium, large
export WHISPER_DEVICE=cpu       # Options: cpu, cuda
export WHISPER_COMPUTE=int8     # Options: int8, int16, float16, float32
python app.py
```

### 2. Android App Setup

1. Open Android Studio
2. Open the project located in the `my-application/` directory
3. In `MainActivity.java`, locate the `SERVER_IP` configuration (around line 58)
4. Update the server IP address to point to your Flask server:
   - For emulator: `10.0.2.2`
   - For physical device: Your computer's LAN IP address
5. Build and run the application

## Testing Instructions

### Android Emulator

1. Start an Android emulator from Android Studio
2. Install and run the app
3. Ensure the Flask server is running
4. The app will use `http://10.0.2.2:5000` to connect to your local server

### Android Phone/Tablet

1. Enable Developer Options and USB Debugging on your device
2. Connect via USB or ensure both device and computer are on the same network
3. Install and run the app
4. Update the `SERVER_IP` in the app configuration to your computer's LAN IP
5. Grant Camera and Microphone permissions when prompted

### Vuzix Blade 2 Glasses

1. Enable Developer Mode on the Vuzix Blade 2
2. Connect via USB or WiFi
3. Install the APK using ADB or Android Studio
4. Configure the server IP address for your network setup
5. Run the application and test image capture, audio output, and voice recording functionality

### Finding Your Computer's IP Address

- **Windows**: Run `ipconfig` in Command Prompt
- **macOS/Linux**: Run `ifconfig` or `ip addr` in Terminal

## Server Endpoints

- `POST /Server` - Upload PNG image frames
- `GET /Server` - View uploaded images (web interface)
- `POST /stt` - Receive text messages
- `POST /stt_audio` - Upload audio for speech-to-text transcription
- `GET /stt_audio` - Check STT system status
- WebSocket on `/` - Real-time instruction channel (Socket.IO)

## Features

- **Real-time Image Streaming**: Continuous PNG frame capture at ~5 fps
- **WebSocket Communication**: Asynchronous navigation instructions via Socket.IO
- **Pre-recorded Audio Instructions**: MP3 playback based on server commands
- **Voice Recording**: On-device AAC/M4A audio capture with gesture controls
- **Speech-to-Text**: Server-side transcription using faster-whisper
- **Gesture Controls**: Touchpad and trackball input support

## Current Status

- ✅ Image capture and PNG upload
- ✅ WebSocket-based real-time instructions
- ✅ Audio instruction playback (MP3)
- ✅ Voice recording and STT integration

## Important Notes

**IP Address Configuration**: You must update the `SERVER_IP` in `MainActivity.java` based on your network configuration and server location. The default localhost configuration will only work with specific setups.

## Troubleshooting

- **Connection Issues**: Verify Flask server is running and IP address is correct
- **Audio Upload Fails**: Ensure ffmpeg is installed and microphone permission is granted
- **No Camera Preview**: Check camera permission and ensure no other app is using the camera
- **WebSocket Not Connecting**: Check server logs and firewall settings for port 5000

---

**Repository**: https://github.com/nada28591/Vuzix-Blade-2
