from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    try:
        # Check if columns already exist
        with db.engine.connect() as conn:
            # Adding is_trials
            try:
                conn.execute(text("ALTER TABLE tournaments ADD COLUMN is_trials BOOLEAN DEFAULT 0"))
                print("Added column is_trials")
            except Exception as e:
                print(f"Column is_trials might already exist: {e}")

            # Adding results_data
            try:
                conn.execute(text("ALTER TABLE tournaments ADD COLUMN results_data TEXT"))
                print("Added column results_data")
            except Exception as e:
                print(f"Column results_data might already exist: {e}")
        
        db.session.commit()
        print("Database schema updated successfully.")
    except Exception as e:
        print(f"Error updating schema: {e}")
