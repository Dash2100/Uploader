from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from ..models import User as UserModel
from .. import User as UserMixin
import hashlib

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        request_data = request.get_json()
        password = request_data['password']

        user = UserModel.query.filter_by(username='admin').first()

        if user and check_password(password):
            login_user(user, remember=True)  # Make sure to login the user
            return {"state":"correct"}
        return {"state":"incorrect"}
    
    return render_template('auth/login.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))  # Ensure 'main.index' is the correct endpoint


def check_password(password):
    password_req = hashlib.sha256(password.encode('utf-8')).hexdigest()

    # Get the password from the database
    password = UserModel.query.filter_by(username='admin').first().password

    if password == password_req:
        return True
    else:
        return False