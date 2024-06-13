from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user

from ..models import User

import hashlib

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    # Check if user is already logged in
    if current_user.is_authenticated:
        return redirect(url_for('main.index_admin'))

    if request.method == 'POST':
        request_data = request.get_json()

        username = request_data.get('username', 'admin')  # 預設使用 admin 帳號
        password = request_data.get('password')

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            return jsonify({'state': 'correct'}), 200
        return jsonify({'state': 'incorrect'}), 401
    
    return render_template('auth/login.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))  # Ensure 'main.index' is the correct endpoint