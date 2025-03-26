import cv2
import torch
import time
import base64
import threading
import subprocess
import os
import numpy as np
from ultralytics import RTDETR
from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS

# Flask app setup
app = Flask(__name__)
CORS(app)

# Constants
STREAM_ID = 'main-camera'
RTSP_URL = 'rtsp://10.0.0.3:8554/cam1'
HLS_DIR = os.path.join(os.path.dirname(__file__), 'hls_streams', STREAM_ID)
os.makedirs(HLS_DIR, exist_ok=True)
FRAME_WIDTH, FRAME_HEIGHT = 960, 544
REQUIRED_CONSECUTIVE_FRAMES = 20
DOG_CLASS_ID = 1

# Model loading
model = RTDETR('best.pt')
model.conf = 0.5
model.to('cuda' if torch.cuda.is_available() else 'cpu')

# Shared state
consecutive_detections = 0
highest_confidence_frame = None
highest_confidence_score = 0
frame_buffer = None
lock = threading.Lock()

# FFmpeg subprocess
ffmpeg_process = None

def start_ffmpeg():
    global ffmpeg_process
    rtmp_url = f'rtmp://127.0.0.1/live/{STREAM_ID}'
    
    cmd = [
        'ffmpeg',
        '-f', 'image2pipe',
        '-vcodec', 'mjpeg',
        '-r', '30',
        '-i', '-',
        '-c:v', 'libx264',
        '-preset', 'ultrafast',
        '-hls_time', '10',              # each .ts segment = 2 seconds
        '-hls_list_size', '20', 
        '-f', 'flv',
        rtmp_url
    ]

    ffmpeg_process = subprocess.Popen(cmd, stdin=subprocess.PIPE)


def detect_and_stream():
    global consecutive_detections, highest_confidence_frame, highest_confidence_score, frame_buffer

    cap = cv2.VideoCapture(RTSP_URL)
    if not cap.isOpened():
        print("Failed to open RTSP stream")
        return

    start_ffmpeg()

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to read frame")
            time.sleep(1)
            continue

        resized = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
        results = model.predict(resized, imgsz=(FRAME_WIDTH, FRAME_HEIGHT))
        detected = False

        for result in results:
            for box in result.boxes:
                class_id = int(box.cls.item())
                confidence = box.conf.item()
                x1, y1, x2, y2 = map(int, box.xyxy[0])

                if class_id == DOG_CLASS_ID and confidence > 0.6:
                    detected = True
                    if confidence > highest_confidence_score:
                        highest_confidence_score = confidence
                        highest_confidence_frame = resized[y1:y2, x1:x2]

        if detected:
            consecutive_detections += 1
            if consecutive_detections >= REQUIRED_CONSECUTIVE_FRAMES:
                if highest_confidence_frame is not None:
                    _, buffer = cv2.imencode('.jpg', highest_confidence_frame)
                    base64_img = base64.b64encode(buffer).decode('utf-8')
                    try:
                        requests.post('http://127.0.0.1:8000/api/pin', json={
                            'animal_type': 'dog',
                            'coordinates': [121.039295, 14.631141],
                            'snapshot': base64_img
                        })
                        print("Pin sent.")
                    except Exception as e:
                        print("Failed to send pin:", e)
                    consecutive_detections = 0
                    highest_confidence_frame = None
                    highest_confidence_score = 0
        else:
            consecutive_detections = 0
            highest_confidence_frame = None
            highest_confidence_score = 0

        annotated = results[0].plot()

        with lock:
            frame_buffer = annotated.copy()

        if ffmpeg_process and ffmpeg_process.stdin:
            _, encoded = cv2.imencode('.jpg', annotated)
            ffmpeg_process.stdin.write(encoded.tobytes())

        time.sleep(1 / 30)  # 30 FPS


@app.route('/api/streams')
def get_streams():
    return jsonify({
        "streams": [
            {
                "id": STREAM_ID,
                "name": "Camera main-camera",
                "location": "Main Location",
                "status": "active",
                "url": RTSP_URL,
                "hls_url": f"http://straysafe.me/hls/{STREAM_ID}.m3u8",
                "flask_hls_url": f"http://straysafe.me/api/hls/{STREAM_ID}/playlist.m3u8",
                "video_url": f"http://straysafe.me/api/video/{STREAM_ID}",
                "rtmp_key": STREAM_ID,
                "type": "rtsp"
            }
        ]
    })

@app.route('/api/video/<stream_id>')
def video_snapshot(stream_id):
    global frame_buffer
    with lock:
        frame = frame_buffer.copy() if frame_buffer is not None else np.zeros((FRAME_HEIGHT, FRAME_WIDTH, 3), np.uint8)
    _, img = cv2.imencode('.jpg', frame)
    return img.tobytes(), 200, {'Content-Type': 'image/jpeg'}

@app.route('/api/hls/<stream_id>/<path:filename>')
def serve_hls_file(stream_id, filename):
    return send_from_directory(HLS_DIR, filename)

if __name__ == '__main__':
    threading.Thread(target=detect_and_stream, daemon=True).start()
    app.run(host='0.0.0.0', port=5000, debug=True)
