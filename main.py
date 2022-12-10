from flask import Flask, request, send_from_directory, render_template, jsonify, make_response, redirect, url_for, Response
from flask_login import LoginManager, UserMixin, login_user,  login_required, logout_user, current_user
from datetime import datetime
from getpass import getpass
from sql_init import sqlinit
import sqlite3
import hashlib
import sys
import json
import os

path = './Uploads'

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
        return send_from_directory(path, file[0], as_attachment=True)
    else:
        return render_template('404.html')

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
            return send_from_directory(path, filename, as_attachment=True)
        else:
            return Response(status=404)
    else:
        return Response(status=404)

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
    if request.method == 'POST':
        if 'file' not in request.files:
            return 'No file part'
        file = request.files['file']
        print(file)
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
            execute_db('INSERT INTO files VALUES (?, ?, ?, ?, ?)', (file.filename, date, size, 0, ""))
            return "success"


@app.route('/admin/download/<string:filename>', methods=['GET'])
@login_required
def download_file(filename):
    #check if file exists
    if filename in os.listdir(path):
        return send_from_directory(path, filename, as_attachment=True)
    else:
        return Response(status=404)


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
    if shortlink == "admin":
        return "illegal"
    #check if shortlink is already in use
    con = sqlite3.connect('database.db')
    cur = con.cursor()
    cur.execute("SELECT * FROM shorturls WHERE url=?", (shortlink,))
    data = cur.fetchone()
    if data:
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
    #load password from json
    with open('data.json', 'r') as f:
        password = json.load(f).get('password')
    if hashlib.sha256(request_pas['password'].encode('utf-8')).hexdigest() == password:
        user = User()
        user.id = 'admin'
        login_user(user) #登入使用者
        return jsonify({'ststus':'correct'})
    return jsonify({'ststus':'incorrect'})
 
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
            with open('data.json', 'w') as f:
                json.dump({'password': password}, f)
            print('Password changed')
    else:
        app.run(debug=True, host='0.0.0.0', port=5090)