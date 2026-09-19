with open('src/sovereign/infrastructure/state/sqlite_repository.py', 'r') as f:
    content = f.read()

bad_str = \"\"\"conn.execute(\"\"\"
                    
                conn.execute('''\"\"\"

good_str = \"\"\"conn.execute('''\"\"\"
content = content.replace(bad_str, good_str)

bad_str_end = \"\"\"                ''')
    
                    CREATE TABLE IF NOT EXISTS checkpoints (\"\"\"

good_str_end = \"\"\"                ''')
                conn.execute(\"\"\"
                    CREATE TABLE IF NOT EXISTS checkpoints (\"\"\"
content = content.replace(bad_str_end, good_str_end)

with open('src/sovereign/infrastructure/state/sqlite_repository.py', 'w') as f:
    f.write(content)
