from App import create_app
import os

app = create_app()

debug = app.config['DEBUG']
port = app.config['PORT']
host = app.config['HOST']

if __name__ == '__main__':
    app.run(debug=debug, port=port, host=host)
