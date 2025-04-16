from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin, current_user
from config import Config
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, session, url_for, Response
import cv2
import torch
import requests
import numpy as np
import function.utils_rotate as utils_rotate
import function.helper as helper
import threading
import time
from flask import request, redirect, url_for
from datetime import datetime
import base64
import os


latest_plate = "unknown"
ESP32_CAM_URL = "http://192.168.137.68/cam.mjpeg"
app = Flask(__name__)
app.config.from_object(Config)

mysql = MySQL(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# User class for session
# User class for Flask-Login
class User(UserMixin):
    def __init__(self, id, username, name, email, phone, role):
        self.id = id
        self.username = username
        self.name = name
        self.email = email
        self.phone = phone
        self.role = role

@login_manager.user_loader
def load_user(user_id):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id, username, name, email, phone, role FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()

    if user:
        return User(*user)  # Unpack all 6 values
    return None

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password_input = request.form['password']
        selected_role = request.form['role']
        remember = 'remember' in request.form  # Check if "Remember Me" is checked

        cur = mysql.connection.cursor()
        # Fetch all necessary fields for the User constructor
        cur.execute("SELECT id, username, name, email, phone, role, password FROM users WHERE username=%s", (username,))
        user = cur.fetchone()
        cur.close()

        if user and check_password_hash(user[6], password_input):
            # Check if the selected role matches the user's actual role
            if user[5] != selected_role:
                flash(f'Role mismatch: You are not an {selected_role}', 'danger')
                return redirect(url_for('login'))
            # Pass all required arguments to User
            user_obj = User(user[0], user[1], user[2], user[3], user[4], user[5])
            login_user(user_obj, remember=remember)
            flash('Login successful!', 'success')
            if user[5] == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('camera'))
        else:
            flash("Invalid username or password", "danger")
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', username=current_user.username, role=current_user.role)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))
@app.route('/camera')
@login_required
def camera():
    return render_template('camera.html', streaming=True)
@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


# --- FUNCTION TO STREAM FRAMES AND DETECT PLATES ---
def gen_frames():
    global latest_plate

    # Load models once here
    yolo_LP_detect = torch.hub.load('yolov5', 'custom', path='model/LP_detector_nano_61.pt', source='local')
    yolo_license_plate = torch.hub.load('yolov5', 'custom', path='model/LP_ocr_nano_62.pt', source='local')
    yolo_license_plate.conf = 0.60

    stream = requests.get(ESP32_CAM_URL, stream=True)
    byte_data = b''

    for chunk in stream.iter_content(chunk_size=1024):
        byte_data += chunk
        a = byte_data.find(b'\xff\xd8')  # JPEG start
        b = byte_data.find(b'\xff\xd9')  # JPEG end

        if a != -1 and b != -1 and b > a:
            jpg = byte_data[a:b + 2]
            byte_data = byte_data[b + 2:]

            frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
            if frame is None:
                continue

            # Detect plates
            plates = yolo_LP_detect(frame, size=640)
            list_plates = plates.pandas().xyxy[0].values.tolist()

            for plate in list_plates:
                x, y, w, h = int(plate[0]), int(plate[1]), int(plate[2] - plate[0]), int(plate[3] - plate[1])
                crop_img = frame[y:y + h, x:x + w]
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)

                for cc in range(2):
                    for ct in range(2):
                        lp = helper.read_plate(yolo_license_plate, utils_rotate.deskew(crop_img, cc, ct))
                        if lp != "unknown":
                            latest_plate = lp  # ✅ Save most recent plate
                            print(f"[STREAM DETECTED] {latest_plate}")
                            cv2.putText(frame, lp, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
                            break

            # Encode and stream frame
            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                continue
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


# --- CAPTURE LATEST PLATE ROUTE ---
@app.route('/capture_plate')
def capture_plate():
    global latest_plate
    plate_to_return = latest_plate  # Save the result first
    print(f"[CAPTURE] Detected number plate: {plate_to_return}")

    latest_plate = "unknown"  # ✅ Reset after use
    return jsonify({"plate": plate_to_return})

@app.route('/register_plate', methods=['POST'])
@login_required
def register_plate():
    try:
        data = request.form
        plate = data.get('license_plate')
        captured_at = datetime.now()
        image_data_url = data.get('image_data')  # Expect base64 image data from client

        # Get user info
        user_id = current_user.id
        name = current_user.username
        email = current_user.email
        phone = current_user.phone

        # Decode base64 image
        if image_data_url and "," in image_data_url:
            header, encoded = image_data_url.split(",", 1)
            image_blob = base64.b64decode(encoded)
        else:
            image_blob = None  # Optional fallback

        # Insert into DB
        cursor = mysql.connection.cursor()
        cursor.execute("""
            INSERT INTO registrations (user_id, license_plate, captured_at, name, email, phone, image)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (user_id, plate, captured_at, name, email, phone, image_blob))
        mysql.connection.commit()
        cursor.close()

        print(f"[REGISTERED] Plate: {plate}, Time: {captured_at}, User: {name}")
        flash(f"Successfully registered plate {plate} at {captured_at.strftime('%Y-%m-%d %H:%M:%S')}", "success")
        return redirect(url_for('camera'))

    except Exception as e:
        print(f"[ERROR] During registration: {str(e)}")
        flash("Registration failed", "danger")
        return "Registration failed", 500

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        role = request.form['role']

        # Hash the password
        hashed_password = generate_password_hash(password)

        try:
            cursor = mysql.connection.cursor()
            cursor.execute(
                "INSERT INTO users (username, password, name, email, phone, role) VALUES (%s, %s, %s, %s, %s, %s)",
                (username, hashed_password, name, email, phone, role)
            )
            mysql.connection.commit()
            cursor.close()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            print(f"[ERROR] During registration: {str(e)}")
            flash('Registration failed. Username may already exist.', 'danger')
            return redirect(url_for('register'))

    return render_template('register.html')

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        new_password = request.form['new_password']

        # Hash the new password
        hashed_password = generate_password_hash(new_password)

        try:
            cursor = mysql.connection.cursor()
            cursor.execute(
                "UPDATE users SET password = %s WHERE email = %s",
                (hashed_password, email)
            )
            mysql.connection.commit()
            affected_rows = cursor.rowcount
            cursor.close()

            if affected_rows == 0:
                flash('No user found with that email address.', 'danger')
                return redirect(url_for('forgot_password'))

            flash('Password reset successful! Please log in with your new password.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            print(f"[ERROR] During password reset: {str(e)}")
            flash('Password reset failed.', 'danger')
            return redirect(url_for('forgot_password'))

    return render_template('forgot_password.html')
@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Access denied: Admins only', 'danger')
        return redirect(url_for('camera'))

    cursor = mysql.connection.cursor()
    cursor.execute("""
        SELECT id, user_id, license_plate, captured_at, name, email, phone, status, note, image
        FROM registrations
        ORDER BY captured_at DESC
    """)
    results = cursor.fetchall()
    cursor.close()

    registrations_list = []
    for row in results:
        reg_id, user_id, plate, captured_at, name, email, phone, status, note, image_blob = row

        # Convert image BLOB to base64
        if image_blob:
            image_base64 = base64.b64encode(image_blob).decode('utf-8')
        else:
            image_base64 = None

        reg_dict = {
            'id': reg_id,
            'user_id': user_id,
            'license_plate': plate,
            'captured_at': captured_at,
            'name': name,
            'email': email,
            'phone': phone,
            'status': status,
            'note': note,
            'image_data': image_base64
        }

        registrations_list.append(reg_dict)

    return render_template('admin_dashboard.html', registrations=registrations_list)

# Approve plate route
@app.route('/approve_plate/<int:registration_id>', methods=['POST'])
@login_required
def approve_plate(registration_id):
    if current_user.role != 'admin':
        flash('Access denied: Admins only', 'danger')
        return redirect(url_for('camera'))

    try:
        cursor = mysql.connection.cursor()
        cursor.execute(
            "UPDATE registrations SET status = 'approved' WHERE id = %s",
            (registration_id,)
        )
        mysql.connection.commit()
        cursor.close()
        flash('Plate approved successfully', 'success')
    except Exception as e:
        print(f"[ERROR] Approving plate: {str(e)}")
        flash('Failed to approve plate', 'danger')

    return redirect(url_for('admin_dashboard'))
@app.route('/deny_plate_with_reason', methods=['POST'])
@login_required
def deny_plate_with_reason():
    if current_user.role != 'admin':
        flash('Access denied: Admins only', 'danger')
        return redirect(url_for('camera'))

    registration_id = request.form.get('registration_id')
    reason = request.form.get('reason')

    try:
        cursor = mysql.connection.cursor()
        cursor.execute(
            "UPDATE registrations SET status = 'denied', note = %s WHERE id = %s",
            (reason, registration_id)
        )
        mysql.connection.commit()
        cursor.close()
        flash('Plate denied with reason provided', 'danger')
    except Exception as e:
        print(f"[ERROR] Denying plate with reason: {str(e)}")
        flash('Failed to deny plate', 'danger')

    return redirect(url_for('admin_dashboard'))

@app.route('/account')
@login_required
def account():
    cursor = mysql.connection.cursor()
    cursor.execute("""
        SELECT license_plate, captured_at, name, email, phone, status, note, image
        FROM registrations
        WHERE user_id = %s
        ORDER BY captured_at DESC
    """, (current_user.id,))
    results = cursor.fetchall()
    cursor.close()

    # Convert image BLOBs to base64 strings
    registrations = []
    for row in results:
        plate, captured_at, name, email, phone, status, note, image_blob = row
        if image_blob:
            image_base64 = base64.b64encode(image_blob).decode('utf-8')
        else:
            image_base64 = None
        registrations.append((plate, captured_at, name, email, phone, status, note, image_base64))

    return render_template('account.html', registrations=registrations)


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    cur = mysql.connection.cursor()

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']

        cur.execute("""
            UPDATE users SET name=%s, email=%s, phone=%s
            WHERE id=%s
        """, (name, email, phone, current_user.id))
        mysql.connection.commit()
        cur.close()

        flash("Profile updated successfully!", "success")
        return redirect(url_for('camera'))

    cur.execute("SELECT name, email, phone FROM users WHERE id=%s", (current_user.id,))
    user = cur.fetchone()
    cur.close()
    return render_template('edit_profile.html', user=user)

if __name__ == '__main__':
    app.run(debug=True)
