import cv2
import torch
import time
import base64
import threading
import subprocess
import os
import numpy as np
import shutil
from collections import deque, defaultdict
from ultralytics import RTDETR
from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
import requests
import tensorflow as tf


app = Flask(__name__)
CORS(app)
# --- CNN and ORB Feature Matcher Setup ---
tf.config.set_visible_devices([], 'GPU')
MODEL_PATH = "model.h5"
DATABASE_PATH = "with_leash"
cnn_model = tf.keras.models.load_model(MODEL_PATH)
orb = cv2.ORB_create(nfeatures=10000)
bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
MATCH_THRESHOLD = 10  # Lower means stricter matching
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
CAT_CLASS_ID = 0
STREAM_IP_RANGE = range(3, 11)
RTSP_BASE = 'rtsp://10.0.0.{ip}:8554/cam1'
STATIC_VIDEO_PATH = 'sample_video.avi'

stream_data = {}
stream_threads = []
model = RTDETR('best.pt')
model.conf = 0.8
model.to('cuda' if torch.cuda.is_available() else 'cpu')

BUFFER_SIZE = 150  # 5 seconds at 30fps
animal_counters = defaultdict(lambda: {"dog": 0, "cat": 0})
last_detected_animals = defaultdict(lambda: {"dog": [], "cat": []})


# --- Notification Stubs ---
def notify_owner(animal_id):
    print(f"Owner notified for animal ID: {animal_id}")

def notify_pound(image_path):
    print(f"Animal pound notified with image: {image_path}")

# --- Helper Functions ---
def preprocess_image(image):
    img = cv2.resize(image, (128, 128))
    img = np.expand_dims(img, axis=-1) if len(img.shape) == 2 else img
    img = img / 255.0
    return np.expand_dims(img, axis=0)

def remove_green_border(image):
    # Filters out green background used in bounding boxes
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lower_green = np.array([55, 80, 70])
    upper_green = np.array([70, 255, 255])
    mask = cv2.inRange(hsv, lower_green, upper_green)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        x, y, w, h = cv2.boundingRect(max(contours, key=cv2.contourArea))
        return image[y:y+h, x:x+w]
    return image

def find_best_match(query_img):
    # Compares detected animal image to known database using ORB feature descriptors
    kp_query, des_query = orb.detectAndCompute(query_img, None)
    if des_query is None:
        return None
    best_match, best_score = None, float("inf")
    for filename in os.listdir(DATABASE_PATH):
        if filename.endswith((".jpg", ".png", ".jpeg")):
            db_img = cv2.imread(os.path.join(DATABASE_PATH, filename), cv2.IMREAD_GRAYSCALE)
            kp_db, des_db = orb.detectAndCompute(db_img, None)
            if des_db is not None:
                matches = bf.match(des_query, des_db)
                score = sum(m.distance for m in matches) / len(matches) if matches else float("inf")
                if score < best_score and score < MATCH_THRESHOLD:
                    best_score, best_match = score, filename
    return best_match if best_score < MATCH_THRESHOLD else None


def stream_static_video(stream_id, video_path):
    cap = cv2.VideoCapture(video_path) 
    if not cap.isOpened():
        print(f"[{stream_id}] Failed to open static video")
        return

    ffmpeg_proc, hls_dir = start_ffmpeg(stream_id)
    stream_data[stream_id] = {
        'url': f'static://{video_path}',
        'buffer': deque(maxlen=BUFFER_SIZE),
        'ffmpeg': ffmpeg_proc,
        'frame_buffer': None,
        'lock': threading.Lock(),
        'hls_dir': hls_dir,
        'consec': 0,
        'high_conf_frame': None,
        'high_score': 0,
        'detected_type': None
    }

    while True:
        ret, frame = cap.read()
        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue

        resized = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
        results = model.predict(resized, imgsz=(FRAME_WIDTH, FRAME_HEIGHT), device='cuda')
        detected = False

        for result in results:
            for box in result.boxes:
                class_id = int(box.cls.item())
                confidence = box.conf.item()
                x1, y1, x2, y2 = map(int, box.xyxy[0])

                if confidence > 0.8:
                    label = 'dog' if class_id == DOG_CLASS_ID else 'cat' if class_id == CAT_CLASS_ID else None
                    if label:
                        # Draw green bounding box
                        cv2.rectangle(resized, (x1, y1), (x2, y2), (0, 255, 0), 2)

                        if is_new_animal((x1, y1, x2, y2), last_detected_animals[stream_id][label]):
                            last_detected_animals[stream_id][label].append({
                                "coords": ((x1 + x2) // 2, (y1 + y2) // 2),
                                "timestamp": time.time()
                            })
                            animal_counters[stream_id][label] += 1
                            print(f"[{stream_id}] New {label} detected. Total: {animal_counters[stream_id][label]}")

                    if label and confidence > stream_data[stream_id]['high_score']:
                        detected = True
                        stream_data[stream_id]['high_score'] = confidence
                        stream_data[stream_id]['high_conf_frame'] = resized[y1:y2, x1:x2]
                        stream_data[stream_id]['detected_type'] = label

        if detected:
            stream_data[stream_id]['consec'] += 1
            if stream_data[stream_id]['consec'] >= REQUIRED_CONSECUTIVE_FRAMES:
                if stream_data[stream_id]['high_conf_frame'] is not None:
                    classify_and_match(
                        stream_data[stream_id]['high_conf_frame'],
                        stream_id,
                        stream_data[stream_id]['detected_type']
                    )
                    stream_data[stream_id]['consec'] = 0
                    stream_data[stream_id]['high_conf_frame'] = None
                    stream_data[stream_id]['high_score'] = 0
                    stream_data[stream_id]['detected_type'] = None
        else:
            stream_data[stream_id]['consec'] = 0
            stream_data[stream_id]['high_conf_frame'] = None
            stream_data[stream_id]['high_score'] = 0
            stream_data[stream_id]['detected_type'] = None

        with stream_data[stream_id]['lock']:
            stream_data[stream_id]['frame_buffer'] = resized.copy()

        if ffmpeg_proc and ffmpeg_proc.stdin:
            with stream_data[stream_id]['lock']:
                _, encoded = cv2.imencode('.jpg', stream_data[stream_id]['frame_buffer'])
                ffmpeg_proc.stdin.write(encoded.tobytes())

        time.sleep(1 / 30)



def start_ffmpeg(stream_id):
    hls_dir = os.path.join(os.path.dirname(__file__), 'hls_streams', stream_id)
    os.makedirs(hls_dir, exist_ok=True)
    rtmp_url = f'rtmp://127.0.0.1/live/{stream_id}'
    cmd = [
        'ffmpeg', '-f', 'image2pipe', '-vcodec', 'mjpeg', '-r', '10', '-i', '-',
        '-c:v', 'h264_nvenc',
        '-preset', 'llhp',              # GPU-friendly low-latency preset
        '-b:v', '1M',
        '-hls_time', '1', '-hls_list_size', '2',
        '-hls_flags', 'delete_segments+append_list+split_by_time',
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


def is_new_animal(current_box, last_boxes, threshold=50, cooldown=30):
    cx, cy = (current_box[0] + current_box[2]) // 2, (current_box[1] + current_box[3]) // 2
    now = time.time()
    for box in last_boxes:
        bx, by = box["coords"]
        if abs(cx - bx) < threshold and abs(cy - by) < threshold:
            if now - box["timestamp"] < cooldown:
                return False
    return True


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
        "high_score": 0,
        "detected_type": None
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

                if confidence > 0.8:
                    label = 'dog' if class_id == DOG_CLASS_ID else 'cat' if class_id == CAT_CLASS_ID else None
                    if label:
                        # Draw green bounding box
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

                        if is_new_animal((x1, y1, x2, y2), last_detected_animals[stream_id][label]):
                            last_detected_animals[stream_id][label].append({
                                "coords": ((x1 + x2) // 2, (y1 + y2) // 2),
                                "timestamp": time.time()
                            })
                            animal_counters[stream_id][label] += 1
                            print(f"[{stream_id}] New {label} detected. Total: {animal_counters[stream_id][label]}")

                    if label and confidence > stream_data[stream_id]['high_score']:
                        detected = True
                        stream_data[stream_id]['high_score'] = confidence
                        stream_data[stream_id]['high_conf_frame'] = frame[y1:y2, x1:x2]
                        stream_data[stream_id]['detected_type'] = label

        if detected:
            stream_data[stream_id]['consec'] += 1
            if stream_data[stream_id]['consec'] >= REQUIRED_CONSECUTIVE_FRAMES:
                if stream_data[stream_id]['high_conf_frame'] is not None:
                    classify_and_match(
                        stream_data[stream_id]['high_conf_frame'],
                        stream_id,
                        stream_data[stream_id]['detected_type']
                    )
                    stream_data[stream_id]['consec'] = 0
                    stream_data[stream_id]['high_conf_frame'] = None
                    stream_data[stream_id]['high_score'] = 0
                    stream_data[stream_id]['detected_type'] = None
        else:
            stream_data[stream_id]['consec'] = 0
            stream_data[stream_id]['high_conf_frame'] = None
            stream_data[stream_id]['high_score'] = 0
            stream_data[stream_id]['detected_type'] = None

        with stream_data[stream_id]['lock']:
            stream_data[stream_id]['frame_buffer'] = frame.copy()

        if ffmpeg_proc and ffmpeg_proc.stdin:
            with stream_data[stream_id]['lock']:
                _, encoded = cv2.imencode('.jpg', stream_data[stream_id]['frame_buffer'])
                ffmpeg_proc.stdin.write(encoded.tobytes())

        time.sleep(1 / 30)
# Main handler to analyze confirmed dog or cat image

def classify_and_match(animal_img, stream_id, animal_type):
    # Use green bounding box removal and CNN+ORB pipeline for stray classification
    cropped = remove_green_border(animal_img)
    prediction = cnn_model.predict(preprocess_image(cropped))
    is_stray = prediction[0] >= 0.3

    gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
    match = find_best_match(gray)

    # Ensure venv/tmp directory exists
    tmp_dir = os.path.join("venv", "tmp")
    os.makedirs(tmp_dir, exist_ok=True)

    # Case 1: Not Stray, Registered
    if not is_stray and match:
        notify_owner(match)
        print(f"[TEST LOG] Case: Not Stray, Registered | Match: {match}")
        return

    # Case 2: Not Stray, Not Registered
    if not is_stray and not match:
        tmp_path = os.path.join(tmp_dir, f"not_stray_unknown_{animal_type}_{stream_id}_{int(time.time())}.jpg")
        cv2.imwrite(tmp_path, animal_img)
        notify_pound(tmp_path)
        print("[TEST LOG] Case: Not Stray, Not Registered | Notified Pound")
        return

    # Case 3: Stray, Registered
    if is_stray and match:
        notify_owner(match)
        print(f"[TEST LOG] Case: Stray, Registered | Match: {match}")
        return

    # Case 4: Stray, Not Registered
    if is_stray and not match:
        tmp_path = os.path.join(tmp_dir, f"stray_unknown_{animal_type}_{stream_id}_{int(time.time())}.jpg")
        cv2.imwrite(tmp_path, animal_img)
        notify_pound(tmp_path)
        print("[TEST LOG] Case: Stray, Not Registered | Notified Pound")

@app.route('/api2/streams')
def get_all_streams():
    active_streams = []
    hls_output_dir = "/var/www/html/hls"  # adjust this to your actual HLS root

    for stream_id, data in stream_data.items():
        m3u8_path = os.path.join(hls_output_dir, f"{stream_id}.m3u8")

        # Check if .m3u8 exists and at least one .ts segment for the stream
        m3u8_exists = os.path.exists(m3u8_path)
        ts_segments = [
            f for f in os.listdir(hls_output_dir)
            if f.startswith(stream_id) and f.endswith(".ts")
        ]
        is_active = m3u8_exists and len(ts_segments) > 0

        if is_active:
            active_streams.append({
                "id": stream_id,
                "name": f"Camera {stream_id}",
                "location": f"RTSP or Static Source from {data.get('url', 'unknown')}",
                "status": "active",
                "url": data.get('url', 'unknown'),
                "hls_url": f"http://straysafe.me/hls/{stream_id}.m3u8",
                "flask_hls_url": f"http://straysafe.me/api/hls/{stream_id}/playlist.m3u8",
                "video_url": f"http://straysafe.me/api/video/{stream_id}",
                "rtmp_key": stream_id,
                "type": "static" if data.get('url', '').startswith('static://') else "rtsp"
            })

    return jsonify({"streams": active_streams})




@app.route('/api2/counters')
def get_animal_counters():
    if not animal_counters:
        return jsonify({"message": "No detections yet", "counters": {}})
    return jsonify({stream_id: counts for stream_id, counts in animal_counters.items()})


@app.route('/api2/video/<stream_id>')
def video_snapshot(stream_id):
    if stream_id not in stream_data:
        return "Stream not found", 404
    with stream_data[stream_id]['lock']:
        frame = stream_data[stream_id]['frame_buffer']
        if frame is None:
            frame = np.zeros((FRAME_HEIGHT, FRAME_WIDTH, 3), np.uint8)
    _, img = cv2.imencode('.jpg', frame)
    return img.tobytes(), 200, {'Content-Type': 'image/jpeg'}


@app.route('/api2/hls/<stream_id>/<path:filename>')
def serve_hls_file(stream_id, filename):
    if stream_id not in stream_data:
        return "Stream not found", 404
    return send_from_directory(stream_data[stream_id]['hls_dir'], filename)

@app.route("/api2/predict", methods=["POST"])
def predict():
    data = request.json
    image_path = data.get("image_path")
    animal_type = data.get("animal_type")
    if not os.path.exists(image_path):
        return jsonify({"error": "Image not found"}), 400
    image = cv2.imread(image_path)
    cropped = remove_green_border(image)

    prediction = cnn_model.predict(preprocess_image(cropped))
    is_stray = prediction[0] >= 0.3

    if not is_stray:
        return jsonify({"predicted_label": "not stray", "action": "none"})

    best_match = find_best_match(cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY))
    if best_match:
        notify_owner(best_match)
        return jsonify({"predicted_label": "stray", "match_found": True, "animal_id": best_match})
    else:
        notify_pound(image_path)
        return jsonify({"predicted_label": "stray", "match_found": False})
    
if __name__ == '__main__':
    for ip in STREAM_IP_RANGE:
        stream_id = f'cam-{ip}'
        rtsp_url = RTSP_BASE.format(ip=ip)
        stream_data[stream_id] = {
            'url': rtsp_url,
            'buffer': deque(maxlen=BUFFER_SIZE)
        }
        threading.Thread(target=monitor_stream, args=(rtsp_url, stream_id), daemon=True).start()

    threading.Thread(target=stream_static_video, args=('static-demo', STATIC_VIDEO_PATH), daemon=True).start()

    app.run(host='0.0.0.0', port=5000, debug=True)
