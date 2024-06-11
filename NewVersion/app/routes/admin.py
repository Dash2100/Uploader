from flask import Blueprint, render_template, request, send_file, send_from_directory, current_app, g
from ..models import File, ShortUrl  # File model
from ..database import db  # db object
from datetime import datetime
import zipfile
import io
import os

from .auth import login_required

admin = Blueprint('admin', __name__)

@admin.before_app_request
def before_request():
    if 'UPLOADS_DIR' in current_app.config:
        g.files_path = current_app.config['UPLOADS_DIR']

@admin.route('/', methods=['GET'])
@login_required
def index():
    # Get all files
    all_files = File.query.all()
    files_list = [{'name': file.name, 'date': file.date, 'size': file.size, 'downloads': file.downloads} for file in all_files]

    # reverse the list
    files_list.reverse()

    return render_template('admin/index.html', all_files=files_list)

@admin.route('/upload', methods=['POST'])
@login_required
def upload():
    # Check if request has the file part
    if 'file' not in request.files:
        return 'No file part', 400
    file = request.files['file']

    print(f"[INFO] {file} uploaded")

    if file.filename == '':
        return 'No selected file', 400
    if file:
        # If filename exists, add underscore in front of it
        while file.filename in os.listdir(g.files_path):
            file.filename = f"_{file.filename}"

        # Save file
        file.save(os.path.join(g.files_path, file.filename))

        # Get current date
        now = datetime.now()
        date = now.strftime("%Y-%m-%d %H:%M:%S")

        # Get file size
        size_bytes = os.path.getsize(os.path.join(g.files_path, file.filename))
        #if size less than 1 MB, show in KB
        if size_bytes < 1000000:
            size = round(size_bytes / 1000, 3).__str__() + ' KB'
        else:
            size = round(size_bytes / 1000000, 3).__str__() + ' MB'

        # Get uploaded file properties
        data = request.form
        share = data['share']

        # Write to db 
        new_file = File(
            name=file.filename,
            date=date,
            size=size,
            share=share
        )
        db.session.add(new_file)
        db.session.commit()

        # Return to index
        return "success", 200
    else:
        return "Error: No file", 400

@admin.route('/test')
@login_required
def testendpoint():
    return "shikanoko nokonko koshitantan"

@admin.route('/download/<file_name>', methods=['GET'])
@login_required
def download_file(file_name):
    # check if file exists
    file = File.query.filter_by(name=file_name).first()
    if not file:
        return render_template('404.html'), 404
    
    # Update downloads count
    file.downloads += 1
    db.session.commit()
    
    # Return file name
    return send_from_directory(g.files_path, file_name, as_attachment=True)

@admin.route('/download/zip', methods=['POST'])
@login_required
def download_zip():
    download_files = request.get_json()['files']

    # check all files is exist
    for file in download_files:
        file = File.query.filter_by(name=file).first()
        if not file:
            return render_template('404.html'), 404
        
    # Update downloads count
    for file in download_files:
        file = File.query.filter_by(name=file).first()
        file.downloads += 1
        db.session.commit()

    zip_buffer = io.BytesIO()
    with zipfile.Zipfile(zip_buffer, 'a') as zip_file:
        for file in download_files:
            zip_file.write(os.path.join(g.files_path, file))

    zip_buffer.seek(0)

    return send_file(zip_buffer,
                     as_attachment=True,
                     download_name='download.zip',
                     mimetype='application/zip')


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

@admin.route('/delfile', methods=['POST'])
@login_required
def del_file():
    filename = request.get_json()['filename']
    if delete_file_by_name(filename):
        return "success", 200   
    else:
        print(f"[ERROR] Error while deleting {filename}")
        return f"error while deleting {filename}", 400

@admin.route('/multidelete', methods=['POST'])
@login_required
def multi_delete():
    files = request.get_json()['files']
    for file in files:
        if delete_file_by_name(file) == False:
            print(f"[ERROR] Error while deleting {file}")
            return f"error while deleting {file}", 400
        
    return "success", 200

@admin.route('/preview/<filename>')
@login_required
def preview_file(filename):
    # check if file exists
    file = File.query.filter_by(name=filename).first()
    if not file:
        return render_template('404.html'), 404
    
    # send preview file
    return send_from_directory(g.files_path, filename)