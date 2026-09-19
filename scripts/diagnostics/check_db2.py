import sqlite3

conn = sqlite3.connect('local_data/sovereign.db')
c = conn.cursor()
c.execute("SELECT item_type, payload FROM state_items WHERE task_id='task-c82e76c2' AND item_type='decision' ORDER BY created_at ASC")
for row in c.fetchall():
    print(f"{row[0]}: {row[1]}")
