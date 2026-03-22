import psycopg2

DATABASE_URL = 'postgresql://findash_user:FJE5YrxJCRvcS7ovmOUEyVIydhF3C3Vg@dpg-d6o0vb94tr6s73eer1vg-a.singapore-postgres.render.com/findash_db_bzrx'

try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # Check if created_at already exists in income table
    cur.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='income' AND column_name='created_at'
    """)
    
    if not cur.fetchone():
        cur.execute("""
            ALTER TABLE income 
            ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        """)
        print("✅ Added created_at to income table")
    else:
        print("ℹ️ created_at already exists in income table")
    
    # Check if created_at already exists in expenses table
    cur.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='expenses' AND column_name='created_at'
    """)
    
    if not cur.fetchone():
        cur.execute("""
            ALTER TABLE expenses 
            ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        """)
        print("✅ Added created_at to expenses table")
    else:
        print("ℹ️ created_at already exists in expenses table")
    
    conn.commit()
    cur.close()
    conn.close()
    
    print("\n🎉 Database updated successfully!")
    
except Exception as e:
    print(f"❌ Error: {e}")