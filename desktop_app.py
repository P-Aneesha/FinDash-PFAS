import webview
import threading
import time
import os
import sys
from flask import Flask, render_template, request, jsonify
import sqlite3
from datetime import datetime

# Get the correct base path (works for both .py and .exe)
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    BASE_DIR = sys._MEIPASS
else:
    # Running as script
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Create Flask app
app = Flask(__name__,
            template_folder=os.path.join(BASE_DIR, 'templates'),
            static_folder=os.path.join(BASE_DIR, 'static'))

# Database path
DB_PATH = os.path.join(BASE_DIR, 'database', 'finance.db')

# Copy database to writable location if running as exe
if getattr(sys, 'frozen', False):
    import shutil
    WRITABLE_DB_PATH = os.path.join(os.path.expanduser('~'), 'FinDash-PFAS', 'finance.db')
    os.makedirs(os.path.dirname(WRITABLE_DB_PATH), exist_ok=True)
    
    if not os.path.exists(WRITABLE_DB_PATH):
        if os.path.exists(DB_PATH):
            shutil.copy(DB_PATH, WRITABLE_DB_PATH)
        else:
            # Create new database if doesn't exist
            conn = sqlite3.connect(WRITABLE_DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute('''CREATE TABLE IF NOT EXISTS income (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                amount REAL NOT NULL,
                date TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
            
            cursor.execute('''CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                amount REAL NOT NULL,
                description TEXT,
                date TEXT NOT NULL,
                day_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
            
            cursor.execute('''CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal_name TEXT NOT NULL,
                target_amount REAL NOT NULL,
                current_savings REAL DEFAULT 0,
                target_date TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
            
            cursor.execute('''CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL UNIQUE,
                monthly_limit REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
            
            conn.commit()
            conn.close()
    
    DB_PATH = WRITABLE_DB_PATH

# Database helper function
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Import routes from your original app.py
# We'll define the main routes here
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/dashboard', methods=['GET'])
def get_dashboard_data():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT SUM(amount) as total FROM income')
    total_income = cursor.fetchone()['total'] or 0
    
    cursor.execute('SELECT SUM(amount) as total FROM expenses')
    total_expenses = cursor.fetchone()['total'] or 0
    
    cursor.execute('SELECT category, SUM(amount) as total FROM expenses GROUP BY category')
    category_data = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute('SELECT day_type, SUM(amount) as total FROM expenses GROUP BY day_type')
    day_type_data = [dict(row) for row in cursor.fetchall()]
    
    balance = total_income - total_expenses
    savings_rate = (balance / total_income * 100) if total_income > 0 else 0
    
    if savings_rate >= 30:
        health_score = min(100, 70 + savings_rate)
    elif savings_rate >= 10:
        health_score = 50 + savings_rate * 2
    else:
        health_score = max(0, savings_rate * 5)
    
    conn.close()
    
    return jsonify({
        'total_income': total_income,
        'total_expenses': total_expenses,
        'balance': balance,
        'category_data': category_data,
        'day_type_data': day_type_data,
        'health_score': round(health_score, 2),
        'savings_rate': round(savings_rate, 2)
    })

# Add other routes from app.py here
@app.route('/api/income', methods=['POST'])
def add_income():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO income (source, amount, date) VALUES (?, ?, ?)',
                   (data['source'], data['amount'], data['date']))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Income added'})

@app.route('/api/expense', methods=['POST'])
def add_expense():
    data = request.json
    date_obj = datetime.strptime(data['date'], '%Y-%m-%d')
    day_type = 'weekend' if date_obj.weekday() >= 5 else 'weekday'
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO expenses (category, amount, description, date, day_type) VALUES (?, ?, ?, ?, ?)',
                   (data['category'], data['amount'], data.get('description', ''), data['date'], day_type))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Expense added'})

@app.route('/api/recommendations', methods=['GET'])
def get_recommendations():
    conn = get_db_connection()
    cursor = conn.cursor()
    recommendations = []
    
    cursor.execute('''SELECT 
        SUM(CASE WHEN day_type='weekend' THEN amount ELSE 0 END) as weekend,
        SUM(CASE WHEN day_type='weekday' THEN amount ELSE 0 END) as weekday
        FROM expenses''')
    result = cursor.fetchone()
    
    if result['weekend'] and result['weekday']:
        if result['weekend'] > result['weekday'] * 0.5:
            excess = result['weekend'] - (result['weekday'] * 0.5)
            recommendations.append({
                'type': 'warning',
                'message': f'You spend ₹{excess:.2f} more on weekends!'
            })
    
    cursor.execute('SELECT category, SUM(amount) as total FROM expenses GROUP BY category ORDER BY total DESC LIMIT 1')
    top = cursor.fetchone()
    if top:
        recommendations.append({
            'type': 'info',
            'message': f'Highest spending: {top["category"]} - ₹{top["total"]:.2f}'
        })
    
    conn.close()
    return jsonify({'recommendations': recommendations})

def start_flask():
    """Start Flask server"""
    app.run(debug=False, port=5000, use_reloader=False, threaded=True)

def main():
    print("Starting FinDash-PFAS Desktop App...")
    print(f"Database location: {DB_PATH}")
    print(f"Base directory: {BASE_DIR}")
    
    # Start Flask
    flask_thread = threading.Thread(target=start_flask, daemon=True)
    flask_thread.start()
    
    # Wait for Flask to start
    time.sleep(3)
    
    # Create window
    webview.create_window(
        title='FinDash-PFAS - Financial Dashboard',
        url='http://localhost:5000',
        width=1400,
        height=900,
        resizable=True,
        fullscreen=False,
        min_size=(800, 600)
    )
    
    webview.start()

if __name__ == '__main__':
    main()