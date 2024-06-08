from flask import Blueprint, render_template, request, send_file, send_from_directory, redirect, url_for
from ..models import File, ShortUrl  # File model
from ..database import db  # db object
from .. import app
from flask_login import login_required
from datetime import datetime
import os

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
    return send_from_directory('files_path', file_name, as_attachment=True)

@main.route('/download/zip', methods=['POST'])
def download_zip():
    download_files = request.get_json()['files']

    # check all files is exist and shared
    for file in download_files:
        file = File.query.filter_by(name=file).first()
        if not file or file.share == 0:
            return render_template('404.html'), 404
        
    # Update downloads count
    for file in download_files:
        file = File.query.filter_by(name=file).first()
        file.downloads += 1
        db.session.commit()

    zip_buffer = io.BytesIO()
    with zipfile.Zipfile(zip_buffer, 'a') as zip_file:
        for file in download_files:
            zip_file.write(os.path.join(files_path, file))

    zip_buffer.seek(0)

    return send_file(zip_buffer,
                     as_attachment=True,
                     download_name='download.zip',
                     mimetype='application/zip')