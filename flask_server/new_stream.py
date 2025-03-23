import cv2
import torch
import time
import requests
import base64
import threading
import socket
import json
from flask import Flask, Response, jsonify
from flask_cors import CORS
from ultralytics import RTDETR
from torchvision import models, transforms
from PIL import Image
import torch.nn as nn
import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
# Enable CORS for integration with Laravel/Vue frontend
CORS(app, resources={r"/*": {"origins": "*"}})

# Environment variables with defaults
MODEL_PATH = os.getenv('MODEL_PATH', 'best.pt')
RESNET_PATH = os.getenv('RESNET_PATH', 'resnet.pth')
API_ENDPOINT = os.getenv('API_ENDPOINT', 'http://127.0.0.1:8000/api/pin')
API_TOKEN = os.getenv('API_TOKEN', 'StraySafeTeam3')
BASE_RTSP_URL = os.getenv('BASE_RTSP_URL', 'rtsp://10.0.0.{}:8554/cam{}')
DEFAULT_CONFIDENCE = float(os.getenv('DEFAULT_CONFIDENCE', '0.5'))
REQUIRED_CONSECUTIVE_FRAMES = int(os.getenv('REQUIRED_CONSECUTIVE_FRAMES', '20'))
DOG_CLASS_ID = int(os.getenv('DOG_CLASS_ID', '1'))
FRAME_WIDTH = int(os.getenv('FRAME_WIDTH', '960'))
FRAME_HEIGHT = int(os.getenv('FRAME_HEIGHT', '544'))

# Setup CUDA if available
device = 'cuda' if torch.cuda.is_available() else 'cpu'
logger.info(f"Using {device} for inference")

# Store active stream objects
active_streams = {}

class RTSPStream:
    def __init__(self, rtsp_url, stream_id):
        self.rtsp_url = rtsp_url
        self.stream_id = stream_id
        self.cap = None
        self.is_running = False
        self.frame_buffer = None
        self.consecutive_detections = 0
        self.highest_confidence_frame = None
        self.highest_confidence_score = 0
        self.lock = threading.Lock()
        self.last_error_time = 0
        self.error_count = 0
        self.coordinates = self._generate_coordinates(stream_id)
        
    def _generate_coordinates(self, stream_id):
        # Mock coordinates based on stream ID - replace with real coordinates in production
        base_lat, base_lng = 14.631141, 121.039295
        offset = (int(stream_id) * 0.001)
        return [base_lng + offset, base_lat + offset]
        
    def connect(self):
        if self.cap is not None and self.cap.isOpened():
            self.cap.release()
        
        logger.info(f"Connecting to RTSP stream: {self.rtsp_url}")
        self.cap = cv2.VideoCapture(self.rtsp_url)
        
        # Set RTSP buffer size and timeout
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize buffering for real-time
        
        if not self.cap.isOpened():
            current_time = time.time()
            if current_time - self.last_error_time > 60:  # Reset error count after 1 minute
                self.error_count = 0
                
            self.error_count += 1
            self.last_error_time = current_time
            
            logger.error(f"Failed to connect to {self.rtsp_url}. Attempt {self.error_count}")
            return False
        
        self.error_count = 0
        return True
    
    def read_frame(self):
        if self.cap is None or not self.cap.isOpened():
            if not self.connect():
                time.sleep(5)  # Wait before retry
                return None
                
        ret, frame = self.cap.read()
        if not ret:
            logger.warning(f"Failed to read frame from {self.rtsp_url}")
            self.connect()  # Try to reconnect
            return None
            
        return frame
    
    def start(self):
        if self.is_running:
            return
            
        self.is_running = True
        threading.Thread(target=self.process_stream, daemon=True).start()
        logger.info(f"Started processing stream {self.stream_id}: {self.rtsp_url}")
    
    def stop(self):
        self.is_running = False
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        logger.info(f"Stopped stream {self.stream_id}: {self.rtsp_url}")
    
    def process_stream(self):
        while self.is_running:
            frame = self.read_frame()
            if frame is None:
                continue
                
            # Resize frame for processing
            resized_frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
            
            # Process with object detection model
            with torch.no_grad():
                results = model.predict(resized_frame, imgsz=(FRAME_WIDTH, FRAME_HEIGHT))
            
            detected_dog = False
            
            for result in results:
                for det in result.boxes.data:
                    class_id = int(det[-1])
                    confidence = float(det[-2])
                    x1, y1, x2, y2 = map(int, det[:4])
                    
                    if class_id == DOG_CLASS_ID and confidence >= 0.6:
                        detected_dog = True
                        if confidence > self.highest_confidence_score:
                            self.highest_confidence_score = confidence
                            cropped_image = resized_frame[y1:y2, x1:x2]
                            self.highest_confidence_frame = cropped_image
            
            if detected_dog:
                self.consecutive_detections += 1
                
                if (self.consecutive_detections >= REQUIRED_CONSECUTIVE_FRAMES and 
                    self.highest_confidence_frame is not None):
                    # Process the detection
                    self._process_detection()
            else:
                self.consecutive_detections = 0
                self.highest_confidence_frame = None
                self.highest_confidence_score = 0
            
            # Store the annotated frame in buffer for streaming
            with self.lock:
                self.frame_buffer = results[0].plot()
            
            # Don't process too quickly to save resources
            time.sleep(0.01)
    
    def _process_detection(self):
        try:
            leash_prediction = classify_leash(self.highest_confidence_frame)
            status_text = "Not Stray" if leash_prediction == "dog_with_leash" else "Stray Dog"
            
            base64_image = encode_image_to_base64(self.highest_confidence_frame)
            logger.info(f"Stream {self.stream_id}: Leash Prediction: {leash_prediction}, Status: {status_text}")
            
            response = requests.post(
                API_ENDPOINT,
                json={
                    'animal_type': 'dog',
                    'leash_status': leash_prediction,
                    'stray_status': status_text,
                    'coordinates': self.coordinates,
                    'snapshot': base64_image,
                    'stream_id': self.stream_id
                },
                headers={
                    'Authorization': f'Bearer {API_TOKEN}'
                },
                verify=False
            )
            
            if response.status_code == 200:
                logger.info(f"Successfully pinned dog from stream {self.stream_id}")
            else:
                logger.error(f"Failed to pin dog from stream {self.stream_id}: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error processing detection from stream {self.stream_id}: {e}")
        
        # Reset detection state
        self.consecutive_detections = 0
        self.highest_confidence_frame = None
        self.highest_confidence_score = 0
    
    def get_frame(self):
        with self.lock:
            if self.frame_buffer is None:
                return None
            return self.frame_buffer.copy()

# Global variables for ML models
model = None
leash_classifier = None

def load_models():
    global model, leash_classifier
    
    try:
        # Load RTDETR model for dog detection
        logger.info(f"Loading RTDETR model from {MODEL_PATH}")
        model = RTDETR(MODEL_PATH)
        model.to(device)
        
        # Load ResNet model for leash classification
        logger.info(f"Loading ResNet model from {RESNET_PATH}")
        leash_classifier = models.resnet50(pretrained=False)
        num_ftrs = leash_classifier.fc.in_features
        leash_classifier.fc = nn.Linear(num_ftrs, 2)  # 2 classes: with leash, without leash
        
        if os.path.exists(RESNET_PATH):
            leash_classifier.load_state_dict(torch.load(RESNET_PATH, map_location=device))
            leash_classifier.to(device)
            leash_classifier.eval()
            logger.info("ResNet model loaded successfully")
        else:
            logger.warning(f"ResNet model file not found at {RESNET_PATH}, using pretrained model")
            leash_classifier = models.resnet50(pretrained=True)
            leash_classifier.to(device)
            leash_classifier.eval()
    
    except Exception as e:
        logger.error(f"Error loading models: {e}")
        raise

def encode_image_to_base64(image):
    """Convert OpenCV image to base64 string"""
    _, buffer = cv2.imencode('.jpg', image)
    return base64.b64encode(buffer).decode('utf-8')

def classify_leash(cropped_image):
    """Classify if the dog has a leash or not"""
    if cropped_image is None or leash_classifier is None:
        return "dog_without_leash"  # Default to no leash if no image or model
    
    # Convert to PIL and preprocess
    pil_image = Image.fromarray(cv2.cvtColor(cropped_image, cv2.COLOR_BGR2RGB))
    preprocess = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
    
    input_tensor = preprocess(pil_image).unsqueeze(0).to(device)
    
    with torch.no_grad():
        output = leash_classifier(input_tensor)
        _, predicted = torch.max(output, 1)
    
    return "dog_with_leash" if predicted.item() == 1 else "dog_without_leash"

# Scan for available RTSP streams on the network
def scan_rtsp_streams():
    available_streams = []
    
    # Try to get local IP address
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        
        ip_prefix = '.'.join(local_ip.split('.')[:3])
        logger.info(f"Scanning for RTSP streams on network: {ip_prefix}.*")
    except:
        # Fallback to default
        ip_prefix = "10.0.0"
        logger.warning(f"Could not determine local network, using default: {ip_prefix}.*")
    
    # For testing purposes, add some sample RTSP streams
    # In production, you would scan the network or read from a configuration
    sample_streams = [
        # Sample RTSP streams - replace with real ones in production
        {"id": "1", "url": "rtsp://wowzaec2demo.streamlock.net/vod/mp4:BigBuckBunny_115k.mp4"},
        {"id": "2", "url": "rtsp://wowzaec2demo.streamlock.net/vod/mp4:BigBuckBunny_115k.mp4"},
        
        # You can also use local video files for testing
        {"id": "3", "url": "sample_videos/dog_video.mp4"},
        {"id": "4", "url": "sample_videos/street_video.mp4"},
        
        # Add more streams as needed
    ]
    
    # Add sample streams to available streams
    available_streams.extend(sample_streams)
    
    # In a real implementation, you would scan the network for RTSP cameras
    # This is just a placeholder for the actual scanning logic
    
    logger.info(f"Found {len(available_streams)} RTSP streams")
    return available_streams

# Initialize and start processing for all available RTSP streams
def initialize_streams():
    available_streams = scan_rtsp_streams()
    
    # Create stream objects for new streams
    for stream_info in available_streams:
        stream_id = stream_info["id"]
        rtsp_url = stream_info["url"]
        
        # Skip if already active
        if stream_id in active_streams and active_streams[stream_id].is_running:
            continue
            
        # Create new stream object
        stream = RTSPStream(rtsp_url, stream_id)
        active_streams[stream_id] = stream
        
        # Start processing
        try:
            stream.start()
        except Exception as e:
            logger.error(f"Error starting stream {stream_id}: {e}")
    
    # Return list of active streams
    return [
        {
            "id": stream_id,
            "url": stream.rtsp_url,
            "status": "active" if stream.is_running else "inactive"
        }
        for stream_id, stream in active_streams.items()
    ]

# Generator for video frames from a specific stream
def generate_frames(stream_id):
    """Generate frames for video streaming"""
    if stream_id not in active_streams:
        logger.error(f"Stream {stream_id} not found")
        return
        
    stream = active_streams[stream_id]
    
    while True:
        # Get the latest frame
        frame = stream.get_frame()
        
        if frame is None:
            # If no frame is available, send a blank frame
            blank_frame = np.zeros((FRAME_HEIGHT, FRAME_WIDTH, 3), dtype=np.uint8)
            _, buffer = cv2.imencode('.jpg', blank_frame)
        else:
            # Encode the frame as JPEG
            _, buffer = cv2.imencode('.jpg', frame)
            
        # Convert to bytes and yield
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
        
        # Don't generate frames too quickly
        time.sleep(0.033)  # ~30 FPS

@app.route('/video/<stream_id>')
def video(stream_id):
    """Stream video for a specific stream ID"""
    return Response(generate_frames(stream_id), 
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/streams', methods=['GET'])
def get_streams():
    """API endpoint to get all available streams"""
    streams = []
    for stream_id, stream in active_streams.items():
        streams.append({
            "id": stream_id,
            "name": f"Camera {stream_id}",
            "location": f"Location {stream_id}",
            "url": stream.rtsp_url,
            "status": "active" if stream.is_running else "inactive",
            "video_url": f"/video/{stream_id}"
        })
    return jsonify({"streams": streams})

@app.route('/scan', methods=['GET'])
def scan_streams():
    """API endpoint to scan for available streams"""
    available_streams = initialize_streams()
    return jsonify({"streams": available_streams})

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "active_streams": len(active_streams),
        "device": device
    })

def periodic_stream_scanner():
    """Periodically scan for new streams"""
    while True:
        try:
            initialize_streams()
        except Exception as e:
            logger.error(f"Error in periodic stream scanner: {e}")
        time.sleep(60)  # Scan every minute

if __name__ == '__main__':
    # Load ML models
    load_models()
    
    # Import numpy here to avoid circular imports
    import numpy as np
    
    # Initial scan for streams
    initialize_streams()
    
    # Start periodic scanner in background
    threading.Thread(target=periodic_stream_scanner, daemon=True).start()
    
    # Run Flask app
    logger.info("Starting Flask web server")
    app.run(debug=False, host='0.0.0.0', port=5000, threaded=True)
