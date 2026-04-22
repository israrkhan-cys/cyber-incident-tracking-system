from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt

auth = Blueprint('auth', __name__)

# We access mysql and bcrypt through current_app
def get_mysql():
    from app import mysql
    return mysql

def get_bcrypt():
    from app import bcrypt
    return bcrypt

# ─── REGISTER ───────────────────────────────────────────
@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email    = request.form['email']
        password = request.form['password']
        role     = request.form['role']

        mysql  = get_mysql()
        bcrypt = get_bcrypt()

        # Hash the password before storing
        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')

        cur = mysql.connection.cursor()
        try:
            cur.execute("""
                INSERT INTO users (username, email, password, role)
                VALUES (%s, %s, %s, %s)
            """, (username, email, hashed_pw, role))
            mysql.connection.commit()
            flash('Account created! Please login.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            flash('Username or email already exists.', 'danger')
        finally:
            cur.close()

    return render_template('auth/register.html')

# ─── LOGIN ──────────────────────────────────────────────
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email    = request.form['email']
        password = request.form['password']

        mysql  = get_mysql()
        bcrypt = get_bcrypt()

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        cur.close()

        if user and bcrypt.check_password_hash(user['password'], password):
            from app import User
            login_user(User(user['user_id'], user['username'], user['role']))
            flash(f"Welcome, {user['username']}!", 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password.', 'danger')

    return render_template('auth/login.html')

# ─── LOGOUT ─────────────────────────────────────────────
@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('auth.login'))