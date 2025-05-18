-- CREATE DATABASE IF NOT EXISTS vehicle_system;

-- USE vehicle_system;

-- CREATE TABLE users (
--     id INT AUTO_INCREMENT PRIMARY KEY,
--     username VARCHAR(50) UNIQUE NOT NULL,
--     password VARCHAR(255) NOT NULL,
--     name VARCHAR(100),
--     email VARCHAR(100),
--     phone VARCHAR(20),
--     role ENUM('user', 'admin') DEFAULT 'user'
-- );
-- INSERT INTO users (username, password, name, email, phone, role)
-- VALUES (
--     'minhtris',
--     'scrypt:32768:8:1$pivYEd0pwHhd8YSC$558adc33be51f373cb1f64aadb31a0394f789c7b27b036b19a6a6df7b677e75baf96a966fade51423d400ea846d3d62c4fb869324e652c20f17f4d62005c5984',  -- hashed password: admin@123
--     'System Admin',
--     'admin@example.com',
--     '0123456789',
--     'user'
-- );
CREATE TABLE registrations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    license_plate VARCHAR(20),
    captured_at DATETIME,
    name VARCHAR(100),
    email VARCHAR(100),
    phone VARCHAR(20),
    status ENUM('pending', 'approved', 'denied') DEFAULT 'pending',
    FOREIGN KEY (user_id) REFERENCES users(id)
);
SELECT * FROM registrations;
INSERT INTO users (username, password, name, email, phone, role)
VALUES (
    'minhtrisadmin',
    'scrypt:32768:8:1$3zdo7pCkiMyIfTKS$7d68dabdc353fb272e636f8d93ea753a0821db5271e97448070b159fb339042b003a812e4a81073d999bc092ded1f12070fcb8c3baf4afd91b80e9d13f71d2c2',  -- hashed password: 123
    'System Admin',
    'admin@example.com',
    '0123456789',
    'admin'
);
ALTER TABLE registrations
ADD image LONGBLOB,
ADD note TEXT;
SELECT id, LENGTH(image) AS img_size FROM registrations WHERE image IS NOT NULL;
CREATE TABLE admin_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    admin_id INT,
    action VARCHAR(255),
    registration_id INT,
    details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (admin_id) REFERENCES users(id),
    FOREIGN KEY (registration_id) REFERENCES registrations(id)
);