# app/database.py
from flask_sqlalchemy import SQLAlchemy
from flask import current_app
import hashlib

db = SQLAlchemy()

def init_db(app):
    with app.app_context():
        db.init_app(app)
        db.create_all()  # 創建所有表
        init_admin_user()  # 初始化管理員用戶

    return db

def init_admin_user():
    from .models import User  # 導入模型要放在函數內部避免循環導入
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin_user = User(username='admin')
        admin_user.set_password('admin')  # 直接使用 set_password 方法來設定密碼
        db.session.add(admin_user)
        db.session.commit()