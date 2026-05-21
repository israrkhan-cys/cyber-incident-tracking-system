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
from routes.incidents import incidents_bp
app.register_blueprint(incidents_bp)


# ── Dashboard ────────────────────────────────────────────
@app.route('/')
@login_required
def index():
    cur = mysql.connection.cursor()

    # Summary counts
    cur.execute("SELECT COUNT(*) AS c FROM incidents WHERE status='open'")
    open_count = cur.fetchone()['c']
    cur.execute("SELECT COUNT(*) AS c FROM incidents WHERE status='investigating'")
    investigating_count = cur.fetchone()['c']
    cur.execute("SELECT COUNT(*) AS c FROM incidents WHERE status='resolved'")
    resolved_count = cur.fetchone()['c']
    cur.execute("SELECT COUNT(*) AS c FROM incidents WHERE status='closed'")
    closed_count = cur.fetchone()['c']
    cur.execute("SELECT COUNT(*) AS c FROM incidents WHERE severity='critical'")
    critical_count = cur.fetchone()['c']
    cur.execute("SELECT COUNT(*) AS c FROM incidents WHERE severity='high'")
    high_count = cur.fetchone()['c']
    cur.execute("SELECT COUNT(*) AS c FROM incidents WHERE severity='medium'")
    medium_count = cur.fetchone()['c']
    cur.execute("SELECT COUNT(*) AS c FROM incidents WHERE severity='low'")
    low_count = cur.fetchone()['c']
    cur.execute("SELECT COUNT(*) AS c FROM incidents")
    total_count = cur.fetchone()['c']

    # Recent incidents (last 5)
    cur.execute("""
        SELECT i.*, c.name AS category_name, u.username AS assignee_name
        FROM incidents i
        LEFT JOIN categories c ON i.category_id = c.category_id
        LEFT JOIN users u ON i.assigned_to = u.user_id
        ORDER BY i.reported_at DESC
        LIMIT 5
    """)
    recent_incidents = cur.fetchall()

    cur.close()

    severity_counts = {
        'critical': critical_count,
        'high': high_count,
        'medium': medium_count,
        'low': low_count,
    }
    status_counts = {
        'open': open_count,
        'investigating': investigating_count,
        'resolved': resolved_count,
        'closed': closed_count,
    }

    return render_template('index.html',
                           recent_incidents=recent_incidents,
                           open_count=open_count,
                           investigating_count=investigating_count,
                           critical_count=critical_count,
                           total_count=total_count,
                           severity_counts=severity_counts,
                           status_counts=status_counts)


# ── Admin: Users ─────────────────────────────────────────
@app.route('/admin/users')
@login_required
def admin_users():
    if current_user.role != 'admin':
        flash('Admin access required.', 'danger')
        return redirect(url_for('index'))
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users ORDER BY created_at DESC")
    users = cur.fetchall()
    cur.close()
    return render_template('admin/users.html', users=users)


@app.route('/admin/users/<int:user_id>/update', methods=['POST'])
@login_required
def admin_update_user(user_id):
    if current_user.role != 'admin':
        flash('Admin access required.', 'danger')
        return redirect(url_for('index'))
    role = request.form.get('role')
    if role not in ('admin', 'analyst', 'viewer'):
        flash('Invalid role.', 'danger')
        return redirect(url_for('admin_users'))
    cur = mysql.connection.cursor()
    cur.execute("UPDATE users SET role = %s WHERE user_id = %s", (role, user_id))
    mysql.connection.commit()
    cur.close()
    flash('User role updated.', 'success')
    return redirect(url_for('admin_users'))


@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@login_required
def admin_delete_user(user_id):
    if current_user.role != 'admin':
        flash('Admin access required.', 'danger')
        return redirect(url_for('index'))
    if user_id == current_user.id:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('admin_users'))
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
    mysql.connection.commit()
    cur.close()
    flash('User deleted.', 'success')
    return redirect(url_for('admin_users'))


if __name__ == '__main__':
    app.run(debug=True)
