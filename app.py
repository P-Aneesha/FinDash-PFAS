from flask import Flask, render_template, request, jsonify, session, redirect
from flask_bcrypt import Bcrypt
from flask_mail import Mail, Message
from functools import wraps
import sqlite3
import secrets
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'change-this-secret-key-to-something-random-and-secure'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

# Email configuration (Gmail)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your-email@gmail.com'  # ⚠️ CHANGE THIS
app.config['MAIL_PASSWORD'] = 'your-app-password-here'  # ⚠️ CHANGE THIS (use Gmail App Password)
app.config['MAIL_DEFAULT_SENDER'] = 'your-email@gmail.com'  # ⚠️ CHANGE THIS

bcrypt = Bcrypt(app)
mail = Mail(app)
def get_db():
    conn = sqlite3.connect('database/finance.db', timeout=30.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL')
    return conn

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
    data = request.json
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username = ?', (data['username'],))
    if c.fetchone():
        conn.close()
        return jsonify({'success': False, 'message': 'User exists'}), 400
    
    pw = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    c.execute('INSERT INTO users (username, email, password_hash, full_name) VALUES (?, ?, ?, ?)',
              (data['username'], data['email'], pw, data.get('full_name', '')))
    conn.commit()
    uid = c.lastrowid
    conn.close()
    
    session['user_id'] = uid
    session['username'] = data['username']
    return jsonify({'success': True})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username = ?', (data['username'],))
    user = c.fetchone()
    conn.close()
    
    if user and bcrypt.check_password_hash(user['password_hash'], data['password']):
        session.permanent = True  # Make session last longer
        session['user_id'] = user['id']
        session['username'] = user['username']
        return jsonify({'success': True})
    
    print(f"❌ Login failed for username: {data.get('username')}")  # Debug
    return jsonify({'success': False, 'message': 'Invalid username or password'}), 401

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
    data = request.json
    conn = get_db()
    c = conn.cursor()
    c.execute('INSERT INTO income (source, amount, date, user_id) VALUES (?, ?, ?, ?)',
              (data['source'], float(data['amount']), data['date'], session['user_id']))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/expense', methods=['POST'])
@login_required
def add_expense():
    data = request.json
    dt = datetime.strptime(data['date'], '%Y-%m-%d')
    day_type = 'weekend' if dt.weekday() >= 5 else 'weekday'
    conn = get_db()
    c = conn.cursor()
    c.execute('INSERT INTO expenses (category, amount, description, date, day_type, user_id) VALUES (?, ?, ?, ?, ?, ?)',
              (data['category'], float(data['amount']), data.get('description', ''), data['date'], day_type, session['user_id']))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/budget', methods=['POST'])
@login_required
def set_budget():
    """Set or update budget for a category"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data received'}), 400
        
        category = data.get('category', '').strip()
        amount = data.get('amount')
        
        print(f"DEBUG Budget: category={category}, amount={amount}")
        
        if not category:
            return jsonify({'success': False, 'error': 'Category is required'}), 400
        
        if not amount:
            return jsonify({'success': False, 'error': 'Amount is required'}), 400
        
        try:
            amount = float(amount)
        except (ValueError, TypeError):
            return jsonify({'success': False, 'error': 'Invalid amount format'}), 400
        
        if amount <= 0:
            return jsonify({'success': False, 'error': 'Amount must be positive'}), 400
        
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'success': False, 'error': 'Not logged in'}), 401
        
        conn = get_db()
        c = conn.cursor()
        
        # Check if budget exists
        c.execute('SELECT id FROM budgets WHERE category = ? AND user_id = ?', (category, user_id))
        existing = c.fetchone()
        
        if existing:
            # UPDATE existing budget
            print(f"Updating existing budget for {category}")
            c.execute('''
                UPDATE budgets 
                SET monthly_limit = ? 
                WHERE category = ? AND user_id = ?
            ''', (amount, category, user_id))
        else:
            # INSERT new budget
            print(f"Creating new budget for {category}")
            c.execute('''
                INSERT INTO budgets (category, monthly_limit, user_id)
                VALUES (?, ?, ?)
            ''', (category, amount, user_id))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Budget set successfully: {category} = ₹{amount}")
        return jsonify({'success': True, 'message': 'Budget set successfully'}), 200
        
    except Exception as e:
        print(f"❌ Budget error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/dashboard')
@login_required
def dashboard():
    conn = get_db()
    c = conn.cursor()
    uid = session['user_id']
    
    c.execute('SELECT SUM(amount) as total FROM income WHERE user_id = ?', (uid,))
    inc = c.fetchone()['total'] or 0
    
    c.execute('SELECT SUM(amount) as total FROM expenses WHERE user_id = ?', (uid,))
    exp = c.fetchone()['total'] or 0
    
    c.execute('SELECT category, SUM(amount) as total FROM expenses WHERE user_id = ? GROUP BY category', (uid,))
    cats = [dict(r) for r in c.fetchall()]
    
    c.execute('SELECT day_type, SUM(amount) as total FROM expenses WHERE user_id = ? GROUP BY day_type', (uid,))
    days = [dict(r) for r in c.fetchall()]
    
    conn.close()
    
    bal = inc - exp
    rate = (bal / inc * 100) if inc > 0 else 0
    score = min(100, 70 + rate) if rate >= 30 else (50 + rate * 2 if rate >= 10 else max(0, rate * 5))
    
    return jsonify({
        'total_income': inc,
        'total_expenses': exp,
        'balance': bal,
        'category_data': cats,
        'day_type_data': days,
        'health_score': round(score, 2)
    })

@app.route('/api/transactions')
@login_required
def transactions():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT id, source as description, amount, date, "Income" as type FROM income WHERE user_id = ?', (session['user_id'],))
    inc = [dict(r) for r in c.fetchall()]
    c.execute('SELECT id, category, amount, date, description, "Expense" as type FROM expenses WHERE user_id = ?', (session['user_id'],))
    exp = [dict(r) for r in c.fetchall()]
    
    exps = [{'id': e['id'], 'description': f"{e['category']} - {e['description']}" if e['description'] else e['category'],
             'amount': e['amount'], 'date': e['date'], 'type': e['type']} for e in exp]
    
    all_t = inc + exps
    all_t.sort(key=lambda x: x['date'], reverse=True)
    conn.close()
    return jsonify({'transactions': all_t})

@app.route('/api/budgets')
@login_required
def budgets():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM budgets WHERE user_id = ?', (session['user_id'],))
    buds = [dict(r) for r in c.fetchall()]
    
    first = datetime.now().replace(day=1).strftime('%Y-%m-%d')
    c.execute('SELECT category, SUM(amount) as spent FROM expenses WHERE date >= ? AND user_id = ? GROUP BY category',
              (first, session['user_id']))
    spend = {r['category']: r['spent'] for r in c.fetchall()}
    
    result = []
    for b in buds:
        s = spend.get(b['category'], 0)
        p = (s / b['monthly_limit'] * 100) if b['monthly_limit'] > 0 else 0
        st = 'exceeded' if p >= 100 else ('warning' if p >= 80 else 'safe')
        result.append({'id': b['id'], 'category': b['category'], 'monthly_limit': b['monthly_limit'],
                      'spent': round(s, 2), 'remaining': round(b['monthly_limit'] - s, 2),
                      'percentage': round(p, 2), 'status': st})
    
    conn.close()
    return jsonify({'budgets': result})

@app.route('/api/income/<int:iid>', methods=['DELETE'])
@login_required
def del_income(iid):
    conn = get_db()
    c = conn.cursor()
    c.execute('DELETE FROM income WHERE id = ? AND user_id = ?', (iid, session['user_id']))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/expense/<int:eid>', methods=['DELETE'])
@login_required
def del_expense(eid):
    conn = get_db()
    c = conn.cursor()
    c.execute('DELETE FROM expenses WHERE id = ? AND user_id = ?', (eid, session['user_id']))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/budget/<int:bid>', methods=['DELETE'])
@login_required
def del_budget(bid):
    conn = get_db()
    c = conn.cursor()
    c.execute('DELETE FROM budgets WHERE id = ? AND user_id = ?', (bid, session['user_id']))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/goal', methods=['POST'])
@login_required
def add_goal():
    data = request.json
    conn = get_db()
    c = conn.cursor()
    c.execute('INSERT INTO goals (goal_name, target_amount, target_date, current_savings, user_id) VALUES (?, ?, ?, ?, ?)',
              (data['goal_name'], float(data['target_amount']), data['target_date'], 
               float(data.get('current_savings', 0)), session['user_id']))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/goals')
@login_required
def get_goals():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM goals WHERE user_id = ? ORDER BY created_at DESC', (session['user_id'],))
    goals = [dict(r) for r in c.fetchall()]
    
    for g in goals:
        if g['target_date']:
            td = datetime.strptime(g['target_date'], '%Y-%m-%d')
            now = datetime.now()
            months = max(1, ((td.year - now.year) * 12 + (td.month - now.month)))
            remaining = g['target_amount'] - g['current_savings']
            g['months_remaining'] = months
            g['monthly_savings_needed'] = round(remaining / months, 2)
            g['remaining_amount'] = round(remaining, 2)
            g['progress_percentage'] = round((g['current_savings'] / g['target_amount'] * 100), 2)
    
    conn.close()
    return jsonify({'goals': goals})

@app.route('/api/goal/<int:gid>', methods=['DELETE'])
@login_required
def delete_goal(gid):
    conn = get_db()
    c = conn.cursor()
    c.execute('DELETE FROM goals WHERE id = ? AND user_id = ?', (gid, session['user_id']))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/goal/<int:gid>/update', methods=['PUT'])
@login_required
def update_goal(gid):
    data = request.json
    conn = get_db()
    c = conn.cursor()
    c.execute('UPDATE goals SET current_savings = current_savings + ? WHERE id = ? AND user_id = ?',
              (float(data['amount']), gid, session['user_id']))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/statistics')
@login_required
def get_statistics():
    conn = get_db()
    c = conn.cursor()
    uid = session['user_id']
    
    c.execute('SELECT COUNT(*) as c FROM income WHERE user_id = ?', (uid,))
    inc_count = c.fetchone()['c']
    c.execute('SELECT COUNT(*) as c FROM expenses WHERE user_id = ?', (uid,))
    exp_count = c.fetchone()['c']
    
    c.execute('SELECT COUNT(*) as c FROM goals WHERE user_id = ?', (uid,))
    goal_count = c.fetchone()['c']
    
    c.execute('SELECT COUNT(*) as c FROM budgets WHERE user_id = ?', (uid,))
    budget_count = c.fetchone()['c']
    
    c.execute('SELECT category, SUM(amount) as total FROM expenses WHERE user_id = ? GROUP BY category ORDER BY total DESC LIMIT 1', (uid,))
    top = c.fetchone()
    
    c.execute('SELECT AVG(total) as avg FROM (SELECT SUM(amount) as total FROM income WHERE user_id = ? GROUP BY strftime("%Y-%m", date))', (uid,))
    avg_inc = c.fetchone()['avg'] or 0
    
    c.execute('SELECT AVG(total) as avg FROM (SELECT SUM(amount) as total FROM expenses WHERE user_id = ? GROUP BY strftime("%Y-%m", date))', (uid,))
    avg_exp = c.fetchone()['avg'] or 0
    
    today = datetime.now()
    first_this = today.replace(day=1).strftime('%Y-%m-%d')
    first_last = (today.replace(day=1) - timedelta(days=1)).replace(day=1).strftime('%Y-%m-%d')
    last_day_last = today.replace(day=1) - timedelta(days=1)
    
    c.execute('SELECT SUM(amount) as total FROM expenses WHERE date >= ? AND user_id = ?', (first_this, uid))
    this_month = c.fetchone()['total'] or 0
    
    c.execute('SELECT SUM(amount) as total FROM expenses WHERE date >= ? AND date < ? AND user_id = ?', 
              (first_last, first_this, uid))
    last_month = c.fetchone()['total'] or 0
    
    change = ((this_month - last_month) / last_month * 100) if last_month > 0 else 0
    
    c.execute('SELECT MIN(date) as first FROM (SELECT date FROM income WHERE user_id = ? UNION SELECT date FROM expenses WHERE user_id = ?)', (uid, uid))
    first = c.fetchone()['first']
    days = (today - datetime.strptime(first, '%Y-%m-%d')).days if first else 0
    
    conn.close()
    
    return jsonify({'statistics': {
        'total_transactions': inc_count + exp_count,
        'avg_monthly_income': round(avg_inc, 2),
        'avg_monthly_expenses': round(avg_exp, 2),
        'top_expense_category': top['category'] if top else 'N/A',
        'top_expense_amount': round(top['total'], 2) if top else 0,
        'days_tracking': days,
        'total_goals': goal_count,
        'total_budgets': budget_count,
        'this_month_expense': round(this_month, 2),
        'last_month_expense': round(last_month, 2),
        'month_over_month_change': round(change, 2)
    }})

@app.route('/api/recommendations')
@login_required
def get_recommendations():
    conn = get_db()
    c = conn.cursor()
    uid = session['user_id']
    recs = []
    
    c.execute('SELECT SUM(CASE WHEN day_type="weekend" THEN amount ELSE 0 END) as weekend, SUM(CASE WHEN day_type="weekday" THEN amount ELSE 0 END) as weekday FROM expenses WHERE user_id = ?', (uid,))
    r = c.fetchone()
    
    if r['weekend'] and r['weekday'] and r['weekend'] > r['weekday'] * 0.5:
        excess = r['weekend'] - (r['weekday'] * 0.5)
        recs.append({'type': 'warning', 'message': f'You spend ₹{excess:.2f} more on weekends!'})
    
    c.execute('SELECT category, SUM(amount) as total FROM expenses WHERE user_id = ? GROUP BY category ORDER BY total DESC LIMIT 1', (uid,))
    top = c.fetchone()
    if top:
        recs.append({'type': 'info', 'message': f'Top spending: {top["category"]} - ₹{top["total"]:.2f}'})
    
    c.execute('SELECT SUM(amount) as total FROM income WHERE user_id = ?', (uid,))
    inc = c.fetchone()['total'] or 0
    c.execute('SELECT SUM(amount) as total FROM expenses WHERE user_id = ?', (uid,))
    exp = c.fetchone()['total'] or 0
    
    if inc > 0:
        rate = ((inc - exp) / inc) * 100
        if rate < 10:
            recs.append({'type': 'danger', 'message': f'Savings rate is only {rate:.1f}%. Try to save at least 10%!'})
    
    conn.close()
    return jsonify({'recommendations': recs})

@app.route('/api/budget-alerts')
@login_required
def get_budget_alerts():
    conn = get_db()
    c = conn.cursor()
    uid = session['user_id']
    
    first = datetime.now().replace(day=1).strftime('%Y-%m-%d')
    
    c.execute('SELECT * FROM budgets WHERE user_id = ?', (uid,))
    buds = [dict(r) for r in c.fetchall()]
    
    c.execute('SELECT category, SUM(amount) as spent FROM expenses WHERE date >= ? AND user_id = ? GROUP BY category', (first, uid))
    spend = {r['category']: r['spent'] for r in c.fetchall()}
    
    alerts = []
    for b in buds:
        s = spend.get(b['category'], 0)
        p = (s / b['monthly_limit'] * 100) if b['monthly_limit'] > 0 else 0
        
        if p >= 100:
            alerts.append({'type': 'danger', 'message': f"🚨 {b['category']} budget exceeded!"})
        elif p >= 80:
            alerts.append({'type': 'warning', 'message': f"⚠️ {b['category']}: {p:.0f}% used"})
    
    conn.close()
    return jsonify({'alerts': alerts})

@app.route('/api/trends')
@login_required
def get_trends():
    conn = get_db()
    c = conn.cursor()
    uid = session['user_id']
    
    today = datetime.now()
    six_ago = today - timedelta(days=180)
    
    c.execute('SELECT strftime("%Y-%m", date) as month, SUM(amount) as total FROM income WHERE date >= ? AND user_id = ? GROUP BY month', (six_ago.strftime('%Y-%m-%d'), uid))
    inc_m = {r['month']: r['total'] for r in c.fetchall()}
    
    c.execute('SELECT strftime("%Y-%m", date) as month, SUM(amount) as total FROM expenses WHERE date >= ? AND user_id = ? GROUP BY month', (six_ago.strftime('%Y-%m-%d'), uid))
    exp_m = {r['month']: r['total'] for r in c.fetchall()}
    
    months, inc_data, exp_data, sav_data = [], [], [], []
    
    for i in range(6):
        md = today - timedelta(days=30 * (5 - i))
        mk = md.strftime('%Y-%m')
        ml = md.strftime('%b %Y')
        months.append(ml)
        inc = inc_m.get(mk, 0)
        exp = exp_m.get(mk, 0)
        inc_data.append(round(inc, 2))
        exp_data.append(round(exp, 2))
        sav_data.append(round(inc - exp, 2))
    
    conn.close()
    return jsonify({'months': months, 'income': inc_data, 'expenses': exp_data, 'savings': sav_data})

@app.route('/api/sms-transaction', methods=['POST'])
def sms_transaction():
    """Auto-add transaction from SMS"""
    try:
        data = request.get_json()
        trans_type = data.get('type')
        amount = float(data.get('amount'))
        description = data.get('description', 'Auto from SMS')
        category = data.get('category', 'Others')
        date = data.get('date')
        
        conn = get_db()
        
        if trans_type == 'income':
            conn.execute('''
                INSERT INTO income (source, amount, date, user_id)
                VALUES (?, ?, ?, 1)
            ''', (description, amount, date))
        else:
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            day_type = 'weekend' if date_obj.weekday() >= 5 else 'weekday'
            
            conn.execute('''
                INSERT INTO expenses (category, amount, description, date, day_type, user_id)
                VALUES (?, ?, ?, ?, ?, 1)
            ''', (category, amount, description, date, day_type))
        
        conn.commit()
        conn.close()
        
        print(f"✅ SMS: {trans_type} ₹{amount} - {description}")
        return jsonify({'success': True}), 200
        
    except Exception as e:
        print(f"❌ SMS error: {str(e)}")
        return jsonify({'success': False}), 500

@app.route('/api/parse-sms', methods=['POST'])
@login_required
def parse_sms():
    """Parse bank SMS and extract transaction details"""
    try:
        data = request.get_json()
        sms_text = data.get('sms', '')
        
        if not sms_text:
            return jsonify({'success': False, 'error': 'No SMS text provided'}), 400
        
        # Determine transaction type
        lower_sms = sms_text.lower()
        if 'debited' in lower_sms or 'withdrawn' in lower_sms or 'paid' in lower_sms:
            trans_type = 'expense'
        elif 'credited' in lower_sms or 'deposited' in lower_sms or 'received' in lower_sms:
            trans_type = 'income'
        else:
            return jsonify({'success': False, 'error': 'Could not determine transaction type'}), 400
        
        # Extract amount
        import re
        amount_pattern = r'(?:rs\.?|inr|₹)\s*([0-9,]+\.?[0-9]*)'
        amount_match = re.search(amount_pattern, sms_text, re.IGNORECASE)
        
        if not amount_match:
            return jsonify({'success': False, 'error': 'Could not extract amount'}), 400
        
        amount = float(amount_match.group(1).replace(',', ''))
        
        # Extract merchant/description
        merchant_pattern = r'(?:at|to)\s+([A-Z][A-Za-z\s&]+?)(?:on|\.|avl|upi|info|ref)'
        merchant_match = re.search(merchant_pattern, sms_text, re.IGNORECASE)
        
        if merchant_match:
            description = merchant_match.group(1).strip()
        else:
            description = 'Bank Transaction'
        
        # Auto-categorize
        desc_lower = description.lower()
        if 'amazon' in desc_lower or 'flipkart' in desc_lower or 'shop' in desc_lower:
            category = 'Shopping'
        elif 'swiggy' in desc_lower or 'zomato' in desc_lower or 'food' in desc_lower:
            category = 'Food'
        elif 'uber' in desc_lower or 'ola' in desc_lower or 'metro' in desc_lower:
            category = 'Transportation'
        elif 'salary' in desc_lower or 'transfer' in desc_lower:
            category = 'Salary'
        else:
            category = 'Others'
        
        # Get current date
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        return jsonify({
            'success': True,
            'type': trans_type,
            'amount': amount,
            'description': description,
            'category': category,
            'date': current_date
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
@app.route('/api/forgot-password', methods=['POST'])
def forgot_password():
    """Send password reset email"""
    try:
        data = request.json
        email = data.get('email', '').strip()
        
        if not email:
            return jsonify({'success': False, 'error': 'Email is required'}), 400
        
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT id, username FROM users WHERE email = ?', (email,))
        user = c.fetchone()
        
        if not user:
            # Don't reveal if email exists or not (security)
            return jsonify({'success': True, 'message': 'If that email exists, a reset link has been sent'}), 200
        
        # Generate reset token
        reset_token = secrets.token_urlsafe(32)
        expiry = (datetime.now() + timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S')
        
        # Store token in database
        c.execute('''
            UPDATE users 
            SET reset_token = ?, reset_token_expiry = ? 
            WHERE id = ?
        ''', (reset_token, expiry, user['id']))
        conn.commit()
        conn.close()
        
        # Send email
        reset_url = f"https://findash-pfas.onrender.com/reset-password?token={reset_token}"
        
        msg = Message(
            'FinDash - Password Reset Request',
            recipients=[email]
        )
        msg.body = f'''Hello {user['username']},

You requested to reset your password for FinDash.

Click the link below to reset your password:
{reset_url}

This link will expire in 1 hour.

If you didn't request this, please ignore this email.

- FinDash Team
'''
        msg.html = f'''
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <h2 style="color: #667eea;">FinDash - Password Reset</h2>
    <p>Hello <strong>{user['username']}</strong>,</p>
    <p>You requested to reset your password for FinDash.</p>
    <p>Click the button below to reset your password:</p>
    <a href="{reset_url}" style="display: inline-block; padding: 12px 24px; background-color: #667eea; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0;">Reset Password</a>
    <p><small>Or copy this link: {reset_url}</small></p>
    <p><small>This link will expire in 1 hour.</small></p>
    <p>If you didn't request this, please ignore this email.</p>
    <p>- FinDash Team 💰</p>
</body>
</html>
'''
        
        mail.send(msg)
        
        return jsonify({'success': True, 'message': 'If that email exists, a reset link has been sent'}), 200
        
    except Exception as e:
        print(f"❌ Forgot password error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': 'Failed to send reset email'}), 500


@app.route('/reset-password')
def reset_password_page():
    """Show password reset page"""
    token = request.args.get('token')
    if not token:
        return "Invalid reset link", 400
    return render_template('reset_password.html', token=token)


@app.route('/api/reset-password', methods=['POST'])
def reset_password():
    """Reset password with token"""
    try:
        data = request.json
        token = data.get('token', '').strip()
        new_password = data.get('password', '').strip()
        
        if not token or not new_password:
            return jsonify({'success': False, 'error': 'Token and password are required'}), 400
        
        if len(new_password) < 6:
            return jsonify({'success': False, 'error': 'Password must be at least 6 characters'}), 400
        
        conn = get_db()
        c = conn.cursor()
        
        # Find user with this token
        c.execute('''
            SELECT id, reset_token_expiry 
            FROM users 
            WHERE reset_token = ?
        ''', (token,))
        user = c.fetchone()
        
        if not user:
            conn.close()
            return jsonify({'success': False, 'error': 'Invalid or expired reset link'}), 400
        
        # Check if token expired
        expiry = datetime.strptime(user['reset_token_expiry'], '%Y-%m-%d %H:%M:%S')
        if datetime.now() > expiry:
            conn.close()
            return jsonify({'success': False, 'error': 'Reset link has expired'}), 400
        
        # Update password
        new_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
        c.execute('''
            UPDATE users 
            SET password_hash = ?, reset_token = NULL, reset_token_expiry = NULL 
            WHERE id = ?
        ''', (new_hash, user['id']))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Password reset successful! You can now login.'}), 200
        
    except Exception as e:
        print(f"❌ Reset password error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': 'Failed to reset password'}), 500
if __name__ == '__main__':
    print("🚀 FinDash starting...")
    print("📍 Open: http://localhost:5000")
    import socket
    ip = socket.gethostbyname(socket.gethostname())
    print(f"📱 Mobile: http://{ip}:5000")
    app.run(host='0.0.0.0', debug=True, port=5000)