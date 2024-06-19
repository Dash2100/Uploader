from flask import Blueprint, render_template, request, send_file, send_from_directory, current_app, g, jsonify

from ..models import File  # File model
from ..database import db  # db object

from datetime import datetime
import zipfile
import base64
import uuid
import io
import os

from .auth import login_required, current_user

files = Blueprint('files', __name__)

@files.before_app_request
def before_request_files():
    if 'UPLOADS_DIR' in current_app.config:
        g.files_path = current_app.config['UPLOADS_DIR']

@files.route('/list', methods=['POST'])
def list_files():
    data = request.get_json()
    page = data.get('page', 1)  # 確保頁碼是整數，預設值為第 1 頁
    admin_mode = data.get('admin_mode', False)  # 預設值為非管理員模式 預設值為非管理員模式

    files_per_page = 15

    query = File.query
    if not admin_mode:
        query = query.filter_by(share=1)
    else:
        if current_user.is_authenticated == False:            
            return jsonify([])

    # 使用 paginate 方法直接在資料庫層面進行分頁
    pagination = query.order_by(File.date.desc()).paginate(page=page, per_page=files_per_page, error_out=False)
    files = pagination.items

    # 建構響應列表
    files_list = [{'uuid': file.uuid, 'name': file.name, 'date': file.date, 'size': file.size, 'downloads': file.downloads} for file in files]

    return jsonify(files_list)


@files.route('/download', methods=['GET'])
def download_file():
    # Get file UUID from request
    file_uuid = request.args.get('file')
    file = File.query.filter_by(uuid=file_uuid).first()
    
    # check file and authentication
    if not file or current_user.is_authenticated == False and file.share == 0:
        return jsonify({'error': 'File not exists or not shared'}), 404
    
    # Update downloads count
    file.downloads += 1
    db.session.commit()

    # Return file name
    return send_from_directory(g.files_path, f'{file_uuid}.{file.extension}', as_attachment=True, download_name=file.name)

# 等待修改成UUID方法取得檔案
@files.route('/download_zip', methods=['POST'])
def download_zip():
    download_files = request.get_json()['files']

    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, 'a') as zip_file:
        for file_name in download_files:
            file = File.query.filter_by(name=file_name).first()

            # check file and authentication
            if not file or current_user.is_authenticated == False and file.share == 0:
                return jsonify({'error': 'File not exists or not shared'}), 404
            
            # Update downloads count
            file = File.query.filter_by(name=file_name).first()
            file.downloads += 1
            db.session.commit()

            # Add file to zip
            file_name_physical = f'{file.uuid}.{file.extension}' if file.extension else file.uuid
            zip_file.write(os.path.join(g.files_path, file_name_physical), file_name)

    zip_buffer.seek(0)

    return send_file(zip_buffer,
                     download_name='Uploader_Downloads.zip',
                     as_attachment=True,
                     mimetype='application/zip')

@files.route('/upload', methods=['POST'])
@login_required
def upload():
    # Check if request has the file part
    if 'file' not in request.files:
        return 'No file part', 400
    
    # Get user upload data
    file = request.files['file']
    share = request.form['share']

    print(f"[INFO] {file} uploaded")

    if file.filename == '' or not file:
        return 'No selected file', 400

    # Generate UUID for file
    file_uuid = uuid.uuid4().__str__()

    # Get file extension
    parts = file.filename.split(".")
    if len(parts) > 1:
        file_extension = parts[-1]
    else:
        file_extension = ''  # No extension

    # Saved file name
    save_file_name = f'{file_uuid}.{file_extension}'

    # Save file
    file_path = os.path.join(g.files_path, save_file_name)
    file.save(file_path)

    # Get current date
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # if size less than 1 MB, show in KB
    size_bytes = os.path.getsize(file_path)
    if size_bytes < 1000000:
        size = round(size_bytes / 1000, 3).__str__() + ' KB'
    else:
        size = round(size_bytes / 1000000, 3).__str__() + ' MB'

    # Write to db 
    new_file = File(
        uuid=file_uuid,
        name=file.filename,
        extension=file_extension,
        date=date,
        size=size,
        share=share
    )

    db.session.add(new_file)
    db.session.commit()

    return "success", 200

def delete_file_by_name(filename):
    file = File.query.filter_by(name=filename).first()
    if not file:
        return False
    
    try:
        os.remove(os.path.join(g.files_path, filename))
        db.session.delete(file) # delete from db
        db.session.commit()
    except Exception as e:
        return False
    
    return True

@files.route('/delfile', methods=['POST'])
@login_required
def del_file():
    filename = request.get_json()['filename']
    if delete_file_by_name(filename):
        return "success", 200   
    else:
        print(f"[ERROR] Error while deleting {filename}")
        return jsonify({'error': 'Error while deleting file'}), 400

@files.route('/multidelete', methods=['POST'])
@login_required
def multi_delete():
    files = request.get_json()['files']
    for file in files:
        if delete_file_by_name(file) == False:
            print(f"[ERROR] Error while deleting {file}")
            return jsonify({'error': 'Error while deleting file'}), 400
        
    return "success", 200