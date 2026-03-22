import psycopg2
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

DATABASE_URL = 'postgresql://findash_user:FJE5YrxJCRvcS7ovmOUEyVIydhF3C3Vg@dpg-d6o0vb94tr6s73eer1vg-a.singapore-postgres.render.com/findash_db_bzrx'

try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # Create test user
    username = 'test'
    password = 'test123'
    hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
    
    # Delete if exists
    cur.execute('DELETE FROM users WHERE username = %s', (username,))
    
    # Insert new
    cur.execute(
        'INSERT INTO users (username, password, fullname, email) VALUES (%s, %s, %s, %s) RETURNING id',
        (username, hashed_pw, 'Test User', 'test@test.com')
    )
    user_id = cur.fetchone()[0]
    
    conn.commit()
    cur.close()
    conn.close()
    
    print(f"✅ Test user created successfully!")
    print(f"   Username: {username}")
    print(f"   Password: {password}")
    print(f"   User ID: {user_id}")
    print(f"\n👉 Now try logging in with these credentials")
    
except Exception as e:
    print(f"❌ Error: {e}")