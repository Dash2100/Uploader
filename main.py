from flask import Flask, request, send_from_directory, render_template, jsonify, make_response, redirect, url_for, Response
from flask_login import LoginManager, UserMixin, login_user,  login_required, logout_user 
from datetime import datetime
from getpass import getpass
import hashlib
import sys
import json
import os

path = './Uploads'
exclude = ['Thumbs.db', '.DS_Store']

app = Flask(__name__, static_url_path='/static')
app.config['SECRET_KEY'] = os.urandom(24)
login_manager = LoginManager(app)  # Create login manager
login_manager.login_view = 'login'  # Set login view

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin')
@login_required
def admin():
    all_files = []
    files = os.listdir(path)
    for f in files:
        file_data = list()
        fullpath = os.path.join(path, f)
        if os.path.isfile(fullpath):
            if f not in exclude:
                file_data.append(f)
                file_data.append(datetime.fromtimestamp(
                    os.path.getmtime(fullpath)).strftime('%Y-%m-%d %H:%M:%S'))
                size_bytes = os.path.getsize(fullpath)
                file_data.append(
                    round(size_bytes / 1000000, 3).__str__() + ' MB')
                all_files.append(file_data)
    all_files.sort(key=lambda x: x[1])
    all_files.reverse()
    return render_template('admin.html', **locals())


@app.route('/upload', methods=['POST'])
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
            return "success"


@app.route('/download/<string:name>')
@login_required
def download_file(name):
    return send_from_directory(path, name)


@app.route('/delfile/<string:file>')
@login_required
def del_file(file):
    try:
        os.remove(os.path.join(path, file))
        return "OK"
    except FileNotFoundError:
        return "Not Found"

## Login

# Create user class
class User(UserMixin):  
    pass 

#

@login_manager.user_loader  
def user_loader(userid):    
    user = User() #繼承UserMixin
    user.id = userid 
    return user

@app.route('/login', methods=['GET', 'POST'])  
def login():  
    if request.method == 'GET':  
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
    if len(sys.argv) == 2:
        if sys.argv[1] == 'passwd':
            password = getpass('Password: ')
            password = hashlib.sha256(password.encode('utf-8')).hexdigest()
            with open('data.json', 'w') as f:
                json.dump({'password': password}, f)
            print('Password changed')
    else:
        app.run(debug=True, host='0.0.0.0', port=5090)