import os
import re
from datetime import datetime

from flask import (Blueprint, current_app, g, jsonify, render_template,
                   request)
from flask_login import current_user, login_required, login_user

from ..database import db
from ..models import File, ShortUrl, User

admin = Blueprint('admin', __name__)

_SHORTLINK_RE = re.compile(r'^[A-Za-z0-9_-]+$')
_RESERVED_LINKS = {'admin', 'auth', 'files', 'preview', 'static', 'quick'}
_RENAME_RE = re.compile(r'^[\w\-. ]+$', re.UNICODE)


@admin.route('/filestate', methods=['POST'])
@login_required
def filestate():
    payload = request.get_json(silent=True) or {}
    file_uuid = payload.get('uuid')
    file = File.query.filter_by(uuid=file_uuid).first()
    if not file:
        return jsonify({'error': 'Not Found'}), 404

    short = ShortUrl.query.filter_by(file_uuid=file_uuid).first()
    return jsonify({
        'share': file.share,
        'link': short.url if short else '',
    })


@admin.route('/share', methods=['POST'])
@login_required
def share_file():
    payload = request.get_json(silent=True) or {}
    file_uuid = payload.get('uuid')
    state = int(payload.get('state', -1))

    file = File.query.filter_by(uuid=file_uuid).first()
    if not file:
        return 'Not Found', 404
    if state not in (0, 1):
        return 'Wrong State', 400

    file.share = state
    file.sharedate = datetime.now().strftime('%Y-%m-%d %H:%M:%S') if state else ''
    db.session.commit()
    return 'OK', 200


@admin.route('/multishare', methods=['POST'])
@login_required
def multishare():
    payload = request.get_json(silent=True) or {}
    uuids = payload.get('uuids') or payload.get('files') or []
    state = int(payload.get('state', -1))
    if state not in (0, 1):
        return 'Wrong State', 400

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    for file_uuid in uuids:
        file = File.query.filter_by(uuid=file_uuid).first()
        if not file:
            db.session.rollback()
            return 'Not Found', 404
        file.share = state
        file.sharedate = now if state else ''

    db.session.commit()
    return 'OK', 200


@admin.route('/shortlink', methods=['POST'])
@login_required
def shortlink():
    payload = request.get_json(silent=True) or {}
    file_uuid = payload.get('uuid')
    short = (payload.get('shortlink') or '').strip()

    if not file_uuid or not short:
        return 'Empty', 400
    if not _SHORTLINK_RE.match(short) or short in _RESERVED_LINKS:
        return 'illegal', 400

    file = File.query.filter_by(uuid=file_uuid).first()
    if not file:
        return 'Not Found', 404

    existing = ShortUrl.query.filter_by(url=short).first()
    if existing and existing.file_uuid != file_uuid:
        return 'Already in use', 409

    current = ShortUrl.query.filter_by(file_uuid=file_uuid).first()
    if current:
        current.url = short
    else:
        db.session.add(ShortUrl(url=short, file_uuid=file_uuid))

    db.session.commit()
    return 'OK', 200


@admin.route('/delshortlink', methods=['POST'])
@login_required
def del_shortlink():
    payload = request.get_json(silent=True) or {}
    file_uuid = payload.get('uuid')
    ShortUrl.query.filter_by(file_uuid=file_uuid).delete()
    db.session.commit()
    return 'OK', 200


@admin.route('/rename', methods=['POST'])
@login_required
def rename():
    payload = request.get_json(silent=True) or {}
    file_uuid = payload.get('uuid')
    new_name = (payload.get('newname') or '').strip()

    if not file_uuid or not new_name:
        return 'illegal', 400
    if not _RENAME_RE.match(new_name):
        return 'illegal', 400

    file = File.query.filter_by(uuid=file_uuid).first()
    if not file:
        return 'Not Found', 404

    if File.query.filter(File.name == new_name, File.uuid != file_uuid).first():
        return 'Already in use', 409

    parts = new_name.rsplit('.', 1)
    new_extension = parts[1] if len(parts) > 1 else ''

    if new_extension != file.extension:
        old_disk = os.path.join(g.files_path, file.disk_name)
        new_disk_name = f'{file.uuid}.{new_extension}' if new_extension else file.uuid
        new_disk = os.path.join(g.files_path, new_disk_name)
        if os.path.exists(old_disk):
            os.rename(old_disk, new_disk)
        file.extension = new_extension

    file.name = new_name
    db.session.commit()
    return 'OK', 200


@admin.route('/quick/<token>')
def quick(token):
    expected = current_app.config.get('QUICK_TOKEN', '')
    if not expected or token != expected:
        return render_template('404.html'), 404

    admin_user = User.query.filter_by(username='admin').first()
    if admin_user:
        login_user(admin_user)
    return render_template('admin/quick.html')
