from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        print("Checking for tournament_type column...")
        result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='tournaments' AND column_name='tournament_type'"))
        if not result.fetchone():
            print("Adding tournament_type column...")
            conn.execute(text("ALTER TABLE tournaments ADD COLUMN tournament_type VARCHAR(50) DEFAULT 'standard'"))
            # In some SQLAlchemy versions/configurations, we need to explicitly commit on the connection
            conn.execute(text("COMMIT"))
            print("Column added.")
        else:
            print("Column already exists.")
    print("Done.")
