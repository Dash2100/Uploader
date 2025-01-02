from flask import Blueprint, render_template, send_from_directory, current_app, g, abort
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
    try:
        # 使用 UUID 查詢文件
        file = File.query.filter_by(uuid=file_uuid).first()
        
        # 檢查文件是否存在資料庫中
        if not file:
            return render_template('404.html'), 404
            
        # 檢查訪問權限
        if not current_user.is_authenticated and file.share == 0:
            return render_template('404.html'), 404

        # 構建完整的文件路徑
        file_path = os.path.join(g.files_path, f'{file_uuid}.{file.extension}')
        
        # 檢查文件是否實際存在於檔案系統中
        if not os.path.exists(file_path):
            return render_template('404.html'), 404

        # 發送預覽文件
        try:
            return send_from_directory(
                directory=g.files_path,
                path=f'{file_uuid}.{file.extension}',
                as_attachment=False,
                download_name=file.name
            )
        except Exception as e:
            current_app.logger.error(f"文件發送失敗: {str(e)}")
            abort(404)
            
    except Exception as e:
        current_app.logger.error(f"預覽過程發生錯誤: {str(e)}")
        return render_template('404.html'), 404

@preview.route('/pdf_viewer', methods=['GET'])
def pdf_viewer():
    return render_template('preview/pdf_viewer.html')