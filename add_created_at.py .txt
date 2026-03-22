import psycopg2

DATABASE_URL = 'postgresql://findash_user:FJE5YrxJCRvcS7ovmOUEyVIydhF3C3Vg@dpg-d6o0vb94tr6s73eer1vg-a.singapore-postgres.render.com/findash_db_bzrx'

try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    try:
        cur.execute("ALTER TABLE income ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        print("✅ Added created_at to income table")
    except Exception as e:
        if "already exists" in str(e):
            print("ℹ️  created_at already exists in income table")
        conn.rollback()
    
    try:
        cur.execute("ALTER TABLE expenses ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        print("✅ Added created_at to expenses table")
    except Exception as e:
        if "already exists" in str(e):
            print("ℹ️  created_at already exists in expenses table")
        conn.rollback()
    
    cur.execute("UPDATE income SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL")
    print(f"✅ Updated {cur.rowcount} income records")
    
    cur.execute("UPDATE expenses SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL")
    print(f"✅ Updated {cur.rowcount} expense records")
    
    conn.commit()
    cur.close()
    conn.close()
    
    print("\n🎉 Database updated successfully!")
    
except Exception as e:
    print(f"❌ Error: {e}")