from flask import Flask, render_template, redirect, url_for, flash, request
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_required, current_user
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

mysql         = MySQL(app)
bcrypt        = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'

class User(UserMixin):
    def __init__(self, user_id, username, role):
        self.id       = user_id
        self.username = username
        self.role     = role

@login_manager.user_loader
def load_user(user_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
    user = cur.fetchone()
    cur.close()
    if user:
        return User(user['user_id'], user['username'], user['role'])
    return None

from routes.auth import auth
app.register_blueprint(auth)

# ── View incident detail ─────────────────────────────────
@app.route('/incident/<int:incident_id>')
@login_required
def incident_detail(incident_id):
    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT i.*, 
               c.name AS category_name,
               r.username AS reporter_name,
               a.username AS assignee_name
        FROM incidents i
        LEFT JOIN categories c ON i.category_id = c.category_id
        LEFT JOIN users r ON i.reported_by = r.user_id
        LEFT JOIN users a ON i.assigned_to = a.user_id
        WHERE i.incident_id = %s
    """, (incident_id,))
    incident = cur.fetchone()

    if not incident:
        flash('Incident not found.', 'danger')
        return redirect(url_for('index'))

    cur.execute("SELECT * FROM assets WHERE incident_id = %s", (incident_id,))
    assets = cur.fetchall()

    cur.execute("""
        SELECT cm.*, u.username
        FROM comments cm
        JOIN users u ON cm.user_id = u.user_id
        WHERE cm.incident_id = %s
        ORDER BY cm.posted_at ASC
    """, (incident_id,))
    comments = cur.fetchall()

    cur.execute("""
        SELECT il.*, u.username
        FROM incident_logs il
        JOIN users u ON il.user_id = u.user_id
        WHERE il.incident_id = %s
        ORDER BY il.logged_at ASC
    """, (incident_id,))
    logs = cur.fetchall()

    cur.close()
    return render_template('incident_detail.html',
                           incident=incident,
                           assets=assets,
                           comments=comments,
                           logs=logs)

# ── Report new incident ──────────────────────────────────
@app.route('/incident/new', methods=['GET', 'POST'])
@login_required
def new_incident():
    if current_user.role not in ('admin', 'analyst'):
        flash('You do not have permission to report incidents.', 'danger')
        return redirect(url_for('index'))

    cur = mysql.connection.cursor()

    if request.method == 'POST':
        title       = request.form['title']
        description = request.form['description']
        severity    = request.form['severity']
        category_id = request.form['category_id'] or None
        assigned_to = request.form['assigned_to'] or None

        cur.execute("""
            INSERT INTO incidents (title, description, severity, status, category_id, reported_by, assigned_to)
            VALUES (%s, %s, %s, 'open', %s, %s, %s)
        """, (title, description, severity, category_id, current_user.id, assigned_to))
        mysql.connection.commit()

        new_id = cur.lastrowid

        cur.execute("""
            INSERT INTO incident_logs (incident_id, user_id, action)
            VALUES (%s, %s, %s)
        """, (new_id, current_user.id, 'Incident reported'))
        mysql.connection.commit()
        cur.close()

        flash('Incident reported successfully.', 'success')
        return redirect(url_for('incident_detail', incident_id=new_id))

    cur.execute("SELECT * FROM categories")
    categories = cur.fetchall()

    cur.execute("SELECT user_id, username, role FROM users ORDER BY username")
    users = cur.fetchall()

    cur.close()
    return render_template('new_incident.html', categories=categories, users=users)

# ── Edit incident ────────────────────────────────────────
@app.route('/incident/<int:incident_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_incident(incident_id):
    if current_user.role not in ('admin', 'analyst'):
        flash('You do not have permission to edit incidents.', 'danger')
        return redirect(url_for('incident_detail', incident_id=incident_id))

    cur = mysql.connection.cursor()

    if request.method == 'POST':
        title       = request.form['title']
        description = request.form['description']
        severity    = request.form['severity']
        status      = request.form['status']
        category_id = request.form['category_id'] or None
        assigned_to = request.form['assigned_to'] or None

        cur.execute("SELECT * FROM incidents WHERE incident_id = %s", (incident_id,))
        old = cur.fetchone()

        cur.execute("""
            UPDATE incidents
            SET title=%s, description=%s, severity=%s, status=%s,
                category_id=%s, assigned_to=%s
            WHERE incident_id=%s
        """, (title, description, severity, status, category_id, assigned_to, incident_id))
        mysql.connection.commit()

        changes = []
        if old['title']       != title:       changes.append('Title updated')
        if old['description'] != description: changes.append('Description updated')
        if old['severity']    != severity:    changes.append(f'Severity changed to {severity}')
        if old['status']      != status:      changes.append(f'Status changed to {status}')
        if str(old['assigned_to'] or '') != str(assigned_to or ''):
            changes.append('Assignee updated')

        for change in changes:
            cur.execute("""
                INSERT INTO incident_logs (incident_id, user_id, action)
                VALUES (%s, %s, %s)
            """, (incident_id, current_user.id, change))
        mysql.connection.commit()
        cur.close()

        flash('Incident updated successfully.', 'success')
        return redirect(url_for('incident_detail', incident_id=incident_id))

    cur.execute("SELECT * FROM incidents WHERE incident_id = %s", (incident_id,))
    incident = cur.fetchone()

    if not incident:
        flash('Incident not found.', 'danger')
        cur.close()
        return redirect(url_for('index'))

    cur.execute("SELECT * FROM categories")
    categories = cur.fetchall()

    cur.execute("SELECT user_id, username, role FROM users ORDER BY username")
    users = cur.fetchall()

    cur.close()
    return render_template('edit_incident.html', incident=incident, categories=categories, users=users)

# ── Dashboard ────────────────────────────────────────────
@app.route('/')
@login_required
def index():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM incidents")
    incidents = cur.fetchall()
    cur.close()
    return render_template('index.html', incidents=incidents)

if __name__ == '__main__':
    app.run(debug=True)