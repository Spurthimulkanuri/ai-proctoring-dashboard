import torch
import cv2
import numpy as np
from PIL import Image
import io
import base64

# Load YOLOv5 model
model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)

def detect_phone(base64_img):
    img_data = base64.b64decode(base64_img.split(",")[1])
    img = Image.open(io.BytesIO(img_data)).convert("RGB")
    img_np = np.array(img)

    results = model(img_np)
    for *box, conf, cls in results.xyxy[0]:
        if int(cls) == 67:  # 67 = cell phone
            return True
    return False

