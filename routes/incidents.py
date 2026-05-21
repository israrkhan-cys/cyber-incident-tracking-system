from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

incidents_bp = Blueprint('incidents', __name__)


def get_mysql():
    from app import mysql
    return mysql


# ── Incidents list ───────────────────────────────────────
@incidents_bp.route('/incidents')
@login_required
def incidents():
    mysql = get_mysql()
    cur = mysql.connection.cursor()

    severity  = request.args.get('severity', '')
    status    = request.args.get('status', '')
    category  = request.args.get('category_id', '')
    search    = request.args.get('search', '')

    query = """
        SELECT i.*,
               c.name AS category_name,
               a.username AS assignee_name
        FROM incidents i
        LEFT JOIN categories c ON i.category_id = c.category_id
        LEFT JOIN users a ON i.assigned_to = a.user_id
        WHERE 1=1
    """
    params = []

    if severity:
        query += " AND i.severity = %s"
        params.append(severity)
    if status:
        query += " AND i.status = %s"
        params.append(status)
    if category:
        query += " AND i.category_id = %s"
        params.append(category)
    if search:
        query += " AND (i.title LIKE %s OR i.description LIKE %s)"
        params.append(f'%{search}%')
        params.append(f'%{search}%')

    query += " ORDER BY i.reported_at DESC"
    cur.execute(query, params)
    all_incidents = cur.fetchall()

    cur.execute("SELECT * FROM categories ORDER BY name")
    categories = cur.fetchall()

    cur.close()
    return render_template('incidents.html',
                           incidents=all_incidents,
                           categories=categories,
                           filters={
                               'severity': severity,
                               'status': status,
                               'category_id': category,
                               'search': search,
                           })


# ── View incident detail ─────────────────────────────────
@incidents_bp.route('/incident/<int:incident_id>')
@login_required
def incident_detail(incident_id):
    mysql = get_mysql()
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


@incidents_bp.route('/incident/<int:incident_id>/delete', methods=['POST'])
@login_required
def delete_incident(incident_id):
    if current_user.role != 'admin':
        flash('Admin access required.', 'danger')
        return redirect(url_for('incidents.incident_detail', incident_id=incident_id))

    mysql = get_mysql()
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM incidents WHERE incident_id = %s", (incident_id,))
    deleted = cur.rowcount
    mysql.connection.commit()
    cur.close()

    if not deleted:
        flash('Incident not found.', 'danger')
    else:
        flash('Incident deleted.', 'success')
    return redirect(url_for('incidents.incidents'))


# ── Assets ───────────────────────────────────────────────
@incidents_bp.route('/incident/<int:incident_id>/asset/add', methods=['POST'])
@login_required
def add_asset(incident_id):
    if current_user.role not in ('admin', 'analyst'):
        flash('Permission denied.', 'danger')
        return redirect(url_for('incidents.incident_detail', incident_id=incident_id))

    asset_type = request.form.get('asset_type', '').strip()
    identifier = request.form.get('identifier', '').strip()

    if not identifier:
        flash('Asset identifier is required.', 'danger')
        return redirect(url_for('incidents.incident_detail', incident_id=incident_id))

    mysql = get_mysql()
    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO assets (incident_id, asset_type, identifier)
        VALUES (%s, %s, %s)
    """, (incident_id, asset_type, identifier))
    mysql.connection.commit()
    cur.close()

    flash('Asset added.', 'success')
    return redirect(url_for('incidents.incident_detail', incident_id=incident_id))


@incidents_bp.route('/incident/<int:incident_id>/asset/<int:asset_id>/delete', methods=['POST'])
@login_required
def delete_asset(incident_id, asset_id):
    if current_user.role not in ('admin', 'analyst'):
        flash('Permission denied.', 'danger')
        return redirect(url_for('incidents.incident_detail', incident_id=incident_id))

    mysql = get_mysql()
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM assets WHERE asset_id = %s AND incident_id = %s", (asset_id, incident_id))
    mysql.connection.commit()
    cur.close()

    flash('Asset removed.', 'success')
    return redirect(url_for('incidents.incident_detail', incident_id=incident_id))


# ── Comments ─────────────────────────────────────────────
@incidents_bp.route('/incident/<int:incident_id>/comment', methods=['POST'])
@login_required
def add_comment(incident_id):
    content = request.form.get('content', '').strip()
    if not content:
        flash('Comment cannot be empty.', 'danger')
        return redirect(url_for('incidents.incident_detail', incident_id=incident_id))

    mysql = get_mysql()
    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO comments (incident_id, user_id, content)
        VALUES (%s, %s, %s)
    """, (incident_id, current_user.id, content))
    mysql.connection.commit()
    cur.close()

    flash('Comment added.', 'success')
    return redirect(url_for('incidents.incident_detail', incident_id=incident_id))


# ── Report new incident ──────────────────────────────────
@incidents_bp.route('/incident/new', methods=['GET', 'POST'])
@login_required
def new_incident():
    if current_user.role not in ('admin', 'analyst'):
        flash('You do not have permission to report incidents.', 'danger')
        return redirect(url_for('index'))

    mysql = get_mysql()
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
        return redirect(url_for('incidents.incident_detail', incident_id=new_id))

    cur.execute("SELECT * FROM categories")
    categories = cur.fetchall()
    cur.execute("SELECT user_id, username, role FROM users ORDER BY username")
    users = cur.fetchall()
    cur.close()

    return render_template('new_incident.html', categories=categories, users=users)


# ── Edit incident ────────────────────────────────────────
@incidents_bp.route('/incident/<int:incident_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_incident(incident_id):
    if current_user.role not in ('admin', 'analyst'):
        flash('You do not have permission to edit incidents.', 'danger')
        return redirect(url_for('incidents.incident_detail', incident_id=incident_id))

    mysql = get_mysql()
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
        return redirect(url_for('incidents.incident_detail', incident_id=incident_id))

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
