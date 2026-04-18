from flask import Flask
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from config import Config

app = Flask(__name__)
app.config.from_object(Config)


mysql  = MySQL(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'

@app.route('/')
def index():

    cur = mysql.connection.cursor()


    cur.execute("SELECT * FROM incidents")
    

    users = cur.fetchall()


    cur.close()


    output = '<h2>Incidents in Database:</h2>'
    for incident in users:
        output += f"<p>{incident['incident_id']} — {incident['title']} — {incident['status']}</p>"

    return output

if __name__ == '__main__':
    app.run(debug=True)