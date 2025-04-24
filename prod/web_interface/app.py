import os
import time
import json
import datetime
import threading
import redis
from flask import Flask, render_template, jsonify, request, Response
import cv2
import numpy as np

from prod.config import (
    REDIS_HOST,
    REDIS_PORT,
    REDIS_PASSWORD,
    REDIS_DB,
    RESULTS_STORE,
    FRAMES_QUEUE,
    FACES_QUEUE,
    RECOGNITION_QUEUE,
    DATABASE_URL
)
from prod.utils import get_redis_connection, decode_image

app = Flask(__name__, template_folder='templates', static_folder='static')
redis_client = get_redis_connection()

# Cache for the latest processed frame from each stream
latest_frames = {}
frame_lock = threading.Lock()

# Background thread to process frames
def update_frames():
    while True:
        try:
            # Get all keys in the results store
            all_results = redis_client.hgetall(RESULTS_STORE)
            
            if not all_results:
                time.sleep(0.5)
                continue
            
            # Process the latest result for each stream
            stream_results = {}
            for key, value in all_results.items():
                key_str = key.decode('utf-8')
                parts = key_str.split(':')
                if len(parts) >= 2:
                    stream_id = parts[0]
                    timestamp = float(parts[1])
                    
                    if stream_id not in stream_results or timestamp > stream_results[stream_id]['timestamp']:
                        result = json.loads(value.decode('utf-8'))
                        stream_results[stream_id] = {
                            'timestamp': timestamp,
                            'data': result
                        }
            
            # Update latest frames with the processed results
            with frame_lock:
                for stream_id, result in stream_results.items():
                    if stream_id not in latest_frames:
                        latest_frames[stream_id] = {'frame': None, 'results': []}
                    
                    latest_frames[stream_id]['results'] = result['data']
        
        except Exception as e:
            print(f"Error updating frames: {str(e)}")
        
        time.sleep(1)

# Routes
@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/api/stats')
def get_stats():
    """Get system statistics"""
    try:
        # Get queue lengths
        frames_queue_len = redis_client.llen(FRAMES_QUEUE)
        faces_queue_len = redis_client.llen(FACES_QUEUE)
        recognition_queue_len = redis_client.llen(RECOGNITION_QUEUE)
        
        # Get active streams
        streams = list(latest_frames.keys())
        
        # Get detection counts
        results_count = len(redis_client.hgetall(RESULTS_STORE))
        
        return jsonify({
            'status': 'running',
            'queues': {
                'frames': frames_queue_len,
                'faces': faces_queue_len,
                'recognition': recognition_queue_len
            },
            'streams': streams,
            'results_count': results_count,
            'timestamp': datetime.datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/results')
def get_results():
    """Get the latest detection results"""
    try:
        all_results = redis_client.hgetall(RESULTS_STORE)
        results = []
        
        for key, value in all_results.items():
            result = json.loads(value.decode('utf-8'))
            result['key'] = key.decode('utf-8')
            results.append(result)
        
        # Sort by timestamp, newest first
        results.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
        
        # Limit to the latest 100 results
        results = results[:100]
        
        return jsonify({
            'results': results,
            'count': len(results)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

def main():
    """Run the Flask app"""
    # Start the frame update thread
    frame_thread = threading.Thread(target=update_frames, daemon=True)
    frame_thread.start()
    
    # Get the host IP and port from environment variables or use defaults
    host = os.environ.get('WEB_HOST', '0.0.0.0')
    port = int(os.environ.get('WEB_PORT', 5000))
    
    print(f"Starting web interface on http://{host}:{port}")
    app.run(host=host, port=port, debug=False, threaded=True)

if __name__ == '__main__':
    main() 