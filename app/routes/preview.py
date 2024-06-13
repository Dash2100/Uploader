from flask import Blueprint, render_template, send_from_directory, current_app, g
from ..models import File

from .auth import current_user

preview = Blueprint('preview', __name__)

@preview.before_app_request
def before_request_preview():
    if 'UPLOADS_DIR' in current_app.config:
        g.files_path = current_app.config['UPLOADS_DIR']

@preview.route('/preview/<filename>')
def preview_file(filename):
    # check if user is logged in, check if file is shared
    if current_user.is_authenticated == False:
        file = File.query.filter_by(name=filename).first()
        if file.share == 0:
            return render_template('404.html'), 404

    # check if file exists
    if not file:
        return render_template('404.html'), 404
    
    # send preview file
    return send_from_directory(g.files_path, filename)

@preview.route('/pdf_viewer', methods=['GET'])
def pdf_viewer():
    return render_template('preview/pdf_viewer.html')