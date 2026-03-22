import psycopg2

DATABASE_URL = 'postgresql://findash_user:FJE5YrxJCRvcS7ovmOUEyVIydhF3C3Vg@dpg-d6o0vb94tr6s73eer1vg-a.singapore-postgres.render.com/findash_db_bzrx'

try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # Create users table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            fullname VARCHAR(100),
            email VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("✅ Users table created")
    
    # Create income table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS income (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            source VARCHAR(100) NOT NULL,
            amount DECIMAL(10, 2) NOT NULL,
            date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("✅ Income table created")
    
    # Create expenses table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            category VARCHAR(50) NOT NULL,
            amount DECIMAL(10, 2) NOT NULL,
            description TEXT,
            date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("✅ Expenses table created")
    
    # Create budgets table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS budgets (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            category VARCHAR(50) NOT NULL,
            monthly_limit DECIMAL(10, 2) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("✅ Budgets table created")
    
    # Create goals table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS goals (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            goal_name VARCHAR(100) NOT NULL,
            target_amount DECIMAL(10, 2) NOT NULL,
            current_savings DECIMAL(10, 2) DEFAULT 0,
            target_date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("✅ Goals table created")
    
    conn.commit()
    cur.close()
    conn.close()
    
    print("\n🎉 All tables created successfully!")
    print("👉 Now go to http://localhost:5000/login and REGISTER a new account")
    
except Exception as e:
    print(f"❌ Error: {e}")