
import cv2
import torch
import time
import requests
import numpy as np
import function.utils_rotate as utils_rotate
import function.helper as helper

# ESP32-CAM Image Capture URL (Adjust this to match your setup)
ESP32_CAM_URL = "http://192.168.137.128/cam-hi.jpg"

# Load YOLO models
yolo_LP_detect = torch.hub.load('yolov5', 'custom', path='model/LP_detector_nano_61.pt', source='local')
yolo_license_plate = torch.hub.load('yolov5', 'custom', path='model/LP_ocr_nano_62.pt', source='local')
yolo_license_plate.conf = 0.60

prev_frame_time = 0

while True:
    try:
        # Fetch an image from ESP32-CAM
        response = requests.get(ESP32_CAM_URL, stream=True, timeout=2)
        if response.status_code != 200:
            print("[ERROR] Failed to retrieve image. Retrying...")
            continue

        # Convert image to OpenCV format
        img_arr = np.array(bytearray(response.content), dtype=np.uint8)
        frame = cv2.imdecode(img_arr, -1)

        if frame is None:
            print("[WARNING] Frame is empty. Retrying...")
            continue

        # Detect plates using YOLO
        plates = yolo_LP_detect(frame, size=640)
        list_plates = plates.pandas().xyxy[0].values.tolist()
        list_read_plates = set()

        for plate in list_plates:
            flag = 0
            x, y, w, h = int(plate[0]), int(plate[1]), int(plate[2] - plate[0]), int(plate[3] - plate[1])
            crop_img = frame[y:y + h, x:x + w]
            cv2.rectangle(frame, (x, y), (x + w, y + h), color=(0, 0, 255), thickness=2)

            for cc in range(2):
                for ct in range(2):
                    lp = helper.read_plate(yolo_license_plate, utils_rotate.deskew(crop_img, cc, ct))
                    if lp != "unknown":
                        list_read_plates.add(lp)
                        cv2.putText(frame, lp, (x, y - 10), cv2.FONT_HERSHEY_COMPLEX, 1.5, (0, 0, 255), 1)
                        flag = 1
                        break
                if flag:
                    break

        # Display FPS
        new_frame_time = time.time()
        fps = int(1 / (new_frame_time - prev_frame_time))
        prev_frame_time = new_frame_time
        cv2.putText(frame, f"FPS: {fps}", (10, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255), 1)

        # Show the image
        cv2.imshow('ESP32-CAM Stream', frame)

        # Press 'q' to exit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Request failed: {e}")
        time.sleep(1)  # Wait before retrying

cv2.destroyAllWindows()
