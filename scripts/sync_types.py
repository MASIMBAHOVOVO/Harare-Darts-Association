from app import create_app, db
from app.models import Tournament

app = create_app()
with app.app_context():
    t = Tournament.query.get(3)
    if t:
        t.tournament_type = 'trials'
        t.is_trials = True
        db.session.commit()
        print(f"Updated tournament {t.name} type to 'trials'.")
