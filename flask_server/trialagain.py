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
from keras.applications.resnet50 import ResNet50, preprocess_input
from keras.models import Model
from sklearn.metrics.pairwise import cosine_similarity


app = Flask(__name__)
CORS(app)
# --- CNN and ORB Feature Matcher Setup ---
tf.config.set_visible_devices([], 'GPU')
MODEL_PATH = "model.h5"
DATABASE_PATH = "/home/straysafe/venv/with_leash"
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

feature_extractor = ResNet50(weights='imagenet', include_top=False, pooling='avg')


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
model.conf = 0.6
model.to('cuda' if torch.cuda.is_available() else 'cpu')

owner_embeddings = {}

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

def get_image_embedding(img):
    # Convert BGR (OpenCV) to RGB
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    resized = cv2.resize(img_rgb, (224, 224))
    x = np.expand_dims(resized, axis=0).astype('float32')
    x = preprocess_input(x)
    return feature_extractor.predict(x)[0]

def precompute_owner_embeddings():
    for fname in os.listdir(DATABASE_PATH):
        if fname.lower().endswith((".jpg", ".png", ".jpeg")):
            path = os.path.join(DATABASE_PATH, fname)
            img = cv2.imread(path)
            if img is None:
                continue
            embedding = get_image_embedding(img)
            owner_embeddings[fname] = embedding
def match_snapshot_to_owner(snapshot_img, threshold=0.85):
    query_embedding = get_image_embedding(snapshot_img)
    best_score = -1
    best_match = None

    for fname, db_embedding in owner_embeddings.items():
        sim = cosine_similarity([query_embedding], [db_embedding])[0][0]
        if sim > best_score:
            best_score = sim
            best_match = fname

    return best_match if best_score >= threshold else None


# def stream_static_video(stream_id, video_path):
#     cap = cv2.VideoCapture(video_path) 
#     if not cap.isOpened():
#         print(f"[{stream_id}] Failed to open static video")
#         return

#     ffmpeg_proc, hls_dir = start_ffmpeg(stream_id)
#     stream_data[stream_id] = {
#         'url': f'static://{video_path}',
#         'buffer': deque(maxlen=BUFFER_SIZE),
#         'ffmpeg': ffmpeg_proc,
#         'frame_buffer': None,
#         'lock': threading.Lock(),
#         'hls_dir': hls_dir,
#         'consec': 0,
#         'high_conf_frame': None,
#         'high_score': 0,
#         'detected_type': None
#     }

#     while True:
#         ret, frame = cap.read()
#         if not ret:
#             cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
#             continue

#         resized = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
#         results = model.predict(resized, imgsz=(FRAME_WIDTH, FRAME_HEIGHT), device='cuda')
#         detected = False

#         for result in results:
#             for box in result.boxes:
#                 class_id = int(box.cls.item())
#                 confidence = box.conf.item()
#                 x1, y1, x2, y2 = map(int, box.xyxy[0])

#                 if confidence > 0.6:
#                     label = 'dog' if class_id == DOG_CLASS_ID else 'cat' if class_id == CAT_CLASS_ID else None
#                     if label:
#                         # Draw green bounding box
#                         cv2.rectangle(resized, (x1, y1), (x2, y2), (0, 255, 0), 2)

#                         if is_new_animal((x1, y1, x2, y2), last_detected_animals[stream_id][label]):
#                             last_detected_animals[stream_id][label].append({
#                                 "coords": ((x1 + x2) // 2, (y1 + y2) // 2),
#                                 "timestamp": time.time()
#                             })
#                             animal_counters[stream_id][label] += 1
#                             print(f"[{stream_id}] New {label} detected. Total: {animal_counters[stream_id][label]}")

#                     if label and confidence > stream_data[stream_id]['high_score']:
#                         detected = True
#                         stream_data[stream_id]['high_score'] = confidence
#                         stream_data[stream_id]['high_conf_frame'] = resized[y1:y2, x1:x2]
#                         stream_data[stream_id]['detected_type'] = label

#         if detected:
#             stream_data[stream_id]['consec'] += 1
#             if stream_data[stream_id]['consec'] >= REQUIRED_CONSECUTIVE_FRAMES:
#                 if stream_data[stream_id]['high_conf_frame'] is not None:
#                     classify_and_match(
#                         stream_data[stream_id]['high_conf_frame'],
#                         stream_id,
#                         stream_data[stream_id]['detected_type']
#                     )
#                     stream_data[stream_id]['consec'] = 0
#                     stream_data[stream_id]['high_conf_frame'] = None
#                     stream_data[stream_id]['high_score'] = 0
#                     stream_data[stream_id]['detected_type'] = None
#         else:
#             stream_data[stream_id]['consec'] = 0
#             stream_data[stream_id]['high_conf_frame'] = None
#             stream_data[stream_id]['high_score'] = 0
#             stream_data[stream_id]['detected_type'] = None

#         with stream_data[stream_id]['lock']:
#             stream_data[stream_id]['frame_buffer'] = resized.copy()

#         if ffmpeg_proc and ffmpeg_proc.stdin:
#             with stream_data[stream_id]['lock']:
#                 _, encoded = cv2.imencode('.jpg', stream_data[stream_id]['frame_buffer'])
#                 ffmpeg_proc.stdin.write(encoded.tobytes())

#         time.sleep(1 / 30)
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
        'debug_data': {},
        'snapshots': {},
        'animal_trackers': defaultdict(lambda: []),
        'last_debug_crop': None
    }

    TIMEOUT_SECONDS = 2
    DIST_THRESHOLD = 80
    save_path = os.path.join("venv", "debug", stream_id)
    os.makedirs(save_path, exist_ok=True)

    def find_existing_tracker(label, box_center):
        for tracker in stream_data[stream_id]['animal_trackers'][label]:
            if np.linalg.norm(np.array(box_center) - np.array(tracker['center'])) < DIST_THRESHOLD:
                tracker['inactive'] = False
                return tracker
        return None

    while True:
        ret, frame = cap.read()
        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue

        resized = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
        debug_snapshot = resized.copy()
        results = model.predict(resized, imgsz=(FRAME_WIDTH, FRAME_HEIGHT), device='cuda')
        current_time = time.time()

        for result in results:
            for box in result.boxes:
                class_id = int(box.cls.item())
                confidence = box.conf.item()
                x1, y1, x2, y2 = map(int, box.xyxy[0])

                if confidence > 0.6:
                    label = 'dog' if class_id == DOG_CLASS_ID else 'cat' if class_id == CAT_CLASS_ID else None
                    if not label:
                        continue

                    cv2.rectangle(resized, (x1, y1), (x2, y2), (0, 255, 0), 2)

                    box_center = ((x1 + x2) // 2, (y1 + y2) // 2)
                    box_area = (x2 - x1) * (y2 - y1)
                    crop = resized[y1:y2, x1:x2]

                    tracker = find_existing_tracker(label, box_center)

                    if tracker is None:
                        new_id = len(stream_data[stream_id]['animal_trackers'][label]) + 1
                        tracker = {
                            'id': new_id,
                            'center': box_center,
                            'max_area': box_area,
                            'best_crop': crop,
                            'last_seen': current_time,
                            'snapshot_saved': False,
                            'inactive': False
                        }
                        stream_data[stream_id]['animal_trackers'][label].append(tracker)
                    else:
                        tracker['center'] = box_center
                        tracker['last_seen'] = current_time
                        if box_area > tracker['max_area']:
                            tracker['max_area'] = box_area
                            tracker['best_crop'] = crop

                    snap_key = f"{label}{tracker['id']}"
                    if not tracker['snapshot_saved'] and snap_key not in stream_data[stream_id]['snapshots']:
                        snapshot_path = os.path.join(save_path, f"{stream_id}_snapshot_{snap_key}.jpg")
                        cv2.imwrite(snapshot_path, debug_snapshot)
                        stream_data[stream_id]['snapshots'][snap_key] = snapshot_path
                        tracker['snapshot_saved'] = True

        for label, trackers in stream_data[stream_id]['animal_trackers'].items():
            for tracker in trackers:
                if not tracker.get('inactive') and tracker['last_seen'] > 0 and (current_time - tracker['last_seen']) > TIMEOUT_SECONDS:
                    crop_key = f"{label}{tracker['id']}"
                    crop_filename = f"{stream_id}_max_{crop_key}.jpg"
                    crop_path = os.path.join(save_path, crop_filename)

                    if tracker['best_crop'] is not None:
                        if os.path.exists(crop_path):
                            existing = cv2.imread(crop_path)
                            if existing is not None and tracker['best_crop'].size > existing.size:
                                cv2.imwrite(crop_path, tracker['best_crop'])
                        else:
                            cv2.imwrite(crop_path, tracker['best_crop'])

                        stream_data[stream_id]['debug_data'][f"high_conf_{crop_key}"] = tracker['best_crop']
                        stream_data[stream_id]['last_debug_crop'] = tracker['best_crop']
                        classify_and_match(tracker['best_crop'], stream_id, label)

                    tracker['inactive'] = True
                    animal_counters[stream_id][label] += 1

        with stream_data[stream_id]['lock']:
            stream_data[stream_id]['frame_buffer'] = resized.copy()

        if ffmpeg_proc and ffmpeg_proc.stdin:
            with stream_data[stream_id]['lock']:
                _, encoded = cv2.imencode('.jpg', stream_data[stream_id]['frame_buffer'])
                ffmpeg_proc.stdin.write(encoded.tobytes())

        time.sleep(1 / 30)



def process_stream(stream_id):
    ffmpeg_proc, hls_dir = start_ffmpeg(stream_id)

    stream_data[stream_id].update({
        'ffmpeg': ffmpeg_proc,
        'frame_buffer': None,
        'lock': threading.Lock(),
        'hls_dir': hls_dir,
        'debug_data': {},
        'snapshots': {},
        'animal_trackers': defaultdict(lambda: [])
    })

    TIMEOUT_SECONDS = 2
    DIST_THRESHOLD = 80
    save_path = os.path.join("venv", "debug", stream_id)
    os.makedirs(save_path, exist_ok=True)

    while True:
        if len(stream_data[stream_id]['buffer']) < BUFFER_SIZE:
            time.sleep(0.1)
            continue

        frame = stream_data[stream_id]['buffer'].popleft()
        debug_snapshot = frame.copy()
        results = model.predict(frame, imgsz=(FRAME_WIDTH, FRAME_HEIGHT), device='cuda')
        current_time = time.time()

        for result in results:
            for box in result.boxes:
                class_id = int(box.cls.item())
                confidence = box.conf.item()
                x1, y1, x2, y2 = map(int, box.xyxy[0])

                if confidence > 0.6:
                    label = 'dog' if class_id == DOG_CLASS_ID else 'cat' if class_id == CAT_CLASS_ID else None
                    if not label:
                        continue

                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

                    box_center = ((x1 + x2) // 2, (y1 + y2) // 2)
                    box_area = (x2 - x1) * (y2 - y1)
                    crop = frame[y1:y2, x1:x2]

                    matched_tracker = None
                    for tracker in stream_data[stream_id]['animal_trackers'][label]:
                        if np.linalg.norm(np.array(box_center) - np.array(tracker['center'])) < DIST_THRESHOLD:
                            matched_tracker = tracker
                            break

                    if matched_tracker is None:
                        new_id = len(stream_data[stream_id]['animal_trackers'][label]) + 1
                        tracker = {
                            'id': new_id,
                            'center': box_center,
                            'max_area': box_area,
                            'best_crop': crop,
                            'last_seen': current_time,
                            'snapshot_saved': False
                        }
                        stream_data[stream_id]['animal_trackers'][label].append(tracker)
                        matched_tracker = tracker
                    else:
                        matched_tracker['center'] = box_center
                        matched_tracker['last_seen'] = current_time

                        if box_area > matched_tracker['max_area']:
                            matched_tracker['max_area'] = box_area
                            matched_tracker['best_crop'] = crop

                    snap_key = f"{label}{matched_tracker['id']}"
                    if not matched_tracker['snapshot_saved'] and snap_key not in stream_data[stream_id]['snapshots']:
                        snapshot_path = os.path.join(save_path, f"{stream_id}_snapshot_{snap_key}.jpg")
                        cv2.imwrite(snapshot_path, debug_snapshot)
                        stream_data[stream_id]['snapshots'][snap_key] = snapshot_path
                        matched_tracker['snapshot_saved'] = True

        for label, trackers in stream_data[stream_id]['animal_trackers'].items():
            for tracker in trackers:
                if tracker['last_seen'] > 0 and (current_time - tracker['last_seen']) > TIMEOUT_SECONDS:
                    crop_key = f"{label}{tracker['id']}"
                    crop_filename = f"{stream_id}_max_{crop_key}.jpg"
                    crop_path = os.path.join(save_path, crop_filename)

                    if tracker['best_crop'] is not None:
                        if os.path.exists(crop_path):
                            existing = cv2.imread(crop_path)
                            if existing is not None and tracker['best_crop'].size > existing.size:
                                cv2.imwrite(crop_path, tracker['best_crop'])
                        else:
                            cv2.imwrite(crop_path, tracker['best_crop'])

                        stream_data[stream_id]['debug_data'][f"high_conf_{crop_key}"] = tracker['best_crop']
                        classify_and_match(tracker['best_crop'], stream_id, label)

                    tracker['last_seen'] = 0  # freeze tracker

        with stream_data[stream_id]['lock']:
            stream_data[stream_id]['frame_buffer'] = frame.copy()

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

# def process_stream(stream_id):
#     ffmpeg_proc, hls_dir = start_ffmpeg(stream_id)

#     stream_data[stream_id].update({
#         "ffmpeg": ffmpeg_proc,
#         "frame_buffer": None,
#         "lock": threading.Lock(),
#         "hls_dir": hls_dir,
#         "consec": 0,
#         "high_conf_frame": None,
#         "high_score": 0,
#         "detected_type": None
#     })

#     while True:
#         if len(stream_data[stream_id]['buffer']) < BUFFER_SIZE:
#             time.sleep(0.1)
#             continue

#         frame = stream_data[stream_id]['buffer'].popleft()
#         results = model.predict(frame, imgsz=(FRAME_WIDTH, FRAME_HEIGHT))
#         detected = False

#         for result in results:
#             for box in result.boxes:
#                 class_id = int(box.cls.item())
#                 confidence = box.conf.item()
#                 x1, y1, x2, y2 = map(int, box.xyxy[0])

#                 if confidence > 0.6:
#                     label = 'dog' if class_id == DOG_CLASS_ID else 'cat' if class_id == CAT_CLASS_ID else None
#                     if label:
#                         # Draw green bounding box
#                         cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

#                         if is_new_animal((x1, y1, x2, y2), last_detected_animals[stream_id][label]):
#                             last_detected_animals[stream_id][label].append({
#                                 "coords": ((x1 + x2) // 2, (y1 + y2) // 2),
#                                 "timestamp": time.time()
#                             })
#                             animal_counters[stream_id][label] += 1
#                             print(f"[{stream_id}] New {label} detected. Total: {animal_counters[stream_id][label]}")

#                     if label and confidence > stream_data[stream_id]['high_score']:
#                         detected = True
#                         stream_data[stream_id]['high_score'] = confidence
#                         stream_data[stream_id]['high_conf_frame'] = frame[y1:y2, x1:x2]
#                         stream_data[stream_id]['detected_type'] = label

#         if detected:
#             stream_data[stream_id]['consec'] += 1
#             if stream_data[stream_id]['consec'] >= REQUIRED_CONSECUTIVE_FRAMES:
#                 if stream_data[stream_id]['high_conf_frame'] is not None:
#                     classify_and_match(
#                         stream_data[stream_id]['high_conf_frame'],
#                         stream_id,
#                         stream_data[stream_id]['detected_type']
#                     )
#                     stream_data[stream_id]['consec'] = 0
#                     stream_data[stream_id]['high_conf_frame'] = None
#                     stream_data[stream_id]['high_score'] = 0
#                     stream_data[stream_id]['detected_type'] = None
#         else:
#             stream_data[stream_id]['consec'] = 0
#             stream_data[stream_id]['high_conf_frame'] = None
#             stream_data[stream_id]['high_score'] = 0
#             stream_data[stream_id]['detected_type'] = None

#         with stream_data[stream_id]['lock']:
#             stream_data[stream_id]['frame_buffer'] = frame.copy()

#         if ffmpeg_proc and ffmpeg_proc.stdin:
#             with stream_data[stream_id]['lock']:
#                 _, encoded = cv2.imencode('.jpg', stream_data[stream_id]['frame_buffer'])
#                 ffmpeg_proc.stdin.write(encoded.tobytes())

#         time.sleep(1 / 30)
# Main handler to analyze confirmed dog or cat image

def classify_and_match(animal_img, stream_id, animal_type):
    # Use green bounding box removal and CNN+ORB pipeline for stray classification
    cropped = remove_green_border(animal_img)
    prediction = cnn_model.predict(preprocess_image(cropped))
    is_stray = prediction[0] >= 0.3

    match = match_snapshot_to_owner(cropped)

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

def save_debug_images(stream_id):
    debug_dir = os.path.join("venv", "debug", stream_id)
    abs_debug_dir = os.path.abspath(debug_dir)
    os.makedirs(abs_debug_dir, exist_ok=True)

    if not os.path.exists(abs_debug_dir):
        return None

    # Find the latest max snapshot file
    max_files = [f for f in os.listdir(abs_debug_dir) if f.startswith(f"{stream_id}_max_") and f.endswith(".jpg")]
    if not max_files:
        return None

    latest_file = max(max_files, key=lambda f: os.path.getmtime(os.path.join(abs_debug_dir, f)))
    high_conf_path = os.path.join(abs_debug_dir, latest_file)
    high_conf_frame = cv2.imread(high_conf_path)

    if high_conf_frame is None:
        return None

    # Save 1: Snapshot with green box (optional, showing original frame if needed)
    snapshot_path = os.path.join(debug_dir, "1_snapshot_green_box.jpg")
    if stream_data.get(stream_id, {}).get("frame_buffer") is not None:
        cv2.imwrite(snapshot_path, stream_data[stream_id]["frame_buffer"])
    else:
        return None

    # Save 2: Cropped and cleaned
    cleaned = remove_green_border(high_conf_frame)
    cleaned_path = os.path.join(debug_dir, "2_cropped_cleaned.jpg")
    cv2.imwrite(cleaned_path, cleaned)

    # Save 3: Classification result
    prediction = cnn_model.predict(preprocess_image(cleaned))[0]
    is_stray = prediction >= 0.3
    classification_result = "stray" if is_stray else "not_stray"

    match = match_snapshot_to_owner(cleaned)
    match_path = None
    if match:
        db_img = cv2.imread(os.path.join(DATABASE_PATH, match))
        if db_img is not None:
            match_path = os.path.join(debug_dir, "3_feature_match.jpg")
            stacked = np.hstack((cleaned, db_img))
            cv2.imwrite(match_path, stacked)

    return {
        "snapshot": snapshot_path,
        "cropped": cleaned_path,
        "classification": classification_result,
        "prediction_score": float(prediction),
        "match": match,
        "match_img": match_path if match else None
    }


@app.route('/api2/debug/<stream_id>')
def debug_pipeline(stream_id):
    result = save_debug_images(stream_id)
    if not result:
        return jsonify({"error": "No frame or detection available"}), 404

    return jsonify({
        "message": "Debug images saved",
        "snapshot_url": f"/api2/debug-img/{stream_id}/1_snapshot_green_box.jpg",
        "cropped_url": f"/api2/debug-img/{stream_id}/2_cropped_cleaned.jpg",
        "classification": result["classification"],
        "prediction_score": result["prediction_score"],
        "match": result["match"],
        "match_img_url": f"/api2/debug-img/{stream_id}/3_feature_match.jpg" if result["match_img"] else None
    })

@app.route('/api2/debug-img/<stream_id>/<filename>')
def serve_debug_image(stream_id, filename):
    debug_dir = os.path.join("venv", "debug", stream_id)
    if not os.path.exists(os.path.join(debug_dir, filename)):
        return "File not found", 404
    return send_from_directory(debug_dir, filename)
@app.route('/api2/streams')
def get_all_streams():
    active_streams = []
    hls_output_dir = "/var/hls"  # adjust this to your actual HLS root

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
