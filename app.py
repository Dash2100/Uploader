from app import create_app

app = create_app()

debug = app.config['DEBUG']
port = app.config['PORT']

if __name__ == '__main__':
    app.run(debug=debug, port=port, host='0.0.0.0')
