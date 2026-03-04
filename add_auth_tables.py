import sqlite3

def add_users_table():
    conn = sqlite3.connect('database/finance.db')
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Add user_id to existing tables
    try:
        cursor.execute('ALTER TABLE income ADD COLUMN user_id INTEGER')
    except:
        pass
    
    try:
        cursor.execute('ALTER TABLE expenses ADD COLUMN user_id INTEGER')
    except:
        pass
    
    try:
        cursor.execute('ALTER TABLE goals ADD COLUMN user_id INTEGER')
    except:
        pass
    
    try:
        cursor.execute('ALTER TABLE budgets ADD COLUMN user_id INTEGER')
    except:
        pass
    
    conn.commit()
    conn.close()
    print("✅ Users table created successfully!")

if __name__ == '__main__':
    add_users_table()