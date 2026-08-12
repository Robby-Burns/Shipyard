import os
import sqlite3

root = r"c:\Users\burns\OneDrive\Documents\GitHub\Shipyard"
for dirpath, _, filenames in os.walk(root):
    for f in filenames:
        if f == "shipyard.db":
            full_path = os.path.join(dirpath, f)
            print("Found shipyard.db at:", full_path)
            try:
                conn = sqlite3.connect(full_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                print("Tables:")
                for t in tables:
                    table_name = t[0]
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                    count = cursor.fetchone()[0]
                    print(f"  - {table_name}: {count} rows")
            except Exception as e:
                print("Error reading:", e)
