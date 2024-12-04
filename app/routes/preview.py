from flask import Blueprint, render_template, send_from_directory, current_app, g
from ..models import File
from .auth import current_user

preview = Blueprint('preview', __name__)

@preview.before_app_request
def before_request_preview():
    if 'UPLOADS_DIR' in current_app.config:
        g.files_path = current_app.config['UPLOADS_DIR']

@preview.route('/<file_uuid>')
def preview_file(file_uuid):
    # 使用 UUID 查詢文件
    file = File.query.filter_by(uuid=file_uuid).first()
    
    # 檢查文件是否存在
    if not file:
        return render_template('404.html'), 404
        
    # 檢查訪問權限
    if not current_user.is_authenticated and file.share == 0:
        return render_template('404.html'), 404
    
    # 構建完整文件名稱
    full_filename = f"{file.uuid}{file.extension}"
    
    # 發送預覽文件
    return send_from_directory(g.files_path, full_filename)

@preview.route('/pdf_viewer', methods=['GET'])
def pdf_viewer():
    return render_template('preview/pdf_viewer.html')