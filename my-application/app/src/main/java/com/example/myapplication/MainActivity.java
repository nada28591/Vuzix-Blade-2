package com.example.myapplication;

import android.Manifest;
import android.content.pm.PackageManager;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.ImageFormat;
import android.graphics.Matrix;
import android.graphics.Rect;
import android.graphics.YuvImage;
import android.media.AudioAttributes;
import android.media.AudioManager;
import android.media.MediaPlayer;
import android.os.Bundle;
import android.util.Size;
import android.view.View;
import android.widget.Button;
import android.widget.Toast;

import androidx.activity.result.ActivityResultCallback;
import androidx.activity.result.ActivityResultLauncher;
import androidx.activity.result.contract.ActivityResultContracts;
import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import androidx.camera.core.CameraSelector;
import androidx.camera.core.ImageAnalysis;
import androidx.camera.core.ImageProxy;
import androidx.camera.core.Preview;
import androidx.camera.lifecycle.ProcessCameraProvider;
import androidx.camera.view.PreviewView;
import androidx.core.content.ContextCompat;

import com.google.common.util.concurrent.ListenableFuture;

import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.util.concurrent.ExecutionException;

import okhttp3.Call;
import okhttp3.Callback;
import okhttp3.MediaType;
import okhttp3.MultipartBody;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;

import io.socket.client.IO;
import io.socket.client.Socket;

public class MainActivity extends AppCompatActivity {

    // -------- configurable --------
    private static final String SERVER_IP = "172.20.10.11"; // <-- change to your PC LAN IP
    private static final String BASE_HTTP = "http://" + SERVER_IP + ":5000";
    private static final String UPLOAD_URL = BASE_HTTP + "/Server";
    private static final String SOCKET_URL  = BASE_HTTP;     // root is fine for Socket.IO
    // ------------------------------

    private double startTime = 0;
    private double period = 0;
    private int count = 0;

    private Button capture;
    private PreviewView previewView;

    private final int cameraFacing = CameraSelector.LENS_FACING_BACK;
    private final OkHttpClient okHttpClient = new OkHttpClient();

    private boolean streaming = false;
    private boolean spoken = false;

    private AudioManager audioManager;
    private Socket mSocket;

    private final ActivityResultLauncher<String> activityResultLauncher =
            registerForActivityResult(
                    new ActivityResultContracts.RequestPermission(),
                    new ActivityResultCallback<Boolean>() {
                        @Override
                        public void onActivityResult(Boolean result) {
                            if (result) startCamera(cameraFacing);
                            else Toast.makeText(MainActivity.this, "Camera permission denied", Toast.LENGTH_SHORT).show();
                        }
                    }
            );

    public MainActivity() {}

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        previewView = findViewById(R.id.cameraPreview);
        capture = findViewById(R.id.capture);

        audioManager = getSystemService(AudioManager.class);
        nudgeVolumeUp(2); // optional

        // Camera permission
        if (ContextCompat.checkSelfPermission(MainActivity.this, Manifest.permission.CAMERA)
                != PackageManager.PERMISSION_GRANTED) {
            activityResultLauncher.launch(Manifest.permission.CAMERA);
        } else {
            startCamera(cameraFacing);
        }

        // Start Socket.IO listener (push channel; independent of uploads)
        startSocketIO();

        capture.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                streaming = !streaming; // toggle streaming on/off
                if (streaming) {
                    Toast.makeText(MainActivity.this, "Streaming started", Toast.LENGTH_SHORT).show();
                    startTime = System.currentTimeMillis();
                    spoken = false;
                } else {
                    double elapsed = (System.currentTimeMillis() - startTime) / 1000.0;
                    Toast.makeText(MainActivity.this, count + " photos in " + elapsed + "s", Toast.LENGTH_LONG).show();
                    startTime = 0;
                    count = 0;
                }
            }
        });
    }

    private void startCamera(int cameraFacing) {
        ListenableFuture<ProcessCameraProvider> listenableFuture = ProcessCameraProvider.getInstance(this);

        listenableFuture.addListener(() -> {
            try {
                ProcessCameraProvider cameraProvider = listenableFuture.get();

                Preview preview = new Preview.Builder().build();
                preview.setSurfaceProvider(previewView.getSurfaceProvider());

                ImageAnalysis imageAnalysis = new ImageAnalysis.Builder()
                        .setTargetResolution(new Size(640, 480))
                        .setBackpressureStrategy(ImageAnalysis.STRATEGY_KEEP_ONLY_LATEST)
                        .build();

                imageAnalysis.setAnalyzer(ContextCompat.getMainExecutor(this), image -> {
                    if (streaming) {
                        byte[] pngBytes = imageToPng(image);
                        ++count;
                        uploadToServer(pngBytes);
                    }
                    image.close();
                });

                CameraSelector cameraSelector = new CameraSelector.Builder()
                        .requireLensFacing(cameraFacing)
                        .build();

                cameraProvider.unbindAll();
                cameraProvider.bindToLifecycle(this, cameraSelector, preview, imageAnalysis);

            } catch (ExecutionException | InterruptedException e) {
                e.printStackTrace();
            }
        }, ContextCompat.getMainExecutor(this));
    }

    private byte[] imageToPng(ImageProxy image) {
        ImageProxy.PlaneProxy[] planes = image.getPlanes();
        int width = image.getWidth();
        int height = image.getHeight();

        byte[] nv21 = new byte[width * height * 3 / 2];
        int pos = 0;

        ByteBuffer yBuffer = planes[0].getBuffer();
        ByteBuffer uBuffer = planes[1].getBuffer();
        ByteBuffer vBuffer = planes[2].getBuffer();

        int yRowStride = planes[0].getRowStride();
        int uvRowStride = planes[1].getRowStride();
        int uvPixelStride = planes[1].getPixelStride();

        // Copy Y plane
        for (int row = 0; row < height; row++) {
            yBuffer.position(row * yRowStride);
            yBuffer.get(nv21, pos, width);
            pos += width;
        }

        // Copy VU plane interleaved
        for (int row = 0; row < height / 2; row++) {
            for (int col = 0; col < width / 2; col++) {
                int vuPos = row * uvRowStride + col * uvPixelStride;
                nv21[pos++] = vBuffer.get(vuPos); // V
                nv21[pos++] = uBuffer.get(vuPos); // U
            }
        }

        // NV21 -> JPEG
        YuvImage yuvImage = new YuvImage(nv21, ImageFormat.NV21, width, height, null);
        ByteArrayOutputStream jpegOut = new ByteArrayOutputStream();
        yuvImage.compressToJpeg(new Rect(0, 0, width, height), 50, jpegOut);
        byte[] jpegBytes = jpegOut.toByteArray();

        Bitmap bitmap = BitmapFactory.decodeByteArray(jpegBytes, 0, jpegBytes.length);
        Matrix matrix = new Matrix();
        matrix.postRotate(180); // adjust if needed
        Bitmap rotated = Bitmap.createBitmap(bitmap, 0, 0, bitmap.getWidth(), bitmap.getHeight(), matrix, true);

        // JPEG -> PNG
        ByteArrayOutputStream pngOut = new ByteArrayOutputStream();
        rotated.compress(Bitmap.CompressFormat.PNG, 100, pngOut);
        return pngOut.toByteArray();
    }

    private void uploadToServer(byte[] pngBytes) {
        RequestBody requestBody = new MultipartBody.Builder()
                .setType(MultipartBody.FORM)
                .addFormDataPart(
                        "file",
                        "frame.png",
                        RequestBody.create(pngBytes, MediaType.parse("image/png"))
                )
                .build();

        Request request = new Request.Builder()
                .url(UPLOAD_URL)
                .post(requestBody)
                .build();

        okHttpClient.newCall(request).enqueue(new Callback() {
            @Override
            public void onFailure(@NonNull Call call, @NonNull IOException e) {
                runOnUiThread(() -> Toast.makeText(MainActivity.this, "Network error", Toast.LENGTH_SHORT).show());
            }

            @Override
            public void onResponse(@NonNull Call call, @NonNull Response response) {
                // We ignore the HTTP response body because instructions come via Socket.IO now.
                response.close();
            }
        });
    }

    // --------- Socket.IO push listener (receives "1" every second) ---------
    private void startSocketIO() {
        try {
            IO.Options opts = new IO.Options();
            opts.reconnection = true;
            // Helps with Flask-SocketIO 5.x (engineio 4)
            opts.transports = new String[] { "websocket", "polling" };
            mSocket = IO.socket(SOCKET_URL, opts);
        } catch (Exception e) {
            e.printStackTrace();
            return;
        }

        mSocket.on(Socket.EVENT_CONNECT, args ->
                runOnUiThread(() ->
                        Toast.makeText(MainActivity.this, "WS connected", Toast.LENGTH_SHORT).show()
                )
        );

        mSocket.on("instruction", args -> runOnUiThread(() -> {
            if (args.length == 0 || !(args[0] instanceof JSONObject)) return;
            JSONObject obj = (JSONObject) args[0];
            String code = obj.optString("code", "");

            long now = System.currentTimeMillis();
            // throttle audio to avoid spamming every second
            if (!spoken || (now - period) >= 1000) {
                spoken = true;
                period = now;

                switch (code) {
                    case "1":
                        // TODO: swap to your "upload success" mp3 if you prefer
                        playRaw(R.raw.left);
                        break;
                    case "2":
                        playRaw(R.raw.right);
                        break;
                    case "3":
                        playRaw(R.raw.left2);
                        break;
                    case "4":
                        playRaw(R.raw.right2);
                        break;
                    case "5":
                        playRaw(R.raw.straight);
                        break;
                    default:
                        playRaw(R.raw.stop);
                        break;
                }
            }
        }));

        mSocket.connect();
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        if (mSocket != null) {
            mSocket.disconnect();
            mSocket.off();
        }
    }

    // ---- Audio helpers ----
    private void playRaw(int resId) {
        if (audioManager != null) {
            audioManager.requestAudioFocus(
                    focusChange -> {},
                    AudioManager.STREAM_MUSIC,
                    AudioManager.AUDIOFOCUS_GAIN_TRANSIENT
            );
        }

        MediaPlayer mp = MediaPlayer.create(this, resId);
        if (mp == null) {
            Toast.makeText(this, "Audio init failed", Toast.LENGTH_SHORT).show();
            return;
        }

        try {
            mp.setAudioAttributes(
                    new AudioAttributes.Builder()
                            .setUsage(AudioAttributes.USAGE_ASSISTANCE_ACCESSIBILITY)
                            .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH)
                            .build()
            );
        } catch (Exception ignored) {}

        mp.setOnCompletionListener(MediaPlayer::release);
        mp.start();
    }

    private void nudgeVolumeUp(int steps) {
        if (audioManager == null) return;
        for (int i = 0; i < steps; i++) {
            audioManager.adjustVolume(AudioManager.ADJUST_RAISE, 0);
        }
    }
}
