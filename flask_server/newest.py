import cv2
import torch
import time
import base64
import threading
import subprocess
import os
import numpy as np
import shutil
from collections import deque
from ultralytics import RTDETR
from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
app = Flask(__name__)
CORS(app)
HLS_CLEANUP_DIR = '/var/hls'
HLS_CLEANED = False
if not HLS_CLEANED and os.path.exists(HLS_CLEANUP_DIR):
    try:
        shutil.rmtree(HLS_CLEANUP_DIR)
        print("/var/hls cleaned.")
    except PermissionError as e:
        print(f"Permission denied while cleaning /var/hls: {e}")
os.makedirs(HLS_CLEANUP_DIR, exist_ok=True)
os.chmod(HLS_CLEANUP_DIR, 0o777)
HLS_CLEANED = True

FRAME_WIDTH, FRAME_HEIGHT = 960, 544
REQUIRED_CONSECUTIVE_FRAMES = 20
DOG_CLASS_ID = 1
STREAM_IP_RANGE = range(3, 11)
RTSP_BASE = 'rtsp://10.0.0.{ip}:8554/cam1'

stream_data = {}
stream_threads = []
model = RTDETR('best.pt')
model.conf = 0.5
model.to('cuda' if torch.cuda.is_available() else 'cpu')

BUFFER_SIZE = 150  # 5 seconds at 30fps


def start_ffmpeg(stream_id):
    hls_dir = os.path.join(os.path.dirname(__file__), 'hls_streams', stream_id)
    os.makedirs(hls_dir, exist_ok=True)
    rtmp_url = f'rtmp://127.0.0.1/live/{stream_id}'
    cmd = [
        'ffmpeg', '-f', 'image2pipe', '-vcodec', 'mjpeg', '-r', '30', '-i', '-',
        '-c:v', 'libx264', '-preset', 'ultrafast', '-tune', 'zerolatency',
        '-hls_time', '2', '-hls_list_size', '3',
        '-hls_flags', 'delete_segments+append_list',
        '-f', 'flv', rtmp_url
    ]
    return subprocess.Popen(cmd, stdin=subprocess.PIPE), hls_dir


def capture_frames(rtsp_url, stream_id):
    cap = cv2.VideoCapture(rtsp_url)
    if not cap.isOpened():
        print(f"Failed to open RTSP stream: {rtsp_url}")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            print(f"[{stream_id}] Failed to read frame")
            time.sleep(1)
            continue

        resized = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
        stream_data[stream_id]['buffer'].append(resized)
        time.sleep(1 / 30)

def monitor_stream(rtsp_url, stream_id):
    while True:
        cap = cv2.VideoCapture(rtsp_url)
        if cap.isOpened():
            cap.release()
            print(f"[{stream_id}] Stream connected. Launching threads.")
            stream_data[stream_id] = {
                'url': rtsp_url,
                'buffer': deque(maxlen=BUFFER_SIZE)
            }
            t1 = threading.Thread(target=capture_frames, args=(rtsp_url, stream_id), daemon=True)
            t2 = threading.Thread(target=process_stream, args=(stream_id,), daemon=True)
            stream_threads.extend([t1, t2])
            t1.start()
            t2.start()
            break
        else:
            print(f"[{stream_id}] Stream not available. Retrying in 30 seconds...")
            time.sleep(30)


def process_stream(stream_id):
    ffmpeg_proc, hls_dir = start_ffmpeg(stream_id)

    stream_data[stream_id].update({
        "ffmpeg": ffmpeg_proc,
        "frame_buffer": None,
        "lock": threading.Lock(),
        "hls_dir": hls_dir,
        "consec": 0,
        "high_conf_frame": None,
        "high_score": 0
    })

    while True:
        if len(stream_data[stream_id]['buffer']) < BUFFER_SIZE:
            time.sleep(0.1)
            continue

        frame = stream_data[stream_id]['buffer'].popleft()
        results = model.predict(frame, imgsz=(FRAME_WIDTH, FRAME_HEIGHT))
        detected = False

        for result in results:
            for box in result.boxes:
                class_id = int(box.cls.item())
                confidence = box.conf.item()
                x1, y1, x2, y2 = map(int, box.xyxy[0])

                if class_id == DOG_CLASS_ID and confidence > 0.6:
                    detected = True
                    if confidence > stream_data[stream_id]['high_score']:
                        stream_data[stream_id]['high_score'] = confidence
                        stream_data[stream_id]['high_conf_frame'] = frame[y1:y2, x1:x2]

        if detected:
            stream_data[stream_id]['consec'] += 1
            if stream_data[stream_id]['consec'] >= REQUIRED_CONSECUTIVE_FRAMES:
                if stream_data[stream_id]['high_conf_frame'] is not None:
                    _, buffer = cv2.imencode('.jpg', stream_data[stream_id]['high_conf_frame'])
                    base64_img = base64.b64encode(buffer).decode('utf-8')
                    try:
                        requests.post('http://127.0.0.1:8000/api/pin', json={
                            'animal_type': 'dog',
                            'coordinates': [121.039295, 14.631141],
                            'snapshot': base64_img
                        })
                        print(f"[{stream_id}] Pin sent.")
                    except Exception as e:
                        print(f"[{stream_id}] Failed to send pin:", e)
                    stream_data[stream_id]['consec'] = 0
                    stream_data[stream_id]['high_conf_frame'] = None
                    stream_data[stream_id]['high_score'] = 0
        else:
            stream_data[stream_id]['consec'] = 0
            stream_data[stream_id]['high_conf_frame'] = None
            stream_data[stream_id]['high_score'] = 0

        annotated = results[0].plot()
        with stream_data[stream_id]['lock']:
            stream_data[stream_id]['frame_buffer'] = annotated.copy()

        if ffmpeg_proc and ffmpeg_proc.stdin:
            _, encoded = cv2.imencode('.jpg', annotated)
            ffmpeg_proc.stdin.write(encoded.tobytes())

        time.sleep(1 / 30)


@app.route('/api/streams')
def get_streams():
    return jsonify({
        "streams": [
            {
                "id": stream_id,
                "name": f"Camera {stream_id}",
                "location": f"RTSP from {data['url']}",
                "status": "active",
                "url": data['url'],
                "hls_url": f"http://straysafe.me/hls/{stream_id}.m3u8",
                "flask_hls_url": f"http://straysafe.me/api/hls/{stream_id}/playlist.m3u8",
                "video_url": f"http://straysafe.me/api/video/{stream_id}",
                "rtmp_key": stream_id,
                "type": "rtsp"
            }
            for stream_id, data in stream_data.items()
        ]
    })


@app.route('/api/video/<stream_id>')
def video_snapshot(stream_id):
    if stream_id not in stream_data:
        return "Stream not found", 404
    with stream_data[stream_id]['lock']:
        frame = stream_data[stream_id]['frame_buffer']
        if frame is None:
            frame = np.zeros((FRAME_HEIGHT, FRAME_WIDTH, 3), np.uint8)
    _, img = cv2.imencode('.jpg', frame)
    return img.tobytes(), 200, {'Content-Type': 'image/jpeg'}


@app.route('/api/hls/<stream_id>/<path:filename>')
def serve_hls_file(stream_id, filename):
    if stream_id not in stream_data:
        return "Stream not found", 404
    return send_from_directory(stream_data[stream_id]['hls_dir'], filename)


if __name__ == '__main__':
    for ip in STREAM_IP_RANGE:
        stream_id = f'cam-{ip}'
        rtsp_url = RTSP_BASE.format(ip=ip)
        stream_data[stream_id] = {
            'url': rtsp_url,
            'buffer': deque(maxlen=BUFFER_SIZE)
        }
        threading.Thread(target=monitor_stream, args=(rtsp_url, stream_id), daemon=True).start()

    app.run(host='0.0.0.0', port=5000, debug=True)
