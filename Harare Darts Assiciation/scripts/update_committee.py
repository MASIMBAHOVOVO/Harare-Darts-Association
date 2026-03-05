import sys
import os
import sqlite3

# Add current directory to path
sys.path.append(os.getcwd())

from app import create_app, db
from app.models import Committee

def update_committee():
    app = create_app()
    with app.app_context():
        # 1. Update Schema if needed (SQLite doesn't support ADD COLUMN IF NOT EXISTS easily)
        # We'll use a raw connection to add columns if they are missing
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if columns exist
        cursor.execute("PRAGMA table_info(committee)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'email' not in columns:
            print("Adding 'email' column to 'committee' table...")
            cursor.execute("ALTER TABLE committee ADD COLUMN email VARCHAR(120)")
        
        if 'phone' not in columns:
            print("Adding 'phone' column to 'committee' table...")
            cursor.execute("ALTER TABLE committee ADD COLUMN phone VARCHAR(50)")
        
        conn.commit()
        conn.close()

        # 2. Clear existing entries
        print("Clearing existing committee entries...")
        Committee.query.delete()
        
        # 3. Add new committee members
        committee_data = [
            {
                "name": "MODEKAI DHEKA",
                "role": "Chairman",
                "phone": "0774 104 784",
                "email": "dmodekai@gmail.com",
                "display_order": 1
            },
            {
                "name": "NOEL MWENDAMBERI",
                "role": "Vice Chairperson",
                "phone": "0716 397147",
                "email": "nmwendas@gmail.com",
                "display_order": 2
            },
            {
                "name": "NYASHA MUSHANGWE",
                "role": "Secretary General",
                "phone": "782491617",
                "email": "nyasha0101@gmail.com",
                "display_order": 3
            },
            {
                "name": "SILAS MARANGWANDA",
                "role": "Treasurer",
                "phone": "0774 436 161",
                "email": "Silasrunyararomarangwanda@gmail.com",
                "display_order": 4
            },
            {
                "name": "CHAPU YVETTE",
                "role": "Public Relations Officer / Fund Raiser",
                "phone": "779370405",
                "email": None,
                "display_order": 5
            },
            {
                "name": "Mavima Tobias",
                "role": "Development Officer",
                "phone": "0772 409 817",
                "email": None,
                "display_order": 6
            },
            {
                "name": "BLESSED GUSHA",
                "role": "Organising/Fixture Secretary",
                "phone": "0714787651-0787883083",
                "email": "andersonjr973@gmail.com",
                "display_order": 7
            },
            {
                "name": "ANGELINE SOME",
                "role": "Committee Member",
                "phone": "774671304",
                "email": None,
                "display_order": 8
            },
            {
                "name": "VIMBAI TAKURA",
                "role": "Committee Member",
                "phone": "0784453517",
                "email": None,
                "display_order": 9
            }
        ]
        
        for data in committee_data:
            member = Committee(
                name=data["name"],
                role=data["role"],
                phone=data["phone"],
                email=data["email"],
                display_order=data["display_order"]
            )
            db.session.add(member)
        
        db.session.commit()
        print("Successfully updated committee information.")

if __name__ == "__main__":
    update_committee()
