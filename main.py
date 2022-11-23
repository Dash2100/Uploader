import os
from flask import Flask, request, send_from_directory, render_template, jsonify, make_response, redirect, url_for, Response
from datetime import datetime

app = Flask(__name__, static_url_path='/static')

path = './Uploads'
exclude = ['Thumbs.db', '.DS_Store']

@app.route('/test')
def test():
    return render_template('test.html')

@app.route('/')
def index():
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
                file_data.append(round(size_bytes / 1000000,3).__str__() + ' MB')
                all_files.append(file_data)
    all_files.sort(key=lambda x: x[1])
    all_files.reverse()
    return render_template('index.html', **locals())

@app.route('/upload', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            print('No file part')
            return ('No file part')
        file = request.files['file']
        print(file)
        if file.filename == '':
            return ('No selected file')
        if file:
            while file.filename in os.listdir(path):
                file.filename = '-' + file.filename
            file.save(os.path.join(path, file.filename))
            return "success"


@app.route('/download/<string:name>')
def download_file(name):
    return send_from_directory(path, name)

@app.route('/delfile/<string:file>')
def del_file(file):
    try:
        os.remove(os.path.join(path, file))
        return "OK"
    except FileNotFoundError:
        return "Not Found"

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5090)
