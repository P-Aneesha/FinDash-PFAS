import sqlite3

# Connect to database
conn = sqlite3.connect('database/finance.db')
c = conn.cursor()

# Check current budgets table structure
c.execute("PRAGMA table_info(budgets)")
columns = c.fetchall()

print("Current budgets table structure:")
for col in columns:
    print(f"  - {col[1]} ({col[2]})")

# Check if monthly_limit column exists
column_names = [col[1] for col in columns]

if 'monthly_limit' not in column_names:
    print("\n❌ monthly_limit column missing!")
    print("Adding monthly_limit column...")
    
    # Add the monthly_limit column
    c.execute("ALTER TABLE budgets ADD COLUMN monthly_limit REAL DEFAULT 0")
    
    # If there's an 'amount' column, copy data to monthly_limit
    if 'amount' in column_names:
        print("Copying data from 'amount' to 'monthly_limit'...")
        c.execute("UPDATE budgets SET monthly_limit = amount")
    
    conn.commit()
    print("✅ Fixed!")
else:
    print("\n✅ monthly_limit column exists!")

# Show final structure
c.execute("PRAGMA table_info(budgets)")
columns = c.fetchall()

print("\nFinal budgets table structure:")
for col in columns:
    print(f"  - {col[1]} ({col[2]})")

conn.close()
print("\n✅ Database check complete!")
