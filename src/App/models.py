import hashlib

from flask_login import UserMixin

from .database import db
from .extensions import login_manager


def generate_password_hash(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def check_password_hash(password_hash, password):
    return password_hash == generate_password_hash(password)


class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128))

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class File(db.Model):
    __tablename__ = 'file'
    uuid = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    extension = db.Column(db.String(32), default='')
    date = db.Column(db.String(32), nullable=False)
    size = db.Column(db.String(32), nullable=False)
    share = db.Column(db.Integer, default=0)
    sharedate = db.Column(db.String(32), default='')
    downloads = db.Column(db.Integer, default=0)

    @property
    def disk_name(self):
        return f'{self.uuid}.{self.extension}' if self.extension else self.uuid


class ShortUrl(db.Model):
    __tablename__ = 'short_url'
    url = db.Column(db.String(80), primary_key=True)
    file_uuid = db.Column(db.String(36), nullable=False, index=True)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
