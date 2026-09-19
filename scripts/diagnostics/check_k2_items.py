import sqlite3
conn = sqlite3.connect('local_data/sovereign.db')
c = conn.cursor()
c.execute("SELECT * FROM state_items WHERE task_id='task-aaa894bd'")
for r in c.fetchall():
    print(r)
