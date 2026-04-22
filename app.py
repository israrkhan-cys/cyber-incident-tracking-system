from flask import Flask, render_template
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

# Register blueprints
from routes.auth import auth
app.register_blueprint(auth)

@app.route('/')
@login_required                  # ← protect home, must be logged in
def index():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM incidents")
    incidents = cur.fetchall()
    cur.close()
    return render_template('index.html', incidents=incidents)

if __name__ == '__main__':
    app.run(debug=True)