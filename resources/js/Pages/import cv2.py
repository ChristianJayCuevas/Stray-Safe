import cv2
import datetime
import time
import multiprocessing
import os
import signal
import sys

# Configuration
STOP_TIME = "19:00"  # Stop recording at this time (24-hour format)
RTSP_STREAMS = [
    "rtsp://ADMIN:12345@192.168.1.5:554/cam/realmonitor?channel=2&subtype=0",
]
OUTPUT_DIR = "D:/PD2 Videos"
TARGET_WIDTH, TARGET_HEIGHT = 960, 544  # Resolution for saved videos
TIMESTAMP = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
os.makedirs(OUTPUT_DIR, exist_ok=True)
stop_event = multiprocessing.Event()

def record_stream(idx, rtsp_url):
    """Records an RTSP stream, resizes frames, and saves as .avi."""
    print(f"[Thread {idx}] Connecting to {rtsp_url}...")
    
    while not stop_event.is_set():
        cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 10)  # Reduce buffering delay
        
        if not cap.isOpened():
            print(f"[Thread {idx}] ❌ Error: Cannot open stream. Retrying in 10s...")
            time.sleep(10)
            continue  # Retry connection
        
        fps = max(int(cap.get(cv2.CAP_PROP_FPS)), 15)  # Default to 15 FPS if unknown
        output_file = os.path.join(OUTPUT_DIR, f"stream_{idx}_{TIMESTAMP}.avi")
        fourcc = cv2.VideoWriter_fourcc(*'XVID')  # AVI format (XVID codec)
        writer = cv2.VideoWriter(output_file, fourcc, fps, (TARGET_WIDTH, TARGET_HEIGHT))
        
        print(f"[Thread {idx}] 🎥 Recording started: {rtsp_url} ({TARGET_WIDTH}x{TARGET_HEIGHT}, {fps} FPS)")
        
        try:
            while not stop_event.is_set():
                if datetime.datetime.now().strftime("%H:%M") == STOP_TIME:
                    print(f"[Thread {idx}] 🛑 Stop time reached. Stopping...")
                    stop_event.set()
                    break
                
                ret, frame = cap.read()
                if ret:
                    frame_resized = cv2.resize(frame, (TARGET_WIDTH, TARGET_HEIGHT))
                    writer.write(frame_resized)
                else:
                    print(f"[Thread {idx}] ⚠️ Frame read failed. Retrying...")
                    time.sleep(1)
        except Exception as e:
            print(f"[Thread {idx}] 🔴 Error: {e}")
        finally:
            cap.release()
            writer.release()
            print(f"[Thread {idx}] ✅ Cleanup complete. Stream closed.")
            break

def signal_handler(sig, frame):
    """Handle Ctrl+C and terminate all processes."""
    print("\n🛑 Ctrl+C detected. Stopping all recordings...")
    stop_event.set()
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    processes = []
    
    for idx, rtsp_url in enumerate(RTSP_STREAMS):
        p = multiprocessing.Process(target=record_stream, args=(idx, rtsp_url), daemon=True)
        p.start()
        processes.append(p)
    
    try:
        for p in processes:
            p.join()
    except KeyboardInterrupt:
        signal_handler(None, None)
    
    cv2.destroyAllWindows()
    print("✅ All recordings finished successfully.")