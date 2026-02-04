Vuzix Blade 2 – Assistive Navigation

An assistive navigation application for Vuzix Blade 2 smart glasses that streams camera images to a server, enables real-time communication, and provides audio navigation instructions to users.
The project focuses on camera streaming, server–client communication, and speech-to-text integration, while the generation of navigation instructions is handled externally.

Repository Structure

Vuzix-Blade-2/
├─ my-application/ # Android Studio project (Vuzix / Android app)
├─ flask/ # Python Flask + Socket.IO server
└─ .gitignore

Usage / Workflow

The application follows this workflow:

Image Capture: The Android app continuously captures camera images when streaming is enabled

Image Upload: Captured frames are converted to PNG format and sent to the Flask server via HTTP POST

Server Handling: The server receives and stores image frames (navigation logic and ML-based decision making are external to this project)

Navigation Instructions: The server sends real-time navigation instructions to the smart glasses via WebSocket (Socket.IO)

Audio Output: The Android app plays pre-recorded MP3 instruction files through the device speakers (Stop, Straight, Right, Right-Right, Left, Left-Left)

Voice Input: Users can record voice commands via gesture controls, which are uploaded to the server for speech-to-text transcription

Gesture Controls

Tap touchpad → Toggle frame streaming on/off
Left swipe (1st) → Start audio recording
Left swipe (2nd) → Stop recording and upload audio
Right swipe → Send test text message

Requirements
Server Requirements

Python Environment

Python 3.8 or higher

pip (latest version)

Python Dependencies
pip install flask
pip install flask-socketio
pip install gevent
pip install gevent-websocket
pip install faster-whisper
pip install python-socketio

System Dependencies

ffmpeg (required for audio processing)

Ubuntu/Debian: sudo apt install ffmpeg

macOS: brew install ffmpeg

Windows: https://ffmpeg.org

Android Development Requirements

Latest version of Android Studio

Android SDK with minimum API level 30 (Android 11)

Gradle 7.0 or higher

Key Android Dependencies

CameraX (camera functionality)

OkHttp (HTTP requests)

Socket.IO client (WebSocket communication)

MediaRecorder (audio capture)

Testing Devices

Android phone or tablet (Android 11+)

Android Studio emulator

Vuzix Blade 2 smart glasses

Setup Instructions
1. Flask Server Setup

Navigate to the flask directory and start the server:

cd flask/
python app.py

The server runs on:
http://0.0.0.0:5000

Optional: Configure Whisper STT Model

export WHISPER_MODEL=small
export WHISPER_DEVICE=cpu
export WHISPER_COMPUTE=int8
python app.py

2. Android App Setup

Open Android Studio

Open the project in the my-application directory

In MainActivity.java, locate the SERVER_IP configuration

Update the server IP address:

Emulator: 10.0.2.2

Physical device / Vuzix Blade 2: your computer’s LAN IP

Build and run the application

Testing Instructions
Android Emulator

Start an emulator

Ensure Flask server is running

App connects via http://10.0.2.2:5000

Android Phone / Tablet

Enable Developer Options and USB Debugging

Ensure device and server are on the same network

Update SERVER_IP to your LAN IP

Grant Camera and Microphone permissions

Vuzix Blade 2 Smart Glasses

Enable Developer Mode

Install APK using ADB or Android Studio

Configure server IP

Test image streaming, audio output, and voice recording

Finding Your Computer’s IP Address

Windows: ipconfig
macOS/Linux: ifconfig or ip addr

Server Endpoints

POST /Server – Upload PNG image frames
GET /Server – View uploaded images
POST /stt – Receive text messages
POST /stt_audio – Upload audio for speech-to-text transcription
GET /stt_audio – STT system status
WebSocket on / – Real-time instruction channel

Features

Real-time image streaming (~5 FPS)

WebSocket-based communication

Pre-recorded audio navigation instructions

Gesture-controlled voice recording

Server-side speech-to-text using faster-whisper

Current Status

Image capture and PNG upload

WebSocket-based real-time instructions

Audio instruction playback

Voice recording and STT integration

Important Notes

The SERVER_IP in MainActivity.java must match your network configuration.
Localhost works only in emulator-specific setups.

Troubleshooting

Connection issues: verify server is running and IP is correct

Audio upload fails: check ffmpeg installation and microphone permission

No camera preview: check camera permission

WebSocket not connecting: check server logs and firewall settings for port 5000
