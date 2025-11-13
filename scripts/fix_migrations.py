import sqlite3
import os

db = os.path.join(os.getcwd(), 'db.sqlite3')
if not os.path.exists(db):
    print('db.sqlite3 not found at', db)
    raise SystemExit(1)

conn = sqlite3.connect(db)
cur = conn.cursor()

print('--- migrations (admin/core) before change ---')
for row in cur.execute("SELECT app,name,applied FROM django_migrations ORDER BY app,name"):
    if row[0] in ('admin', 'core'):
        print(row)

cur.execute('DELETE FROM django_migrations WHERE app=? AND name=?', ('admin', '0001_initial'))
conn.commit()
print('\nDeleted admin.0001_initial (if it existed)')

print('\n--- migrations (admin/core) after change ---')
for row in cur.execute("SELECT app,name,applied FROM django_migrations ORDER BY app,name"):
    if row[0] in ('admin', 'core'):
        print(row)

conn.close()
print('\nDone')
