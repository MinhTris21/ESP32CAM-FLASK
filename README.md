📝 Project Overview
Student ID: 21200363
Major: Embedded Systems & Computer Engineering
Course: FETEL
This project develops an automated system for detecting and registering vehicle license plates using the ESP32-CAM. The system captures images, processes them to extract license plate numbers, and stores the data via a Flask-based web server. It is designed for applications like parking management, traffic monitoring, and smart city infrastructure.

✨ Key Features
Real-Time Image Capture: Captures high-quality images using the ESP32-CAM's OV2640 camera module.
License Plate Recognition: Uses image processing and OCR (via Tesseract) to detect and extract license plate numbers accurately.
Web-Based Registration: A Python Flask web app provides an interface to display, store, and manage license plate data.
Scalable Design: Combines lightweight processing on the ESP32-CAM with server-side computation for efficiency.
Data Storage: Integrates SQLite for persistent storage of license plate records.
🛠️ Technologies Used
Hardware: ESP32-CAM microcontroller
Programming Languages:
C++ (for ESP32-CAM firmware)
Python (for Flask web app and OCR processing)
Frameworks & Libraries:
Python Flask (web framework)
OpenCV (image processing)
Tesseract OCR (text extraction)
SQLite (database)
Communication: Wi-Fi for real-time data transfer between ESP32-CAM and Flask server
📋 System Architecture
ESP32-CAM: Captures images and performs initial processing (e.g., grayscale conversion, edge detection).
Image Transmission: Sends processed images to the Flask server over Wi-Fi.
Flask Server: Uses OpenCV and Tesseract OCR to extract license plate numbers and store them in SQLite.
Web Interface: Displays detected plates and allows users to manage records (view, edit, delete).
