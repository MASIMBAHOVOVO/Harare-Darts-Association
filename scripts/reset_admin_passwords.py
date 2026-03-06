import os
import sys
from werkzeug.security import generate_password_hash

# add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from app import create_app, db
from app.models import User

app = create_app()
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('POSTGRES_URL')

passwords = {
    'secretary': 'hda2024sec',
    'fixture_sec': 'hda2024fix',
    'captain1': 'hda2024cap'
}

with app.app_context():
    for username, pwd in passwords.items():
        user = User.query.filter_by(username=username).first()
        if user:
            print(f"Updating password for {username}")
            user.password_hash = generate_password_hash(pwd)
        else:
            print(f"Creating user {username}")
            user = User(username=username, password_hash=generate_password_hash(pwd), role='secretary_general' if username=='secretary' else ('fixture_secretary' if username=='fixture_sec' else 'captain'), full_name=username)
            db.session.add(user)
    db.session.commit()
    print("Passwords reset/created.")