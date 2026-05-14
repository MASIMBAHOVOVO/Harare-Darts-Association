from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    try:
        with db.engine.connect() as conn:
            try:
                conn.execute(text("ALTER TABLE tournaments ADD COLUMN tournament_type VARCHAR(50) DEFAULT 'standard'"))
                print("Added column tournament_type")
            except Exception as e:
                print(f"Column tournament_type might already exist: {e}")
        
        db.session.commit()
        print("Database schema updated successfully.")
    except Exception as e:
        print(f"Error updating schema: {e}")
