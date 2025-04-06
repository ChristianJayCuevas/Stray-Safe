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
from datetime import datetime
import json


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

# Store notification history by stream_id and animal_type
notification_history = []

# Replace the notify_owner and notify_pound functions with expanded versions
def notify_owner(owner_id, animal_img=None, animal_info=None):
    """
    Notify the owner of a detected pet
    
    Args:
        owner_id: The owner's ID or image filename
        animal_img: The detected animal image
        animal_info: Additional information about the detection
    """
    timestamp = datetime.now().isoformat()
    
    notification = {
        "id": f"owner_notify_{int(time.time())}",
        "type": "owner_notification",
        "owner_id": owner_id,
        "timestamp": timestamp,
        "status": "sent",
        "animal_info": animal_info
    }
    
    # Save the notification to history
    notification_history.insert(0, notification)
    
    # Limit notification history size
    if len(notification_history) > 1000:
        notification_history.pop()
    
    print(f"Owner notified for animal ID: {owner_id}")
    return notification

def notify_pound(image_path, animal_info=None):
    """
    Notify the animal pound about a stray animal
    
    Args:
        image_path: Path to the animal image
        animal_info: Additional information about the detection
    """
    timestamp = datetime.now().isoformat()
    
    notification = {
        "id": f"pound_notify_{int(time.time())}",
        "type": "pound_notification",
        "image_path": image_path,
        "timestamp": timestamp,
        "status": "sent",
        "animal_info": animal_info
    }
    
    # Save the notification to history
    notification_history.insert(0, notification)
    
    # Limit notification history size
    if len(notification_history) > 1000:
        notification_history.pop()
    
    print(f"Animal pound notified with image: {image_path}")
    return notification

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
    """
    Load pet images from DATABASE_PATH and precompute their embeddings for faster matching
    """
    print(f"Loading pet images from: {DATABASE_PATH}")
    count = 0
    
    try:
        # Check if directory exists
        if not os.path.exists(DATABASE_PATH):
            print(f"WARNING: Directory {DATABASE_PATH} does not exist!")
            os.makedirs(DATABASE_PATH, exist_ok=True)
            print(f"Created directory {DATABASE_PATH}")
            return 0
            
        # List all files in the directory
        image_files = [f for f in os.listdir(DATABASE_PATH) 
                     if f.lower().endswith((".jpg", ".png", ".jpeg"))]
        
        print(f"Found {len(image_files)} image files in {DATABASE_PATH}")
        
        for fname in image_files:
            path = os.path.join(DATABASE_PATH, fname)
            img = cv2.imread(path)
            
            if img is None:
                print(f"Failed to read image: {path}")
                continue
                
            # Store the embedding
            embedding = get_image_embedding(img)
            owner_embeddings[fname] = embedding
            count += 1
            
        print(f"Successfully loaded {count} pet images and computed embeddings")
    except Exception as e:
        print(f"Error loading pet database: {str(e)}")
    
    return count

def match_snapshot_to_owner(snapshot_img, threshold=0.65):
    """
    Match a detected animal to owner records using visual similarities.
    Uses both color histogram matching and feature detection for improved accuracy.
    Falls back to CNN embeddings if visual matching fails.
    
    Lowered threshold to 0.65 to be more permissive with matches.
    """
    best_match = None
    best_score = -1
    match_method = "unknown"
    
    # Track all potential matches for similar colored animals
    all_matches = []
    
    # First try visual feature matching for better animal recognition
    for fname in owner_embeddings:
        path = os.path.join(DATABASE_PATH, fname)
        owner_img = cv2.imread(path)
        if owner_img is None:
            continue
            
        try:
            # Color histogram comparison - effective for dog coat colors
            # Convert to HSV color space which better represents color similarities
            hsv1 = cv2.cvtColor(snapshot_img, cv2.COLOR_BGR2HSV)
            hsv2 = cv2.cvtColor(owner_img, cv2.COLOR_BGR2HSV)
            
            # Calculate histograms for hue and saturation channels
            h_bins = 50
            s_bins = 60
            histSize = [h_bins, s_bins]
            # hue varies from 0 to 179, saturation from 0 to 255
            ranges = [0, 180, 0, 256] 
            
            hist1 = cv2.calcHist([hsv1], [0, 1], None, histSize, ranges)
            hist2 = cv2.calcHist([hsv2], [0, 1], None, histSize, ranges)
            
            cv2.normalize(hist1, hist1, 0, 1, cv2.NORM_MINMAX)
            cv2.normalize(hist2, hist2, 0, 1, cv2.NORM_MINMAX)
            
            # Compare histograms - correlation method works well for color similarity
            color_sim = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
            
            # Feature matching with ORB
            # Convert to grayscale for feature detection
            gray1 = cv2.cvtColor(snapshot_img, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(owner_img, cv2.COLOR_BGR2GRAY)
            
            # Resize images to be similar scale for better comparison
            max_dim = 512
            scale1 = max_dim / max(gray1.shape)
            scale2 = max_dim / max(gray2.shape)
            
            if scale1 < 1:
                gray1 = cv2.resize(gray1, (int(gray1.shape[1] * scale1), int(gray1.shape[0] * scale1)))
            if scale2 < 1:
                gray2 = cv2.resize(gray2, (int(gray2.shape[1] * scale2), int(gray2.shape[0] * scale2)))
            
            # Detect keypoints and compute descriptors
            keypoints1, descriptors1 = orb.detectAndCompute(gray1, None)
            keypoints2, descriptors2 = orb.detectAndCompute(gray2, None)
            
            # Check if we have enough keypoints
            feature_sim = 0
            if descriptors1 is not None and descriptors2 is not None and len(descriptors1) > 10 and len(descriptors2) > 10:
                # Match keypoints
                matches = bf.match(descriptors1, descriptors2)
                
                # Sort matches by distance (lower is better)
                matches = sorted(matches, key=lambda x: x.distance)
                
                # Take only good matches (lower distance)
                good_matches = matches[:min(30, len(matches))]
                
                # Calculate feature similarity score based on quality of matches
                feature_sim = len(good_matches) / min(len(keypoints1), len(keypoints2))
            
            # Combined similarity score with weighted factors
            # We give more weight to color for animals since coat color is distinctive
            combined_sim = 0.70 * color_sim + 0.30 * feature_sim
            
            # Track all potential matches with decent similarity
            color_threshold = 0.55  # Lower threshold for color similarity
            
            # If color is similar enough, add to potential matches
            if color_sim >= color_threshold:
                match_info = {
                    'filename': fname,
                    'combined_score': combined_sim,
                    'color_score': color_sim,
                    'feature_score': feature_sim,
                    'path': path
                }
                all_matches.append(match_info)
            
            if combined_sim > best_score and combined_sim >= threshold:
                best_score = combined_sim
                best_match = fname
                match_method = "visual"
                
        except Exception as e:
            print(f"Error comparing images: {e}")
    
    # If no good visual match, fall back to the existing CNN embedding method
    if best_match is None:
        query_embedding = get_image_embedding(snapshot_img)
        for fname, db_embedding in owner_embeddings.items():
            sim = cosine_similarity([query_embedding], [db_embedding])[0][0]
            if sim > best_score and sim >= threshold * 0.9:  # Slightly lower threshold for CNN
                best_score = sim
                best_match = fname
                match_method = "embedding"
                
                # Also add to all_matches for completeness
                all_matches.append({
                    'filename': fname,
                    'combined_score': sim,
                    'color_score': 0,  # Not applicable for CNN embedding
                    'feature_score': 0,  # Not applicable for CNN embedding
                    'method': 'embedding',
                    'path': os.path.join(DATABASE_PATH, fname)
                })
    
    if best_match:
        print(f"Matched to owner image '{best_match}' with {match_method} similarity of {best_score:.2f}")
    
    # Sort all matches by combined score (highest first)
    all_matches.sort(key=lambda x: x['combined_score'], reverse=True)
    
    # Return more detailed match information
    return {
        'match': best_match,
        'score': float(best_score) if best_score > -1 else 0.0,
        'method': match_method,
        'all_matches': all_matches  # Include all potential matches
    } if best_match else {'all_matches': all_matches} if all_matches else None

def find_matching_tracker(stream_id, label, box_center, box_area, crop, current_time):
    # First check active trackers using position
    position_match = None
    appearance_matches = []
    
    if label in stream_data[stream_id]['active_tracks']:
        for track_id, tracker in stream_data[stream_id]['active_tracks'][label].items():
            # Check position-based match first (for animals moving continuously)
            distance = np.linalg.norm(np.array(box_center) - np.array(tracker['center']))
            if distance < DIST_THRESHOLD:
                position_match = (track_id, tracker)
            
            # Also check appearance similarity for potential matches across the frame
            if tracker['best_crop'] is not None and distance >= DIST_THRESHOLD:
                # Calculate appearance similarity - use global function
                similarity = calculate_appearance_similarity(crop, tracker['best_crop'])
                if similarity > 0.6:  # Adjust threshold as needed
                    appearance_matches.append((track_id, tracker, similarity))
    
    # If we have a position match, use that with priority
    if position_match:
        track_id, tracker = position_match
        tracker['center'] = box_center
        tracker['last_seen'] = current_time
        tracker['inactive'] = False
        tracker['frames_tracked'] += 1
        # Only update the best crop if the area is significantly larger
        if box_area > tracker['max_area'] * MIN_AREA_INCREASE:
            return tracker, True  # Return tracker and flag to update crop
        return tracker, False  # Return tracker but don't update crop
    
    # If no position match but we have appearance matches, use the best one
    if appearance_matches:
        # Sort by similarity score (highest first)
        appearance_matches.sort(key=lambda x: x[2], reverse=True)
        track_id, tracker, similarity = appearance_matches[0]
        print(f"[{stream_id}] Matched {label}{track_id} by appearance with similarity {similarity:.2f}")
        tracker['center'] = box_center  # Update position
        tracker['last_seen'] = current_time
        tracker['inactive'] = False
        tracker['frames_tracked'] += 1
        # Always update the crop for appearance matches to handle angle changes
        tracker['max_area'] = max(box_area, tracker['max_area'])
        tracker['best_crop'] = crop
        return tracker, True
    
    # Then check recent history (animals that disappeared not long ago)
    history_match = None
    history_appearance_matches = []
    
    if label in stream_data[stream_id]['tracking_history']:
        for track_id, history in list(stream_data[stream_id]['tracking_history'][label].items()):
            # Check if animal disappeared recently
            time_since_disappearance = current_time - history['disappeared_at']
            if time_since_disappearance < REAPPEARANCE_TIMEOUT:
                # Position-based match
                distance = np.linalg.norm(np.array(box_center) - np.array(history['last_center']))
                if distance < DIST_THRESHOLD * 1.5:  # Allow slightly larger threshold for reappearing animals
                    history_match = (track_id, history)
                
                # Appearance-based match
                if history['best_crop'] is not None and distance >= DIST_THRESHOLD * 1.5:
                    similarity = calculate_appearance_similarity(crop, history['best_crop'])
                    if similarity > 0.55:  # Slightly lower threshold for historical matches
                        history_appearance_matches.append((track_id, history, similarity))
    
    # Process position-based history match
    if history_match:
        track_id, history = history_match
        return reactivate_from_history(stream_id, label, track_id, history, box_center, box_area, crop, current_time, True)
    
    # Process appearance-based history match if available
    if history_appearance_matches:
        history_appearance_matches.sort(key=lambda x: x[2], reverse=True)
        track_id, history, similarity = history_appearance_matches[0]
        print(f"[{stream_id}] Matched historical {label}{track_id} by appearance with similarity {similarity:.2f}")
        return reactivate_from_history(stream_id, label, track_id, history, box_center, box_area, crop, current_time, True)
    
    # No match found
    return None, False

def reactivate_from_history(stream_id, label, track_id, history, box_center, box_area, crop, current_time, update_crop):
    if label not in stream_data[stream_id]['active_tracks']:
        stream_data[stream_id]['active_tracks'][label] = {}
    
    # Restore the tracker from history
    tracker = {
        'id': track_id,
        'center': box_center,
        'max_area': max(box_area, history['max_area']) if update_crop else history['max_area'],
        'best_crop': crop if update_crop else history['best_crop'],
        'last_seen': current_time,
        'first_seen': history['first_seen'],
        'snapshot_saved': history['snapshot_saved'],
        'inactive': False,
        'frames_tracked': history['frames_tracked'] + 1
    }
    
    stream_data[stream_id]['active_tracks'][label][track_id] = tracker
    # Remove from history
    del stream_data[stream_id]['tracking_history'][label][track_id]
    time_since_disappearance = current_time - history['disappeared_at']
    print(f"[{stream_id}] Reactivated {label}{track_id} after {time_since_disappearance:.1f}s")
    
    return tracker, update_crop

def create_new_tracker(stream_id, label, box_center, box_area, crop, current_time):
    # Initialize tracking structures if needed
    if label not in stream_data[stream_id]['active_tracks']:
        stream_data[stream_id]['active_tracks'][label] = {}
    
    # Generate a new ID
    used_ids = set(stream_data[stream_id]['active_tracks'][label].keys())
    if label in stream_data[stream_id]['tracking_history']:
        used_ids.update(stream_data[stream_id]['tracking_history'][label].keys())
    new_id = 1
    while new_id in used_ids:
        new_id += 1
    
    # Create new tracker
    tracker = {
        'id': new_id,
        'center': box_center,
        'max_area': box_area,
        'best_crop': crop,
        'last_seen': current_time,
        'first_seen': current_time,
        'snapshot_saved': False,
        'inactive': False,
        'frames_tracked': 1
    }
    stream_data[stream_id]['active_tracks'][label][new_id] = tracker
    print(f"[{stream_id}] Created new tracker for {label}{new_id}")
    return tracker

def calculate_appearance_similarity(img1, img2):
    """Calculate visual similarity between two animal crops"""
    # Resize images to the same size for comparison
    size = (64, 64)
    img1_resized = cv2.resize(img1, size)
    img2_resized = cv2.resize(img2, size)
    
    # Convert to grayscale
    gray1 = cv2.cvtColor(img1_resized, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(img2_resized, cv2.COLOR_BGR2GRAY)
    
    # Method 1: Use a combination of histogram comparison
    hist1 = cv2.calcHist([gray1], [0], None, [64], [0, 256])
    hist2 = cv2.calcHist([gray2], [0], None, [64], [0, 256])
    cv2.normalize(hist1, hist1, 0, 1, cv2.NORM_MINMAX)
    cv2.normalize(hist2, hist2, 0, 1, cv2.NORM_MINMAX)
    hist_similarity = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
    
    # Method 2: Use feature matching with ORB
    try:
        # Detect ORB keypoints and descriptors
        kp1, des1 = orb.detectAndCompute(gray1, None)
        kp2, des2 = orb.detectAndCompute(gray2, None)
        
        # Check if enough keypoints were found
        if des1 is not None and des2 is not None and len(des1) > 10 and len(des2) > 10:
            # Match descriptors
            matches = bf.match(des1, des2)
            
            # Calculate feature similarity based on number of good matches
            feature_similarity = len(matches) / max(len(kp1), len(kp2))
            
            # Combine both methods, giving more weight to feature matching
            combined_similarity = 0.3 * hist_similarity + 0.7 * feature_similarity
        else:
            # Fall back to histogram similarity if not enough keypoints
            combined_similarity = hist_similarity
    except:
        # If ORB fails, just use histogram similarity
        combined_similarity = hist_similarity
    
    return combined_similarity

# Define constants needed by the functions above
DIST_THRESHOLD = 80  # Distance threshold in pixels
REAPPEARANCE_TIMEOUT = 30  # Duration in seconds to consider an animal as "new" again
MIN_AREA_INCREASE = 1.2  # Minimum ratio increase in box area to update best crop

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
        'last_debug_crop': None,
        'active_tracks': {},  # Store currently active tracks for quick lookup
        'tracking_history': {}  # Store historical tracking data for better deduplication
    }

    TIMEOUT_SECONDS = 2
    save_path = os.path.join("venv", "debug", stream_id)
    os.makedirs(save_path, exist_ok=True)

    while True:
        ret, frame = cap.read()
        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue

        resized = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
        debug_snapshot = resized.copy()
        results = model.predict(resized, imgsz=(FRAME_WIDTH, FRAME_HEIGHT), device='cuda')
        current_time = time.time()

        # Track all currently detected boxes
        detected_in_frame = {
            'dog': set(),
            'cat': set()
        }

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
                    crop = resized[y1:y2, x1:x2].copy()  # Create a copy to avoid reference issues
                    
                    # Try to match with existing tracker
                    tracker, update_crop = find_matching_tracker(stream_id, label, box_center, box_area, crop, current_time)
                    
                    # If no matching tracker, create a new one
                    if tracker is None:
                        tracker = create_new_tracker(stream_id, label, box_center, box_area, crop, current_time)
                        update_crop = True  # Always update crop for new trackers
                    
                    # Mark this tracker as detected in this frame
                    detected_in_frame[label].add(tracker['id'])
                    
                    # Update best crop if needed
                    if update_crop:
                        tracker['max_area'] = box_area
                        tracker['best_crop'] = crop
                    
                    # Save snapshot if needed
                    snap_key = f"{label}{tracker['id']}"
                    if not tracker['snapshot_saved'] and snap_key not in stream_data[stream_id]['snapshots']:
                        snapshot_path = os.path.join(save_path, f"{stream_id}_snapshot_{snap_key}.jpg")
                        cv2.imwrite(snapshot_path, debug_snapshot)
                        stream_data[stream_id]['snapshots'][snap_key] = snapshot_path
                        tracker['snapshot_saved'] = True

        # Check for trackers that were not detected in this frame
        for label in ['dog', 'cat']:
            if label in stream_data[stream_id]['active_tracks']:
                for track_id, tracker in list(stream_data[stream_id]['active_tracks'][label].items()):
                    if track_id not in detected_in_frame[label]:
                        time_since_last_seen = current_time - tracker['last_seen']
                        
                        # If not seen for a while, deactivate and process
                        if time_since_last_seen > TIMEOUT_SECONDS:
                            # Only process stable tracks (seen in multiple frames)
                            if tracker['frames_tracked'] >= 3:
                                crop_key = f"{label}{tracker['id']}"
                                crop_filename = f"{stream_id}_max_{crop_key}.jpg"
                                crop_path = os.path.join(save_path, crop_filename)
                                
                                if tracker['best_crop'] is not None:
                                    # Save the best crop
                                    if os.path.exists(crop_path):
                                        existing = cv2.imread(crop_path)
                                        if existing is not None and tracker['best_crop'].size > existing.size:
                                            cv2.imwrite(crop_path, tracker['best_crop'])
                                    else:
                                        cv2.imwrite(crop_path, tracker['best_crop'])
                                    
                                    # Store for debugging and classify
                                    stream_data[stream_id]['debug_data'][f"high_conf_{crop_key}"] = tracker['best_crop']
                                    classify_and_match(tracker['best_crop'], stream_id, label)
                                    
                                # Count animal only once when it's processed
                                animal_counters[stream_id][label] += 1
                                print(f"[{stream_id}] Processed {label}{track_id} after {tracker['frames_tracked']} frames")
                            
                            # Move to history for potential reappearance tracking
                            if label not in stream_data[stream_id]['tracking_history']:
                                stream_data[stream_id]['tracking_history'][label] = {}
                                
                            stream_data[stream_id]['tracking_history'][label][track_id] = {
                                'last_center': tracker['center'],
                                'max_area': tracker['max_area'],
                                'best_crop': tracker['best_crop'],
                                'first_seen': tracker['first_seen'],
                                'disappeared_at': current_time,
                                'snapshot_saved': tracker['snapshot_saved'],
                                'frames_tracked': tracker['frames_tracked']
                            }
                            
                            # Remove from active tracks
                            del stream_data[stream_id]['active_tracks'][label][track_id]

        # Clean up old history entries
        for label in ['dog', 'cat']:
            if label in stream_data[stream_id]['tracking_history']:
                for track_id in list(stream_data[stream_id]['tracking_history'][label].keys()):
                    history = stream_data[stream_id]['tracking_history'][label][track_id]
                    if current_time - history['disappeared_at'] > REAPPEARANCE_TIMEOUT:
                        del stream_data[stream_id]['tracking_history'][label][track_id]

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
        'animal_trackers': defaultdict(lambda: []),
        'active_tracks': {},
        'tracking_history': {}
    })

    TIMEOUT_SECONDS = 2
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

        # Track all currently detected boxes
        detected_in_frame = {
            'dog': set(),
            'cat': set()
        }

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
                    crop = frame[y1:y2, x1:x2].copy()
                    
                    # Try to match with existing tracker
                    tracker, update_crop = find_matching_tracker(stream_id, label, box_center, box_area, crop, current_time)
                    
                    # If no matching tracker, create a new one
                    if tracker is None:
                        tracker = create_new_tracker(stream_id, label, box_center, box_area, crop, current_time)
                        update_crop = True  # Always update crop for new trackers
                    
                    # Mark this tracker as detected in this frame
                    detected_in_frame[label].add(tracker['id'])
                    
                    # Update best crop if needed
                    if update_crop:
                        tracker['max_area'] = box_area
                        tracker['best_crop'] = crop
                    
                    # Save snapshot if needed
                    snap_key = f"{label}{tracker['id']}"
                    if not tracker['snapshot_saved'] and snap_key not in stream_data[stream_id]['snapshots']:
                        snapshot_path = os.path.join(save_path, f"{stream_id}_snapshot_{snap_key}.jpg")
                        cv2.imwrite(snapshot_path, debug_snapshot)
                        stream_data[stream_id]['snapshots'][snap_key] = snapshot_path
                        tracker['snapshot_saved'] = True

        # Check for trackers that were not detected in this frame
        for label in ['dog', 'cat']:
            if label in stream_data[stream_id]['active_tracks']:
                for track_id, tracker in list(stream_data[stream_id]['active_tracks'][label].items()):
                    if track_id not in detected_in_frame[label]:
                        time_since_last_seen = current_time - tracker['last_seen']
                        
                        # If not seen for a while, deactivate and process
                        if time_since_last_seen > TIMEOUT_SECONDS:
                            # Only process stable tracks (seen in multiple frames)
                            if tracker['frames_tracked'] >= 3:
                                crop_key = f"{label}{tracker['id']}"
                                crop_filename = f"{stream_id}_max_{crop_key}.jpg"
                                crop_path = os.path.join(save_path, crop_filename)
                                
                                if tracker['best_crop'] is not None:
                                    # Save the best crop
                                    if os.path.exists(crop_path):
                                        existing = cv2.imread(crop_path)
                                        if existing is not None and tracker['best_crop'].size > existing.size:
                                            cv2.imwrite(crop_path, tracker['best_crop'])
                                    else:
                                        cv2.imwrite(crop_path, tracker['best_crop'])
                                    
                                    # Store for debugging and classify
                                    stream_data[stream_id]['debug_data'][f"high_conf_{crop_key}"] = tracker['best_crop']
                                    classify_and_match(tracker['best_crop'], stream_id, label)
                                    
                                # Count animal only once when it's processed
                                animal_counters[stream_id][label] += 1
                                print(f"[{stream_id}] Processed {label}{track_id} after {tracker['frames_tracked']} frames")
                            
                            # Move to history for potential reappearance tracking
                            if label not in stream_data[stream_id]['tracking_history']:
                                stream_data[stream_id]['tracking_history'][label] = {}
                                
                            stream_data[stream_id]['tracking_history'][label][track_id] = {
                                'last_center': tracker['center'],
                                'max_area': tracker['max_area'],
                                'best_crop': tracker['best_crop'],
                                'first_seen': tracker['first_seen'],
                                'disappeared_at': current_time,
                                'snapshot_saved': tracker['snapshot_saved'],
                                'frames_tracked': tracker['frames_tracked']
                            }
                            
                            # Remove from active tracks
                            del stream_data[stream_id]['active_tracks'][label][track_id]

        # Clean up old history entries
        for label in ['dog', 'cat']:
            if label in stream_data[stream_id]['tracking_history']:
                for track_id in list(stream_data[stream_id]['tracking_history'][label].keys()):
                    history = stream_data[stream_id]['tracking_history'][label][track_id]
                    if current_time - history['disappeared_at'] > REAPPEARANCE_TIMEOUT:
                        del stream_data[stream_id]['tracking_history'][label][track_id]

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


# This will store detailed information about detected animals
detected_animals_log = []

# Add this function to log detected animals
def log_animal_detection(stream_id, animal_type, animal_id, classification_result, match_result=None, image_path=None):
    """
    Log a detected animal with detailed information for tracking purposes
    """
    timestamp = datetime.now().isoformat()
    
    detection_entry = {
        "id": f"{stream_id}_{animal_type}{animal_id}_{int(time.time())}",
        "stream_id": stream_id,
        "animal_type": animal_type,
        "animal_id": animal_id,
        "timestamp": timestamp,
        "classification": classification_result,
        "image_path": image_path
    }
    
    # Add match information if available
    if match_result:
        detection_entry["match"] = match_result.get("match")
        detection_entry["match_score"] = match_result.get("score", 0)
        detection_entry["match_method"] = match_result.get("method", "none")
    
    # Add to the beginning of the list for most recent first
    detected_animals_log.insert(0, detection_entry)
    
    # Keep the log at a reasonable size (store last 1000 detections)
    if len(detected_animals_log) > 1000:
        detected_animals_log.pop()
    
    return detection_entry

# Update the classify_and_match function to include case information and use the new notification functions
def classify_and_match(animal_img, stream_id, animal_type):
    # Extract animal ID from the tracker if available
    animal_id = None
    for tracker_data in stream_data.get(stream_id, {}).get('animal_trackers', {}).get(animal_type, []):
        if tracker_data.get('best_crop') is animal_img or np.array_equal(tracker_data.get('best_crop', np.array([])), animal_img):
            animal_id = tracker_data.get('id')
            break
    
    # Use ID from filename if not found in trackers
    if animal_id is None:
        # Try to extract from debug data keys
        for key in stream_data.get(stream_id, {}).get('debug_data', {}):
            if key.startswith(f"high_conf_{animal_type}"):
                animal_id = key.split("_")[-1].replace(animal_type, "")
                break
    
    # Default ID if still not found
    if animal_id is None:
        animal_id = str(len(detected_animals_log) + 1)
    
    # Use green bounding box removal and CNN+ORB pipeline for stray classification
    cropped = remove_green_border(animal_img)
    prediction = cnn_model.predict(preprocess_image(cropped))
    is_stray = prediction[0] >= 0.3
    classification_result = "stray" if is_stray else "not_stray"

    match_result = match_snapshot_to_owner(cropped)
    match = match_result.get('match') if match_result else None
    match_score = match_result.get('score', 0) if match_result else 0
    match_method = match_result.get('method', "none") if match_result else "none"
    
    # Save image to a predictable path for later reference
    img_dir = os.path.join("venv", "detected", stream_id)
    os.makedirs(img_dir, exist_ok=True)
    img_filename = f"{stream_id}_{animal_type}{animal_id}_{int(time.time())}.jpg"
    img_path = os.path.join(img_dir, img_filename)
    cv2.imwrite(img_path, animal_img)

    # Prepare common animal info for notifications
    animal_info = {
        "stream_id": stream_id,
        "animal_type": animal_type,
        "animal_id": animal_id,
        "classification": classification_result,
        "prediction_score": float(prediction[0]),
        "is_stray": is_stray,
        "match": match,
        "match_score": match_score,
        "match_method": match_method,
        "image_path": img_path,
        "timestamp": datetime.now().isoformat(),
        "detection_id": f"{stream_id}_{animal_type}{animal_id}_{int(time.time())}"
    }

    # Log the detection with detailed information
    detection_entry = log_animal_detection(
        stream_id=stream_id,
        animal_type=animal_type,
        animal_id=animal_id,
        classification_result=classification_result,
        match_result=match_result,
        image_path=img_path
    )
    
    # Add detection ID to animal info
    if detection_entry and "id" in detection_entry:
        animal_info["detection_id"] = detection_entry["id"]

    # Ensure venv/tmp directory exists
    tmp_dir = os.path.join("venv", "tmp")
    os.makedirs(tmp_dir, exist_ok=True)

    notification_info = None
    notification_case = None

    # Case 1: Not Stray, Registered
    if not is_stray and match:
        notification_case = "not_stray_registered"
        notification_info = notify_owner(match, animal_img, animal_info)
        print(f"[TEST LOG] Case: Not Stray, Registered | Match: {match} (score: {match_score:.2f}, method: {match_method})")
        
    # Case 2: Not Stray, Not Registered
    elif not is_stray and not match:
        notification_case = "not_stray_unregistered"
        tmp_path = os.path.join(tmp_dir, f"not_stray_unknown_{animal_type}_{stream_id}_{int(time.time())}.jpg")
        cv2.imwrite(tmp_path, animal_img)
        notification_info = notify_pound(tmp_path, animal_info)
        print("[TEST LOG] Case: Not Stray, Not Registered | Notified Pound")
        
    # Case 3: Stray, Registered
    elif is_stray and match:
        notification_case = "stray_registered"
        notification_info = notify_owner(match, animal_img, animal_info)
        print(f"[TEST LOG] Case: Stray, Registered | Match: {match} (score: {match_score:.2f}, method: {match_method})")
        
    # Case 4: Stray, Not Registered
    elif is_stray and not match:
        notification_case = "stray_unregistered"
        tmp_path = os.path.join(tmp_dir, f"stray_unknown_{animal_type}_{stream_id}_{int(time.time())}.jpg")
        cv2.imwrite(tmp_path, animal_img)
        notification_info = notify_pound(tmp_path, animal_info)
        print("[TEST LOG] Case: Stray, Not Registered | Notified Pound")
    
    return {
        "animal_info": animal_info,
        "notification_case": notification_case,
        "notification_info": notification_info
    }

def save_debug_images(stream_id):
    debug_dir = os.path.join("venv", "debug", stream_id)
    abs_debug_dir = os.path.abspath(debug_dir)
    os.makedirs(abs_debug_dir, exist_ok=True)

    if not os.path.exists(abs_debug_dir):
        return None

    # Find the latest max snapshot file matching pattern stream_id_max_dog1.jpg or stream_id_max_cat1.jpg
    max_files = [f for f in os.listdir(abs_debug_dir) if f.startswith(f"{stream_id}_max_") and 
                (f.find("dog") != -1 or f.find("cat") != -1) and f.endswith(".jpg")]
    
    if not max_files:
        return None

    # Get the latest file by modification time
    latest_file = max(max_files, key=lambda f: os.path.getmtime(os.path.join(abs_debug_dir, f)))
    high_conf_path = os.path.join(abs_debug_dir, latest_file)
    high_conf_frame = cv2.imread(high_conf_path)

    if high_conf_frame is None:
        return None
    
    # Determine animal type from filename
    animal_type = "dog" if "dog" in latest_file else "cat"
    animal_id = latest_file.split("_")[-1].split(".")[0]  # Extract the ID (e.g., "dog1" -> "1")
    
    # Use the existing frame buffer if available for context
    snapshot_path = None
    if stream_data.get(stream_id, {}).get("frame_buffer") is not None:
        snapshot_path = os.path.join(debug_dir, "1_snapshot_with_detection.jpg")
        cv2.imwrite(snapshot_path, stream_data[stream_id]["frame_buffer"])
    
    # If we have a snapshot saved for this animal, use that instead
    snapshot_key = f"{animal_type}{animal_id}"
    if stream_id in stream_data and 'snapshots' in stream_data[stream_id] and snapshot_key in stream_data[stream_id]['snapshots']:
        snapshot_path = stream_data[stream_id]['snapshots'][snapshot_key]

    # Save cropped and cleaned image
    cleaned = remove_green_border(high_conf_frame)
    cleaned_path = os.path.join(debug_dir, "2_cropped_cleaned.jpg")
    cv2.imwrite(cleaned_path, cleaned)

    # Get classification result
    prediction = cnn_model.predict(preprocess_image(cleaned))[0]
    is_stray = prediction >= 0.3
    classification_result = "stray" if is_stray else "not_stray"

    # Try to find a match with registered owners using enhanced matching
    match_result = match_snapshot_to_owner(cleaned)
    match = match_result.get('match') if match_result else None
    match_score = match_result.get('score', 0) if match_result else 0
    match_method = match_result.get('method', 'none') if match_result else 'none'
    
    # Determine notification case based on stray classification and match result
    notification_case = None
    if is_stray and match:
        notification_case = "stray_registered"
    elif is_stray and not match:
        notification_case = "stray_unregistered"
    elif not is_stray and match:
        notification_case = "not_stray_registered"
    elif not is_stray and not match:
        notification_case = "not_stray_unregistered"
    
    # Get all matches for similar colored animals
    all_matches = match_result.get('all_matches', []) if match_result else []
    
    match_path = None
    color_matches_paths = []
    
    # Process the best match (if any)
    if match:
        db_img = cv2.imread(os.path.join(DATABASE_PATH, match))
        if db_img is not None:
            match_path = os.path.join(debug_dir, "3_feature_match.jpg")
            # Resize images to same height for side-by-side comparison
            h1, w1 = cleaned.shape[:2]
            h2, w2 = db_img.shape[:2]
            target_height = max(h1, h2)
            
            resized1 = cv2.resize(cleaned, (int(w1 * target_height / h1), target_height)) if h1 != target_height else cleaned
            resized2 = cv2.resize(db_img, (int(w2 * target_height / h2), target_height)) if h2 != target_height else db_img
            
            # Add match information to the comparison image
            info_text = f"Match: {match} (Score: {match_score:.2f}, Method: {match_method})"
            font = cv2.FONT_HERSHEY_SIMPLEX
            
            # Create a blank info bar
            info_bar = np.ones((40, resized1.shape[1] + resized2.shape[1], 3), dtype=np.uint8) * 255
            cv2.putText(info_bar, info_text, (10, 30), font, 0.7, (0, 0, 0), 2)
            
            # Stack the images vertically with the info bar
            stacked = np.vstack([info_bar, np.hstack((resized1, resized2))])
            cv2.imwrite(match_path, stacked)
    
    # If this is a dog, also save comparisons for all color matches
    if animal_type == "dog" and all_matches:
        # Create directory for color matches
        color_matches_dir = os.path.join(debug_dir, "color_matches")
        os.makedirs(color_matches_dir, exist_ok=True)
        
        # Save up to top 5 color matches for quick reference
        for idx, match_info in enumerate(all_matches[:5]):
            if 'path' not in match_info:
                continue
                
            owner_img = cv2.imread(match_info['path'])
            if owner_img is None:
                continue
            
            # Create comparison
            color_match_path = os.path.join(color_matches_dir, f"color_match_{idx+1}_{os.path.basename(match_info['path'])}")
            
            # Resize images to same height
            h1, w1 = cleaned.shape[:2]
            h2, w2 = owner_img.shape[:2]
            target_height = max(h1, h2)
            
            resized1 = cv2.resize(cleaned, (int(w1 * target_height / h1), target_height)) if h1 != target_height else cleaned
            resized2 = cv2.resize(owner_img, (int(w2 * target_height / h2), target_height)) if h2 != target_height else owner_img
            
            # Add match information to the comparison image
            color_score = match_info.get('color_score', 0)
            combined_score = match_info.get('combined_score', 0)
            info_text = f"Match: {match_info['filename']} (Color: {color_score:.2f}, Combined: {combined_score:.2f})"
            font = cv2.FONT_HERSHEY_SIMPLEX
            
            # Create a blank info bar
            info_bar = np.ones((40, resized1.shape[1] + resized2.shape[1], 3), dtype=np.uint8) * 255
            cv2.putText(info_bar, info_text, (10, 30), font, 0.7, (0, 0, 0), 2)
            
            # Stack the images vertically with the info bar
            stacked = np.vstack([info_bar, np.hstack((resized1, resized2))])
            cv2.imwrite(color_match_path, stacked)
            
            # Add path to list of color matches
            color_matches_paths.append(color_match_path)

    # Save timestamp for when analysis was performed
    analysis_time = time.strftime("%Y-%m-%d %H:%M:%S")

    return {
        "animal_type": animal_type,
        "animal_id": animal_id,
        "original_file": latest_file,
        "snapshot": snapshot_path,
        "cropped": cleaned_path,
        "classification": classification_result,
        "prediction_score": float(prediction),
        "match": match,
        "match_score": match_score,
        "match_method": match_method,
        "match_img": match_path,
        "all_matches_count": len(all_matches),
        "color_matches_paths": color_matches_paths,
        "notification_case": notification_case,
        "analysis_time": analysis_time
    }

# Add a new API endpoint to get detected animals
@app.route('/api2/detected', methods=['GET'])
def get_detected_animals():
    # Get query parameters
    stream_id = request.args.get('stream_id')
    animal_type = request.args.get('animal_type')  # 'dog' or 'cat'
    classification = request.args.get('classification')  # 'stray' or 'not_stray'
    limit = int(request.args.get('limit', 100))  # Default to 100 results
    
    # Filter results based on query parameters
    filtered_results = detected_animals_log.copy()
    
    if stream_id:
        filtered_results = [d for d in filtered_results if d['stream_id'] == stream_id]
    
    if animal_type:
        filtered_results = [d for d in filtered_results if d['animal_type'] == animal_type]
    
    if classification:
        filtered_results = [d for d in filtered_results if d['classification'] == classification]
    
    # Limit the number of results
    filtered_results = filtered_results[:limit]
    
    # Add image URLs for frontend display
    for result in filtered_results:
        if result.get('image_path'):
            result['image_url'] = f"/api2/detected-img/{result['stream_id']}/{os.path.basename(result['image_path'])}"
    
    return jsonify({
        "count": len(filtered_results),
        "detected_animals": filtered_results
    })

# Add endpoint to serve detected animal images
@app.route('/api2/detected-img/<stream_id>/<filename>')
def serve_detected_image(stream_id, filename):
    img_dir = os.path.join("venv", "detected", stream_id)
    if not os.path.exists(os.path.join(img_dir, filename)):
        return "File not found", 404
    return send_from_directory(img_dir, filename)

# Add endpoint to get statistics about detected animals
@app.route('/api2/stats')
def get_animal_stats():
    # Count by animal type
    animal_types = {}
    for animal in detected_animals_log:
        animal_type = animal['animal_type']
        if animal_type not in animal_types:
            animal_types[animal_type] = 0
        animal_types[animal_type] += 1
    
    # Count by stream
    streams = {}
    for animal in detected_animals_log:
        stream_id = animal['stream_id']
        if stream_id not in streams:
            streams[stream_id] = 0
        streams[stream_id] += 1
    
    # Count by classification
    classifications = {}
    for animal in detected_animals_log:
        classification = animal['classification']
        if classification not in classifications:
            classifications[classification] = 0
        classifications[classification] += 1
    
    # Count by match status
    matches = {"matched": 0, "unmatched": 0}
    for animal in detected_animals_log:
        if animal.get('match'):
            matches["matched"] += 1
        else:
            matches["unmatched"] += 1
    
    return jsonify({
        "total_detections": len(detected_animals_log),
        "by_animal_type": animal_types,
        "by_stream": streams,
        "by_classification": classifications,
        "by_match_status": matches
    })

@app.route('/api2/debug/<stream_id>')
def debug_pipeline(stream_id):
    result = save_debug_images(stream_id)
    if not result:
        return jsonify({"error": "No detections available in debug directory"}), 404

    # Construct URLs for frontend
    snapshot_url = None
    if result["snapshot"]:
        if os.path.basename(result["snapshot"]).startswith(stream_id):
            # If it's a snapshot from stream_data['snapshots']
            snapshot_url = f"/api2/debug-img/{stream_id}/{os.path.basename(result['snapshot'])}"
        else:
            # If it's the standard snapshot
            snapshot_url = f"/api2/debug-img/{stream_id}/{os.path.basename(result['snapshot'])}"
    
    # Construct URLs for color matches
    color_match_urls = []
    if result.get("color_matches_paths"):
        for path in result["color_matches_paths"]:
            dir_name = os.path.basename(os.path.dirname(path))
            file_name = os.path.basename(path)
            color_match_urls.append(f"/api2/debug-img/{stream_id}/{dir_name}/{file_name}")

    return jsonify({
        "message": "Debug analysis complete",
        "animal_type": result["animal_type"],
        "animal_id": result["animal_id"],
        "original_file": result["original_file"],
        "snapshot_url": snapshot_url,
        "cropped_url": f"/api2/debug-img/{stream_id}/{os.path.basename(result['cropped'])}",
        "classification": result["classification"],
        "prediction_score": result["prediction_score"],
        "match": result["match"],
        "match_score": result.get("match_score", 0),
        "match_method": result.get("match_method", "none"),
        "match_img_url": f"/api2/debug-img/{stream_id}/{os.path.basename(result['match_img'])}" if result.get("match_img") else None,
        "all_matches_count": result.get("all_matches_count", 0),
        "color_match_urls": color_match_urls,
        "notification_case": result.get("notification_case"),
        "analysis_time": result["analysis_time"],
        "all_matches_url": f"/api2/all-matches/{stream_id}"
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
    
# Add a new endpoint to show all potential matches for an animal
@app.route('/api2/all-matches/<stream_id>')
def show_all_matches(stream_id):
    debug_dir = os.path.join("venv", "debug", stream_id)
    abs_debug_dir = os.path.abspath(debug_dir)
    os.makedirs(abs_debug_dir, exist_ok=True)

    if not os.path.exists(abs_debug_dir):
        return jsonify({"error": "Debug directory not found"}), 404

    # Find the latest max snapshot file matching pattern stream_id_max_dog1.jpg or stream_id_max_cat1.jpg
    max_files = [f for f in os.listdir(abs_debug_dir) if f.startswith(f"{stream_id}_max_") and 
                (f.find("dog") != -1 or f.find("cat") != -1) and f.endswith(".jpg")]
    
    if not max_files:
        return jsonify({"error": "No animal snapshots found"}), 404

    # Get the latest file by modification time
    latest_file = max(max_files, key=lambda f: os.path.getmtime(os.path.join(abs_debug_dir, f)))
    high_conf_path = os.path.join(abs_debug_dir, latest_file)
    high_conf_frame = cv2.imread(high_conf_path)

    if high_conf_frame is None:
        return jsonify({"error": "Could not read image file"}), 500
    
    # Determine animal type from filename
    animal_type = "dog" if "dog" in latest_file else "cat"
    animal_id = latest_file.split("_")[-1].split(".")[0]  # Extract the ID (e.g., "dog1" -> "1")
    
    # Clean the image
    cleaned = remove_green_border(high_conf_frame)
    
    # Find all potential matches
    match_result = match_snapshot_to_owner(cleaned)
    if not match_result or 'all_matches' not in match_result or not match_result['all_matches']:
        return jsonify({"error": "No matches found", "animal_type": animal_type, "animal_id": animal_id}), 404
    
    # Directory to save comparison images
    comparisons_dir = os.path.join(abs_debug_dir, "comparisons")
    os.makedirs(comparisons_dir, exist_ok=True)
    
    # Create side-by-side comparisons for all matches
    comparison_results = []
    
    for idx, match_info in enumerate(match_result['all_matches']):
        owner_img_path = match_info['path']
        owner_img = cv2.imread(owner_img_path)
        
        if owner_img is None:
            continue
            
        # Create side-by-side comparison
        comparison_path = os.path.join(comparisons_dir, f"comparison_{idx+1}_{os.path.basename(owner_img_path)}")
        
        # Resize images to same height
        h1, w1 = cleaned.shape[:2]
        h2, w2 = owner_img.shape[:2]
        target_height = max(h1, h2)
        
        resized1 = cv2.resize(cleaned, (int(w1 * target_height / h1), target_height)) if h1 != target_height else cleaned
        resized2 = cv2.resize(owner_img, (int(w2 * target_height / h2), target_height)) if h2 != target_height else owner_img
        
        # Add match information to the comparison image
        color_score = match_info.get('color_score', 0)
        combined_score = match_info.get('combined_score', 0)
        info_text = f"Match: {match_info['filename']} (Color: {color_score:.2f}, Combined: {combined_score:.2f})"
        font = cv2.FONT_HERSHEY_SIMPLEX
        
        # Create a blank info bar
        info_bar = np.ones((40, resized1.shape[1] + resized2.shape[1], 3), dtype=np.uint8) * 255
        cv2.putText(info_bar, info_text, (10, 30), font, 0.7, (0, 0, 0), 2)
        
        # Stack the images vertically with the info bar
        stacked = np.vstack([info_bar, np.hstack((resized1, resized2))])
        cv2.imwrite(comparison_path, stacked)
        
        comparison_results.append({
            "rank": idx + 1,
            "filename": match_info['filename'],
            "combined_score": match_info['combined_score'],
            "color_score": match_info.get('color_score', 0),
            "feature_score": match_info.get('feature_score', 0),
            "method": match_info.get('method', 'visual'),
            "comparison_url": f"/api2/debug-img/{stream_id}/comparisons/{os.path.basename(comparison_path)}"
        })
    
    return jsonify({
        "animal_type": animal_type,
        "animal_id": animal_id,
        "original_file": latest_file,
        "matches_count": len(comparison_results),
        "matches": comparison_results
    })

# Add API endpoints for notifications
@app.route('/api2/notifications', methods=['GET'])
def get_notifications():
    """Get a list of all notifications with filtering options"""
    
    # Parse query parameters
    notification_type = request.args.get('type')  # 'owner_notification' or 'pound_notification'
    limit = int(request.args.get('limit', 50))
    stream_id = request.args.get('stream_id')
    animal_type = request.args.get('animal_type')
    notification_case = request.args.get('case')  # stray_registered, not_stray_unregistered, etc.
    
    # Filter notifications based on parameters
    filtered_notifications = notification_history.copy()
    
    if notification_type:
        filtered_notifications = [n for n in filtered_notifications if n.get('type') == notification_type]
    
    if notification_case:
        filtered_notifications = [n for n in filtered_notifications if 
                                n.get('animal_info', {}).get('notification_case') == notification_case]
    
    if stream_id:
        filtered_notifications = [n for n in filtered_notifications if 
                                n.get('animal_info', {}).get('stream_id') == stream_id]
    
    if animal_type:
        filtered_notifications = [n for n in filtered_notifications if 
                                n.get('animal_info', {}).get('animal_type') == animal_type]
    
    # Limit results
    limited_notifications = filtered_notifications[:limit]
    
    return jsonify({
        "count": len(limited_notifications),
        "notifications": limited_notifications
    })

@app.route('/api2/notifications/stats', methods=['GET'])
def get_notification_stats():
    """Get statistics about notifications"""
    
    # Count by notification type
    by_type = {
        "owner_notification": 0,
        "pound_notification": 0
    }
    
    # Count by notification case
    by_case = {
        "stray_registered": 0,
        "stray_unregistered": 0,
        "not_stray_registered": 0,
        "not_stray_unregistered": 0
    }
    
    # Count by stream
    by_stream = {}
    
    # Count by animal type
    by_animal_type = {
        "dog": 0,
        "cat": 0
    }
    
    for notification in notification_history:
        # Count by type
        ntype = notification.get('type')
        if ntype in by_type:
            by_type[ntype] += 1
        
        # Get animal info
        animal_info = notification.get('animal_info', {})
        
        # Count by case
        case = animal_info.get('notification_case')
        if case in by_case:
            by_case[case] += 1
        
        # Count by stream
        stream = animal_info.get('stream_id')
        if stream:
            if stream not in by_stream:
                by_stream[stream] = 0
            by_stream[stream] += 1
        
        # Count by animal type
        atype = animal_info.get('animal_type')
        if atype in by_animal_type:
            by_animal_type[atype] += 1
    
    return jsonify({
        "total": len(notification_history),
        "by_type": by_type,
        "by_case": by_case,
        "by_stream": by_stream,
        "by_animal_type": by_animal_type
    })

@app.route('/api2/notifications/<notification_id>', methods=['GET'])
def get_notification_details(notification_id):
    """Get detailed information about a specific notification"""
    
    for notification in notification_history:
        if notification.get('id') == notification_id:
            return jsonify(notification)
    
    return jsonify({"error": "Notification not found"}), 404

# Add this API endpoint to check database status
@app.route('/api2/database/status')
def check_database():
    """Debug endpoint to check database status"""
    # Re-load database to ensure fresh data
    count = precompute_owner_embeddings()
    
    return jsonify({
        "database_path": DATABASE_PATH,
        "files_loaded": count,
        "sample_files": list(owner_embeddings.keys())[:5] if owner_embeddings else [],
        "status": "ok" if count > 0 else "error"
    })

if __name__ == '__main__':
    # Initialize the pet database
    print("Initializing pet database...")
    precompute_owner_embeddings()
    
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
