import sqlite3

conn = sqlite3.connect('local_data/sovereign.db')
c = conn.cursor()
c.execute("SELECT passport_id, qualification_identity, deployment_identity, capability_contract FROM capability_passports WHERE qualification_status='QUALIFIED'")
for r in c.fetchall():
    print(r)
