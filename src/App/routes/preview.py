from flask import Blueprint, render_template, send_from_directory, current_app, g, jsonify, abort
import os
from ..models import File
from .auth import current_user

preview = Blueprint('preview', __name__)

@preview.before_app_request
def before_request_preview():
    if 'UPLOADS_DIR' in current_app.config:
        g.files_path = current_app.config['UPLOADS_DIR']

@preview.route('/<file_uuid>')
def preview_file(file_uuid):
    file = File.query.filter_by(uuid=file_uuid).first()

    if not file:
        return render_template('404.html'), 404

    uploads_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), g.files_path)
    file_path = os.path.join(uploads_dir, f'{file_uuid}.{file.extension}')
            
    # 檢查訪問權限
    if not current_user.is_authenticated and file.share == 0:
        return render_template('403.html'), 403
    
    return send_from_directory(uploads_dir, f'{file_uuid}.{file.extension}', as_attachment=False, download_name=file.name)

@preview.route('/pdf_viewer', methods=['GET'])
def pdf_viewer():
    return render_template('preview/pdf_viewer.html')