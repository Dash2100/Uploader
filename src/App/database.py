from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_db(app):
    db.init_app(app)
    with app.app_context():
        from . import models  # noqa: F401  ensure models are registered
        db.create_all()
        init_admin_user()
    return db


def init_admin_user():
    from .models import User
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin_user = User(username='admin')
        admin_user.set_password('admin')
        db.session.add(admin_user)
        db.session.commit()
