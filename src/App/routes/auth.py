from flask import (Blueprint, jsonify, redirect, render_template, request,
                   url_for)
from flask_login import (current_user, login_required, login_user,
                         logout_user)

from ..models import User

auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index_admin'))

    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        username = data.get('username', 'admin')
        password = data.get('password', '')

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
    return redirect(url_for('main.index_guest'))
