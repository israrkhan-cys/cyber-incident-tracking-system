 # Cyber Incident Tracking System (CITS)

A web-based cyber incident tracking system built with Flask, MySQL, and HTML/CSS.

## Tech Stack
- Python (Flask)
- MariaDB / MySQL
- HTML(jinja2), CSS
- Chart.js

## Team Setup

### 1. Clone the repo
git clone https://github.com/yourusername/CITS.git
cd CITS

### 2. Create virtual environment
python -m venv .venv

source .venv/bin/activate

### 3. Install dependencies
pip install -r requirements.txt --break-system-packages

### 4. Setup config
cp config.example.py config.py
# Open config.py and fill in your DB credentials

### 5. Setup database
mysql -u root -p < db/schema.sql

### 6. Run the app
python app.py
Visit http://127.0.0.1:5000
