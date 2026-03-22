import psycopg2

DATABASE_URL = 'postgresql://findash_user:FJE5YrxJCRvcS7ovmOUEyVIydhF3C3Vg@dpg-d6o0vb94tr6s73eer1vg-a.singapore-postgres.render.com/findash_db_bzrx'

print("🔄 Setting up database...")

try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # Drop existing tables (fresh start)
    print("🗑️  Dropping existing tables...")
    cur.execute('DROP TABLE IF EXISTS goals CASCADE')
    cur.execute('DROP TABLE IF EXISTS budgets CASCADE')
    cur.execute('DROP TABLE IF EXISTS expenses CASCADE')
    cur.execute('DROP TABLE IF EXISTS income CASCADE')
    cur.execute('DROP TABLE IF EXISTS users CASCADE')
    
    # Create users table
    print("📝 Creating users table...")
    cur.execute('''
        CREATE TABLE users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            fullname VARCHAR(100),
            email VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create income table
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
    
    # Create expenses table
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
    
    # Create budgets table
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
    
    # Create goals table
    print("📝 Creating goals table...")
    cur.execute('''
        CREATE TABLE goals (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            goal_name VARCHAR(100) NOT NULL,
            target_amount DECIMAL(10, 2) NOT NULL,
            current_savings DECIMAL(10, 2) DEFAULT 0,
            target_date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    cur.close()
    conn.close()
    
    print("\n✅ Database setup complete!")
    print("✅ All tables created successfully!")
    print("\n👉 Now run: python app.py")
    print("👉 Then go to: http://localhost:5000/login")
    print("👉 Click 'Register' and create a new account")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()