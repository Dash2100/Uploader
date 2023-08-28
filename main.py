from flask import Flask, request, send_from_directory, render_template, jsonify, redirect, url_for, send_file
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from getpass import getpass
import hashlib
import zipfile
import json
import sys
import re
import os
import io

from App.database import *

path = './Uploads'
quick_token = 'jJPaERsj6wPq58VShWMAGVsS3V97FRN4UqM'

app = Flask(__name__, static_url_path='/static')
app.config['SECRET_KEY'] = os.urandom(24)
login_manager = LoginManager(app)  # Create login manager
login_manager.login_view = 'login'  # Set login view

#database
engine = create_engine('sqlite:///database.db')
Session = sessionmaker(bind=engine)
db = Session()

@app.route('/')
def index():
    #get all share=1 files in database use sqlalchemy
    all_files = db.query(Files).filter(Files.share == 1).all()
    #sort list by sharedate
    all_files.sort(key=lambda x: x[4], reverse=True)
    return render_template('index.html', **locals())

@app.route('/<link>', methods = ['GET'])
def link(link):
    #get file from database
    file = db.query(ShortUrls).filter(ShortUrls.url == link).first()

    if file:
        #update downloads
        db.query(Files).filter(Files.name == file.file).update({Files.downloads: Files.downloads + 1})
        db.commit()
        return send_from_directory(path, file[0], as_attachment=True)
    else:
        return render_template('404.html')

@app.route('/pdfview', methods=['GET'])
def pdf():
    return render_template('viewer.html')

@app.route('/download/<filename>')
def download(filename):
    #check if file exists
    if filename in os.listdir(path):
        #check file share state
        share = db.query(Files).filter(Files.name == filename).first()[3]
        if share == 1:
            #update downloads
            db.query(Files).filter(Files.name == filename).update({Files.downloads: Files.downloads + 1})
            return send_from_directory(path, filename, as_attachment=True)
        else:
            return render_template('404.html')
    else:
        return render_template('404.html')
    
@app.route('/download/zip', methods=['POST'])
def download_zip():

    download_files = request.get_json()['files']

    #check all file share state is on
    shared_data = db.query(Files).filter(Files.share == 1).all()
    shared_files = [name[0] for name in shared_data]

    for file in download_files:
        if file not in shared_files:
            return 'error'
    

    zip_buffer = io.BytesIO() # create a BytesIO buffer to hold the zip file
    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        for file in download_files:
            zip_file.write(os.path.join(path, file))

    zip_buffer.seek(0) # set the buffer's file position to the beginning

    return send_file(zip_buffer,
                     download_name='download.zip',
                     as_attachment=True,
                     mimetype='application/zip')
    
@app.route('/preview/<filename>')
def preview(filename):
    #check if file exists
    if filename in os.listdir(path):
        #check file share state
        share = db.query(Files).filter(Files.name == filename).first()[3]
        if share == 1:
            return send_from_directory(path, filename)
        else:
            return render_template('404.html')
    else:
        return render_template('404.html')

@app.route('/quick/<token>')
def quickUP(token):
    if token == quick_token:
        #login as admin
        user = User()
        user.id = 'admin'
        login_user(user)
        return render_template('quick.html', **locals())
    else:
        return render_template('404.html')

@app.route('/admin')
@login_required
def admin():
    all_files = db.query(Files).all()
    all_files.reverse()
    return render_template('admin.html', **locals())


@app.route('/admin/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        return 'No file part'
    file = request.files['file']
    data = request.form
    share = data['share']
    print(f"[INFO] {file} uploaded")
    if file.filename == '':
        return 'No selected file'
    if file:
        while file.filename in os.listdir(path):
            file.filename = '-' + file.filename
        file.save(os.path.join(path, file.filename))
        # Add file to database
        now = datetime.now()
        date = now.strftime("%Y-%m-%d %H:%M:%S")
        #get file size in MB
        size_bytes = os.path.getsize(os.path.join(path, file.filename))
        #if size less than 1 MB, show in KB
        if size_bytes < 1000000:
            size = round(size_bytes / 1000, 3).__str__() + ' KB'
        else:
            size = round(size_bytes / 1000000, 3).__str__() + ' MB'
        filename_base64 = file.filename.encode('utf-8')
        if share == '0':
            #update database
            db.add(Files(name=file.filename, date=date, size=size, share=0, sharedate="", downloads=0))
        else:
            #update database
            db.add(Files(name=file.filename, date=date, size=size, share=1, sharedate=date, downloads=0))
        return "success"


@app.route('/admin/download/<string:filename>', methods=['GET'])
@login_required
def download_file(filename):
    #check if file exists
    if filename in os.listdir(path):
        #update downloads
        db.query(Files).filter(Files.name == filename).update({Files.downloads: Files.downloads + 1})
        return send_from_directory(path, filename, as_attachment=True)
    else:
        return render_template('404.html')

@app.route('/admin/download/zip', methods=['POST'])
@login_required
def download_zip_admin():
    download_files = request.get_json()['files']

    zip_buffer = io.BytesIO() # create a BytesIO buffer to hold the zip file
    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        for file in download_files:
            zip_file.write(os.path.join(path, file))

    zip_buffer.seek(0) # set the buffer's file position to the beginning

    return send_file(zip_buffer,
                     download_name='download.zip',
                     as_attachment=True,
                     mimetype='application/zip')

@app.route('/admin/preview/<filename>')
@login_required
def admin_preview(filename):
    #check if file exists
    if filename in os.listdir(path):
        return send_from_directory(path, filename)
    else:
        return render_template('404.html')

@app.route('/admin/delfile' , methods=['POST'])
@login_required
def del_file():
    filename = request.get_json()['filename']
    try:
        os.remove(os.path.join(path, filename))
        #delete file and shortlink from database
        db.query(Files).filter(Files.name == filename).delete()
        db.query(ShortUrls).filter(ShortUrls.file == filename).delete()
        db.commit()
        return "OK"
    except FileNotFoundError:
        return "Not Found"

@app.route('/admin/multidelete', methods=['POST'])
@login_required
def multi_delete():
    files = request.get_json()['files']
    for file in files:
        try:
            os.remove(os.path.join(path, file))
            #delete file and shortlink from database
            db.query(Files).filter(Files.name == file).delete()
            db.query(ShortUrls).filter(ShortUrls.file == file).delete()
            db.commit()
        except FileNotFoundError:
            pass
    return "OK"

#use get to change share status in database
@app.route('/admin/share', methods=['POST'])
@login_required
def share_file():
    filename = request.get_json()['filename']
    state = request.get_json()['state']
    data = db.query(Files).filter(Files.name == filename).first()
    if data:
        if state == 1:
            #update database
            db.query(Files).filter(Files.name == filename).update({Files.share: 1})
            #sharedate
            now = datetime.now()
            date = now.strftime("%Y-%m-%d %H:%M:%S")
            db.query(Files).filter(Files.name == filename).update({Files.sharedate: date})
        elif state == 0:
            db.query(Files).filter(Files.name == filename).update({Files.share: 0})
            db.query(Files).filter(Files.name == filename).update({Files.sharedate: ""})
        else:
            return "Wrong State"
        db.commit()
        return "OK"
    else:
        return "Not Found"

@app.route('/admin/multishare', methods=['POST'])
@login_required
def multishare():
    files = request.get_json()['files']
    state = request.get_json()['state']
    for file in files:
        data = db.query(Files).filter(Files.name == file).first()
        if data:
            if state == 1:
                #update database
                db.query(Files).filter(Files.name == file).update({Files.share: 1})
                #sharedate
                now = datetime.now()
                date = now.strftime("%Y-%m-%d %H:%M:%S")
                db.query(Files).filter(Files.name == file).update({Files.sharedate: date})
            elif state == 0:
                db.query(Files).filter(Files.name == file).update({Files.share: 0})
                db.query(Files).filter(Files.name == file).update({Files.sharedate: ""})
            else:
                return "Wrong State"
        else:
            return "Not Found"
    return "OK"

#get share state from files table and short link from shorturls table
@app.route('/admin/filestate', methods=['POST'])
@login_required
def file_state():
    filename = request.get_json()['filename']
    share = db.query(Files).filter(Files.name == filename).first()[3]
    link = db.query(ShortUrls).filter(ShortUrls.file == filename).first()
    if link:
        link = link[0]
    else:
        link = ""
    return json.dumps({'share': share, 'link': link})


@app.route('/admin/shortlink', methods=['POST'])
@login_required
def shortlink():
    filename = request.get_json()['filename']
    shortlink = request.get_json()['shortlink']
    #check if value is valid
    if shortlink == "" or filename == "":
        return "Empty"
    #check if user is using a illegal character
    if not re.match("^[a-zA-Z0-9_-]*$", shortlink):
        return "illegal"
    if shortlink == "admin":
        return "illegal"
    #check if shortlink is already in use
    data = db.query(ShortUrls).filter(ShortUrls.url == shortlink).first()
    print(data)
    if data:
        print("Already in use")
        return "Already in use"
    #check if file already has a shortlink
    data = db.query(ShortUrls).filter(ShortUrls.file == filename).first()
    if data:
        #update shortlink
        db.query(ShortUrls).filter(ShortUrls.file == filename).update({ShortUrls.url: shortlink})
    db.add(ShortUrls(file=filename, url=shortlink))
    return "OK"

@app.route('/admin/delshortlink', methods=['POST'])
@login_required
def del_shortlink():
    filename = request.get_json()['filename']
    #check if file has a shortlink
    data = db.query(ShortUrls).filter(ShortUrls.file == filename).first()
    if data:
        #delete shortlink
        db.query(ShortUrls).filter(ShortUrls.file == filename).delete()
        return "OK"
    else:
        return "Not Found"

#rename file
@app.route('/admin/rename', methods=['POST'])
@login_required
def rename():
    filename = request.get_json()['filename']
    newname = request.get_json()['newname']
    #check if value is valid
    if newname == "" or filename == "":
        return "illegal"

    #check if user is using a illegal character
    if not re.match(r"^[\w\-. ]+$", newname, re.UNICODE):
        return "illegal"

    #check if newname is already in use
    data = db.query(Files).filter(Files.name == newname).first()
    if data:
        return "Already in use"

    #check if file has a shortlink
    data = db.query(ShortUrls).filter(ShortUrls.file == filename).first()
    if data:
        #update shortlink
        db.query(ShortUrls).filter(ShortUrls.file == filename).update({ShortUrls.file: newname})
    #rename file
    os.rename(os.path.join(path, filename), os.path.join(path, newname))
    #update database
    db.query(Files).filter(Files.name == filename).update({Files.name: newname})
    return "OK"

## Login

# Create user class
class User(UserMixin):  
    pass 

@login_manager.user_loader  
def user_loader(userid):    
    user = User() #繼承UserMixin
    user.id = userid 
    return user

@app.route('/login', methods=['GET', 'POST'])  
def login():
    if request.method == 'GET':  
            if current_user.is_authenticated:  
                return redirect(url_for('admin'))
            return render_template('login.html')
    request_pas = request.get_json()
    #load password from db
    password = db.query(Users).filter(Users.username == 'admin').first()
    password = password[1]
    print(password)
    if hashlib.sha256(request_pas['password'].encode('utf-8')).hexdigest() == password:
        user = User()
        user.id = 'admin'
        login_user(user) #登入使用者
        return jsonify({'state':'correct'})
    return jsonify({'state':'incorrect'})
 
@app.route('/logout')
@login_required 
def logout():  
    logout_user()  
    return redirect(url_for('index'))

if __name__ == "__main__":
    sqlinit()
    if len(sys.argv) == 2:
        if sys.argv[1] == 'user':
            username = input('Username: ')
            password = getpass('Password: ')
            password = hashlib.sha256(password.encode('utf-8')).hexdigest()
            db.add(Users(username=username, password=password))
            db.commit()
    else:
        app.run(debug=True, host='0.0.0.0', port=5090)