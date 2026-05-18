import os

from flask import (Blueprint, g, redirect, render_template,
                   send_from_directory)
from flask_login import login_required

from ..database import db
from ..models import File, ShortUrl
from ..utils import is_safe_uploads_path

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


@main.route('/favicon.ico')
def favicon():
    return redirect('/static/favicon.ico', code=301)


@main.route('/<string(minlength=1,maxlength=80):link>', methods=['GET'])
def shortlink_download(link):
    if '.' in link:
        return render_template('404.html'), 404

    short = db.session.get(ShortUrl, link)
    if not short:
        return render_template('404.html'), 404

    file = db.session.get(File, short.file_uuid)
    if not file or file.share != 1:
        return render_template('404.html'), 404

    if not is_safe_uploads_path(g.files_path, file.disk_name):
        return render_template('404.html'), 404

    disk_path = os.path.join(g.files_path, file.disk_name)
    if not os.path.isfile(disk_path):
        return render_template('404.html'), 404

    File.query.filter_by(uuid=file.uuid).update(
        {File.downloads: File.downloads + 1},
        synchronize_session=False,
    )
    db.session.commit()

    return send_from_directory(
        g.files_path, file.disk_name,
        as_attachment=True, download_name=file.name,
    )
