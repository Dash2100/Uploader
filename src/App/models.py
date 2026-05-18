import hashlib
import re

from flask_login import UserMixin
from werkzeug.security import check_password_hash as _wz_check
from werkzeug.security import generate_password_hash as _wz_generate

from .database import db
from .extensions import login_manager

_LEGACY_SHA256_RE = re.compile(r'^[0-9a-f]{64}$')


def _legacy_matches(password_hash, password):
    return password_hash == hashlib.sha256(password.encode('utf-8')).hexdigest()


class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(255))

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        self.password_hash = _wz_generate(password)

    def check_password(self, password):
        stored = self.password_hash or ''
        if _LEGACY_SHA256_RE.match(stored):
            if _legacy_matches(stored, password):
                # Transparent upgrade to salted hash on successful login
                self.set_password(password)
                db.session.commit()
                return True
            return False
        try:
            return _wz_check(stored, password)
        except (ValueError, TypeError):
            return False


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
    try:
        return db.session.get(User, int(user_id))
    except (TypeError, ValueError):
        return None
