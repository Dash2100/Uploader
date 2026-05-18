import io
import os
import uuid as uuid_lib
import zipfile
from datetime import datetime, timezone

from flask import (Blueprint, current_app, g, jsonify, request, send_file,
                   send_from_directory)
from flask_login import current_user, login_required
from sqlalchemy.exc import SQLAlchemyError

from ..database import db
from ..models import File, ShortUrl
from ..utils import (is_safe_uploads_path, safe_int, sanitize_extension,
                     split_extension)

files = Blueprint('files', __name__)

_MAX_ZIP_FILES = 200
_MAX_ZIP_BYTES = 1024 * 1024 * 1024  # 1 GiB cap in memory


def _human_size(size_bytes):
    if size_bytes < 1000 * 1000:
        return f'{round(size_bytes / 1000, 3)} KB'
    return f'{round(size_bytes / (1000 * 1000), 3)} MB'


def _serialize(file, include_share=False):
    out = {
        'uuid': file.uuid,
        'name': file.name,
        'date': file.date,
        'size': file.size,
        'downloads': file.downloads,
    }
    if include_share:
        out['share'] = file.share
    return out


def _can_access(file):
    if not file:
        return False
    if file.share == 1:
        return True
    return current_user.is_authenticated


def _increment_downloads(file_uuid):
    File.query.filter_by(uuid=file_uuid).update(
        {File.downloads: File.downloads + 1},
        synchronize_session=False,
    )
    db.session.commit()


@files.route('/list', methods=['POST'])
def list_files():
    data = request.get_json(silent=True) or {}
    page = safe_int(data.get('page'), default=1, minimum=1, maximum=100000)
    admin_mode = bool(data.get('admin_mode', False))
    per_page = 15

    if admin_mode and not current_user.is_authenticated:
        return jsonify({'error': 'unauthorized'}), 401

    query = File.query if admin_mode else File.query.filter_by(share=1)
    pagination = query.order_by(File.date.desc()).paginate(
        page=page, per_page=per_page, error_out=False,
    )
    return jsonify([_serialize(f, include_share=admin_mode) for f in pagination.items])


@files.route('/download', methods=['GET'])
def download_file():
    file_uuid = request.args.get('file', '')
    file = db.session.get(File, file_uuid)

    if not _can_access(file):
        return jsonify({'error': 'File not exists or not shared'}), 404

    if not is_safe_uploads_path(g.files_path, file.disk_name):
        current_app.logger.warning('Unsafe disk_name detected: %s', file.disk_name)
        return jsonify({'error': 'Not found'}), 404

    _increment_downloads(file.uuid)
    return send_from_directory(
        g.files_path, file.disk_name,
        as_attachment=True, download_name=file.name,
    )


@files.route('/download_zip', methods=['POST'])
def download_zip():
    payload = request.get_json(silent=True) or {}
    raw_uuids = payload.get('files') or payload.get('uuids') or []
    if not isinstance(raw_uuids, list) or not raw_uuids:
        return jsonify({'error': 'No files specified'}), 400
    if len(raw_uuids) > _MAX_ZIP_FILES:
        return jsonify({'error': f'Too many files (max {_MAX_ZIP_FILES})'}), 400

    seen = set()
    uuids = []
    for u in raw_uuids:
        if isinstance(u, str) and u not in seen:
            seen.add(u)
            uuids.append(u)

    files_to_zip = []
    total_bytes = 0
    for file_uuid in uuids:
        file = db.session.get(File, file_uuid)
        if not _can_access(file):
            return jsonify({'error': 'File not exists or not shared'}), 404
        if not is_safe_uploads_path(g.files_path, file.disk_name):
            return jsonify({'error': 'Not found'}), 404
        disk_path = os.path.join(g.files_path, file.disk_name)
        if not os.path.isfile(disk_path):
            return jsonify({'error': 'File missing on disk'}), 404
        size = os.path.getsize(disk_path)
        total_bytes += size
        if total_bytes > _MAX_ZIP_BYTES:
            return jsonify({'error': 'Zip too large'}), 413
        files_to_zip.append((file, disk_path))

    zip_buffer = io.BytesIO()
    used_arcnames = {}
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for file, disk_path in files_to_zip:
            arc = file.name
            count = used_arcnames.get(arc, 0)
            if count:
                base, _, ext = arc.rpartition('.')
                if base:
                    arc = f'{base} ({count}).{ext}'
                else:
                    arc = f'{file.name} ({count})'
            used_arcnames[file.name] = count + 1
            zip_file.write(disk_path, arcname=arc)

    for file, _ in files_to_zip:
        _increment_downloads(file.uuid)

    zip_buffer.seek(0)
    return send_file(
        zip_buffer,
        download_name='Uploader_Downloads.zip',
        as_attachment=True,
        mimetype='application/zip',
    )


@files.route('/upload', methods=['POST'])
@login_required
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file_storage = request.files['file']
    share_raw = str(request.form.get('share', '0')).strip().lower()
    share = 1 if share_raw in ('1', 'true', 'on', 'yes') else 0

    if not file_storage or not file_storage.filename:
        return jsonify({'error': 'No selected file'}), 400

    display_name, extracted_ext = split_extension(file_storage.filename)
    extension = sanitize_extension(extracted_ext)
    file_uuid = str(uuid_lib.uuid4())
    disk_name = f'{file_uuid}.{extension}' if extension else file_uuid

    if not is_safe_uploads_path(g.files_path, disk_name):
        return jsonify({'error': 'Invalid filename'}), 400

    disk_path = os.path.join(g.files_path, disk_name)
    file_storage.save(disk_path)

    try:
        size = _human_size(os.path.getsize(disk_path))
        now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

        new_file = File(
            uuid=file_uuid,
            name=display_name,
            extension=extension,
            date=now,
            size=size,
            share=share,
            sharedate=now if share else '',
        )
        db.session.add(new_file)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        try:
            if os.path.exists(disk_path):
                os.remove(disk_path)
        except OSError:
            pass
        current_app.logger.exception('Upload DB commit failed for %s', file_uuid)
        return jsonify({'error': 'Upload failed'}), 500

    current_app.logger.info('Uploaded %s as %s', display_name, file_uuid)
    return jsonify({'state': 'success', 'uuid': file_uuid}), 200


def _delete_by_uuid(file_uuid):
    file = db.session.get(File, file_uuid)
    if not file:
        return False

    disk_name = file.disk_name
    try:
        ShortUrl.query.filter_by(file_uuid=file_uuid).delete()
        db.session.delete(file)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        current_app.logger.exception('Delete DB op failed for %s', file_uuid)
        return False

    disk_path = os.path.join(g.files_path, disk_name)
    try:
        if os.path.exists(disk_path):
            os.remove(disk_path)
    except OSError:
        current_app.logger.warning('Disk delete failed for %s (DB row already removed)', disk_path)
    return True


@files.route('/delfile', methods=['POST'])
@login_required
def del_file():
    payload = request.get_json(silent=True) or {}
    file_uuid = payload.get('uuid')
    if not file_uuid or not isinstance(file_uuid, str):
        return jsonify({'error': 'Missing uuid'}), 400

    if _delete_by_uuid(file_uuid):
        return 'OK', 200
    return jsonify({'error': 'Error while deleting file'}), 400


@files.route('/multidelete', methods=['POST'])
@login_required
def multi_delete():
    payload = request.get_json(silent=True) or {}
    uuids = payload.get('uuids') or payload.get('files') or []
    if not isinstance(uuids, list):
        return jsonify({'error': 'Invalid payload'}), 400

    succeeded, failed = [], []
    for file_uuid in uuids:
        if not isinstance(file_uuid, str):
            failed.append(file_uuid)
            continue
        if _delete_by_uuid(file_uuid):
            succeeded.append(file_uuid)
        else:
            failed.append(file_uuid)

    if failed:
        return jsonify({
            'error': 'Some files could not be deleted',
            'succeeded': succeeded,
            'failed': failed,
        }), 207
    return 'OK', 200
