import sqlite3
conn = sqlite3.connect('local_data/sovereign.db')
c = conn.cursor()
c.execute("SELECT task_id, status FROM tasks ORDER BY created_at DESC LIMIT 3")
for r in c.fetchall():
    print(r)
c.execute("SELECT * FROM state_items WHERE task_id='task-03f16a26'")
for r in c.fetchall():
    print(r)
