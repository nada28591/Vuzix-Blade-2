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
1. **Image Capture**: The Android app continuously captures JPG images using the device camera
2. **Image Processing**: The captured JPG images are converted to PNG format in the Flask server
3. **Server Communication**: Images are sent to the Flask API via HTTP POST requests
4. **ML Processing**: The server converts the images to PNG (done) then processes them through machine learning models (integration in progress)
5. **Navigation Instructions**: The ML model generates navigation instructions based on image analysis (pending ML integration)
6. **Audio Output**: The Android app receives confirmation and plays audio instructions via MP3 files through the device speakers (currently plays confirmation MP3 upon successful upload, with plans to expand to multiple instruction MP3 files)

## Requirements
### Server Requirements
- Python 3.7 or higher
- Flask installed: `pip install flask`
- Additional Python dependencies that might be needed

### Android Development Requirements
- Latest version of Android Studio
- Android SDK with minimum API level compatible with Vuzix Blade 2 (API 30)

### Testing Devices
The application can be tested on:
- Any Android device (phone/tablet)
- Android Studio emulator
- Actual Vuzix Blade 2 smart glasses

## Setup Instructions
### 1. Flask Server Setup
Navigate to the `flask/` directory and start the Flask server
The server will start running on `http://localhost:5000` by default.

### 2. Android App Setup
1. Open Android Studio
2. Open the project located in the `my-application/` directory
3. In the Android app code, locate the API base URL configuration
4. Update the base URL to point to your Flask server:
   - For emulator: `http://10.0.2.2:5000/Server`
   - For physical device: `http://YOUR_COMPUTER_IP:5000/Server`
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
4. Update the server IP address in the app configuration to your computer's LAN IP

### Vuzix Blade 2 Glasses
1. Enable Developer Mode on the Vuzix Blade 2
2. Connect via USB or WiFi
3. Install the APK using ADB or Android Studio
4. Configure the server IP address for your network setup
5. Run the application and test image capture and audio output functionality

### IP Address Configuration
**Important**: You must update the IP address in the Android Studio code based on your network configuration and server location. The default localhost configuration will only work with specific setups.
