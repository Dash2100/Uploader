import os

from flask import current_app, g
from flask_login import LoginManager

login_manager = LoginManager()


def init_login_manager(app):
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'


def resolve_uploads_dir(app):
    uploads_dir = app.config.get('UPLOADS_DIR', 'Uploads')
    if not os.path.isabs(uploads_dir):
        uploads_dir = os.path.abspath(os.path.join(app.root_path, '..', uploads_dir))
    return uploads_dir


def register_request_helpers(app):
    app.config['UPLOADS_DIR'] = resolve_uploads_dir(app)

    @app.before_request
    def _attach_files_path():
        g.files_path = current_app.config['UPLOADS_DIR']
