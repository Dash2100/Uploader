from flask import Blueprint, render_template, send_from_directory, current_app
from ..database import db  # db object
from ..models import File, ShortUrl  # File model

from .auth import login_required

main = Blueprint('main', __name__)

@main.route('/', methods=['GET'])
def index_guest():
    # Get all shared files
    shared_files = File.query.filter_by(share=1).all()
    files_list = [{'uuid': file.uuid, 'name': file.name, 'date': file.date, 'size': file.size, 'downloads': file.downloads} for file in shared_files]

    return render_template('guest/index.html', all_files=files_list)

@main.route('/admin', methods=['GET'])
@login_required
def index_admin():
    # Get all files
    all_files = File.query.all()
    files_list = [{'uuid': file.uuid, 'name': file.name, 'date': file.date, 'size': file.size, 'downloads': file.downloads} for file in all_files]

    # reverse the list
    files_list.reverse()

    return render_template('admin/index.html', all_files=files_list)

@main.route('/<link>', methods=['GET'])
def download(link):
    try:
        # Get file name from ShortUrl
        file = ShortUrl.query.filter_by(url=link).first()
        file_name = file.file
    except:
        return render_template('404.html'), 404

    # Update downloads count
    file = File.query.filter_by(name=file_name).first()
    file.downloads += 1
    db.session.commit()

    # Return file name
    files_path = current_app.config['UPLOADS_DIR']
    return send_from_directory(files_path, file_name, as_attachment=True)

@main.route('/test')
@login_required
def testendpoint():
    return "shikanoko nokonko koshitantan"