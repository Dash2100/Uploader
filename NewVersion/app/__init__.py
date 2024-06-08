from flask import Flask
from flask_login import LoginManager
from .database import init_db
from app.models import *
import os

from .routes.main import main
from .routes.admin import admin
from .routes.auth import auth
from .routes.preview import preview

login_manager = LoginManager()

def create_app():
    app = Flask(__name__, static_url_path='/static', instance_relative_config=True)
    
    app.config['SECRET_KEY'] = os.urandom(24)
    app.config.from_pyfile('application.cfg', silent=True)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # init db and create default accounts
    init_db(app)

    # Create Uploads Folder
    uploads_dir = app.config['UPLOADS_DIR']
    if not os.path.exists(uploads_dir):
        os.makedirs(uploads_dir)

    # Register blueprints
    app.register_blueprint(main)
    app.register_blueprint(auth, url_prefix='/auth')
    app.register_blueprint(admin, url_prefix='/admin')
    app.register_blueprint(preview, url_prefix='/preview')

    # Authentication
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    return app
