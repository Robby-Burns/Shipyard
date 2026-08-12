import sqlite3

conn = sqlite3.connect('shipyard.db')
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("Tables in shipyard.db:")
for t in tables:
    table_name = t[0]
    cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
    count = cursor.fetchone()[0]
    print(f" - {table_name}: {count} rows")
