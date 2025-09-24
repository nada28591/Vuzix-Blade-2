# System Architecture

```mermaid
flowchart TD
    A[User taps Vuzix Blade 2 touchpad → streaming starts] --> B[Camera starts capturing frames]
    B --> C[Frames converted to JPEG]
    C --> D[Send frames via OkHttp POST to Flask server IP address]
    D --> E[Flask server receives images]
    E --> F[Convert to PNG format]
    F --> G[Save in 'uploads' folder]
    G --> H[Server responds with dummy message 'Images Uploaded Successfully' for each uploaded image]
    H --> I[User taps again → streaming stops]
    I --> J[Android app plays the dummy message using TextToSpeech]
