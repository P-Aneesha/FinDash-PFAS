import psycopg2
DATABASE_URL = "postgresql://findash_user:FJE5YrxJCRvcS7ovmOUEyVIydhF3C3Vg@dpg-d6o0vb94tr6s73eer1vg-a.singapore-postgres.render.com/findash_db_bzrx"

print("🔌 Connecting to PostgreSQL...")
try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    print("✅ Connected successfully!")
    
    print("\n📊 Creating tables...")
    
    # Users table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            email VARCHAR(255),
            password_hash VARCHAR(255) NOT NULL,
            full_name VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("✅ Users table created")
    
    # Income table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS income (
            id SERIAL PRIMARY KEY,
            source VARCHAR(255) NOT NULL,
            amount DECIMAL(10, 2) NOT NULL,
            date DATE NOT NULL,
            user_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    print("✅ Income table created")
    
    # Expenses table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id SERIAL PRIMARY KEY,
            category VARCHAR(100) NOT NULL,
            amount DECIMAL(10, 2) NOT NULL,
            description TEXT,
            date DATE NOT NULL,
            day_type VARCHAR(20),
            user_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    print("✅ Expenses table created")
    
    # Budgets table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS budgets (
            id SERIAL PRIMARY KEY,
            category VARCHAR(100) NOT NULL,
            monthly_limit DECIMAL(10, 2) NOT NULL DEFAULT 0,
            user_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    print("✅ Budgets table created")
    
    # Goals table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS goals (
            id SERIAL PRIMARY KEY,
            goal_name VARCHAR(255) NOT NULL,
            target_amount DECIMAL(10, 2) NOT NULL,
            current_savings DECIMAL(10, 2) DEFAULT 0,
            target_date DATE,
            user_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    print("✅ Goals table created")
    
    conn.commit()
    cur.close()
    conn.close()
    
    print("\n🎉 ALL TABLES CREATED SUCCESSFULLY!")
    print("✅ PostgreSQL database is ready to use!")
    print("\nNext: Update requirements.txt and app.py")
    
except Exception as e:
    print(f"❌ Error: {str(e)}")
    print("\nMake sure you:")
    print("1. Copied the correct Internal Database URL")
    print("2. Installed psycopg2-binary")
