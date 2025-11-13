import sqlite3
import os

db = os.path.join(os.getcwd(), 'db.sqlite3')
if not os.path.exists(db):
    print('db.sqlite3 not found at', db)
    raise SystemExit(1)

conn = sqlite3.connect(db)
cur = conn.cursor()

print('--- admin migrations (before) ---')
for row in cur.execute("SELECT app,name,applied FROM django_migrations WHERE app='admin' ORDER BY name"):
    print(row)

cur.execute("DELETE FROM django_migrations WHERE app='admin'")
conn.commit()
print('\nDeleted all admin migrations (if any)')

print('\n--- admin migrations (after) ---')
for row in cur.execute("SELECT app,name,applied FROM django_migrations WHERE app='admin' ORDER BY name"):
    print(row)

conn.close()
print('\nDone')
