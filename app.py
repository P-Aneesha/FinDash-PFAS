from flask import Flask, render_template, request, jsonify, session, redirect
from flask_bcrypt import Bcrypt
from functools import wraps
import psycopg2
import psycopg2.extras
import os
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'change-this-secret-key-to-something-random-and-secure'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

bcrypt = Bcrypt(app)

def get_db():
    """Connect to PostgreSQL database"""
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    if not DATABASE_URL:
        print("⚠️ WARNING: DATABASE_URL not found! Using default...")
        DATABASE_URL = 'postgresql://findash_user:FJE5YrxJCRvcS7ovmOUEyVIydhF3C3Vg@dpg-d6o0vb94tr6s73eer1vg-a.singapore-postgres.render.com/findash_db_bzrx'
    
    print(f"🔌 Connecting to: {DATABASE_URL[:30]}...")
    conn = psycopg2.connect(DATABASE_URL)
    conn.cursor_factory = psycopg2.extras.RealDictCursor
    return conn

def close_db(conn):
    """Safely close database connection"""
    try:
        if conn:
            conn.close()
    except:
        pass

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Login required'}), 401
        return f(*args, **kwargs)
    return decorated

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/api/register', methods=['POST'])
def register():
    conn = None
    try:
        data = request.json
        conn = get_db()
        c = conn.cursor()
        
        c.execute('SELECT * FROM users WHERE username = %s', (data['username'],))
        if c.fetchone():
            return jsonify({'success': False, 'message': 'User exists'}), 400
        
        pw = bcrypt.generate_password_hash(data['password']).decode('utf-8')
        c.execute('''
            INSERT INTO users (username, email, password_hash, full_name) 
            VALUES (%s, %s, %s, %s) RETURNING id
        ''', (data['username'], data['email'], pw, data.get('full_name', '')))
        
        uid = c.fetchone()['id']
        conn.commit()
        
        session['user_id'] = uid
        session['username'] = data['username']
        return jsonify({'success': True})
    except Exception as e:
        print(f"❌ Register error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        close_db(conn)

@app.route('/api/login', methods=['POST'])
def login():
    conn = None
    try:
        data = request.json
        conn = get_db()
        c = conn.cursor()
        
        c.execute('SELECT * FROM users WHERE username = %s', (data['username'],))
        user = c.fetchone()
        
        if user and bcrypt.check_password_hash(user['password_hash'], data['password']):
            session.permanent = True
            session['user_id'] = user['id']
            session['username'] = user['username']
            return jsonify({'success': True})
        
        print(f"❌ Login failed for username: {data.get('username')}")
        return jsonify({'success': False, 'message': 'Invalid username or password'}), 401
    except Exception as e:
        print(f"❌ Login error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        close_db(conn)

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})

@app.route('/api/current-user')
def current_user():
    if 'user_id' in session:
        return jsonify({'logged_in': True, 'username': session['username']})
    return jsonify({'logged_in': False})

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('index.html')

@app.route('/api/income', methods=['POST'])
@login_required
def add_income():
    conn = None
    try:
        data = request.json
        conn = get_db()
        c = conn.cursor()
        
        c.execute('''
            INSERT INTO income (source, amount, date, user_id) 
            VALUES (%s, %s, %s, %s)
        ''', (data['source'], float(data['amount']), data['date'], session['user_id']))
        
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        print(f"❌ Add income error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        close_db(conn)

@app.route('/api/expense', methods=['POST'])
@login_required
def add_expense():
    conn = None
    try:
        data = request.json
        dt = datetime.strptime(data['date'], '%Y-%m-%d')
        day_type = 'weekend' if dt.weekday() >= 5 else 'weekday'
        
        conn = get_db()
        c = conn.cursor()
        
        c.execute('''
            INSERT INTO expenses (category, amount, description, date, day_type, user_id) 
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (data['category'], float(data['amount']), data.get('description', ''), 
              data['date'], day_type, session['user_id']))
        
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        print(f"❌ Add expense error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        close_db(conn)

@app.route('/api/budget', methods=['POST'])
@login_required
def set_budget():
    conn = None
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data received'}), 400
        
        category = data.get('category', '').strip()
        amount = data.get('amount')
        
        if not category or not amount:
            return jsonify({'success': False, 'error': 'Category and amount required'}), 400
        
        amount = float(amount)
        if amount <= 0:
            return jsonify({'success': False, 'error': 'Amount must be positive'}), 400
        
        user_id = session.get('user_id')
        conn = get_db()
        c = conn.cursor()
        
        c.execute('SELECT id FROM budgets WHERE category = %s AND user_id = %s', 
                  (category, user_id))
        existing = c.fetchone()
        
        if existing:
            c.execute('''
                UPDATE budgets 
                SET monthly_limit = %s 
                WHERE category = %s AND user_id = %s
            ''', (amount, category, user_id))
        else:
            c.execute('''
                INSERT INTO budgets (category, monthly_limit, user_id)
                VALUES (%s, %s, %s)
            ''', (category, amount, user_id))
        
        conn.commit()
        return jsonify({'success': True, 'message': 'Budget set successfully'}), 200
    except Exception as e:
        print(f"❌ Budget error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        close_db(conn)

# Add ALL other routes here (dashboard, transactions, budgets, goals, etc.)
# I'll provide them if needed, but first let's test if PostgreSQL is working

if __name__ == '__main__':
    print("🚀 FinDash starting...")
    print("📍 Open: http://localhost:5000")
    app.run(host='0.0.0.0', debug=True, port=5000)