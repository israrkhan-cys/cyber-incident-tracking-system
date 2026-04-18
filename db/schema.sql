DROP DATABASE IF EXISTS cyber_incidents;
CREATE DATABASE cyber_incidents;
USE cyber_incidents;

CREATE TABLE users (
    user_id    INT AUTO_INCREMENT PRIMARY KEY,
    username   VARCHAR(50)  NOT NULL UNIQUE,
    email      VARCHAR(100) NOT NULL UNIQUE,
    password   VARCHAR(255) NOT NULL,
    role       ENUM('admin','analyst','viewer') DEFAULT 'viewer',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE categories (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    description TEXT
);

CREATE TABLE incidents (
    incident_id  INT AUTO_INCREMENT PRIMARY KEY,
    title        VARCHAR(200) NOT NULL,
    description  TEXT,
    severity     ENUM('low','medium','high','critical') NOT NULL,
    status       ENUM('open','investigating','resolved','closed') DEFAULT 'open',
    category_id  INT,
    reported_by  INT,
    assigned_to  INT,
    reported_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at   DATETIME ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(category_id) ON DELETE SET NULL,
    FOREIGN KEY (reported_by) REFERENCES users(user_id) ON DELETE SET NULL,
    FOREIGN KEY (assigned_to) REFERENCES users(user_id) ON DELETE SET NULL
);

CREATE TABLE incident_logs (
    log_id      INT AUTO_INCREMENT PRIMARY KEY,
    incident_id INT NOT NULL,
    user_id     INT NOT NULL,
    action      VARCHAR(255) NOT NULL,
    logged_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (incident_id) REFERENCES incidents(incident_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id)     REFERENCES users(user_id)         ON DELETE CASCADE
);

CREATE TABLE assets (
    asset_id    INT AUTO_INCREMENT PRIMARY KEY,
    incident_id INT NOT NULL,
    asset_type  VARCHAR(100),
    identifier  VARCHAR(200),
    FOREIGN KEY (incident_id) REFERENCES incidents(incident_id) ON DELETE CASCADE
);

CREATE TABLE comments (
    comment_id  INT AUTO_INCREMENT PRIMARY KEY,
    incident_id INT NOT NULL,
    user_id     INT NOT NULL,
    content     TEXT NOT NULL,
    posted_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (incident_id) REFERENCES incidents(incident_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id)     REFERENCES users(user_id)         ON DELETE CASCADE
);

INSERT INTO users (username, email, password, role) VALUES
('admin',   'admin@cyber.com',   'hashed_later', 'admin'),
('analyst1','analyst@cyber.com', 'hashed_later', 'analyst'),
('viewer1', 'viewer@cyber.com',  'hashed_later', 'viewer');

INSERT INTO categories (name, description) VALUES
('Phishing',    'Email-based social engineering attacks'),
('Ransomware',  'Malware that encrypts files for ransom'),
('DDoS',        'Distributed Denial of Service attacks'),
('Data Breach', 'Unauthorized access to sensitive data'),
('Insider Threat', 'Threats from within the organization');

INSERT INTO incidents (title, description, severity, status, category_id, reported_by, assigned_to) VALUES
('Phishing email targeting HR', 'Multiple HR staff received suspicious emails with malicious links', 'high', 'open', 1, 3, 2),
('Ransomware on File Server',   'File server FS-01 has been encrypted, ransom note found',          'critical', 'investigating', 2, 2, 2),
('DDoS on public web portal',   'Website experiencing abnormal traffic, response time degraded',    'medium', 'resolved', 3, 1, 2);

INSERT INTO assets (incident_id, asset_type, identifier) VALUES
(1, 'Workstation', '192.168.1.45'),
(2, 'Server',      'FS-01 / 10.0.0.12'),
(3, 'Web Server',  'webserver.company.com');

INSERT INTO incident_logs (incident_id, user_id, action) VALUES
(1, 3, 'Incident reported'),
(2, 2, 'Incident reported'),
(2, 2, 'Status changed to investigating'),
(3, 1, 'Incident reported'),
(3, 2, 'Status changed to resolved');

INSERT INTO comments (incident_id, user_id, content) VALUES
(1, 2, 'Blocked sender domain at email gateway. Monitoring for further attempts.'),
(2, 2, 'Isolated affected server from network. Contacting backup team.'),
(3, 1, 'Traffic normalized after enabling rate limiting on load balancer.');
