import cv2
import mediapipe as mp
import base64
import time
import requests

# Setup
mp_face = mp.solutions.face_mesh
mp_hands = mp.solutions.hands

student_id = "spurthi_raj"  # change this dynamically

API_URL = "http://127.0.0.1:5000/upload_snapshot"

def send_violation(frame, violation_type):
    _, buffer = cv2.imencode('.jpg', frame)
    img_b64 = base64.b64encode(buffer).decode('utf-8')
    data = {
        "image": f"data:image/jpeg;base64,{img_b64}",
        "student_id": student_id,
        "violation_type": violation_type
    }
    response = requests.post(API_URL, json=data)
    print(f"[📸] Sent: {violation_type}, Status: {response.status_code}")

def main():
    cap = cv2.VideoCapture(0)
    with mp_face.FaceMesh(static_image_mode=False, max_num_faces=1, refine_landmarks=True) as face_mesh, \
         mp_hands.Hands(max_num_hands=2) as hands:

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            face_results = face_mesh.process(rgb)
            hand_results = hands.process(rgb)

            # 🔍 Check 1: No Face
            if not face_results.multi_face_landmarks:
                send_violation(frame, "face_not_detected")

            # 🔍 Check 2: Lip Movement (mouth open detection)
            elif face_results.multi_face_landmarks:
                mouth_open = is_mouth_open(face_results.multi_face_landmarks[0])
                if mouth_open:
                    send_violation(frame, "talking")

            # 🔍 Check 3: Hand / Phone Use
            if hand_results.multi_hand_landmarks:
                send_violation(frame, "mobile_or_hand")

            cv2.imshow("Proctoring", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()

def is_mouth_open(landmarks):
    # Upper & Lower lip indices (based on mediapipe mesh)
    upper = landmarks.landmark[13].y
    lower = landmarks.landmark[14].y
    diff = abs(upper - lower)
    return diff > 0.03  # threshold can be tuned

if __name__ == '__main__':
    main()

