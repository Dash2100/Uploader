from flask import (Blueprint, g, render_template, send_from_directory)
from flask_login import login_required

from ..database import db
from ..models import File, ShortUrl

main = Blueprint('main', __name__)


@main.route('/', methods=['GET'])
def index_guest():
    shared_files = (
        File.query.filter_by(share=1)
        .order_by(File.sharedate.desc())
        .all()
    )
    return render_template('guest/index.html', all_files=shared_files)


@main.route('/admin', methods=['GET'])
@login_required
def index_admin():
    return render_template('admin/index.html')


@main.route('/<link>', methods=['GET'])
def shortlink_download(link):
    short = ShortUrl.query.filter_by(url=link).first()
    if not short:
        return render_template('404.html'), 404

    file = File.query.filter_by(uuid=short.file_uuid).first()
    if not file or file.share != 1:
        return render_template('404.html'), 404

    file.downloads += 1
    db.session.commit()

    return send_from_directory(
        g.files_path, file.disk_name,
        as_attachment=True, download_name=file.name,
    )
