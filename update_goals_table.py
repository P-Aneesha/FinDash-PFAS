import sqlite3

def update_goals_table():
    conn = sqlite3.connect('database/finance.db')
    cursor = conn.cursor()
    
    # Add new columns
    try:
        cursor.execute('ALTER TABLE goals ADD COLUMN target_months INTEGER')
    except:
        pass
    
    try:
        cursor.execute('ALTER TABLE goals ADD COLUMN monthly_savings REAL DEFAULT 0')
    except:
        pass
    
    conn.commit()
    conn.close()
    print("✅ Goals table updated successfully!")

if __name__ == '__main__':
    update_goals_table()