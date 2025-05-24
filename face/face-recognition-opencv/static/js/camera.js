// Camera access and processing
let video = null;
let canvas = null;
let captureInterval = null;
let streaming = false;

// Initialize the camera
function startCamera() {
    video = document.getElementById('video');
    canvas = document.getElementById('canvas');
    const startButton = document.getElementById('startButton');
    const stopButton = document.getElementById('stopButton');
    
    navigator.mediaDevices.getUserMedia({ video: true, audio: false })
        .then(function(stream) {
            video.srcObject = stream;
            video.play();
            streaming = true;
            
            startButton.disabled = true;
            stopButton.disabled = false;
            
            // Start sending frames to the server
            startCapturing();
        })
        .catch(function(err) {
            console.log("An error occurred: " + err);
            alert("Camera access error: " + err.message);
        });
}

// Stop the camera
function stopCamera() {
    const startButton = document.getElementById('startButton');
    const stopButton = document.getElementById('stopButton');
    
    if (streaming) {
        stopCapturing();
        
        if (video.srcObject) {
            video.srcObject.getTracks().forEach(track => track.stop());
        }
        
        streaming = false;
        startButton.disabled = false;
        stopButton.disabled = true;
        
        // Clear the recognition result
        document.getElementById('recognitionResult').innerHTML = '';
    }
}

// Start capturing frames
function startCapturing() {
    if (captureInterval) {
        clearInterval(captureInterval);
    }
    
    captureInterval = setInterval(captureFrame, 500); // Capture every 500ms
}

// Stop capturing frames
function stopCapturing() {
    if (captureInterval) {
        clearInterval(captureInterval);
        captureInterval = null;
    }
}

// Capture a frame and send to server
function captureFrame() {
    if (!streaming) return;
    
    const context = canvas.getContext('2d');
    
    if (video.videoWidth && video.videoHeight) {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        context.drawImage(video, 0, 0, video.videoWidth, video.videoHeight);
        
        // Convert canvas to base64 image
        const imageData = canvas.toDataURL('image/jpeg', 0.8);
        
        // Send to server for processing
        fetch('/process_frame', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ image: imageData })
        })
        .then(response => response.json())
        .then(data => {
            // Update the recognition result
            const resultDiv = document.getElementById('recognitionResult');
            if (data.faces.length > 0) {
                let html = '<div class="recognition-results">';
                data.faces.forEach(face => {
                    html += `<div class="face-result ${face.label === 'Unknown' ? 'unknown' : 'known'}">
                        <span class="name">${face.label}</span>
                        <span class="confidence">${Math.round(face.confidence * 100)}%</span>
                    </div>`;
                });
                html += '</div>';
                resultDiv.innerHTML = html;
            } else {
                resultDiv.innerHTML = '<div class="no-faces">No faces detected</div>';
            }
        })
        .catch(error => {
            console.error('Error processing frame:', error);
        });
    }
}

// Initialize when the page loads
document.addEventListener('DOMContentLoaded', function() {
    const startButton = document.getElementById('startButton');
    const stopButton = document.getElementById('stopButton');
    
    startButton.addEventListener('click', startCamera);
    stopButton.addEventListener('click', stopCamera);
    
    // Initially disable the stop button
    stopButton.disabled = true;
});