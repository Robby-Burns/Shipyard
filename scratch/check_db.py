import sqlite3

def check():
    conn = sqlite3.connect('shipyard.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    print('Tables:', cursor.fetchall())
    
    cursor.execute('SELECT id, title, status, current_step, error_message FROM workflow_runs ORDER BY created_at DESC LIMIT 5')
    print('Recent Workflow Runs:')
    for row in cursor.fetchall():
        print(row)

if __name__ == '__main__':
    check()
