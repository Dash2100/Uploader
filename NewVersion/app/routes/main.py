from flask import Blueprint, render_template, send_from_directory, request, send_file, current_app
from flask_sqlalchemy import SQLAlchemy
from ..database import db  # db object
from ..models import File, ShortUrl  # File model
import zipfile
import os
import io

main = Blueprint('main', __name__)

@main.route('/', methods=['GET'])
def index():
    # Get all shared files
    shared_files = File.query.filter_by(share=1).all()
    files_list = [{'name': file.name, 'date': file.date, 'size': file.size, 'downloads': file.downloads} for file in shared_files]

    return render_template('guest/index.html', all_files=files_list)

@main.route('/<link>', methods=['GET'])
def download(link):
    # Get file name from ShortUrl
    file = ShortUrl.query.filter_by(url=link).first()
    file_name = file.file

    # Update downloads count
    file = File.query.filter_by(name=file_name).first()
    file.downloads += 1
    db.session.commit()

    # Return file name
    files_path = current_app.config['UPLOADS_DIR']
    return send_from_directory(files_path, file_name, as_attachment=True)

@main.route('/download/<file_name>', methods=['GET'])
def download_file(file_name):
    # check if file exists and is shared
    file = File.query.filter_by(name=file_name).first()
    if not file or file.share == 0:
        return render_template('404.html'), 404
    
    # Update downloads count
    file.downloads += 1
    db.session.commit()

    # Return file name
    files_path = current_app.config['UPLOADS_DIR']
    return send_from_directory(files_path, file_name, as_attachment=True)

@main.route('/download/zip', methods=['POST'])
def download_zip():
    download_files = request.get_json()['files']
    files_path = current_app.config['UPLOADS_DIR']

    # check all files is exist and shared
    for file_name in download_files:
        file = File.query.filter_by(name=file_name).first()
        if not file or file.share == 0:
            return render_template('404.html'), 404
        
    # Update downloads count
    for file_name in download_files:
        file = File.query.filter_by(name=file_name).first()
        file.downloads += 1
        db.session.commit()

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'a') as zip_file:  # Corrected typo 'Zipfile' to 'ZipFile'
        for file_name in download_files:
            zip_file.write(os.path.join(files_path, file_name), arcname=file_name)

    zip_buffer.seek(0)

    return send_file(zip_buffer,
                     attachment_filename='download.zip',
                     as_attachment=True,
                     mimetype='application/zip')
