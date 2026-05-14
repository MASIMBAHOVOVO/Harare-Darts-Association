import sqlite3

conn = sqlite3.connect('hda.db')
conn.row_factory = sqlite3.Row

cursor = conn.cursor()
cursor.execute("SELECT * FROM fixtures WHERE home_team_number = 7 OR away_team_number = 7")
fixtures = cursor.fetchall()
print(f"Fixtures for team 7: {len(fixtures)}")
for f in fixtures:
    print(dict(f))

cursor.execute('''
    SELECT r.* FROM results r
    JOIN fixtures f ON r.fixture_id = f.id
    WHERE f.home_team_number = 7 OR f.away_team_number = 7
''')
results = cursor.fetchall()
print(f"Results for team 7: {len(results)}")
for r in results:
    print(dict(r))







