import sqlite3
conn = sqlite3.connect('database.db')
cur = conn.cursor()
print('Tables:')
for row in cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall():
    print('-', row[0])

print('\nSchema for office_work_detail:')
try:
    for r in cur.execute("PRAGMA table_info(office_work_detail)"):
        print(r)
except Exception as e:
    print('Error:', e)

conn.close()
