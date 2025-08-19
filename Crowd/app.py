from flask import Flask, Response, jsonify
from flask_cors import CORS
from ultralytics import YOLO
import cv2
from datetime import datetime

app = Flask(__name__)
CORS(app)
model = YOLO("yolov8n.pt")

# Video source
video_source = r"C:\Users\tamil\OneDrive\Pictures\hack\crowdai\Crowd\crowd.mp4"
cap = cv2.VideoCapture(video_source)

zone_threshold = 3  
expected_total_people = 500
previous_counts = {"zone1": 0, "zone2": 0, "zone3": 0}
clear_times = {"zone1": None, "zone2": None, "zone3": None}

@app.route('/video_feed')
def video_feed():
    """ Stream full video frame by frame """
    def generate():
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Loop video
                continue
            _, buffer = cv2.imencode('.jpg', frame)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/get_crowd_data')
def get_crowd_data():
    """ Detect people and return crowd data """
    global cap, previous_counts, clear_times, expected_total_people
    ret, frame = cap.read()
    if not ret:
        return jsonify({"error": "Failed to read video feed"})

    results = model(frame)
    h, w, _ = frame.shape

    zones = {"zone1": 0, "zone2": 0, "zone3": 0}
    total_people = 0

    for box in results[0].boxes.xyxy:
        x1, _, x2, _ = map(int, box[:4])
        center_x = (x1 + x2) // 2

        if center_x < w // 3:
            zones["zone1"] += 1
        elif center_x < 2 * w // 3:
            zones["zone2"] += 1
        else:
            zones["zone3"] += 1

        total_people += 1

    missing_people = max(0, expected_total_people - total_people)

    alerts = []
    for zone, count in zones.items():
        if count > zone_threshold and previous_counts[zone] <= zone_threshold:
            alert_message = f"\U0001F6A8 {zone} overcrowded! Move to another zone."
            alerts.append(alert_message)

        if count <= zone_threshold and previous_counts[zone] > zone_threshold:
            clear_times[zone] = datetime.now().strftime('%H:%M:%S')
            clear_message = f"✅ {zone} is now clear. Cleared at {clear_times[zone]}"
            alerts.append(clear_message)

    previous_counts = zones.copy()

    return jsonify({
        "people_per_zone": zones,
        "total_people": total_people,
        "missing_people": missing_people,
        "clear_times": clear_times,
        "alert": " | ".join(alerts) if alerts else "No overcrowding"
    })

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)