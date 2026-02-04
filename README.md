# Vuzix Blade 2 - Assistive Navigation

An assistive navigation application for Vuzix Blade 2 smart glasses that captures images, streams them to a server, and provides audio navigation instructions to users.  
The project focuses on camera streaming, server–client communication, and speech-to-text integration. Machine-learning-based navigation logic can be integrated on the server side but is not implemented as part of this repository.

## Repository Structure



## Usage / Workflow

The application follows this workflow:

1. **Image Capture**: The Android app continuously captures camera images when streaming is enabled.
2. **Image Upload**: Captured frames are converted to PNG format and sent to the Flask server via HTTP POST.
3. **Server Processing**: The server receives and stores the images. (Any ML-based processing or navigation decision logic is external to this project.)
4. **Navigation Instructions**: The server sends real-time navigation instructions via WebSocket (Socket.IO) to the smart glasses.
5. **Audio Output**: The Android app plays pre-recorded MP3 instruction files through the device speakers (currently 6 instructions: Stop, Straight, Right, Right-Right, Left, Left-Left).
6. **Voice Input**: Users can record voice commands via gesture controls, which are uploaded to the server for speech-to-text transcription using faster-whisper.

## Gesture Controls

| Gesture            | Action                                      |
|--------------------|---------------------------------------------|
| **Tap touchpad**   | Toggle frame streaming on/off               |
| **Left swipe (1st)** | Start audio recording                     |
| **Left swipe (2nd)** | Stop recording and upload to server       |
| **Right swipe**    | Send test text message                      |

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


cd flask/
python app.py

export WHISPER_MODEL=small      # Options: tiny, base, small, medium, large
export WHISPER_DEVICE=cpu       # Options: cpu, cuda
export WHISPER_COMPUTE=int8     # Options: int8, int16, float16, float32
python app.py
