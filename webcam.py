# from PIL import Image
# import cv2
# import torch
# import math
# import function.utils_rotate as utils_rotate
# from IPython.display import display
# import os
# import time
# import argparse
# import function.helper as helper
#
# yolo_LP_detect = torch.hub.load('yolov5', 'custom', path='model/LP_detector.pt', force_reload=True, source='local')
# yolo_license_plate = torch.hub.load('yolov5', 'custom', path='model/LP_ocr.pt', force_reload=True, source='local')
# yolo_license_plate.conf = 0.60
#
# prev_frame_time = 0
# new_frame_time = 0
#
# # Optional: Set lower webcam resolution to reduce processing load
# vid = cv2.VideoCapture(0)  # Use default webcam
# vid.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)  # Adjust resolution (e.g., 1280x720)
# vid.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
# if not vid.isOpened():
#     print("Error: Could not open webcam.")
#     exit()
#
# frame_skip = 1  # Process every frame (set to 2 or 3 to skip frames)
# frame_count = 0
#
# while True:
#     ret, img = vid.read()
#     if not ret:
#         print("Failed to capture frame")
#         break
#
#     frame_count += 1
#     if frame_count % frame_skip != 0:
#         continue  # Skip frame
#
#     plates = yolo_LP_detect(img, size=416)  # Reduced size for faster inference
#     list_plates = plates.pandas().xyxy[0].values.tolist()
#     list_read_plates = set()
#     if len(list_plates) > 0:  # Only process plates if detected
#         for plate in list_plates:
#             flag = 0
#             x = int(plate[0])  # xmin
#             y = int(plate[1])  # ymin
#             w = int(plate[2] - plate[0])  # xmax - xmin
#             h = int(plate[3] - plate[1])  # ymax - ymin
#             crop_img = img[y:y+h, x:x+w]
#             cv2.rectangle(img, (int(plate[0]), int(plate[1])), (int(plate[2]), int(plate[3])), color=(0, 0, 225), thickness=2)
#             lp = ""
#             for cc in range(0, 2):
#                 for ct in range(0, 2):
#                     lp = helper.read_plate(yolo_license_plate, utils_rotate.deskew(crop_img, cc, ct))
#                     if lp != "unknown":
#                         list_read_plates.add(lp)
#                         cv2.putText(img, lp, (int(plate[0]), int(plate[1]-10)), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12), 2)
#                         flag = 1
#                         break
#                 if flag == 1:
#                     break
#
#     # Calculate and display FPS
#     new_frame_time = time.time()
#     fps = 1 / (new_frame_time - prev_frame_time)
#     prev_frame_time = new_frame_time
#     fps = int(fps)
#     cv2.putText(img, str(fps), (7, 70), cv2.FONT_HERSHEY_SIMPLEX, 3, (100, 255, 0), 3, cv2.LINE_AA)
#
#     cv2.imshow('frame', img)
#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         break
#
# vid.release()
# cv2.destroyAllWindows()
from PIL import Image
import cv2
import torch
import math
import function.utils_rotate as utils_rotate
from IPython.display import display
import os
import time
import argparse
import function.helper as helper

yolo_LP_detect = torch.hub.load('yolov5', 'custom', path='model/LP_detector.pt', force_reload=True, source='local')
yolo_license_plate = torch.hub.load('yolov5', 'custom', path='model/LP_ocr.pt', force_reload=True, source='local')
yolo_license_plate.conf = 0.60

prev_frame_time = 0
new_frame_time = 0

# Optional: Set lower webcam resolution to reduce processing load
vid = cv2.VideoCapture(0)  # Use default webcam
vid.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)  # Adjust resolution (e.g., 1280x720)
vid.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
if not vid.isOpened():
    print("Error: Could not open webcam.")
    exit()

frame_skip = 1  # Process every frame (set to 2 or 3 to skip frames)
frame_count = 0

while True:
    ret, img = vid.read()
    if not ret:
        print("Failed to capture frame")
        break

    frame_count += 1
    if frame_count % frame_skip != 0:
        continue  # Skip frame

    plates = yolo_LP_detect(img, size=416)  # Reduced size for faster inference
    list_plates = plates.pandas().xyxy[0].values.tolist()
    list_read_plates = set()
    if len(list_plates) > 0:  # Only process plates if detected
        for plate in list_plates:
            flag = 0
            x = int(plate[0])  # xmin
            y = int(plate[1])  # ymin
            w = int(plate[2] - plate[0])  # xmax - xmin
            h = int(plate[3] - plate[1])  # ymax - ymin
            crop_img = img[y:y+h, x:x+w]
            cv2.rectangle(img, (int(plate[0]), int(plate[1])), (int(plate[2]), int(plate[3])), color=(0, 0, 225), thickness=2)
            lp = ""
            for cc in range(0, 2):
                for ct in range(0, 2):
                    lp = helper.read_plate(yolo_license_plate, utils_rotate.deskew(crop_img, cc, ct))
                    if lp != "unknown":
                        list_read_plates.add(lp)
                        cv2.putText(img, lp, (int(plate[0]), int(plate[1]-10)), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12), 2)
                        flag = 1
                        break
                if flag == 1:
                    break

    # Calculate and display FPS
    new_frame_time = time.time()
    fps = 1 / (new_frame_time - prev_frame_time)
    prev_frame_time = new_frame_time
    fps = int(fps)
    cv2.putText(img, str(fps), (7, 70), cv2.FONT_HERSHEY_SIMPLEX, 3, (100, 255, 0), 3, cv2.LINE_AA)

    cv2.imshow('frame', img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

vid.release()
cv2.destroyAllWindows()