from flask import Flask, request, send_from_directory, render_template, jsonify, redirect, url_for, send_file
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
from getpass import getpass
import sqlite3
import hashlib
import zipfile
import json
import sys
import re
import os
import io

from App.sql_init import sqlinit

path = './Uploads'
quick_token = 'jJPaERsj6wPq58VShWMAGVsS3V97FRN4UqM'

app = Flask(__name__, static_url_path='/static')
app.config['SECRET_KEY'] = os.urandom(24)
login_manager = LoginManager(app)  # Create login manager
login_manager.login_view = 'login'  # Set login view

def execute_db(command, vals):
    con = sqlite3.connect('database.db')
    cur = con.cursor()
    cur.execute(command, vals)
    con.commit()
    con.close()

@app.route('/')
def index():
    #get all share=1 files in database
    con = sqlite3.connect('database.db')
    cur = con.cursor()
    cur.execute("SELECT * FROM files WHERE share=1")
    all_files = cur.fetchall()
    con.close()
    #sort list by sharedate
    all_files.sort(key=lambda x: x[4], reverse=True)
    return render_template('index.html', **locals())

@app.route('/<link>', methods = ['GET'])
def link(link):
    #get file from database
    con = sqlite3.connect('database.db')
    cur = con.cursor()
    cur.execute("SELECT file FROM shorturls WHERE url=?", (link,))
    file = cur.fetchone()
    con.close()

    if file:
        #update downloads
        execute_db("UPDATE files SET downloads=downloads+1 WHERE name=?", (file[0],))
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
        con = sqlite3.connect('database.db')
        cur = con.cursor()
        cur.execute("SELECT share FROM files WHERE name=?", (filename,))
        share = cur.fetchone()[0]
        con.close()
        if share == 1:
            #update downloads
            execute_db("UPDATE files SET downloads=downloads+1 WHERE name=?", (filename,))
            return send_from_directory(path, filename, as_attachment=True)
        else:
            return render_template('404.html')
    else:
        return render_template('404.html')
    
@app.route('/download/zip', methods=['POST'])
def download_zip():

    download_files = request.get_json()['files']

    #check all file share state is on
    con = sqlite3.connect('database.db')
    cur = con.cursor()
    cur.execute("SELECT name FROM files WHERE share=1")
    shared_data = cur.fetchall()
    con.close()
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
        con = sqlite3.connect('database.db')
        cur = con.cursor()
        cur.execute("SELECT share FROM files WHERE name=?", (filename,))
        share = cur.fetchone()[0]
        con.close()
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
    con = sqlite3.connect('database.db')
    cur = con.cursor()
    cur.execute("SELECT * FROM files")
    all_files = cur.fetchall()
    con.close()
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
            execute_db('INSERT INTO files VALUES (?, ?, ?, ?, ?, ?)', (file.filename, date, size, 0, "", 0))
        else:
            execute_db('INSERT INTO files VALUES (?, ?, ?, ?, ?, ?)', (file.filename, date, size, 1, date, 0))
        return "success"


@app.route('/admin/download/<string:filename>', methods=['GET'])
@login_required
def download_file(filename):
    #check if file exists
    if filename in os.listdir(path):
        #update downloads
        execute_db("UPDATE files SET downloads=downloads+1 WHERE name=?", (filename,))
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
        #check file share state
        con = sqlite3.connect('database.db')
        cur = con.cursor()
        cur.execute("SELECT share FROM files WHERE name=?", (filename,))
        share = cur.fetchone()[0]
        con.close()
        return send_from_directory(path, filename)
    else:
        return render_template('404.html')

@app.route('/admin/delfile' , methods=['POST'])
@login_required
def del_file():
    filename = request.get_json()['filename']
    try:
        os.remove(os.path.join(path, filename))
        execute_db('DELETE FROM files WHERE name = ?', (filename,))
        execute_db('DELETE FROM shorturls WHERE file = ?', (filename,))
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
            execute_db('DELETE FROM files WHERE name = ?', (file,))
            execute_db('DELETE FROM shorturls WHERE file = ?', (file,))
        except FileNotFoundError:
            pass
    return "OK"

#use get to change share status in database
@app.route('/admin/share', methods=['POST'])
@login_required
def share_file():
    filename = request.get_json()['filename']
    state = request.get_json()['state']
    con = sqlite3.connect('database.db')
    cur = con.cursor()
    cur.execute("SELECT * FROM files WHERE name=?", (filename,))
    data = cur.fetchone()
    con.close()
    if data:
        if state == 1:
            execute_db('UPDATE files SET share=1 WHERE name=?', (filename,))
            #sharedate
            now = datetime.now()
            date = now.strftime("%Y-%m-%d %H:%M:%S")
            execute_db('UPDATE files SET sharedate=? WHERE name=?', (date, filename))
        elif state == 0:
            execute_db('UPDATE files SET share=0 WHERE name=?', (filename,))
            execute_db('UPDATE files SET sharedate=? WHERE name=?', ("", filename))
        else:
            return "Wrong State"
        return "OK"
    else:
        return "Not Found"

@app.route('/admin/multishare', methods=['POST'])
@login_required
def multishare():
    files = request.get_json()['files']
    state = request.get_json()['state']
    for file in files:
        con = sqlite3.connect('database.db')
        cur = con.cursor()
        cur.execute("SELECT * FROM files WHERE name=?", (file,))
        data = cur.fetchone()
        con.close()
        if data:
            if state == 1:
                execute_db('UPDATE files SET share=1 WHERE name=?', (file,))
                #sharedate
                now = datetime.now()
                date = now.strftime("%Y-%m-%d %H:%M:%S")
                execute_db('UPDATE files SET sharedate=? WHERE name=?', (date, file))
            elif state == 0:
                execute_db('UPDATE files SET share=? WHERE name=?', (0,file,))
                execute_db('UPDATE files SET sharedate=? WHERE name=?', ("", file))
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
    con = sqlite3.connect('database.db')
    cur = con.cursor()
    cur.execute("SELECT share FROM files WHERE name=?", (filename,))
    share = cur.fetchone()[0]
    cur.execute("SELECT url FROM shorturls WHERE file=?", (filename,))
    link = cur.fetchone()
    con.close()
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
    con = sqlite3.connect('database.db')
    cur = con.cursor()
    cur.execute("SELECT * FROM shorturls WHERE url=?", (shortlink,))
    data = cur.fetchone()
    print(data)
    if data:
        print("Already in use")
        return "Already in use"
    #check if file already has a shortlink
    cur.execute("SELECT * FROM shorturls WHERE file=?", (filename,))
    data = cur.fetchone()
    con.close()
    if data:
        #update shortlink
        execute_db('UPDATE shorturls SET url=? WHERE file=?', (shortlink, filename))
    execute_db('INSERT INTO shorturls VALUES (?, ?)', (shortlink, filename))
    return "OK"

@app.route('/admin/delshortlink', methods=['POST'])
@login_required
def del_shortlink():
    filename = request.get_json()['filename']
    execute_db('DELETE FROM shorturls WHERE file = ?', (filename,))
    return "OK"

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

    #check if file has a shortlink
    con = sqlite3.connect('database.db')
    cur = con.cursor()

    #check if newname is already in use
    cur.execute("SELECT * FROM files WHERE name=?", (newname,))
    data = cur.fetchone()
    if data:
        return "Already in use"

    #check if file has a shortlink
    cur.execute("SELECT * FROM shorturls WHERE file=?", (filename,))
    data = cur.fetchone()
    con.close()
    if data:
        #update shortlink
        execute_db('UPDATE shorturls SET file=? WHERE file=?', (newname, filename))
    #rename file
    os.rename(os.path.join(path, filename), os.path.join(path, newname))
    #update database
    execute_db('UPDATE files SET name=? WHERE name=?', (newname, filename))
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
    con = sqlite3.connect('database.db')
    cur = con.cursor()
    cur.execute("SELECT password FROM Users where username = 'admin'")
    password = cur.fetchone()[0]
    con.close()
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
        if sys.argv[1] == 'passwd':
            password = getpass('Password: ')
            password = hashlib.sha256(password.encode('utf-8')).hexdigest()
            execute_db('UPDATE Users SET password=? WHERE username=?', (password, 'admin'))
            print(password)
            print('Password changed')
    else:
        app.run(debug=True, host='0.0.0.0', port=5090)