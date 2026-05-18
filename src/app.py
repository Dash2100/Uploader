import getpass
import sys

from App import create_app
from App.database import db
from App.models import User

app = create_app()


def _change_password():
    new_password = getpass.getpass('New admin password: ')
    if not new_password:
        print('Aborted: empty password')
        sys.exit(1)
    with app.app_context():
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin')
            db.session.add(admin)
        admin.set_password(new_password)
        db.session.commit()
    print('Admin password updated.')


if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1] == 'passwd':
        _change_password()
    else:
        app.run(
            debug=app.config['DEBUG'],
            host=app.config['HOST'],
            port=app.config['PORT'],
        )
