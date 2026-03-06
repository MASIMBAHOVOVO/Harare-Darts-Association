"""Script to migrate data from the local SQLite database to a PostgreSQL database on Vercel."""
import os
import sys
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db

def migrate():
    """Migrate all data from local SQLite database (hda.db) to the external PostgreSQL database."""
    # 1. Fetch the PostgreSQL URL directly from the environment or user input
    postgres_url = os.environ.get('POSTGRES_URL') or os.environ.get('DATABASE_URL')
    if not postgres_url:
        postgres_url = input("Please enter your Vercel POSTGRES_URL starting with postgres:// or postgresql:// :\n> ")
    
    if not postgres_url:
        print("Error: No PostgreSQL URL provided.")
        sys.exit(1)
        
    # Fix the schema prefix for SQLAlchemy 1.4+
    if postgres_url.startswith("postgres://"):
        postgres_url = postgres_url.replace("postgres://", "postgresql://", 1)

    print(f"Connecting to PostgreSQL database: {postgres_url.split('@')[-1]}")
    
    # 2. Setup standard Flask app context to access SQLAlchemy Models
    app = create_app()
    
    # Force the app configuration to use the postgres URL directly for initialization
    app.config['SQLALCHEMY_DATABASE_URI'] = postgres_url
    
    with app.app_context():
        # Make sure target tables exist
        print("Creating tables in PostgreSQL if they do not exist...")
        db.create_all()
        
        # We need a separate session/engine for SQLite
        sqlite_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'hda.db')
        sqlite_uri = f'sqlite:///{sqlite_path}'
        
        if not os.path.exists(sqlite_path):
            print(f"Error: Could not find local SQLite database at {sqlite_path}")
            sys.exit(1)
            
        print(f"Connecting to local SQLite database at {sqlite_path}")
        sqlite_engine = create_engine(sqlite_uri)
        SessionSQLite = sessionmaker(bind=sqlite_engine)
        sqlite_session = SessionSQLite()

        # Reflect the tables so we can copy them dynamically without knowing model specifics
        meta_sqlite = MetaData()
        meta_sqlite.reflect(bind=sqlite_engine)
        
        meta_postgres = MetaData()
        meta_postgres.reflect(bind=db.engine)
        
        # Copy data table by table to preserve foreign key order, roughly
        # Or better yet, disable foreign key checks, copy all, enable.
        # But we'll try straight copy first, or using models.
        
        # It's safest to copy table by table using core inserts since that includes standard schema structure
        for table_name in meta_sqlite.tables:
            sqlite_table = meta_sqlite.tables[table_name]
            postgres_table = meta_postgres.tables.get(table_name)
            
            if postgres_table is None:
                print(f"Warning: Table '{table_name}' not found in PostgreSQL. Skipping.")
                continue
                
            print(f"Migrating table: {table_name}")
            
            # Fetch all rows from sqlite
            rows = sqlite_session.execute(sqlite_table.select()).fetchall()
            print(f"  Found {len(rows)} rows to migrate.")
            
            if not rows:
                continue

            # Clear existing data in target database table before insertion (Optional depending on preference)
            # db.session.execute(postgres_table.delete())
            # db.session.commit()
            
            # Insert all rows
            try:
                # Convert rows to a list of dicts to insert them in bulk
                insert_data = [dict(row._mapping) for row in rows]
                db.session.execute(postgres_table.insert(), insert_data)
                db.session.commit()
                print(f"  Successfully inserted {len(rows)} rows into {table_name}")
            except Exception as e:
                db.session.rollback()
                print(f"  Error inserting rows for {table_name}: {e}")
                
        # Update PostgreSQL sequences to avoid duplicate key violations on new inserts
        for table_name in meta_postgres.tables:
            postgres_table = meta_postgres.tables[table_name]
            if 'id' in postgres_table.columns:
                try:
                    from sqlalchemy import text
                    seq_name = f"{table_name}_id_seq"
                    db.session.execute(text(f"SELECT setval('{seq_name}', COALESCE((SELECT MAX(id)+1 FROM {table_name}), 1), false)"))
                    db.session.commit()
                    print(f"  Resynchronized sequence for {table_name}")
                except Exception as e:
                    db.session.rollback()
                    # It's fine if it fails, the table might not have a sequence
                    pass

        print("\nMigration completed successfully!")
        
if __name__ == "__main__":
    migrate()
