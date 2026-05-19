# 🛡️ Cyber Incident Tracking System (CITS)

A web-based cybersecurity incident tracking system that allows organizations to report,
track, investigate, and resolve cyber incidents with role-based access control.

## Team

|       Name         |
|--------------------|
| Muhammad Israr     |      
| Saad Ali           |      
| Mohammad bin nawaz |      


## Tech Stack

| Layer    | Technology          |
|----------|---------------------|
| Backend  | Python 3, Flask     |
| Database | MariaDB / MySQL     |
| Frontend | HTML, Jinja2, CSS   |
| Charts   | Chart.js            |
| Auth     | Flask-Login, Bcrypt |

## Features

- Role-based access — Admin, Analyst, Viewer
- Report and track incidents (Phishing, DDoS, Ransomware, etc.)
- Incident status lifecycle — Open → Investigating → Resolved → Closed
- Automatic audit log on every action
- Affected assets tracking
- Comment threads per incident
- Dashboard with live charts

## Team Setup

### 1. Clone the repo
\```bash
git clone https://github.com/israrkhan-cys/cyber-incident-tracking-system.git
cd cyber-incident-tracking-system
\```

### 2. Create virtual environment
\```bash
python -m venv .venv
source .venv/bin/activate
\```

### 3. Install dependencies
\```bash
pip install -r requirements.txt --break-system-packages
\```

### 4. Setup config
\```bash
cp config.example.py config.py
# Open config.py and fill in your own DB credentials
\```

### 5. Setup database
\```bash
mysql -u your_db_user -p < db/schema.sql
\```

### 6. Run the app
\```bash
python app.py
\```
Visit → http://127.0.0.1:5000

## Default Test Accounts

After running schema.sql, these accounts are available:

| Username | Email              | Role    |
|----------|--------------------|---------|
| admin    | admin@cyber.com    | admin   |
| analyst1 | analyst@cyber.com  | analyst |
| viewer1  | viewer@cyber.com   | viewer  |

> ⚠️ Passwords in the DB are placeholder — register fresh accounts via /register

\```

## Course
Database Systems — FAST University Peshawar
