# StraySafe Flask Detection Server

This is the Flask server component of the StraySafe system that handles real-time video processing and dog detection. It works seamlessly with the StraySafe web application.

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- PyTorch
- OpenCV
- Flask
- CORS
- Ultralytics RTDETR

### Installation

1. Install the required Python packages:

```bash
pip install flask flask-cors opencv-python torch torchvision ultralytics python-dotenv pillow
```

2. Place your trained models in the same directory:
   - `best.pt` - The RTDETR model for dog detection
   - `resnet.pth` - The ResNet model for leash classification

3. Rename `env_config.txt` to `.env` to configure the server:

```bash
mv env_config.txt .env
```

4. Edit the `.env` file to match your environment settings.

### Running the Server

Start the Flask server:

```bash
python new_stream.py
```

The server will run on port 5000 by default and will be accessible at `http://localhost:5000`.

## API Endpoints

- `/streams` - GET: Returns a list of all available video streams
- `/video/<stream_id>` - GET: Streams video for the specified stream ID
- `/scan` - GET: Scans for new RTSP streams
- `/health` - GET: Health check endpoint

## Integration with StraySafe Web App

The StraySafe web application is already configured to connect to this Flask server. Make sure both are running on the same server for seamless integration.

The web app will automatically fetch the list of available streams from the `/streams` endpoint and display the video feeds using the `/video/<stream_id>` endpoint.

## Troubleshooting

- If you encounter CORS issues, make sure the Flask server is running on the same domain as the web application or that CORS is properly configured.
- If video streams are not loading, check that the RTSP URLs are accessible from the server.
- If models are not loading, verify that the model files exist in the correct location and have the correct format.
