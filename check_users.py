import psycopg2

DATABASE_URL = 'postgresql://findash_user:FJE5YrxJCRvcS7ovmOUEyVIydhF3C3Vg@dpg-d6o0vb94tr6s73eer1vg-a.singapore-postgres.render.com/findash_db_bzrx'

try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # Check if users table exists
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'users'
    """)
    
    if cur.fetchone():
        print("✅ Users table exists")
        
        # List all users
        cur.execute('SELECT id, username, email, created_at FROM users')
        users = cur.fetchall()
        
        if users:
            print(f"\n📊 Found {len(users)} user(s):")
            for user in users:
                print(f"  - ID: {user[0]}, Username: {user[1]}, Email: {user[2]}, Created: {user[3]}")
        else:
            print("\n❌ NO USERS FOUND!")
            print("👉 You need to REGISTER a new account first!")
    else:
        print("❌ Users table DOES NOT exist!")
        print("👉 Run the database schema creation script first!")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Database Error: {e}")
    print("\nPossible issues:")
    print("1. Database server is down")
    print("2. Wrong DATABASE_URL")
    print("3. Network connection issue")