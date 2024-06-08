from .database import db  # 更新導入語句
from flask_login import UserMixin

class User(db.Model):
    username = db.Column(db.String(80), primary_key=True)
    password = db.Column(db.String(120), nullable=False)

class File(db.Model):
    name = db.Column(db.String(120), primary_key=True)
    date = db.Column(db.String(120), nullable=False)
    size = db.Column(db.String(120), nullable=False)
    share = db.Column(db.Integer, default=0)
    sharedate = db.Column(db.String(120))
    downloads = db.Column(db.Integer, default=0)

class ShortUrl(db.Model):
    url = db.Column(db.String(80), primary_key=True)
    file = db.Column(db.String(120), nullable=False)
