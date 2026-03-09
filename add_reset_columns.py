import sqlite3

conn = sqlite3.connect('database/finance.db', timeout=30.0)
conn.execute('PRAGMA journal_mode=WAL')

print("Adding password reset columns to users table...")

try:
    conn.execute('ALTER TABLE users ADD COLUMN reset_token TEXT')
    print("✅ Added reset_token column")
except Exception as e:
    print(f"reset_token column might already exist: {e}")

try:
    conn.execute('ALTER TABLE users ADD COLUMN reset_token_expiry TEXT')
    print("✅ Added reset_token_expiry column")
except Exception as e:
    print(f"reset_token_expiry column might already exist: {e}")

conn.commit()
conn.close()

print("\n✅ Database updated!")
