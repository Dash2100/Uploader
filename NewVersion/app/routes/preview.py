from flask import Blueprint, render_template, send_from_directory
from ..models import File  # File model
from .auth import login_required

preview = Blueprint('preview', __name__)

@preview.route('/pdf_viewer', methods=['GET'])
def index():
    return render_template('preview/pdf_viewer.html')

@preview.route('/<file_name>')
def preview_file(filename):
    # check if file exists and is shared
    file = File.query.filter_by(name=filename).first()
    if not file or file.share == 0:
        return render_template('404.html'), 404
    
    # send preview file
    return send_from_directory('files_path', filename)

@preview.route('/admin/<file_name>')
@login_required
def preview_file_admin(filename):
    # check if file exists
    file = File.query.filter_by(name=filename).first()
    if not file:
        return render_template('404.html'), 404
    
    # send preview file
    return send_from_directory('files_path', filename)