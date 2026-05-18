from flask import Blueprint, g, render_template, send_from_directory
from flask_login import current_user

from ..models import File

preview = Blueprint('preview', __name__)


@preview.route('/<file_uuid>')
def preview_file(file_uuid):
    file = File.query.filter_by(uuid=file_uuid).first()
    if not file:
        return render_template('404.html'), 404

    if not current_user.is_authenticated and file.share == 0:
        return render_template('403.html'), 403

    return send_from_directory(
        g.files_path, file.disk_name,
        as_attachment=False, download_name=file.name,
    )


@preview.route('/pdf_viewer', methods=['GET'])
def pdf_viewer():
    return render_template('preview/pdf_viewer.html')
