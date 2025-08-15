package com.example.myapplication;
//alooo
import android.Manifest;
import android.content.pm.PackageManager;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.ImageButton;
import android.widget.Toast;

import androidx.activity.result.ActivityResultCallback;
import androidx.activity.result.ActivityResultLauncher;
import androidx.activity.result.contract.ActivityResultContracts;
import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import androidx.camera.core.AspectRatio;
import androidx.camera.core.CameraSelector;
import androidx.camera.core.ImageCapture;
import androidx.camera.core.ImageCaptureException;
import androidx.camera.core.Preview;
import androidx.camera.lifecycle.ProcessCameraProvider;
import androidx.camera.view.PreviewView;
import androidx.core.content.ContextCompat;

import com.google.common.util.concurrent.ListenableFuture;

import java.io.File;
import java.io.IOException;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.Executor;
import java.util.concurrent.Executors;

import okhttp3.Call;
import okhttp3.Callback;
import okhttp3.MediaType;
import okhttp3.MultipartBody;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;

public class MainActivity extends AppCompatActivity {

    private Button capture;
    private PreviewView previewView;
    private final int cameraFacing = CameraSelector.LENS_FACING_BACK;
    private final OkHttpClient okHttpClient = new OkHttpClient();
    private final ActivityResultLauncher<String> activityResultLauncher = registerForActivityResult(new ActivityResultContracts.RequestPermission(), new ActivityResultCallback<Boolean>() {
        @Override
        public void onActivityResult(Boolean result) {
            if(result)
                startCamera(cameraFacing);
        }
    });
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        previewView=findViewById(R.id.cameraPreview);
        capture=findViewById(R.id.capture);

        if(ContextCompat.checkSelfPermission(MainActivity.this, Manifest.permission.CAMERA)!= PackageManager.PERMISSION_GRANTED){
            activityResultLauncher.launch(Manifest.permission.CAMERA);
        }
        else{
            startCamera(cameraFacing);
        }

    }

    private void startCamera(int cameraFacing) {
        int aspectRatio = aspectRatio(previewView.getWidth(),previewView.getHeight());
        ListenableFuture<ProcessCameraProvider> listenableFuture = ProcessCameraProvider.getInstance(this);

        listenableFuture.addListener(() -> {
            try{
                ProcessCameraProvider cameraProvider = (ProcessCameraProvider) listenableFuture.get();

                Preview preview = new Preview.Builder().setTargetAspectRatio(aspectRatio).build();

                preview.setSurfaceProvider(previewView.getSurfaceProvider());

                ImageCapture imageCapture = new ImageCapture.Builder().setCaptureMode(ImageCapture.CAPTURE_MODE_MINIMIZE_LATENCY)
                        .setTargetRotation(getWindowManager().getDefaultDisplay().getRotation()).build();

                CameraSelector cameraSelector = new CameraSelector.Builder()
                        .requireLensFacing(cameraFacing).build();

                cameraProvider.unbindAll();

                cameraProvider.bindToLifecycle(this, cameraSelector, preview, imageCapture);

                capture.setOnClickListener(new View.OnClickListener() {
                    @Override
                    public void onClick(View v) {

                            takePicture(imageCapture);

                    }
                });
            } catch (ExecutionException | InterruptedException e) {
                e.printStackTrace();
            }
        }, ContextCompat.getMainExecutor(this));
    }

    private int aspectRatio(int width, int height) {
        double previewRatio = (double)Math.max(width, height)/Math.min(width, height);
        if(Math.abs(previewRatio - 4.0/3.0) <= Math.abs(previewRatio - 16.0/9.0)){
            return AspectRatio.RATIO_4_3;
        }
        return AspectRatio.RATIO_16_9;
    }

    public void takePicture(ImageCapture imageCapture){
        final File file = new File(getExternalFilesDir(null),System.currentTimeMillis() + ".jpg");
        ImageCapture.OutputFileOptions outputFileOptions = new ImageCapture.OutputFileOptions.Builder(file).build();
        imageCapture.takePicture(outputFileOptions, Executors.newCachedThreadPool(), new ImageCapture.OnImageSavedCallback() {
            @Override
            public void onImageSaved(@NonNull ImageCapture.OutputFileResults outputFileResults) {
                runOnUiThread(new Runnable() {
                    @Override
                    public void run() {
                        //Toast.makeText(MainActivity.this, "Image Saved at" + file.getPath(), Toast.LENGTH_SHORT).show();
                        server(file);
                    }
                });
                startCamera(cameraFacing);
            }

            @Override
            public void onError(@NonNull ImageCaptureException exception) {
                runOnUiThread(new Runnable() {
                    @Override
                    public void run() {
                        Toast.makeText(MainActivity.this, "Failed", Toast.LENGTH_SHORT).show();
                    }
                });
                startCamera(cameraFacing);
            }
        });
    }

    private void server(File file) {
        RequestBody requestBody = new MultipartBody.Builder()
                .setType(MultipartBody.FORM)
                .addFormDataPart("file", file.getName(),
                        RequestBody.create(file, MediaType.parse("image/jpeg")))
                .build();

        Request request = new Request.Builder()
                .url("http://192.168.1.7:5000/Server")    //Change to the IP address of my device
                .post(requestBody)
                .build();

        okHttpClient.newCall(request).enqueue(new Callback() {
            @Override
            public void onFailure(@NonNull Call call, @NonNull IOException e) {
                runOnUiThread(() ->
                        Toast.makeText(MainActivity.this, "Network not found", Toast.LENGTH_SHORT).show()
                );
            }

            @Override
            public void onResponse(@NonNull Call call, @NonNull Response response) throws IOException {
                String res = response.body().string();
                runOnUiThread(() ->
                        Toast.makeText(MainActivity.this, res, Toast.LENGTH_SHORT).show()
                );
            }
        });
    }
}
