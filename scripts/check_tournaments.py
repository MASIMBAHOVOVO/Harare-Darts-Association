from app import create_app, db
from app.models import Tournament

app = create_app()
with app.app_context():
    tournaments = Tournament.query.all()
    for t in tournaments:
        print(f"ID: {t.id} | Name: {t.name} | Trials: {t.is_trials}")
