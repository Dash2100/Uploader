import time
from collections import defaultdict, deque
from threading import Lock

from flask import (Blueprint, jsonify, redirect, render_template, request,
                   url_for)
from flask_login import (current_user, login_required, login_user,
                         logout_user)

from ..models import User
from ..utils import safe_next_url

auth = Blueprint('auth', __name__)

_RATE_WINDOW_SEC = 60
_RATE_MAX_ATTEMPTS = 8
_attempts = defaultdict(deque)
_attempts_lock = Lock()


def _rate_limit_hit(key):
    now = time.monotonic()
    with _attempts_lock:
        bucket = _attempts[key]
        while bucket and now - bucket[0] > _RATE_WINDOW_SEC:
            bucket.popleft()
        if len(bucket) >= _RATE_MAX_ATTEMPTS:
            return True
        bucket.append(now)
        return False


def _rate_limit_reset(key):
    with _attempts_lock:
        _attempts.pop(key, None)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index_admin'))

    if request.method == 'POST':
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({'state': 'incorrect'}), 400

        username = (data.get('username') or 'admin').strip()
        password = data.get('password')
        if not username or not isinstance(password, str) or password == '':
            return jsonify({'state': 'incorrect'}), 400

        client_ip = request.remote_addr or 'unknown'
        rate_key = f'{client_ip}:{username}'
        if _rate_limit_hit(rate_key):
            return jsonify({'state': 'rate_limited'}), 429

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            _rate_limit_reset(rate_key)
            return jsonify({'state': 'correct'}), 200
        return jsonify({'state': 'incorrect'}), 401

    return render_template('auth/login.html')


@auth.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    target = safe_next_url(request.args.get('next')) or url_for('main.index_guest')
    return redirect(target)


@auth.route('/next', methods=['GET'])
def post_login_redirect():
    target = safe_next_url(request.args.get('next'))
    if not target:
        return redirect(url_for('main.index_admin'))
    return redirect(target)
