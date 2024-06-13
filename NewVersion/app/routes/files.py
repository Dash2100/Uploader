from flask import Blueprint, render_template, request, send_file, send_from_directory, current_app, g

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

@files.route('/download', methods=['GET'])
def download_file():
    # Get file UUID from request
    file_uuid = request.args.get('file')
    file = File.query.filter_by(uuid=file_uuid).first()

    # check if file exists
    if not file:
        return render_template('404.html'), 404

    # check if user is logged in and file is shared
    # if current_user.is_authenticated == False:
    #     if file.share == 0:
    #         return render_template('404.html'), 404
        
    # Change file name to original name
    file_name = file.name

    # Update downloads count
    file.downloads += 1
    db.session.commit()

    # Return file name
    return send_from_directory(g.files_path, f'{file_uuid}.{file.extension}', as_attachment=True, download_name=file_name)

# 等待修改成UUID方法取得檔案
@files.route('/download_zip', methods=['POST'])
def download_zip():
    download_files = request.get_json()['files']

    for file_name in download_files:
        file = File.query.filter_by(name=file_name).first()

        if not file:
            return "Files not exist", 400

        # check if user is logged in
        if current_user.is_authenticated == False:
            if file.share == 0:
                return render_template('404.html'), 404
        
    # Update downloads count
    for file_name in download_files:
        file = File.query.filter_by(name=file_name).first()
        file.downloads += 1
        db.session.commit()

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'a') as zip_file:  # Corrected typo 'Zipfile' to 'ZipFile'
        for file_name in download_files:
            zip_file.write(os.path.join(g.files_path, file_name), arcname=file_name)

    zip_buffer.seek(0)

    return send_file(zip_buffer,
                     attachment_filename='Uploader_Downloads.zip',
                     as_attachment=True,
                     mimetype='application/zip')

@files.route('/upload', methods=['POST'])
@login_required
def upload():
    # Check if request has the file part
    if 'file' not in request.files:
        return 'No file part', 400
    
    # Get uploaded file properties
    data = request.form
    share = data['share']
    
    file = request.files['file']

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

    # Return to index
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
        return f"error while deleting {filename}", 400

@files.route('/multidelete', methods=['POST'])
@login_required
def multi_delete():
    files = request.get_json()['files']
    for file in files:
        if delete_file_by_name(file) == False:
            print(f"[ERROR] Error while deleting {file}")
            return f"error while deleting {file}", 400
        
    return "success", 200