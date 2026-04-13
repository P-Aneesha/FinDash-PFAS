import psycopg2

DATABASE_URL = 'postgresql://findash_user:a1FrpDSnEKRwtmFpLF03ZZ8n5XhkrI8b@dpg-d7dta79kh4rs73a19a2g-a.singapore-postgres.render.com/findash_db_vzgj'

print("🔄 Connecting to PostgreSQL...")
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()
print("✅ Connected!")

print("🗑️  Dropping all existing tables...")
cur.execute('DROP TABLE IF EXISTS goals CASCADE')
cur.execute('DROP TABLE IF EXISTS budgets CASCADE')
cur.execute('DROP TABLE IF EXISTS expenses CASCADE')
cur.execute('DROP TABLE IF EXISTS income CASCADE')
cur.execute('DROP TABLE IF EXISTS "Users" CASCADE')   # drop old wrong-case table
cur.execute('DROP TABLE IF EXISTS users CASCADE')      # drop lowercase too (clean slate)

print("📝 Creating users table (lowercase)...")
cur.execute('''
    CREATE TABLE users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        email VARCHAR(100),
        full_name VARCHAR(100),
        security_question TEXT,
        security_answer TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

print("📝 Creating income table...")
cur.execute('''
    CREATE TABLE income (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        source VARCHAR(100) NOT NULL,
        amount DECIMAL(10, 2) NOT NULL,
        date DATE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

print("📝 Creating expenses table...")
cur.execute('''
    CREATE TABLE expenses (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        category VARCHAR(50) NOT NULL,
        amount DECIMAL(10, 2) NOT NULL,
        description TEXT,
        date DATE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

print("📝 Creating budgets table...")
cur.execute('''
    CREATE TABLE budgets (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        category VARCHAR(50) NOT NULL,
        monthly_limit DECIMAL(10, 2) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

print("📝 Creating goals table...")
cur.execute('''
    CREATE TABLE goals (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        goal_name VARCHAR(100) NOT NULL,
        target_amount DECIMAL(10, 2) NOT NULL,
        current_savings DECIMAL(10, 2) DEFAULT 0,
        target_date DATE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

conn.commit()
cur.close()
conn.close()

print("\n✅ ALL TABLES RECREATED SUCCESSFULLY!")
print("👉 Now run: python app.py")
print("👉 Go to: http://localhost:5000/login and register a new account")