from flask import Flask, redirect, url_for
from config import Config

from database.db import db
from utils.cloudinary_config import configurar_cloudinary

from flask_login import LoginManager

from routes.auth_routes import auth
from routes.admin_routes import admin
from routes.docente_routes import docente
from routes.estudiante_routes import estudiante

from models import *


app = Flask(__name__)

app.config.from_object(Config)

db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)


with app.app_context():
    configurar_cloudinary()
    db.create_all()


@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))


app.register_blueprint(auth)
app.register_blueprint(admin)
app.register_blueprint(docente)
app.register_blueprint(estudiante)


@app.route('/')
def home():
    return redirect(url_for('auth.login'))


if __name__ == '__main__':
    app.run()