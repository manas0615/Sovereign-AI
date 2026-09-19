import sqlite3

conn = sqlite3.connect('local_data/sovereign.db')
c = conn.cursor()
c.execute("SELECT metadata FROM qualification_results")
for r in c.fetchall():
    print(r)
