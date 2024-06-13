from flask_sqlalchemy import SQLAlchemy

from .database import db

from .extensions import login_manager
from flask_login import UserMixin

import hashlib

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128))

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class File(db.Model):
    uuid = db.Column(db.String(120), primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    extension = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(120), nullable=False)
    size = db.Column(db.String(120), nullable=False)
    share = db.Column(db.Integer, default=0)
    sharedate = db.Column(db.String(120))
    downloads = db.Column(db.Integer, default=0)

class ShortUrl(db.Model):
    url = db.Column(db.String(80), primary_key=True)
    file = db.Column(db.String(120), nullable=False)

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

def generate_password_hash(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_password_hash(password_hash, password):
    return password_hash == generate_password_hash(password)