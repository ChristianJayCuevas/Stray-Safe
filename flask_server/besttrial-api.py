# Add a new API endpoint to get detected animals
@app.route('/api2/detected', methods=['GET'])
def get_detected_animals():
    # Get query parameters
    stream_id = request.args.get('stream_id')
    animal_type = request.args.get('animal_type')  # 'dog' or 'cat'
    classification = request.args.get('classification')  # 'stray' or 'not_stray'
    notification_type = request.args.get('notification_type')  # 'owner_notification' or 'pound_notification'
    notification_case = request.args.get('notification_case')  # 'stray_registered', 'stray_unregistered', etc.
    limit = int(request.args.get('limit', 100))  # Default to 100 results
    
    # If no detections exist for the requested stream_id, run save_debug_images to populate the log
    if stream_id and not any(d['stream_id'] == stream_id for d in detected_animals_log):
        result = save_debug_images(stream_id)
        # If debug analysis was successful, wait a moment for the log to update
        if result:
            time.sleep(0.2)  # Short delay to ensure the log is updated
    # If no specific stream_id was provided, check all available streams
    elif not stream_id:
        # Get list of all stream IDs
        all_streams = list(stream_data.keys())
        for sid in all_streams:
            # Only analyze streams with no detections in the log
            if not any(d['stream_id'] == sid for d in detected_animals_log):
                save_debug_images(sid)
    
    # Filter results based on query parameters
    filtered_results = detected_animals_log.copy()
    
    if stream_id:
        filtered_results = [d for d in filtered_results if d['stream_id'] == stream_id]
    
    if animal_type:
        filtered_results = [d for d in filtered_results if d['animal_type'] == animal_type]
    
    if classification:
        filtered_results = [d for d in filtered_results if d['classification'] == classification]
        
    if notification_type:
        filtered_results = [d for d in filtered_results if d.get('notification_type') == notification_type]
        
    if notification_case:
        filtered_results = [d for d in filtered_results if d.get('notification_case') == notification_case]
    
    # Limit the number of results
    filtered_results = filtered_results[:limit]
    
    # Add image URLs for frontend display
    for result in filtered_results:
        # Add image URL
        if result.get('image_path'):
            result['image_url'] = f"/api2/detected-img/{result['stream_id']}/{os.path.basename(result['image_path'])}"
        
        # Ensure all fields are present (for backward compatibility with older entries)
        if 'notification_case' not in result:
            # Determine notification case based on classification and match status
            is_stray = result.get('classification') == 'stray'
            has_match = bool(result.get('match'))
            
            # Set notification case and type if not already present
            if is_stray and has_match:
                result['notification_case'] = 'stray_registered'
                result['notification_type'] = 'owner_notification'
            elif is_stray and not has_match:
                result['notification_case'] = 'stray_unregistered'
                result['notification_type'] = 'pound_notification'
            elif not is_stray and has_match:
                result['notification_case'] = 'not_stray_registered'
                result['notification_type'] = 'owner_notification'
            elif not is_stray and not has_match:
                result['notification_case'] = 'not_stray_unregistered'
                result['notification_type'] = 'pound_notification'
    
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
        # Check both the direct stream_id and the one in animal_info
        filtered_notifications = [n for n in filtered_notifications if 
                               (n.get('stream_id') == stream_id or 
                                n.get('animal_info', {}).get('stream_id') == stream_id)]
    
    if animal_type:
        filtered_notifications = [n for n in filtered_notifications if 
                                n.get('animal_info', {}).get('animal_type') == animal_type]
    
    # Limit results
    limited_notifications = filtered_notifications[:limit]
    
    # Add display-friendly stream_id to each notification if not already present
    for notification in limited_notifications:
        if 'stream_id' not in notification:
            notification['stream_id'] = notification.get('animal_info', {}).get('stream_id', 'unknown')
    
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
        
        # Get stream_id either from the notification directly or from animal_info
        stream_id = notification.get('stream_id') or animal_info.get('stream_id', 'unknown')
        
        # Count by case
        case = animal_info.get('notification_case')
        if case in by_case:
            by_case[case] += 1
        
        # Count by stream
        if stream_id:
            if stream_id not in by_stream:
                by_stream[stream_id] = 0
            by_stream[stream_id] += 1
        
        # Count by animal type
        atype = animal_info.get('animal_type')
        if atype in by_animal_type:
            by_animal_type[atype] += 1
    
    return jsonify({
        "total": len(notification_history),
        "by_type": by_type,
        "by_case": by_case,
        "by_stream": by_stream,
        "by_animal_type": by_animal_type,
        "recent_streams": list(by_stream.keys())[:5]  # Include 5 most recent streams for quick reference
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

@app.route('/api2/test-notification', methods=['GET'])
def test_notification():
    """
    Test endpoint to create a notification for debugging purposes
    """
    stream_id = request.args.get('stream_id', 'test-stream')
    animal_type = request.args.get('animal_type', 'dog')
    notify_type = request.args.get('notify_type', 'owner')  # 'owner' or 'pound'
    
    # Create dummy animal info
    animal_info = {
        "stream_id": stream_id,
        "animal_type": animal_type,
        "animal_id": "test1",
        "classification": "not_stray" if notify_type == "owner" else "stray",
        "prediction_score": 0.2 if notify_type == "owner" else 0.8,
        "is_stray": notify_type != "owner",
        "match": "test_owner.jpg" if notify_type == "owner" else None,
        "match_score": 0.75 if notify_type == "owner" else 0,
        "match_method": "test" if notify_type == "owner" else "none",
        "timestamp": datetime.now().isoformat(),
        "detection_id": f"{stream_id}_{animal_type}test1_{int(time.time())}",
        "notification_case": "not_stray_registered" if notify_type == "owner" else "stray_unregistered"
    }
    
    notification = None
    
    # Create a notification
    if notify_type == "owner":
        # Create owner notification
        notification = notify_owner("test_owner.jpg", None, animal_info)
    else:
        # Create pound notification
        tmp_path = os.path.join("venv", "tmp", f"test_{animal_type}_{stream_id}_{int(time.time())}.jpg")
        os.makedirs(os.path.dirname(tmp_path), exist_ok=True)
        
        # Create a blank image if needed for testing
        test_img = np.ones((100, 100, 3), dtype=np.uint8) * 255
        cv2.imwrite(tmp_path, test_img)
        
        notification = notify_pound(tmp_path, animal_info)
    
    return jsonify({
        "status": "success",
        "message": f"Created test {notify_type} notification for {stream_id}",
        "notification": notification
    })