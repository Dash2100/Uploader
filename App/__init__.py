from flask import Flask

from .database import init_db
from .extensions import init_login_manager
import os

from .routes.main import main
from .routes.auth import auth
from .routes.files import files
from .routes.preview import preview

def create_app():
    app = Flask(__name__, static_url_path='/static', instance_relative_config=True)
    
    app.config.from_pyfile('application.cfg', silent=True)

    app.config['SECRET_KEY'] = os.urandom(24)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize the database
    init_db(app)

    # Initialize Login Manager
    init_login_manager(app)

    # Create Uploads Folder
    uploads_dir = app.config['UPLOADS_DIR']
    if not os.path.exists(uploads_dir):
        os.makedirs(uploads_dir)

    # Register blueprints
    app.register_blueprint(main, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/auth')
    app.register_blueprint(files, url_prefix='/files')
    app.register_blueprint(preview, url_prefix='/preview')

    return app
