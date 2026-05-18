import io
import os
import uuid as uuid_lib
import zipfile
from datetime import datetime

from flask import (Blueprint, current_app, g, jsonify, request, send_file,
                   send_from_directory)
from flask_login import current_user, login_required

from ..database import db
from ..models import File, ShortUrl

files = Blueprint('files', __name__)


def _human_size(size_bytes):
    if size_bytes < 1000 * 1000:
        return f'{round(size_bytes / 1000, 3)} KB'
    return f'{round(size_bytes / (1000 * 1000), 3)} MB'


def _serialize(file):
    return {
        'uuid': file.uuid,
        'name': file.name,
        'date': file.date,
        'size': file.size,
        'downloads': file.downloads,
        'share': file.share,
    }


def _can_access(file):
    if not file:
        return False
    if file.share == 1:
        return True
    return current_user.is_authenticated


@files.route('/list', methods=['POST'])
def list_files():
    data = request.get_json(silent=True) or {}
    page = int(data.get('page', 1))
    admin_mode = bool(data.get('admin_mode', False))
    per_page = 15

    query = File.query
    if admin_mode:
        if not current_user.is_authenticated:
            return jsonify([])
    else:
        query = query.filter_by(share=1)

    pagination = query.order_by(File.date.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    return jsonify([_serialize(f) for f in pagination.items])


@files.route('/download', methods=['GET'])
def download_file():
    file_uuid = request.args.get('file')
    file = File.query.filter_by(uuid=file_uuid).first()

    if not _can_access(file):
        return jsonify({'error': 'File not exists or not shared'}), 404

    file.downloads += 1
    db.session.commit()

    return send_from_directory(
        g.files_path, file.disk_name,
        as_attachment=True, download_name=file.name,
    )


@files.route('/download_zip', methods=['POST'])
def download_zip():
    payload = request.get_json(silent=True) or {}
    uuids = payload.get('files') or payload.get('uuids') or []

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for file_uuid in uuids:
            file = File.query.filter_by(uuid=file_uuid).first()
            if not _can_access(file):
                return jsonify({'error': 'File not exists or not shared'}), 404

            file.downloads += 1
            disk_path = os.path.join(g.files_path, file.disk_name)
            zip_file.write(disk_path, arcname=file.name)

    db.session.commit()
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

    file = request.files['file']
    share = 1 if str(request.form.get('share', '0')) in ('1', 'true', 'True') else 0

    if not file or file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    current_app.logger.info(f'Uploading {file.filename}')

    file_uuid = str(uuid_lib.uuid4())
    parts = file.filename.rsplit('.', 1)
    extension = parts[1] if len(parts) > 1 else ''
    disk_name = f'{file_uuid}.{extension}' if extension else file_uuid

    disk_path = os.path.join(g.files_path, disk_name)
    file.save(disk_path)

    date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    size = _human_size(os.path.getsize(disk_path))

    new_file = File(
        uuid=file_uuid,
        name=file.filename,
        extension=extension,
        date=date,
        size=size,
        share=share,
        sharedate=date if share else '',
    )
    db.session.add(new_file)
    db.session.commit()

    return jsonify({'state': 'success', 'uuid': file_uuid}), 200


def _delete_by_uuid(file_uuid):
    file = File.query.filter_by(uuid=file_uuid).first()
    if not file:
        return False

    try:
        disk_path = os.path.join(g.files_path, file.disk_name)
        if os.path.exists(disk_path):
            os.remove(disk_path)
        ShortUrl.query.filter_by(file_uuid=file_uuid).delete()
        db.session.delete(file)
        db.session.commit()
    except OSError as exc:
        current_app.logger.error(f'Failed deleting {file_uuid}: {exc}')
        db.session.rollback()
        return False

    return True


@files.route('/delfile', methods=['POST'])
@login_required
def del_file():
    payload = request.get_json(silent=True) or {}
    file_uuid = payload.get('uuid') or payload.get('filename')
    if not file_uuid:
        return jsonify({'error': 'Missing uuid'}), 400

    if _delete_by_uuid(file_uuid):
        return 'OK', 200
    return jsonify({'error': 'Error while deleting file'}), 400


@files.route('/multidelete', methods=['POST'])
@login_required
def multi_delete():
    payload = request.get_json(silent=True) or {}
    uuids = payload.get('uuids') or payload.get('files') or []
    for file_uuid in uuids:
        if not _delete_by_uuid(file_uuid):
            return jsonify({'error': f'Error while deleting {file_uuid}'}), 400
    return 'OK', 200
