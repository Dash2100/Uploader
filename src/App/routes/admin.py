import hmac
import os
import re
from datetime import datetime, timezone

from flask import (Blueprint, current_app, g, jsonify, render_template,
                   request)
from flask_login import current_user, login_required, login_user
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from ..database import db
from ..models import File, ShortUrl, User
from ..utils import is_safe_uploads_path, sanitize_extension, split_extension

admin = Blueprint('admin', __name__)

_SHORTLINK_RE = re.compile(r'^[A-Za-z0-9_-]{1,40}$')
_RESERVED_LINKS = {
    'admin', 'auth', 'files', 'preview', 'static',
    'quick', 'login', 'logout', 'favicon.ico', 'instance', 'uploads',
}
_RENAME_RE = re.compile(r'^[\w\-. ]+$', re.UNICODE)
_MIN_QUICK_TOKEN_LEN = 16


def _now_str():
    return datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')


def _parse_state(payload):
    raw = payload.get('state')
    try:
        n = int(raw)
    except (TypeError, ValueError):
        return None
    return n if n in (0, 1) else None


@admin.route('/filestate', methods=['POST'])
@login_required
def filestate():
    payload = request.get_json(silent=True) or {}
    file_uuid = payload.get('uuid')
    if not file_uuid or not isinstance(file_uuid, str):
        return jsonify({'error': 'Missing uuid'}), 400

    file = db.session.get(File, file_uuid)
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
    state = _parse_state(payload)

    if not file_uuid or not isinstance(file_uuid, str):
        return jsonify({'error': 'Missing uuid'}), 400
    if state is None:
        return 'Wrong State', 400

    file = db.session.get(File, file_uuid)
    if not file:
        return 'Not Found', 404

    file.share = state
    file.sharedate = _now_str() if state else ''
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        current_app.logger.exception('share toggle failed')
        return jsonify({'error': 'Database error'}), 500
    return 'OK', 200


@admin.route('/multishare', methods=['POST'])
@login_required
def multishare():
    payload = request.get_json(silent=True) or {}
    raw_uuids = payload.get('uuids') or payload.get('files') or []
    state = _parse_state(payload)

    if not isinstance(raw_uuids, list) or not raw_uuids:
        return jsonify({'error': 'No files specified'}), 400
    if state is None:
        return 'Wrong State', 400

    uuids = [u for u in raw_uuids if isinstance(u, str)]
    target_files = File.query.filter(File.uuid.in_(uuids)).all()
    if len(target_files) != len(set(uuids)):
        return 'Not Found', 404

    now = _now_str()
    for file in target_files:
        file.share = state
        file.sharedate = now if state else ''
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        current_app.logger.exception('multishare commit failed')
        return jsonify({'error': 'Database error'}), 500
    return 'OK', 200


@admin.route('/shortlink', methods=['POST'])
@login_required
def shortlink():
    payload = request.get_json(silent=True) or {}
    file_uuid = payload.get('uuid')
    short = (payload.get('shortlink') or '').strip()

    if not file_uuid or not isinstance(file_uuid, str) or not short:
        return 'Empty', 400
    if not _SHORTLINK_RE.match(short) or short.lower() in _RESERVED_LINKS:
        return 'illegal', 400

    file = db.session.get(File, file_uuid)
    if not file:
        return 'Not Found', 404

    existing = db.session.get(ShortUrl, short)
    if existing and existing.file_uuid != file_uuid:
        return 'Already in use', 409

    current = ShortUrl.query.filter_by(file_uuid=file_uuid).first()
    try:
        if current:
            if current.url != short:
                db.session.delete(current)
                db.session.flush()
                db.session.add(ShortUrl(url=short, file_uuid=file_uuid))
        else:
            db.session.add(ShortUrl(url=short, file_uuid=file_uuid))
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return 'Already in use', 409
    except SQLAlchemyError:
        db.session.rollback()
        current_app.logger.exception('shortlink commit failed')
        return jsonify({'error': 'Database error'}), 500
    return 'OK', 200


@admin.route('/delshortlink', methods=['POST'])
@login_required
def del_shortlink():
    payload = request.get_json(silent=True) or {}
    file_uuid = payload.get('uuid')
    if not file_uuid or not isinstance(file_uuid, str):
        return jsonify({'error': 'Missing uuid'}), 400

    try:
        ShortUrl.query.filter_by(file_uuid=file_uuid).delete()
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        current_app.logger.exception('delshortlink failed')
        return jsonify({'error': 'Database error'}), 500
    return 'OK', 200


@admin.route('/rename', methods=['POST'])
@login_required
def rename():
    payload = request.get_json(silent=True) or {}
    file_uuid = payload.get('uuid')
    new_name_raw = (payload.get('newname') or '').strip()

    if not file_uuid or not isinstance(file_uuid, str) or not new_name_raw:
        return 'illegal', 400
    if not _RENAME_RE.match(new_name_raw):
        return 'illegal', 400
    if new_name_raw.strip('. ') == '':
        return 'illegal', 400
    if len(new_name_raw) > 255:
        return 'illegal', 400

    file = db.session.get(File, file_uuid)
    if not file:
        return 'Not Found', 404

    new_name, ext_part = split_extension(new_name_raw)
    new_extension = sanitize_extension(ext_part)

    if File.query.filter(File.name == new_name, File.uuid != file_uuid).first():
        return 'Already in use', 409

    old_disk_name = file.disk_name
    new_disk_name = f'{file.uuid}.{new_extension}' if new_extension else file.uuid

    if not is_safe_uploads_path(g.files_path, new_disk_name):
        return 'illegal', 400

    disk_renamed = False
    if new_disk_name != old_disk_name:
        old_path = os.path.join(g.files_path, old_disk_name)
        new_path = os.path.join(g.files_path, new_disk_name)
        if os.path.exists(old_path):
            try:
                os.rename(old_path, new_path)
                disk_renamed = True
            except OSError:
                current_app.logger.exception('Disk rename failed for %s', file_uuid)
                return jsonify({'error': 'Rename failed on disk'}), 500

    file.name = new_name
    file.extension = new_extension
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        if disk_renamed:
            try:
                os.rename(
                    os.path.join(g.files_path, new_disk_name),
                    os.path.join(g.files_path, old_disk_name),
                )
            except OSError:
                current_app.logger.exception('Disk rename rollback failed for %s', file_uuid)
        current_app.logger.exception('Rename DB commit failed for %s', file_uuid)
        return jsonify({'error': 'Database error'}), 500
    return 'OK', 200


@admin.route('/quick/<token>')
def quick(token):
    expected = current_app.config.get('QUICK_TOKEN', '') or ''
    if len(expected) < _MIN_QUICK_TOKEN_LEN:
        return render_template('404.html'), 404
    if not hmac.compare_digest(str(token), expected):
        return render_template('404.html'), 404

    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        return render_template('404.html'), 404
    login_user(admin_user)
    return render_template('admin/quick.html')
