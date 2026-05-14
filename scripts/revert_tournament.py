from app import create_app, db
from app.models import Tournament

app = create_app()
with app.app_context():
    t = Tournament.query.get(3)
    if t:
        t.is_upcoming = True
        t.results_data = None
        t.results = None
        db.session.commit()
        print(f"Reverted tournament {t.name} to 'Upcoming' status and cleared results.")
