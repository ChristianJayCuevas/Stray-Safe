import cv2
import torch
import time
import requests
import base64
import threading
import socket
import json
from flask import Flask, Response, jsonify, request, send_file, send_from_directory
from flask_cors import CORS
from ultralytics import RTDETR
from torchvision import models, transforms
from PIL import Image
import torch.nn as nn
import os
import logging
from dotenv import load_dotenv
import numpy as np
import io
import shutil
import subprocess
import glob
from datetime import datetime

# Load environment variables from .env file if it exists
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Environment variables with defaults
MODEL_PATH = os.getenv('MODEL_PATH', 'best.pt')
RESNET_PATH = os.getenv('RESNET_PATH', 'resnet.pth')
API_ENDPOINT = os.getenv('API_ENDPOINT', 'http://127.0.0.1:8000/api/pin')
API_TOKEN = os.getenv('API_TOKEN', 'StraySafeTeam3')
# Updated RTSP URL format
BASE_RTSP_URL = os.getenv('BASE_RTSP_URL', 'rtsp://10.0.0.3:8554/cam1')
EXTERNAL_STREAMS_API = os.getenv('EXTERNAL_STREAMS_API', 'http://192.168.1.24:5000/streams')
DEFAULT_CONFIDENCE = float(os.getenv('DEFAULT_CONFIDENCE', '0.5'))
REQUIRED_CONSECUTIVE_FRAMES = int(os.getenv('REQUIRED_CONSECUTIVE_FRAMES', '20'))
DOG_CLASS_ID = int(os.getenv('DOG_CLASS_ID', '1'))
FRAME_WIDTH = int(os.getenv('FRAME_WIDTH', '960'))
FRAME_HEIGHT = int(os.getenv('FRAME_HEIGHT', '544'))

# Server configuration
SERVER_HOST = os.getenv('SERVER_HOST', '0.0.0.0')  # Listen on all interfaces
SERVER_PORT = int(os.getenv('SERVER_PORT', '5000'))
# Update SERVER_URLS to include potential VPS URL
SERVER_URLS = os.getenv('SERVER_URLS', 'http://127.0.0.1:5000,http://localhost:5000').split(',')
# Allow CORS from any origin by default, can be restricted through env var
CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*')

# Constants
MAX_HLS_DIR_SIZE_MB = 100  # Maximum size for HLS directory in MB
HLS_CLEANUP_INTERVAL = 60  # Check HLS directory size every 60 seconds
HLS_SEGMENT_DURATION = 4  # Duration of each HLS segment in seconds

# Directory for HLS files
HLS_DIR = os.getenv('HLS_DIR', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hls_streams'))
os.makedirs(HLS_DIR, exist_ok=True)
logger.info(f"HLS directory created at: {HLS_DIR}")

# Setup CUDA if available
device = 'cuda' if torch.cuda.is_available() else 'cpu'
logger.info(f"Using {device} for inference")

app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": CORS_ORIGINS.split(',') if CORS_ORIGINS != '*' else '*',
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "expose_headers": ["Content-Range", "X-Content-Range"],
        "supports_credentials": True
    }
})

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
        self.hls_path = HLS_DIR
        os.makedirs(self.hls_path, exist_ok=True)
        self.ffmpeg_process = None
        self.ffmpeg_restart_count = 0
        self.max_ffmpeg_restarts = 5
        self.ffmpeg_restart_delay = 1  # Initial delay in seconds
        self.max_ffmpeg_restart_delay = 30  # Maximum delay in seconds
        self.last_ffmpeg_restart = 0
        self.ffmpeg_monitor_thread = None
        self.ffmpeg_health_check_interval = 1  # Check FFmpeg health every second
        self.ffmpeg_health_timeout = 5  # Timeout for health check in seconds
        self.last_frame_time = time.time()
        self.frame_timeout = 10  # Maximum time without frames before considering FFmpeg dead
        
    def _generate_coordinates(self, stream_id):
        # Fixed default coordinates for the fixed camera
        # Using base coordinates from the original code
        base_lat, base_lng = 14.631141, 121.039295
        # Since we're using a fixed camera, we can just use a fixed offset
        # or return the base coordinates directly
        return [base_lng, base_lat]
        
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
        threading.Thread(target=self._process_stream, daemon=True).start()
        logger.info(f"Started processing stream {self.stream_id}: {self.rtsp_url}")
    
    def stop(self):
        self.is_running = False
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        logger.info(f"Stopped stream {self.stream_id}: {self.rtsp_url}")
    
    def _monitor_ffmpeg_health(self):
        """Monitor FFmpeg process health and handle recovery"""
        while self.is_running and self.ffmpeg_process:
            try:
                # Check if process is still running
                if self.ffmpeg_process.poll() is not None:
                    logger.error(f"FFmpeg process terminated unexpectedly for stream {self.stream_id}")
                    self._restart_ffmpeg()
                    continue

                # Check if we're receiving frames
                current_time = time.time()
                if current_time - self.last_frame_time > self.frame_timeout:
                    logger.warning(f"No frames received for {self.frame_timeout} seconds, restarting FFmpeg")
                    self._restart_ffmpeg()
                    continue

                # Check if stdin pipe is still open
                if self.ffmpeg_process.stdin:
                    try:
                        self.ffmpeg_process.stdin.write(b'')  # Test write
                    except (BrokenPipeError, IOError):
                        logger.error(f"FFmpeg stdin pipe broken for stream {self.stream_id}")
                        self._restart_ffmpeg()
                        continue

                time.sleep(self.ffmpeg_health_check_interval)

            except Exception as e:
                logger.error(f"Error in FFmpeg health monitoring: {str(e)}")
                self._restart_ffmpeg()
                time.sleep(self.ffmpeg_health_check_interval)

    def _restart_ffmpeg(self):
        """Restart FFmpeg process with exponential backoff"""
        current_time = time.time()
        
        # Check if we've restarted too recently
        if current_time - self.last_ffmpeg_restart < self.ffmpeg_restart_delay:
            logger.warning(f"Too soon to restart FFmpeg, waiting {self.ffmpeg_restart_delay} seconds")
            return

        # Check if we've exceeded max restarts
        if self.ffmpeg_restart_count >= self.max_ffmpeg_restarts:
            logger.error(f"Max FFmpeg restarts ({self.max_ffmpeg_restarts}) exceeded for stream {self.stream_id}")
            self.is_running = False
            return

        try:
            # Clean up existing process
            if self.ffmpeg_process:
                try:
                    self.ffmpeg_process.terminate()
                    self.ffmpeg_process.wait(timeout=5)
                except Exception as e:
                    logger.warning(f"Error terminating FFmpeg process: {str(e)}")
                try:
                    self.ffmpeg_process.kill()
                except:
                    pass
                self.ffmpeg_process = None

            # Start new FFmpeg process
            if self._start_ffmpeg():
                self.ffmpeg_restart_count = 0  # Reset restart count on success
                self.ffmpeg_restart_delay = 1  # Reset delay on success
                self.last_ffmpeg_restart = current_time
                logger.info(f"Successfully restarted FFmpeg for stream {self.stream_id}")
            else:
                self.ffmpeg_restart_count += 1
                self.ffmpeg_restart_delay = min(self.ffmpeg_restart_delay * 2, self.max_ffmpeg_restart_delay)
                logger.warning(f"Failed to restart FFmpeg for stream {self.stream_id}, attempt {self.ffmpeg_restart_count}")

        except Exception as e:
            logger.error(f"Error during FFmpeg restart: {str(e)}")
            self.ffmpeg_restart_count += 1
            self.ffmpeg_restart_delay = min(self.ffmpeg_restart_delay * 2, self.max_ffmpeg_restart_delay)

    def _start_ffmpeg(self):
        """Start ffmpeg process for RTMP streaming"""
        try:
            # Ensure HLS directory exists
            os.makedirs(self.hls_path, exist_ok=True)
            logger.info(f"HLS path for stream {self.stream_id}: {self.hls_path}")

            # Define RTMP Output URL with fixed stream key instead of timestamp
            rtmp_stream_key = f"{self.stream_id}"
            rtmp_url = f"rtmp://127.0.0.1/live/{rtmp_stream_key}"
            
            # Store stream key for reference
            self.rtmp_stream_key = rtmp_stream_key
            
            # FFmpeg command with improved settings
            ffmpeg_cmd = [
                'ffmpeg',
                '-i', self.rtsp_url,
                '-c:v', 'libx264',
                '-preset', 'ultrafast',
                '-tune', 'zerolatency',
                '-profile:v', 'baseline',
                '-b:v', '1500k',
                '-maxrate', '1500k',
                '-bufsize', '3000k',
                '-r', '30',
                '-g', '60',
                '-keyint_min', '60',
                '-sc_threshold', '0',
                '-f', 'flv',
                '-flvflags', 'no_duration_filesize',  # Add this to prevent file size issues
                '-stimeout', '5000000',  # Add socket timeout
                rtmp_url
            ]

            # Start FFmpeg process with improved error handling
            logger.info(f"Starting FFmpeg for stream {self.stream_id} with key {rtmp_stream_key}: {' '.join(ffmpeg_cmd)}")
            self.ffmpeg_process = subprocess.Popen(
                ffmpeg_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=10**8,
                close_fds=True
            )

            # Start monitoring thread if not already running
            if not self.ffmpeg_monitor_thread or not self.ffmpeg_monitor_thread.is_alive():
                self.ffmpeg_monitor_thread = threading.Thread(
                    target=self._monitor_ffmpeg_health,
                    daemon=True
                )
                self.ffmpeg_monitor_thread.start()

            # Log FFmpeg output in a separate thread
            def log_ffmpeg_output():
                while self.ffmpeg_process and self.ffmpeg_process.poll() is None:
                    try:
                        stderr_line = self.ffmpeg_process.stderr.readline().decode('utf-8', errors='ignore').strip()
                        if stderr_line:
                            logger.debug(f"FFmpeg [{self.stream_id}]: {stderr_line}")
                    except Exception as e:
                        logger.error(f"Error reading FFmpeg output: {str(e)}")
                        break
                    time.sleep(0.1)

            # Start output logging thread
            threading.Thread(target=log_ffmpeg_output, daemon=True).start()

            logger.info(f"Started RTMP streaming for {self.stream_id} with stream key {rtmp_stream_key}")
            return True

        except Exception as e:
            logger.error(f"Failed to start FFmpeg: {str(e)}")
            if self.ffmpeg_process:
                try:
                    self.ffmpeg_process.terminate()
                    self.ffmpeg_process.wait(timeout=5)
                except:
                    pass
                try:
                    self.ffmpeg_process.kill()
                except:
                    pass
                self.ffmpeg_process = None
            return False

    def _process_stream(self):
        """Process frames from the RTSP stream"""
        reconnect_delay = 1
        max_reconnect_delay = 30
        
        # Start ffmpeg process for HLS streaming
        if not self._start_ffmpeg():
            logger.error(f"Failed to start HLS streaming for {self.stream_id}")
            self.is_running = False
            return
        
        while self.is_running:
            if not self.cap or not self.cap.isOpened():
                if not self.connect():
                    time.sleep(reconnect_delay)
                    reconnect_delay = min(reconnect_delay * 2, max_reconnect_delay)
                    continue
                else:
                    reconnect_delay = 1
            
            try:
                ret, frame = self.cap.read()
                if not ret:
                    logger.warning(f"Failed to read frame from {self.rtsp_url}")
                    self.cap.release()
                    self.cap = None
                    continue
                
                # Update last frame time for health monitoring
                self.last_frame_time = time.time()
                
                # Resize frame to desired dimensions
                frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
                
                # Process with object detection model
                with torch.no_grad():
                    results = model(frame, verbose=False)
                
                detected_dog = False
                
                # Create a copy of the frame for drawing bounding boxes
                annotated_frame = frame.copy()
                
                # Process all detection results
                for result in results:
                    for box in result.boxes:
                        class_id = int(box.cls.item())
                        confidence = box.conf.item()
                        
                        # Only process if confidence is above threshold
                        if confidence >= 0.6:
                            # Get bounding box coordinates
                            x1, y1, x2, y2 = map(int, box.xyxy[0])
                            
                            # Check if it's a dog
                            if class_id == DOG_CLASS_ID:
                                detected_dog = True
                                if confidence > self.highest_confidence_score:
                                    self.highest_confidence_score = confidence
                                    cropped_image = frame[y1:y2, x1:x2]
                                    self.highest_confidence_frame = cropped_image
                            
                            # Draw bounding box for all detected objects
                            color = (0, 255, 0) if class_id == DOG_CLASS_ID else (255, 0, 0)
                            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)
                            
                            # Create label with class and confidence
                            class_name = "Dog" if class_id == DOG_CLASS_ID else f"Class {class_id}"
                            label = f"{class_name}: {confidence:.2f}"
                            
                            # Draw label background
                            text_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
                            cv2.rectangle(annotated_frame, (x1, y1 - 20), (x1 + text_size[0], y1), color, -1)
                            
                            # Draw label text
                            cv2.putText(annotated_frame, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
                
                if detected_dog:
                    self.consecutive_detections += 1
                    
                    if (self.consecutive_detections >= REQUIRED_CONSECUTIVE_FRAMES and 
                        self.highest_confidence_frame is not None):
                        self._process_detection()
                else:
                    self.consecutive_detections = 0
                    self.highest_confidence_frame = None
                    self.highest_confidence_score = 0
                
                # Store the annotated frame in buffer for streaming
                with self.lock:
                    # Always use our manually annotated frame to ensure bounding boxes are visible
                    self.frame_buffer = annotated_frame
                
                # Write frame to ffmpeg process with improved error handling
                if self.ffmpeg_process and self.ffmpeg_process.poll() is None:
                    try:
                        # Encode the frame to raw bytes before sending to ffmpeg
                        if isinstance(self.frame_buffer, np.ndarray):
                            # Convert to BGR format if it's not already
                            if self.frame_buffer.shape[2] == 4:  # RGBA format
                                self.frame_buffer = cv2.cvtColor(self.frame_buffer, cv2.COLOR_RGBA2BGR)
                            
                            # Encode to raw bytes
                            _, encoded_frame = cv2.imencode('.bmp', self.frame_buffer)
                            self.ffmpeg_process.stdin.write(encoded_frame.tobytes())
                        else:
                            logger.warning(f"Invalid frame buffer type: {type(self.frame_buffer)}")
                    except (BrokenPipeError, IOError) as e:
                        logger.error(f"Error writing to ffmpeg: {str(e)}")
                        self._restart_ffmpeg()
                else:
                    # Restart ffmpeg if it has stopped
                    self._restart_ffmpeg()
                
            except Exception as e:
                logger.error(f"Error processing stream {self.stream_id}: {str(e)}")
                if self.cap:
                    self.cap.release()
                    self.cap = None
                time.sleep(1)
    
    def _process_detection(self):
        """Process a detected dog and send to the API"""
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
        
        # Reset detection tracking
        self.consecutive_detections = 0
        self.highest_confidence_frame = None
        self.highest_confidence_score = 0
    
    def get_frame(self):
        """Get the latest frame from the buffer"""
        with self.lock:
            if self.frame_buffer is None:
                return None
            return self.frame_buffer.copy()

def load_models():
    logger.info("Loading detection model...")
    global model, resnet_model, class_names, resnet_transform
    
    # Load the RTDETR model for object detection
    model = RTDETR(MODEL_PATH)
    model.conf = DEFAULT_CONFIDENCE
    model.to(device)
    
    # Load the ResNet model for leash classification
    logger.info("Loading classification model...")
    resnet_model = models.resnet50(weights=None)
    resnet_model.fc = nn.Linear(in_features=2048, out_features=2)
    
    # Load state dict with weights_only=True for security
    resnet_model.load_state_dict(
        torch.load(
            RESNET_PATH,
            map_location=torch.device(device),
            weights_only=True
        )
    )
    resnet_model.to(device)
    resnet_model.eval()
    
    # Image transformation pipeline
    resnet_transform = transforms.Compose([
        transforms.Resize((640, 640)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    class_names = ['dog_with_leash', 'dog_without_leash']
    logger.info("Models loaded successfully")

def encode_image_to_base64(image):
    _, buffer = cv2.imencode('.jpg', image)
    return base64.b64encode(buffer).decode('utf-8')

def classify_leash(cropped_image):
    image_pil = Image.fromarray(cv2.cvtColor(cropped_image, cv2.COLOR_BGR2RGB))
    image_tensor = resnet_transform(image_pil).unsqueeze(0).to(device)

    with torch.no_grad():
        outputs = resnet_model(image_tensor)
        _, predicted_class = torch.max(outputs, 1)
        predicted_label = class_names[predicted_class.item()]

    return predicted_label

def scan_rtsp_streams():
    """Initialize with fixed RTSP URL instead of scanning"""
    available_streams = []
    
    # Using the fixed RTSP URL directly
    rtsp_url = BASE_RTSP_URL
    stream_id = "main-camera"
    
    logger.info(f"Testing RTSP stream: {rtsp_url}")
    try:
        cap = cv2.VideoCapture(rtsp_url)
        
        if cap.isOpened():
            ret, _ = cap.read()
            if ret:
                available_streams.append({
                    "stream_id": stream_id,
                    "rtsp_url": rtsp_url,
                    "ip": "192.168.1.5",
                    "camera": "channel-2"
                })
                logger.info(f"Found working RTSP stream: {rtsp_url}")
            else:
                logger.error(f"Could not read frame from RTSP stream: {rtsp_url}")
            cap.release()
        else:
            logger.error(f"Could not connect to RTSP stream: {rtsp_url}")
    except Exception as e:
        logger.error(f"Error testing RTSP stream: {str(e)}")
                
    return available_streams

def initialize_streams():
    """Initialize and start processing for all available RTSP streams"""
    global active_streams
    
    # Get the available stream (fixed URL)
    available_streams = scan_rtsp_streams()
    logger.info(f"Found {len(available_streams)} available RTSP streams")
    
    # Initialize streams
    for stream_info in available_streams:
        stream_id = stream_info["stream_id"]
        rtsp_url = stream_info["rtsp_url"]
        
        # Check if stream already exists and is running
        if stream_id in active_streams:
            existing_stream = active_streams[stream_id]
            if existing_stream.is_running:
                logger.info(f"Stream {stream_id} is already running, skipping initialization")
                continue
            else:
                logger.info(f"Stream {stream_id} exists but is not running, restarting")
                existing_stream.stop()
        
        try:
            logger.info(f"Creating new stream instance for {stream_id}")
            stream = RTSPStream(rtsp_url, stream_id)
            
            # Start the stream processing
            logger.info(f"Starting stream processing for {stream_id}")
            stream.start()
            
            # Store the stream instance
            active_streams[stream_id] = stream
            logger.info(f"Successfully initialized and started stream {stream_id}")
            
            # Add a small delay between stream initializations
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"Failed to initialize stream {stream_id}: {str(e)}")
            if stream_id in active_streams:
                del active_streams[stream_id]
    
    # Clean up any streams that are no longer available
    current_ids = [s["stream_id"] for s in available_streams]
    for stream_id in list(active_streams.keys()):
        if stream_id not in current_ids:
            logger.info(f"Cleaning up stream {stream_id} that is no longer available")
            active_streams[stream_id].stop()
            del active_streams[stream_id]
    
    return available_streams

def generate_frames(stream_id):
    """Generator for video frames from a specific stream"""
    if stream_id not in active_streams:
        logger.error(f"Stream {stream_id} not found in generate_frames")
        return
        
    stream = active_streams[stream_id]
    
    # Add a small delay to ensure the stream is initialized
    time.sleep(0.5)
    
    while True:
        with stream.lock:
            if stream.frame_buffer is None:
                # If no frame is available yet, send a blank frame
                blank_frame = np.zeros((FRAME_HEIGHT, FRAME_WIDTH, 3), np.uint8)
                _, frame_bytes = cv2.imencode('.jpg', blank_frame)
                yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame_bytes.tobytes() + b'\r\n')
                time.sleep(0.5)  # Wait a bit longer for the first frame
                continue
                
            # Get the latest frame
            frame = stream.frame_buffer.copy()
        
        # Encode the frame as JPEG
        _, frame_bytes = cv2.imencode('.jpg', frame)
        frame_bytes = frame_bytes.tobytes()
        
        # Yield the frame with proper multipart format
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
        # Control the frame rate to avoid overwhelming the client
        time.sleep(0.033)  # ~30 FPS

def cleanup_hls_directory():
    """Check HLS directory size and clean up old files if needed"""
    while True:
        try:
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(HLS_DIR):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    total_size += os.path.getsize(fp)
            
            # Convert to MB
            total_size_mb = total_size / (1024 * 1024)
            
            # If size exceeds limit, remove oldest files
            if total_size_mb > MAX_HLS_DIR_SIZE_MB:
                logger.info(f"HLS directory size ({total_size_mb:.2f} MB) exceeds limit. Cleaning up...")
                
                # Get all .ts files sorted by modification time
                ts_files = []
                for dirpath, dirnames, filenames in os.walk(HLS_DIR):
                    for f in filenames:
                        if f.endswith('.ts'):
                            fp = os.path.join(dirpath, f)
                            ts_files.append((fp, os.path.getmtime(fp)))
                
                # Sort by modification time (oldest first)
                ts_files.sort(key=lambda x: x[1])
                
                # Remove oldest files until we're under the limit
                for file_path, _ in ts_files:
                    if total_size_mb <= MAX_HLS_DIR_SIZE_MB * 0.8:  # Remove until we're at 80% of the limit
                        break
                    
                    file_size = os.path.getsize(file_path) / (1024 * 1024)
                    os.remove(file_path)
                    total_size_mb -= file_size
                    logger.info(f"Removed old HLS segment: {file_path}")
        
        except Exception as e:
            logger.error(f"Error in HLS cleanup: {str(e)}")
        
        # Sleep for the specified interval
        time.sleep(HLS_CLEANUP_INTERVAL)

# Function to get the server's public URL
def get_server_url(request=None):
    """Get the server's public URL based on the request or environment variables"""
    if request:
        # Try to determine URL from request
        host = request.headers.get('Host')
        if host:
            scheme = request.headers.get('X-Forwarded-Proto', 'http')
            return f"{scheme}://{host}"
    
    # If we can't determine from request, use the first URL from SERVER_URLS
    return SERVER_URLS[0] if SERVER_URLS else "http://localhost:5000"

# Function to get absolute URL for a stream
def get_absolute_url(relative_url, request=None):
    """Convert a relative URL to an absolute URL"""
    base_url = get_server_url(request)
    if relative_url.startswith('http'):
        return relative_url
    elif relative_url.startswith('/'):
        return f"{base_url}{relative_url}"
    else:
        return f"{base_url}/{relative_url}"

@app.route('/hls/<stream_id>/<path:filename>', methods=['GET', 'OPTIONS'])
def hls_stream(stream_id, filename):
    """Serve HLS stream files"""
    # Handle OPTIONS request for CORS preflight
    if request.method == 'OPTIONS':
        response = Response()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        response.headers.add('Access-Control-Max-Age', '3600')
        return response
        
    stream_dir = os.path.join(HLS_DIR, stream_id)
    file_path = os.path.join(stream_dir, filename)
    
    logger.debug(f"HLS request for {stream_id}/{filename}")
    
    # Check if the stream directory exists
    if not os.path.exists(stream_dir):
        # Try to start the stream if it doesn't exist
        if stream_id in active_streams:
            # Stream exists but directory doesn't, create it
            os.makedirs(stream_dir, exist_ok=True)
            logger.info(f"Created HLS directory for existing stream: {stream_id}")
        else:
            # Try to fetch from external source
            try:
                external_response = requests.get(f"{EXTERNAL_STREAMS_API}?internal=true", timeout=3)
                if external_response.status_code == 200:
                    external_data = external_response.json()
                    if 'streams' in external_data and isinstance(external_data['streams'], list):
                        for ext_stream in external_data['streams']:
                            if ext_stream['id'] == stream_id and 'url' in ext_stream and ext_stream['url'].startswith('rtsp://'):
                                # Create a new stream instance
                                try:
                                    new_stream = RTSPStream(ext_stream['url'], stream_id)
                                    new_stream.start()
                                    active_streams[stream_id] = new_stream
                                    logger.info(f"Added external stream on-demand: {stream_id}")
                                    # Create the directory
                                    os.makedirs(stream_dir, exist_ok=True)
                                    # Give it a moment to initialize
                                    time.sleep(2)
                                    break
                                except Exception as e:
                                    logger.error(f"Failed to initialize external stream {stream_id}: {str(e)}")
            except Exception as e:
                logger.error(f"Failed to fetch external stream {stream_id}: {str(e)}")
    
    # If the directory still doesn't exist, return an error
    if not os.path.exists(stream_dir):
        logger.error(f"HLS directory for stream {stream_id} does not exist")
        return jsonify({"error": f"Stream {stream_id} not found"}), 404
    
    # If the file doesn't exist and it's the playlist, wait briefly for it to be created
    if filename == 'playlist.m3u8' and not os.path.exists(file_path):
        logger.warning(f"Playlist for stream {stream_id} not found, waiting...")
        # Wait for a short time for the playlist to be created
        for _ in range(10):  # Try for up to 1 second
            time.sleep(0.1)
            if os.path.exists(file_path):
                break
    
    # If the file still doesn't exist, return an error
    if not os.path.exists(file_path):
        logger.error(f"HLS file not found: {file_path}")
        return jsonify({"error": f"File {filename} not available for stream {stream_id}"}), 404
    
    # Add CORS headers
    response = send_from_directory(stream_dir, filename)
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    response.headers.add('Cache-Control', 'no-cache, no-store, must-revalidate')
    
    # Set content type explicitly for m3u8 and ts files
    if filename.endswith('.m3u8'):
        response.headers.set('Content-Type', 'application/vnd.apple.mpegurl')
    elif filename.endswith('.ts'):
        response.headers.set('Content-Type', 'video/mp2t')
    
    return response

@app.route('/hls/<stream_id>.m3u8', methods=['GET', 'OPTIONS'])
def hls_stream_direct(stream_id):
    """Serve HLS stream playlist directly with .m3u8 extension"""
    # Handle OPTIONS request for CORS preflight
    if request.method == 'OPTIONS':
        response = Response()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        response.headers.add('Access-Control-Max-Age', '3600')
        return response
    
    # Redirect to the playlist.m3u8 file in the stream directory
    return hls_stream(stream_id, 'playlist.m3u8')

@app.route('/video/<stream_id>', methods=['GET', 'OPTIONS'])
def video(stream_id):
    """Stream video for a specific stream ID"""
    # Add CORS headers for video streaming
    if request.method == 'OPTIONS':
        # Handle preflight request
        response = Response()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,OPTIONS')
        return response
    
    # Check if the client wants a single frame (for img tag) or streaming
    single_frame = request.args.get('frame', 'false').lower() == 'true'
    
    # Check if the stream exists
    if stream_id not in active_streams:
        # Try to fetch from external source if not in our active streams
        try:
            # Use internal flag to prevent recursion
            external_url = f"{EXTERNAL_STREAMS_API}?internal=true"
            external_response = requests.get(external_url, timeout=3)
            if external_response.status_code == 200:
                external_data = external_response.json()
                if 'streams' in external_data and isinstance(external_data['streams'], list):
                    # Add external streams to our list
                    for ext_stream in external_data['streams']:
                        # Make sure we don't add duplicates
                        if not any(s['id'] == ext_stream['id'] for s in active_streams):
                            # Add HLS URL if not present
                            if 'hls_url' not in ext_stream:
                                ext_stream['hls_url'] = f"/hls/{ext_stream['id']}/playlist.m3u8"
                            active_streams[ext_stream['id']] = ext_stream
        except Exception as e:
            logger.error(f"Failed to fetch external streams: {str(e)}")
            
    # If stream still doesn't exist, return an error
    if stream_id not in active_streams:
        logger.error(f"Stream {stream_id} not found")
        return jsonify({"error": f"Stream {stream_id} not found"}), 404
    
    # If client wants a single frame, return the current frame as a JPEG
    if single_frame:
        stream = active_streams[stream_id]
        with stream.lock:
            if stream.frame_buffer is None:
                # If no frame is available, send a blank frame
                blank_frame = np.zeros((FRAME_HEIGHT, FRAME_WIDTH, 3), np.uint8)
                cv2.putText(blank_frame, "Waiting for stream...", (50, FRAME_HEIGHT//2), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                _, frame_bytes = cv2.imencode('.jpg', blank_frame)
                frame_data = io.BytesIO(frame_bytes.tobytes())
            else:
                # Get the latest frame
                frame = stream.frame_buffer.copy()
                _, frame_bytes = cv2.imencode('.jpg', frame)
                frame_data = io.BytesIO(frame_bytes.tobytes())
        
        frame_data.seek(0)
        response = send_file(frame_data, mimetype='image/jpeg')
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Cache-Control', 'no-cache, no-store, must-revalidate')
        return response
    
    # Otherwise, redirect to HLS stream
    hls_url = f"/hls/{stream_id}.m3u8"
    return jsonify({"hls_url": hls_url}), 200

@app.route('/streams', methods=['GET'])
def get_streams():
    """Get list of available streams"""
    # Check if we're being called from the internal API
    is_internal = request.args.get('internal', 'false').lower() == 'true'
    
    # Initialize streams list
    streams_list = []
    
    # Add active streams to the list
    for stream_id, stream in active_streams.items():
        if isinstance(stream, RTSPStream):
            # Get the stream key if available
            rtmp_stream_key = getattr(stream, 'rtmp_stream_key', stream_id)
            
            # Build URLs
            # For Nginx-served HLS (preferred for browser)
            nginx_hls_url = f"/hls/{rtmp_stream_key}.m3u8"

            flask_hls_url = f"/api/hls/{stream_id}/playlist.m3u8"
            # Video direct URL
            video_url = f"/api/video/{stream_id}"
            
            stream_info = {
                'id': stream_id,
                'name': f'Camera {stream_id}',
                'location': 'Main Location',
                'status': 'active',
                'url': stream.rtsp_url,
                'video_url': get_absolute_url(video_url, request),
                'hls_url': get_absolute_url(nginx_hls_url, request),  # Primary HLS URL (Nginx)
                'flask_hls_url': get_absolute_url(flask_hls_url, request),  # Backup HLS URL (Flask)
                'rtmp_key': rtmp_stream_key,  # Include the RTMP stream key
                'type': 'rtsp'
            }
            streams_list.append(stream_info)
    
    # If no streams are active, add a default main-camera stream
    if not streams_list:
        # Create a default main-camera stream if it doesn't exist
        if 'main-camera' not in active_streams:
            try:
                # Use the default RTSP URL from environment
                rtsp_url = BASE_RTSP_URL
                new_stream = RTSPStream(rtsp_url, 'main-camera')
                new_stream.start()
                active_streams['main-camera'] = new_stream
                logger.info(f"Created default main-camera stream with URL: {rtsp_url}")
                
                # Wait a moment for ffmpeg to start and create the RTMP stream
                time.sleep(2)
                
                # Get the stream key if available
                rtmp_stream_key = getattr(new_stream, 'rtmp_stream_key', 'main-camera')
                
                # Add it to the streams list with proper URLs
                streams_list.append({
                    'id': 'main-camera',
                    'name': 'Main Camera',
                    'location': 'Main Location',
                    'status': 'active',
                    'url': rtsp_url,
                    'video_url': get_absolute_url(f'/api/video/main-camera', request),
                    'hls_url': get_absolute_url(f'/hls/{rtmp_stream_key}.m3u8', request),
                    'flask_hls_url': get_absolute_url(f'/api/hls/main-camera/playlist.m3u8', request),
                    'rtmp_key': rtmp_stream_key,
                    'type': 'rtsp'
                })
            except Exception as e:
                logger.error(f"Failed to create default main-camera stream: {str(e)}")
                # Add a placeholder for the main camera even if it fails
                streams_list.append({
                    'id': 'main-camera',
                    'name': 'Main Camera',
                    'location': 'Main Location',
                    'status': 'inactive',
                    'url': '',
                    'video_url': get_absolute_url(f'/api/video/main-camera', request),
                    'hls_url': get_absolute_url(f'/hls/main-camera.m3u8', request),
                    'flask_hls_url': get_absolute_url(f'/api/hls/main-camera/playlist.m3u8', request),
                    'type': 'rtsp'
                })
    
    return jsonify({'streams': streams_list})

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
    """Periodically check the fixed stream connection"""
    while True:
        try:
            logger.info("Starting periodic stream scan")
            initialize_streams()
            
            # Log current active streams
            active_count = len([s for s in active_streams.values() if s.is_running])
            logger.info(f"Currently active streams: {active_count}")
            
            # Check each active stream
            for stream_id, stream in active_streams.items():
                if not stream.is_running:
                    logger.warning(f"Stream {stream_id} is not running, attempting restart")
                    try:
                        stream.start()
                        logger.info(f"Successfully restarted stream {stream_id}")
                    except Exception as e:
                        logger.error(f"Failed to restart stream {stream_id}: {str(e)}")
            
        except Exception as e:
            logger.error(f"Error in periodic stream scanner: {e}")
        
        # Wait before next scan
        time.sleep(60)  # Check every minute

if __name__ == '__main__':
    # Load ML models
    load_models()
    
    # Import numpy here to avoid circular imports
    import numpy as np
    
    # Initial stream initialization
    logger.info("Starting initial stream initialization")
    initialize_streams()
    
    # Start periodic scanner in background
    scanner_thread = threading.Thread(target=periodic_stream_scanner, daemon=True)
    scanner_thread.start()
    logger.info("Started periodic stream scanner")
    
    # Start the cleanup thread
    cleanup_thread = threading.Thread(target=cleanup_hls_directory, daemon=True)
    cleanup_thread.start()
    logger.info("Started HLS cleanup thread")
    
    # Print server URLs for convenience
    print("\nServer URLs:")
    for url in SERVER_URLS:
        print(f" * {url}")
    
    # Run the Flask app
    app.run(host=SERVER_HOST, port=SERVER_PORT, debug=True, threaded=True)