import sqlite3

conn = sqlite3.connect('database/finance.db')
c = conn.cursor()

print("Backing up existing budgets...")
c.execute("SELECT * FROM budgets")
old_budgets = c.fetchall()
print(f"Found {len(old_budgets)} existing budgets")

print("\nDropping old budgets table...")
c.execute("DROP TABLE IF EXISTS budgets")

print("Creating new budgets table with correct structure...")
c.execute('''
    CREATE TABLE budgets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT NOT NULL,
        monthly_limit REAL NOT NULL DEFAULT 0,
        user_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
''')

# If there were old budgets, try to restore them
if old_budgets:
    print(f"\nRestoring {len(old_budgets)} budgets...")
    for budget in old_budgets:
        try:
            # Assuming old structure: id, category, amount/monthly_limit, user_id, created_at
            if len(budget) >= 4:
                c.execute('''
                    INSERT INTO budgets (category, monthly_limit, user_id)
                    VALUES (?, ?, ?)
                ''', (budget[1], budget[2], budget[3]))
        except Exception as e:
            print(f"  Warning: Could not restore budget: {e}")

conn.commit()
conn.close()

print("\n✅ Budgets table recreated successfully!")
print("✅ You can now set budgets in your app!")
