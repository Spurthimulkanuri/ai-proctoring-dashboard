# test_violation_sender.py
import cv2
import base64
import requests

def send_violation(frame, violation_type):
    _, buffer = cv2.imencode('.jpg', frame)
    img_b64 = base64.b64encode(buffer).decode('utf-8')
    data = {
        "image": f"data:image/jpeg;base64,{img_b64}",
        "student_id": "narendra",
        "violation_type": violation_type
    }
    print("[📤] Sending to /upload_snapshot", data.get("violation_type"))
    response = requests.post("http://127.0.0.1:5000/upload_snapshot", json=data)
    print("[✅] Response:", response.json())

cap = cv2.VideoCapture(0)
ret, frame = cap.read()
if ret:
    send_violation(frame, "mobile_or_hand")
cap.release()

