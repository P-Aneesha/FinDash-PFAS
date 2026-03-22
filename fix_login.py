import psycopg2

DATABASE_URL = "postgresql://findash_user:FJE5YrxJCRvcS7ovmOUEyVIydhF3C3Vg@dpg-d6o0vb94tr6s73eer1vg-a.singapore-postgres.render.com/findash_db_bzrx"

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# Check what columns exist
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='users'")
cols = [r[0] for r in cur.fetchall()]
print("Current columns:", cols)

# Add missing columns if needed
if 'password_hash' not in cols:
    cur.execute("ALTER TABLE users ADD COLUMN password_hash VARCHAR(255)")
    print("✅ Added password_hash")

if 'email' not in cols:
    cur.execute("ALTER TABLE users ADD COLUMN email VARCHAR(255)")
    print("✅ Added email")

if 'full_name' not in cols:
    cur.execute("ALTER TABLE users ADD COLUMN full_name VARCHAR(255)")
    print("✅ Added full_name")

if 'reset_token' not in cols:
    cur.execute("ALTER TABLE users ADD COLUMN reset_token TEXT")
    print("✅ Added reset_token")

if 'reset_token_expiry' not in cols:
    cur.execute("ALTER TABLE users ADD COLUMN reset_token_expiry TEXT")
    print("✅ Added reset_token_expiry")

conn.commit()
cur.close()
conn.close()
print("\n✅ Database fixed! Try logging in again.")