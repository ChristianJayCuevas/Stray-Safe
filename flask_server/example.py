import cv2
import torch
from ultralytics import RTDETR

def process_video(video_path, model_path, conf_threshold=0.1, output_video="output.avi", start_time=24*60, end_time=24*60+30, skip_frames=1):
    # Load YOLO model (Use GPU if available)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = RTDETR(model_path).to(device)

    # Open video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Cannot open video {video_path}")
        return
    
    # Get video properties
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = cv2.VideoWriter_fourcc(*"XVID")  # Codec for AVI
    out = cv2.VideoWriter(output_video, fourcc, fps, (width, height))

    # Convert time to frame numbers
    start_frame = start_time * fps
    end_frame = end_time * fps
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

    print(f"Processing frames from {start_time} sec to {end_time} sec...")

    frame_count = start_frame
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret or frame_count > end_frame:
            break

        # Skip frames for faster processing
        if frame_count % skip_frames == 0:
            # Run YOLO detection
            results = model(frame, verbose=False)

            # Draw bounding boxes
            for result in results:
                for box in result.boxes:
                    if box.conf.item() > conf_threshold:  
                        x1, y1, x2, y2 = map(int, box.xyxy[0])  
                        cls = int(box.cls.item())  
                        conf = round(box.conf.item(), 2)  

                        # Draw rectangle and label
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        label = f"Class {cls}: {conf:.2f}"
                        cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # Save frame to output video
        out.write(frame)
        frame_count += 1

    cap.release()
    out.release()
    print(f"Processing complete. Output video saved as {output_video}.")
