# 🚗 License Plate Recognition System Using ESP32-CAM

An embedded system that detects and registers vehicle license plates using the ESP32-CAM. Captured images are processed with OCR and stored in a structured database, all managed through a lightweight Flask web interface.

---

## 🔧 Key Features

- **Real-Time Image Capture:**  
  ESP32-CAM (OV2640) captures images on demand.

- **License Plate Detection:**  
  OpenCV and Tesseract OCR extract plate numbers from images.

- **Web-Based Interface:**  
  Flask app displays, stores, and manages plate data.

- **Efficient Architecture:**  
  ESP32 handles image capture; server performs processing and storage.

- **Data Persistence:**  
  License plate records stored via SQL for reliable access.

---

## 💡 System Overview


---

## 🛠 Technologies

- **Hardware:** ESP32-CAM (OV2640)
- **Languages:** C++ (ESP32), Python (Flask & processing)
- **Libraries:** OpenCV, Tesseract OCR
- **Database:** SQLite via SQL Workbench
- **Communication:** Wi-Fi (ESP32 ↔ Server)
