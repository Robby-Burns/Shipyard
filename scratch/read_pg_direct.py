import sys
import json
import psycopg

db_url = "postgresql://postgres:postgrespassword@localhost:5432/shipyard"
print("Connecting using psycopg to:", db_url)

try:
    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, title, status, messages, specification FROM intake_sessions ORDER BY created_at DESC;")
            rows = cur.fetchall()
            if not rows:
                print("No sessions found in PostgreSQL!")
                sys.exit(0)
            
            for row in rows:
                session_id, title, status, messages, specification = row
                print("=" * 60)
                print("SESSION ID:", session_id)
                print("TITLE:", title)
                print("STATUS:", status)
                print("SPECIFICATION LENGTH:", len(specification) if specification else 0)
                print("\n--- MESSAGES ---")
                
                # Check if messages is string or list/dict
                if isinstance(messages, str):
                    msgs = json.loads(messages)
                else:
                    msgs = messages
                    
                for msg in msgs:
                    print(f"[{msg['role'].upper()}]:")
                    content = msg['content']
                    if len(content) > 300:
                        print(content[:300] + "... (TRUNCATED)")
                    else:
                        print(content)
                    print("-" * 40)
                print("=" * 60)
except Exception as e:
    print("Error:", e)
