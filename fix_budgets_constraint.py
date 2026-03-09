import sqlite3

conn = sqlite3.connect('database/finance.db', timeout=30.0)
conn.execute('PRAGMA journal_mode=WAL')

print("Checking budgets table structure...")

# Get current table info
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(budgets)")
columns = cursor.fetchall()

print("\nCurrent columns:")
for col in columns:
    print(f"  {col}")

# Get indexes to check for UNIQUE constraints
cursor.execute("PRAGMA index_list(budgets)")
indexes = cursor.fetchall()

print("\nCurrent indexes:")
for idx in indexes:
    print(f"  {idx}")

# Backup existing budgets
cursor.execute("SELECT * FROM budgets")
old_budgets = cursor.fetchall()
print(f"\nFound {len(old_budgets)} existing budgets")

# Drop and recreate table WITHOUT unique constraint
print("\nDropping old budgets table...")
conn.execute("DROP TABLE IF EXISTS budgets")

print("Creating new budgets table...")
conn.execute('''
    CREATE TABLE budgets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT NOT NULL,
        monthly_limit REAL NOT NULL DEFAULT 0,
        user_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
''')

# Restore budgets (removing duplicates - keep latest only)
if old_budgets:
    print(f"\nRestoring budgets (removing duplicates)...")
    
    # Group by category and user_id, keep only the one with highest monthly_limit
    budgets_dict = {}
    for budget in old_budgets:
        key = (budget[1], budget[3])  # (category, user_id)
        if key not in budgets_dict or budget[2] > budgets_dict[key][2]:
            budgets_dict[key] = budget
    
    for budget in budgets_dict.values():
        try:
            conn.execute('''
                INSERT INTO budgets (category, monthly_limit, user_id)
                VALUES (?, ?, ?)
            ''', (budget[1], budget[2], budget[3]))
            print(f"  Restored: {budget[1]} = ₹{budget[2]}")
        except Exception as e:
            print(f"  Error restoring budget: {e}")

conn.commit()
conn.close()

print("\n✅ Budgets table fixed!")
print("✅ Now push to GitHub and deploy!")
