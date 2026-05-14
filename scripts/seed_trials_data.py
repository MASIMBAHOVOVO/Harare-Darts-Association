import json
from app import create_app, db
from app.models import Tournament

app = create_app()
with app.app_context():
    t = Tournament.query.get(3)
    if t:
        t.is_trials = True
        dummy_data = {
            "men": [
                {"pos": 1, "name": "Masimba M Hovovo", "one_eighties": 13, "closures": "142,135,156", "points": 20},
                {"pos": 2, "name": "Test Player 2", "one_eighties": 5, "closures": "100", "points": 18},
                {"pos": 8, "name": "Qualified Last", "one_eighties": 2, "closures": "80", "points": 15},
                {"pos": 9, "name": "Not Qualified", "one_eighties": 0, "closures": "—", "points": 10}
            ],
            "women": [
                {"pos": 1, "name": "Female Star", "one_eighties": 3, "closures": "110", "points": 19},
                {"pos": 6, "name": "Female Last Qualified", "one_eighties": 1, "closures": "60", "points": 12},
                {"pos": 7, "name": "Female Not Qualified", "one_eighties": 0, "closures": "—", "points": 8}
            ],
            "junior_men": [],
            "junior_women": []
        }
        t.results_data = json.dumps(dummy_data)
        t.is_upcoming = False
        db.session.commit()
        print(f"Updated tournament {t.name} with dummy Trials data.")
