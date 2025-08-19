from flask import Flask, Response, jsonify
from flask_cors import CORS
import cv2
import numpy as np
from ultralytics import YOLO
import time
import requests
import telebot

app = Flask(__name__)
CORS(app)

model = YOLO("yolov8n.pt")
VIDEO_PATH = r"C:\\Users\\tamil\\OneDrive\\Pictures\\hack\\crowdai\\Crowd\\Highway-2.mp4"
max_vehicles_per_zone = 10

TOKEN = "7695804495:AAGjeDcJRGaiTyWgAW-gtDUrozNAcqS596A"
CHAT_ID = "2132444686"
bot = telebot.TeleBot(TOKEN)

previous_positions = {}
distance_per_pixel = 0.05  # Adjust based on real-world scaling

def estimate_speed(vehicle_id, new_x):
    new_x = float(new_x)  # Convert tensor to float
    if vehicle_id in previous_positions:
        old_x, old_time = previous_positions[vehicle_id]
        time_diff = time.time() - old_time
        if time_diff > 0:
            speed = abs(new_x - old_x) * distance_per_pixel / time_diff
            previous_positions[vehicle_id] = (new_x, time.time())
            return round(float(speed), 2)
    previous_positions[vehicle_id] = (new_x, time.time())
    return 0

def generate_frames():
    cap = cv2.VideoCapture(VIDEO_PATH)
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        height, width, _ = frame.shape
        results = model(frame)
        vehicles = {}
        max_speed = 0
        max_speed_zone = ""

        for i, (box, cls) in enumerate(zip(results[0].boxes.xyxy, results[0].boxes.cls)):
            if int(cls) in [2, 3, 5, 7]:  # Car, Motorbike, Bus, Truck
                vehicle_id = f"{cls}_{i}"
                zone = "zone1" if box[0] < width//3 else "zone2" if box[0] < 2*width//3 else "zone3"
                vehicles[zone] = vehicles.get(zone, 0) + 1
                speed = estimate_speed(vehicle_id, box[0])
                if speed > max_speed:
                    max_speed = speed
                    max_speed_zone = zone
                
                cv2.putText(frame, f"Speed: {speed} km/h", (int(box[0]), int(box[1] - 10)), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        if max_speed > 0:
            cv2.putText(frame, f"Max Speed: {max_speed} km/h in {max_speed_zone}", 
                        (10, height - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        _, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    
    cap.release()

@app.route('/traffic_feed')
def traffic_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/get_traffic_data')
def get_traffic_data():
    data = {
        "vehicles_per_zone": {
            "zone1": np.random.randint(0, 20),
            "zone2": np.random.randint(0, 20),
            "zone3": np.random.randint(0, 20)
        },
        "highest_speed": max(previous_positions.values(), key=lambda x: x[0], default=(0,))[0] if previous_positions else 0
    }
    return jsonify(data)

if __name__ == "__main__":
    print("Flask server running at http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
