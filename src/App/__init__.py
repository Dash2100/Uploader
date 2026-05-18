import os

from flask import Flask, render_template

from .database import init_db
from .extensions import init_login_manager, register_request_helpers


def _normalize_sqlite_uri(uri, instance_path):
    prefix = 'sqlite:///'
    if not uri.startswith(prefix):
        return uri
    path = uri[len(prefix):]
    if path == ':memory:' or os.path.isabs(path):
        return uri
    return prefix + os.path.normpath(os.path.join(instance_path, path))


def create_app():
    app = Flask(
        __name__,
        static_url_path='/static',
        instance_relative_config=True,
    )

    app.config.from_pyfile('application.cfg', silent=True)

    if not app.config.get('SECRET_KEY'):
        app.config['SECRET_KEY'] = os.urandom(24)
    app.config.setdefault('SQLALCHEMY_TRACK_MODIFICATIONS', False)
    app.config.setdefault('UPLOADS_DIR', 'Uploads')
    app.config.setdefault('SQLALCHEMY_DATABASE_URI', 'sqlite:///database.db')
    app.config.setdefault('QUICK_TOKEN', '')
    app.config.setdefault('DEBUG', False)
    app.config.setdefault('HOST', '127.0.0.1')
    app.config.setdefault('PORT', 5090)
    app.config.setdefault('SESSION_COOKIE_HTTPONLY', True)
    app.config.setdefault('SESSION_COOKIE_SAMESITE', 'Lax')
    if not app.config.get('DEBUG'):
        app.config.setdefault('SESSION_COOKIE_SECURE', True)

    os.makedirs(app.instance_path, exist_ok=True)
    app.config['SQLALCHEMY_DATABASE_URI'] = _normalize_sqlite_uri(
        app.config['SQLALCHEMY_DATABASE_URI'], app.instance_path,
    )

    init_db(app)
    init_login_manager(app)
    register_request_helpers(app)

    os.makedirs(app.config['UPLOADS_DIR'], exist_ok=True)

    from .routes.auth import auth
    from .routes.main import main
    from .routes.files import files
    from .routes.preview import preview
    from .routes.admin import admin

    app.register_blueprint(main)
    app.register_blueprint(auth, url_prefix='/auth')
    app.register_blueprint(files, url_prefix='/files')
    app.register_blueprint(preview, url_prefix='/preview')
    app.register_blueprint(admin, url_prefix='/admin')

    @app.errorhandler(404)
    def _not_found(_):
        return render_template('404.html'), 404

    @app.errorhandler(403)
    def _forbidden(_):
        return render_template('403.html'), 403

    @app.errorhandler(413)
    def _too_large(_):
        from flask import jsonify
        return jsonify({'error': 'File too large'}), 413

    return app
