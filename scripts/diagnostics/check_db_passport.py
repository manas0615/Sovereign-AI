import sqlite3
import json

conn = sqlite3.connect('local_data/sovereign.db')
c = conn.cursor()
c.execute("SELECT * FROM capability_passports WHERE qualification_status='QUALIFIED'")
for r in c.fetchall():
    print(r)
