import os

from flask import (Blueprint, abort, g, render_template, request,
                   send_from_directory)
from flask_login import current_user

from ..database import db
from ..models import File
from ..utils import is_safe_uploads_path

preview = Blueprint('preview', __name__)

_INLINE_IMAGE_MIMES = {
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'png': 'image/png',
    'gif': 'image/gif',
    'webp': 'image/webp',
    'bmp': 'image/bmp',
    'ico': 'image/x-icon',
    'tiff': 'image/tiff',
    'svg': 'image/svg+xml',
}
_INLINE_PDF_EXT = 'pdf'
_TEXT_PLAIN = 'text/plain'


def _safe_mime(extension):
    ext = (extension or '').lower()
    if ext == _INLINE_PDF_EXT:
        return 'application/pdf'
    if ext in _INLINE_IMAGE_MIMES:
        return _INLINE_IMAGE_MIMES[ext]
    return _TEXT_PLAIN


def _harden(response):
    response.headers['Content-Security-Policy'] = (
        "sandbox; default-src 'none'; img-src 'self' data:; "
        "style-src 'unsafe-inline'; media-src 'self'"
    )
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'no-referrer'
    response.headers.pop('Cache-Control', None)
    response.headers['Cache-Control'] = 'private, no-store'
    return response


@preview.route('/<file_uuid>')
def preview_file(file_uuid):
    file = db.session.get(File, file_uuid)
    if not file:
        return render_template('404.html'), 404

    if not current_user.is_authenticated and file.share == 0:
        return render_template('403.html'), 403

    if not is_safe_uploads_path(g.files_path, file.disk_name):
        return render_template('404.html'), 404

    disk_path = os.path.join(g.files_path, file.disk_name)
    if not os.path.isfile(disk_path):
        return render_template('404.html'), 404

    mimetype = _safe_mime(file.extension)
    response = send_from_directory(
        g.files_path, file.disk_name,
        as_attachment=False,
        download_name=file.name,
        mimetype=mimetype,
    )
    return _harden(response)


@preview.route('/pdf_viewer', methods=['GET'])
def pdf_viewer():
    file_param = request.args.get('file', '')
    if not file_param.startswith('/preview/'):
        abort(400)
    rest = file_param[len('/preview/'):]
    if not rest or '/' in rest or '?' in rest or '#' in rest:
        abort(400)
    return render_template('preview/pdf_viewer.html')
