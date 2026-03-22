from flask import Flask, render_template, request, jsonify, session, redirect
from flask_bcrypt import Bcrypt
from functools import wraps
import psycopg2
import psycopg2.extras
import os
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'change-this-secret-key-to-something-random-and-secure'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

bcrypt = Bcrypt(app)

def get_db():
    # Use Render's PostgreSQL database directly
    DATABASE_URL = 'postgresql://findash_user:FJE5YrxJCRvcS7ovmOUEyVIydhF3C3Vg@dpg-d6o0vb94tr6s73eer1vg-a.singapore-postgres.render.com/findash_db_bzrx'
    
    conn = psycopg2.connect(DATABASE_URL)
    conn.cursor_factory = psycopg2.extras.RealDictCursor
    return conn

def close_db(conn):
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

@app.route('/api/dashboard')
@login_required
def dashboard():
    conn = None
    try:
        conn = get_db()
        c = conn.cursor()
        uid = session['user_id']
        
        c.execute('SELECT COALESCE(SUM(amount), 0) as total FROM income WHERE user_id = %s', (uid,))
        inc = c.fetchone()['total']
        
        c.execute('SELECT COALESCE(SUM(amount), 0) as total FROM expenses WHERE user_id = %s', (uid,))
        exp = c.fetchone()['total']
        
        c.execute('''
            SELECT category, SUM(amount) as total 
            FROM expenses 
            WHERE user_id = %s 
            GROUP BY category
        ''', (uid,))
        cats = [dict(r) for r in c.fetchall()]
        
        days = []
        
        bal = float(inc) - float(exp)
        rate = (bal / float(inc) * 100) if float(inc) > 0 else 0
        score = min(100, 70 + rate) if rate >= 30 else (50 + rate * 2 if rate >= 10 else max(0, rate * 5))
        
        return jsonify({
            'total_income': float(inc),
            'total_expenses': float(exp),
            'balance': bal,
            'category_data': [{'category': r['category'], 'total': round(float(r['total']),2)} for r in cats],
            'day_type_data': days,
            'health_score': round(score, 2)
        })
    except Exception as e:
        print(f"❌ Dashboard error: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        close_db(conn)

@app.route('/api/transactions')
@login_required
def transactions():
    conn = None
    try:
        conn = get_db()
        c = conn.cursor()
        
        c.execute('''
            SELECT id, source as description, amount, date, created_at, 'Income' as type 
            FROM income 
            WHERE user_id = %s
        ''', (session['user_id'],))
        inc = [dict(r) for r in c.fetchall()]
        
        c.execute('''
            SELECT id, category, amount, date, description, created_at, 'Expense' as type 
            FROM expenses 
            WHERE user_id = %s
        ''', (session['user_id'],))
        exp = [dict(r) for r in c.fetchall()]
        
        exps = []
        for e in exp:
            desc = f"{e['category']} - {e['description']}" if e['description'] else e['category']
            exps.append({
                'id': e['id'],
                'description': desc,
                'amount': float(e['amount']),
                'date': str(e['date']),
                'created_at': str(e['created_at']) if e['created_at'] else None,
                'type': e['type']
            })
        
        for i in inc:
            i['date'] = str(i['date'])
            i['amount'] = float(i['amount'])
            i['created_at'] = str(i['created_at']) if i.get('created_at') else None
        
        all_t = inc + exps
        all_t.sort(key=lambda x: x['created_at'] or '', reverse=True)
        
        return jsonify({'transactions': all_t})
    except Exception as e:
        print(f"❌ Transactions error: {str(e)}")
        return jsonify({'error': str(e)}), 500
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

@app.route('/api/budgets')
@login_required
def budgets():
    conn = None
    try:
        conn = get_db()
        c = conn.cursor()
        
        c.execute('SELECT * FROM budgets WHERE user_id = %s', (session['user_id'],))
        buds = [dict(r) for r in c.fetchall()]
        
        first = datetime.now().replace(day=1).strftime('%Y-%m-%d')
        c.execute('''
            SELECT category, SUM(amount) as spent 
            FROM expenses 
            WHERE date >= %s AND user_id = %s 
            GROUP BY category
        ''', (first, session['user_id']))
        spend = {r['category']: float(r['spent']) for r in c.fetchall()}
        
        result = []
        for b in buds:
            s = spend.get(b['category'], 0)
            limit = float(b['monthly_limit'])
            p = (s / limit * 100) if limit > 0 else 0
            st = 'exceeded' if p >= 100 else ('warning' if p >= 80 else 'safe')
            result.append({
                'id': b['id'],
                'category': b['category'],
                'monthly_limit': limit,
                'spent': round(s, 2),
                'remaining': round(limit - s, 2),
                'percentage': round(p, 2),
                'status': st
            })
        
        return jsonify({'budgets': result})
    except Exception as e:
        print(f"❌ Budgets error: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        close_db(conn)

@app.route('/api/income/<int:iid>', methods=['DELETE'])
@login_required
def del_income(iid):
    conn = None
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('DELETE FROM income WHERE id = %s AND user_id = %s', (iid, session['user_id']))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        print(f"❌ Delete income error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        close_db(conn)

@app.route('/api/expense/<int:eid>', methods=['DELETE'])
@login_required
def del_expense(eid):
    conn = None
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('DELETE FROM expenses WHERE id = %s AND user_id = %s', (eid, session['user_id']))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        print(f"❌ Delete expense error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        close_db(conn)

@app.route('/api/budget/<int:bid>', methods=['DELETE'])
@login_required
def del_budget(bid):
    conn = None
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('DELETE FROM budgets WHERE id = %s AND user_id = %s', (bid, session['user_id']))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        print(f"❌ Delete budget error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        close_db(conn)

@app.route('/api/goal', methods=['POST'])
@login_required
def add_goal():
    conn = None
    try:
        data = request.json
        conn = get_db()
        c = conn.cursor()
        
        c.execute('''
            INSERT INTO goals (goal_name, target_amount, target_date, current_savings, user_id) 
            VALUES (%s, %s, %s, %s, %s)
        ''', (data['goal_name'], float(data['target_amount']), data['target_date'], 
              float(data.get('current_savings', 0)), session['user_id']))
        
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        print(f"❌ Add goal error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        close_db(conn)

@app.route('/api/goals')
@login_required
def get_goals():
    conn = None
    try:
        conn = get_db()
        c = conn.cursor()
        
        c.execute('SELECT * FROM goals WHERE user_id = %s ORDER BY created_at DESC', 
                  (session['user_id'],))
        goals = [dict(r) for r in c.fetchall()]
        
        for g in goals:
            g['target_amount'] = float(g['target_amount'])
            g['current_savings'] = float(g['current_savings'])
            
            if g['target_date']:
                g['target_date'] = str(g['target_date'])
                td = datetime.strptime(g['target_date'], '%Y-%m-%d')
                now = datetime.now()
                months = max(1, ((td.year - now.year) * 12 + (td.month - now.month)))
                remaining = g['target_amount'] - g['current_savings']
                g['months_remaining'] = months
                g['monthly_savings_needed'] = round(remaining / months, 2)
                g['remaining_amount'] = round(remaining, 2)
                g['progress_percentage'] = round((g['current_savings'] / g['target_amount'] * 100), 2)
        
        return jsonify({'goals': goals})
    except Exception as e:
        print(f"❌ Goals error: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        close_db(conn)

@app.route('/api/goal/<int:gid>', methods=['DELETE'])
@login_required
def delete_goal(gid):
    conn = None
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('DELETE FROM goals WHERE id = %s AND user_id = %s', (gid, session['user_id']))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        print(f"❌ Delete goal error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        close_db(conn)

@app.route('/api/goal/<int:gid>/update', methods=['PUT'])
@login_required
def update_goal(gid):
    conn = None
    try:
        data = request.json
        conn = get_db()
        c = conn.cursor()
        
        c.execute('''
            UPDATE goals 
            SET current_savings = current_savings + %s 
            WHERE id = %s AND user_id = %s
        ''', (float(data['amount']), gid, session['user_id']))
        
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        print(f"❌ Update goal error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        close_db(conn)

@app.route('/api/statistics')
@login_required
def get_statistics():
    conn = None
    try:
        conn = get_db()
        c = conn.cursor()
        uid = session['user_id']
        
        c.execute('SELECT COUNT(*) as c FROM income WHERE user_id = %s', (uid,))
        inc_count = c.fetchone()['c']
        
        c.execute('SELECT COUNT(*) as c FROM expenses WHERE user_id = %s', (uid,))
        exp_count = c.fetchone()['c']
        
        c.execute('SELECT COUNT(*) as c FROM goals WHERE user_id = %s', (uid,))
        goal_count = c.fetchone()['c']
        
        c.execute('SELECT COUNT(*) as c FROM budgets WHERE user_id = %s', (uid,))
        budget_count = c.fetchone()['c']
        
        c.execute('''
            SELECT category, SUM(amount) as total 
            FROM expenses 
            WHERE user_id = %s 
            GROUP BY category 
            ORDER BY total DESC 
            LIMIT 1
        ''', (uid,))
        top = c.fetchone()
        
        c.execute('''
            SELECT AVG(total) as avg 
            FROM (
                SELECT SUM(amount) as total 
                FROM income 
                WHERE user_id = %s 
                GROUP BY TO_CHAR(date, 'YYYY-MM')
            ) AS subq
        ''', (uid,))
        avg_inc = c.fetchone()['avg'] or 0
        
        c.execute('''
            SELECT AVG(total) as avg 
            FROM (
                SELECT SUM(amount) as total 
                FROM expenses 
                WHERE user_id = %s 
                GROUP BY TO_CHAR(date, 'YYYY-MM')
            ) AS subq
        ''', (uid,))
        avg_exp = c.fetchone()['avg'] or 0
        
        today = datetime.now()
        first_this = today.replace(day=1).strftime('%Y-%m-%d')
        first_last = (today.replace(day=1) - timedelta(days=1)).replace(day=1).strftime('%Y-%m-%d')
        
        c.execute('''
            SELECT COALESCE(SUM(amount), 0) as total 
            FROM expenses 
            WHERE date >= %s AND user_id = %s
        ''', (first_this, uid))
        this_month = float(c.fetchone()['total'])
        
        c.execute('''
            SELECT COALESCE(SUM(amount), 0) as total 
            FROM expenses 
            WHERE date >= %s AND date < %s AND user_id = %s
        ''', (first_last, first_this, uid))
        last_month = float(c.fetchone()['total'])
        
        change = ((this_month - last_month) / last_month * 100) if last_month > 0 else 0
        
        c.execute('''
            SELECT MIN(date) as first 
            FROM (
                SELECT date FROM income WHERE user_id = %s 
                UNION 
                SELECT date FROM expenses WHERE user_id = %s
            ) combined
        ''', (uid, uid))
        first = c.fetchone()['first']
        if first:
            if hasattr(first, 'year'):
                days = (today.date() - first).days
            else:
                from datetime import date
                days = (today.date() - date.fromisoformat(str(first))).days
        else:
            days = 0
        
        return jsonify({'statistics': {
            'total_transactions': inc_count + exp_count,
            'avg_monthly_income': round(float(avg_inc), 2),
            'avg_monthly_expenses': round(float(avg_exp), 2),
            'top_expense_category': top['category'] if top else 'N/A',
            'top_expense_amount': round(float(top['total']), 2) if top else 0,
            'days_tracking': days,
            'total_goals': goal_count,
            'total_budgets': budget_count,
            'this_month_expense': round(this_month, 2),
            'last_month_expense': round(last_month, 2),
            'month_over_month_change': round(change, 2)
        }})
    except Exception as e:
        print(f"❌ Statistics error: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        close_db(conn)

@app.route('/api/recommendations')
@login_required
def get_recommendations():
    conn = None
    try:
        conn = get_db()
        c = conn.cursor()
        uid = session['user_id']
        recs = []
        
        # weekend analysis skipped - day_type column not in DB
        
        c.execute('''
            SELECT category, SUM(amount) as total 
            FROM expenses 
            WHERE user_id = %s 
            GROUP BY category 
            ORDER BY total DESC 
            LIMIT 1
        ''', (uid,))
        top = c.fetchone()
        if top:
            recs.append({'type': 'info', 'message': f'Top spending: {top["category"]} - ₹{float(top["total"]):.2f}'})
        
        c.execute('SELECT COALESCE(SUM(amount), 0) as total FROM income WHERE user_id = %s', (uid,))
        inc = float(c.fetchone()['total'])
        
        c.execute('SELECT COALESCE(SUM(amount), 0) as total FROM expenses WHERE user_id = %s', (uid,))
        exp = float(c.fetchone()['total'])
        
        if inc > 0:
            rate = ((inc - exp) / inc) * 100
            if rate < 10:
                recs.append({'type': 'danger', 'message': f'Savings rate is only {rate:.1f}%. Try to save at least 10%!'})
        
        return jsonify({'recommendations': recs})
    except Exception as e:
        print(f"❌ Recommendations error: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        close_db(conn)

@app.route('/api/budget-alerts')
@login_required
def get_budget_alerts():
    conn = None
    try:
        conn = get_db()
        c = conn.cursor()
        uid = session['user_id']
        
        first = datetime.now().replace(day=1).strftime('%Y-%m-%d')
        
        c.execute('SELECT * FROM budgets WHERE user_id = %s', (uid,))
        buds = [dict(r) for r in c.fetchall()]
        
        c.execute('''
            SELECT category, SUM(amount) as spent 
            FROM expenses 
            WHERE date >= %s AND user_id = %s 
            GROUP BY category
        ''', (first, uid))
        spend = {r['category']: float(r['spent']) for r in c.fetchall()}
        
        alerts = []
        for b in buds:
            s = spend.get(b['category'], 0)
            limit = float(b['monthly_limit'])
            p = (s / limit * 100) if limit > 0 else 0
            
            if p >= 100:
                alerts.append({'type': 'danger', 'message': f"🚨 {b['category']} budget exceeded!"})
            elif p >= 80:
                alerts.append({'type': 'warning', 'message': f"⚠️ {b['category']}: {p:.0f}% used"})
        
        return jsonify({'alerts': alerts})
    except Exception as e:
        print(f"❌ Budget alerts error: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        close_db(conn)

@app.route('/api/trends')
@login_required
def get_trends():
    conn = None
    try:
        conn = get_db()
        c = conn.cursor()
        uid = session['user_id']
        
        today = datetime.now()
        six_ago = today - timedelta(days=180)
        
        c.execute('''
            SELECT TO_CHAR(date, 'YYYY-MM') as month, SUM(amount) as total 
            FROM income 
            WHERE date >= %s AND user_id = %s 
            GROUP BY TO_CHAR(date, 'YYYY-MM')
        ''', (six_ago.strftime('%Y-%m-%d'), uid))
        inc_m = {r['month']: float(r['total']) for r in c.fetchall()}
        
        c.execute('''
            SELECT TO_CHAR(date, 'YYYY-MM') as month, SUM(amount) as total 
            FROM expenses 
            WHERE date >= %s AND user_id = %s 
            GROUP BY TO_CHAR(date, 'YYYY-MM')
        ''', (six_ago.strftime('%Y-%m-%d'), uid))
        exp_m = {r['month']: float(r['total']) for r in c.fetchall()}
        
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
        
        return jsonify({'months': months, 'income': inc_data, 'expenses': exp_data, 'savings': sav_data})
    except Exception as e:
        print(f"❌ Trends error: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        close_db(conn)

@app.route('/api/parse-sms', methods=['POST'])
@login_required
def parse_sms():
    try:
        data = request.get_json()
        sms_text = data.get('sms', '')
        
        if not sms_text:
            return jsonify({'success': False, 'error': 'No SMS text provided'}), 400
        
        lower_sms = sms_text.lower()
        if 'debited' in lower_sms or 'withdrawn' in lower_sms or 'paid' in lower_sms:
            trans_type = 'expense'
        elif 'credited' in lower_sms or 'deposited' in lower_sms or 'received' in lower_sms:
            trans_type = 'income'
        else:
            return jsonify({'success': False, 'error': 'Could not determine transaction type'}), 400
        
        import re
        amount_pattern = r'(?:rs\.?|inr|₹)\s*([0-9,]+\.?[0-9]*)'
        amount_match = re.search(amount_pattern, sms_text, re.IGNORECASE)
        
        if not amount_match:
            return jsonify({'success': False, 'error': 'Could not extract amount'}), 400
        
        amount = float(amount_match.group(1).replace(',', ''))
        
        merchant_pattern = r'(?:at|to)\s+([A-Z][A-Za-z\s&]+?)(?:on|\.|avl|upi|info|ref)'
        merchant_match = re.search(merchant_pattern, sms_text, re.IGNORECASE)
        
        description = merchant_match.group(1).strip() if merchant_match else 'Bank Transaction'
        
        desc_lower = description.lower()
        if 'amazon' in desc_lower or 'flipkart' in desc_lower or 'shop' in desc_lower:
            category = 'Shopping'
        elif 'swiggy' in desc_lower or 'zomato' in desc_lower or 'food' in desc_lower:
            category = 'Food'
        elif 'uber' in desc_lower or 'ola' in desc_lower or 'metro' in desc_lower:
            category = 'Transport'
        elif 'salary' in desc_lower or 'transfer' in desc_lower:
            category = 'Salary'
        else:
            category = 'Other'
        
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
        print(f"❌ Parse SMS error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/achievements')
@login_required
def get_achievements():
    conn = None
    try:
        conn = get_db()
        cur = conn.cursor()
        uid = session['user_id']
        achievements = []

        cur.execute('SELECT COUNT(*) as c FROM income WHERE user_id = %s', (uid,))
        inc_count = cur.fetchone()['c']
        cur.execute('SELECT COUNT(*) as c FROM expenses WHERE user_id = %s', (uid,))
        exp_count = cur.fetchone()['c']

        if inc_count + exp_count >= 1:
            achievements.append({'icon': '🎉', 'title': 'First Transaction!', 'desc': 'You added your first transaction!', 'unlocked': True})
        else:
            achievements.append({'icon': '🎉', 'title': 'First Transaction!', 'desc': 'Add your first transaction to unlock!', 'unlocked': False})

        cur.execute('SELECT COALESCE(SUM(amount),0) as total FROM income WHERE user_id = %s', (uid,))
        inc = float(cur.fetchone()['total'])
        cur.execute('SELECT COALESCE(SUM(amount),0) as total FROM expenses WHERE user_id = %s', (uid,))
        exp = float(cur.fetchone()['total'])

        if inc > 0 and ((inc - exp) / inc * 100) >= 30:
            achievements.append({'icon': '⚔️', 'title': 'Savings Warrior!', 'desc': 'You saved more than 30% of your income!', 'unlocked': True})
        else:
            achievements.append({'icon': '⚔️', 'title': 'Savings Warrior!', 'desc': 'Save more than 30% of income to unlock!', 'unlocked': False})

        cur.execute('SELECT COUNT(*) as c FROM budgets WHERE user_id = %s', (uid,))
        bud_count = cur.fetchone()['c']
        if bud_count >= 1:
            achievements.append({'icon': '💰', 'title': 'Budget Master!', 'desc': 'You set up your first budget!', 'unlocked': True})
        else:
            achievements.append({'icon': '💰', 'title': 'Budget Master!', 'desc': 'Set up a budget to unlock!', 'unlocked': False})

        cur.execute('SELECT COUNT(*) as c FROM goals WHERE user_id = %s', (uid,))
        goal_count = cur.fetchone()['c']
        if goal_count >= 1:
            achievements.append({'icon': '🎯', 'title': 'Goal Crusher!', 'desc': 'You created your first savings goal!', 'unlocked': True})
        else:
            achievements.append({'icon': '🎯', 'title': 'Goal Crusher!', 'desc': 'Create a goal to unlock!', 'unlocked': False})

        if inc_count + exp_count >= 10:
            achievements.append({'icon': '🔥', 'title': '10 Transaction Streak!', 'desc': 'You logged 10 transactions!', 'unlocked': True})
        else:
            achievements.append({'icon': '🔥', 'title': '10 Transaction Streak!', 'desc': f'Log {10 - (inc_count + exp_count)} more transactions to unlock!', 'unlocked': False})

        return jsonify({'achievements': achievements})
    except Exception as e:
        print(f"Achievements error: {e}")
        return jsonify({'achievements': []})
    finally:
        close_db(conn)


@app.route('/api/analytics/monthly')
@login_required
def monthly_analytics():
    conn = None
    try:
        conn = get_db()
        cur = conn.cursor()
        uid = session['user_id']
        today = datetime.now()
        months, inc_data, exp_data = [], [], []
        for i in range(12):
            md = today - timedelta(days=30 * (11 - i))
            mk = md.strftime('%Y-%m')
            cur.execute("SELECT COALESCE(SUM(amount),0) as t FROM income WHERE TO_CHAR(date,'YYYY-MM')=%s AND user_id=%s", (mk, uid))
            inc = float(cur.fetchone()['t'])
            cur.execute("SELECT COALESCE(SUM(amount),0) as t FROM expenses WHERE TO_CHAR(date,'YYYY-MM')=%s AND user_id=%s", (mk, uid))
            exp = float(cur.fetchone()['t'])
            months.append(md.strftime('%b %Y'))
            inc_data.append(round(inc, 2))
            exp_data.append(round(exp, 2))
        return jsonify({'months': months, 'income': inc_data, 'expenses': exp_data})
    except Exception as e:
        print(f"Monthly analytics error: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        close_db(conn)


@app.route('/api/analytics/heatmap')
@login_required
def spending_heatmap():
    conn = None
    try:
        conn = get_db()
        cur = conn.cursor()
        uid = session['user_id']
        cur.execute("""
            SELECT TO_CHAR(date, 'Day') as day_name,
                   EXTRACT(DOW FROM date) as day_num,
                   COALESCE(SUM(amount), 0) as total
            FROM expenses WHERE user_id = %s
            GROUP BY TO_CHAR(date, 'Day'), EXTRACT(DOW FROM date)
            ORDER BY day_num
        """, (uid,))
        rows = cur.fetchall()
        days = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday']
        data = {d: 0 for d in days}
        for r in rows:
            data[r['day_name'].strip()] = round(float(r['total']), 2)
        return jsonify({'heatmap': [{'day': d, 'total': data[d]} for d in days]})
    except Exception as e:
        print(f"Heatmap error: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        close_db(conn)


@app.route('/api/analytics/categories')
@login_required
def category_trends():
    conn = None
    try:
        conn = get_db()
        cur = conn.cursor()
        uid = session['user_id']
        today = datetime.now()
        cur.execute("SELECT DISTINCT category FROM expenses WHERE user_id=%s", (uid,))
        categories = [r['category'] for r in cur.fetchall()]
        months = []
        for i in range(6):
            md = today - timedelta(days=30 * (5 - i))
            months.append(md.strftime('%b %Y'))
        result = {}
        for cat in categories:
            result[cat] = []
            for i in range(6):
                md = today - timedelta(days=30 * (5 - i))
                mk = md.strftime('%Y-%m')
                cur.execute("SELECT COALESCE(SUM(amount),0) as t FROM expenses WHERE category=%s AND TO_CHAR(date,'YYYY-MM')=%s AND user_id=%s", (cat, mk, uid))
                result[cat].append(round(float(cur.fetchone()['t']), 2))
        return jsonify({'months': months, 'categories': result})
    except Exception as e:
        print(f"Category trends error: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        close_db(conn)


@app.route('/api/notifications')
@login_required
def get_notifications():
    conn = None
    try:
        conn = get_db()
        cur = conn.cursor()
        uid = session['user_id']
        notifications = []
        today = datetime.now()

        cur.execute('SELECT * FROM budgets WHERE user_id = %s', (uid,))
        buds = [dict(r) for r in cur.fetchall()]
        cur.execute('SELECT category, SUM(amount) as spent FROM expenses WHERE user_id = %s GROUP BY category', (uid,))
        spend = {r['category']: float(r['spent']) for r in cur.fetchall()}

        for b in buds:
            s = spend.get(b['category'], 0)
            limit = float(b['monthly_limit'])
            p = (s / limit * 100) if limit > 0 else 0
            if p >= 100:
                notifications.append({'type': 'danger', 'icon': '🚨', 'title': 'Budget Exceeded!', 'message': f"{b['category']} budget exceeded by ₹{round(s-limit,2)}", 'time': 'Now'})
            elif p >= 80:
                notifications.append({'type': 'warning', 'icon': '⚠️', 'title': 'Budget Warning', 'message': f"{b['category']} is {p:.0f}% used — ₹{round(limit-s,2)} remaining", 'time': 'Now'})

        cur.execute('SELECT * FROM goals WHERE user_id = %s', (uid,))
        goals = [dict(r) for r in cur.fetchall()]
        for g in goals:
            if g['target_date']:
                td = datetime.strptime(str(g['target_date']), '%Y-%m-%d')
                days_left = (td.date() - today.date()).days
                current = float(g['current_savings'])
                target = float(g['target_amount'])
                if 0 < days_left <= 30 and current < target:
                    notifications.append({'type': 'warning', 'icon': '🎯', 'title': 'Goal Deadline Near!', 'message': f"'{g['goal_name']}' deadline in {days_left} days — ₹{round(target-current,2)} still needed", 'time': f'{days_left} days left'})

        week_ago = (today - timedelta(days=7)).strftime('%Y-%m-%d')
        cur.execute('SELECT COALESCE(SUM(amount),0) as total FROM expenses WHERE date >= %s AND user_id = %s', (week_ago, uid))
        week_exp = float(cur.fetchone()['total'])
        cur.execute('SELECT COALESCE(SUM(amount),0) as total FROM income WHERE date >= %s AND user_id = %s', (week_ago, uid))
        week_inc = float(cur.fetchone()['total'])
        if week_exp > 0 or week_inc > 0:
            notifications.append({'type': 'info', 'icon': '📊', 'title': 'Weekly Summary', 'message': f"This week: Income ₹{round(week_inc,2)} | Expenses ₹{round(week_exp,2)} | Saved ₹{round(week_inc-week_exp,2)}", 'time': 'This week'})

        days_remaining = 30 - today.day
        if days_remaining <= 5:
            notifications.append({'type': 'info', 'icon': '🧾', 'title': 'Month End Reminder', 'message': f"Only {days_remaining} days left in month — check pending bills!", 'time': f'{days_remaining} days'})

        if not notifications:
            notifications.append({'type': 'success', 'icon': '✅', 'title': 'All Good!', 'message': 'No alerts right now. Keep up the great work!', 'time': 'Now'})

        return jsonify({'notifications': notifications})
    except Exception as e:
        print(f"Notifications error: {e}")
        return jsonify({'notifications': []})
    finally:
        close_db(conn)



@app.route('/api/analytics/weekday-weekend')
@login_required
def weekday_weekend():
    conn = None
    try:
        conn = get_db()
        cur = conn.cursor()
        uid = session['user_id']

        # Total spending weekday vs weekend
        cur.execute("""
            SELECT 
                CASE WHEN EXTRACT(DOW FROM date) IN (0,6) THEN 'Weekend' ELSE 'Weekday' END as day_type,
                COALESCE(SUM(amount), 0) as total,
                COUNT(*) as txn_count
            FROM expenses WHERE user_id = %s
            GROUP BY day_type
        """, (uid,))
        rows = cur.fetchall()
        weekday_total = 0
        weekend_total = 0
        weekday_count = 0
        weekend_count = 0
        for r in rows:
            if r['day_type'] == 'Weekday':
                weekday_total = float(r['total'])
                weekday_count = int(r['txn_count'])
            else:
                weekend_total = float(r['total'])
                weekend_count = int(r['txn_count'])

        weekday_avg = round(weekday_total / weekday_count, 2) if weekday_count > 0 else 0
        weekend_avg = round(weekend_total / weekend_count, 2) if weekend_count > 0 else 0

        # Daily spending for last 30 days (for calendar heatmap)
        cur.execute("""
            SELECT date, COALESCE(SUM(amount), 0) as total
            FROM expenses 
            WHERE user_id = %s AND date >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY date ORDER BY date
        """, (uid,))
        daily = [{'date': str(r['date']), 'total': round(float(r['total']), 2)} for r in cur.fetchall()]

        return jsonify({
            'weekday_total': round(weekday_total, 2),
            'weekend_total': round(weekend_total, 2),
            'weekday_avg': weekday_avg,
            'weekend_avg': weekend_avg,
            'weekday_count': weekday_count,
            'weekend_count': weekend_count,
            'daily': daily
        })
    except Exception as e:
        print(f"Weekday weekend error: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        close_db(conn)


@app.route('/api/change-password', methods=['POST'])
@login_required
def change_password():
    conn = None
    try:
        data = request.json
        conn = get_db()
        cur = conn.cursor()
        cur.execute('SELECT * FROM users WHERE id = %s', (session['user_id'],))
        user = cur.fetchone()
        if not bcrypt.check_password_hash(user['password_hash'], data['current_password']):
            return jsonify({'success': False, 'message': 'Current password is wrong!'}), 400
        new_hash = bcrypt.generate_password_hash(data['new_password']).decode('utf-8')
        cur.execute('UPDATE users SET password_hash = %s WHERE id = %s', (new_hash, session['user_id']))
        conn.commit()
        return jsonify({'success': True, 'message': 'Password changed successfully!'})
    except Exception as e:
        print(f"Change password error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        close_db(conn)


@app.route('/api/setup-security', methods=['POST'])
@login_required
def setup_security():
    conn = None
    try:
        data = request.json
        conn = get_db()
        cur = conn.cursor()
        # Add columns if not exist
        try:
            cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS security_question TEXT")
            cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS security_answer TEXT")
            conn.commit()
        except:
            conn.rollback()
        answer_hash = bcrypt.generate_password_hash(data['answer'].lower().strip()).decode('utf-8')
        cur.execute('UPDATE users SET security_question = %s, security_answer = %s WHERE id = %s',
                   (data['question'], answer_hash, session['user_id']))
        conn.commit()
        return jsonify({'success': True, 'message': 'Security question saved!'})
    except Exception as e:
        print(f"Setup security error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        close_db(conn)


@app.route('/api/get-security-question', methods=['POST'])
def get_security_question():
    conn = None
    try:
        data = request.json
        conn = get_db()
        cur = conn.cursor()
        cur.execute('SELECT security_question FROM users WHERE username = %s', (data['username'],))
        user = cur.fetchone()
        if not user:
            return jsonify({'success': False, 'message': 'Username not found!'}), 404
        if not user['security_question']:
            return jsonify({'success': False, 'message': 'No security question set for this account!'}), 400
        return jsonify({'success': True, 'question': user['security_question']})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        close_db(conn)


@app.route('/api/reset-password', methods=['POST'])
def reset_password():
    conn = None
    try:
        data = request.json
        conn = get_db()
        cur = conn.cursor()
        cur.execute('SELECT * FROM users WHERE username = %s', (data['username'],))
        user = cur.fetchone()
        if not user:
            return jsonify({'success': False, 'message': 'Username not found!'}), 404
        if not user['security_answer']:
            return jsonify({'success': False, 'message': 'No security question set!'}), 400
        if not bcrypt.check_password_hash(user['security_answer'], data['answer'].lower().strip()):
            return jsonify({'success': False, 'message': 'Wrong answer!'}), 400
        new_hash = bcrypt.generate_password_hash(data['new_password']).decode('utf-8')
        cur.execute('UPDATE users SET password_hash = %s WHERE id = %s', (new_hash, user['id']))
        conn.commit()
        return jsonify({'success': True, 'message': 'Password reset successfully!'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        close_db(conn)


@app.route('/api/profile')
@login_required
def get_profile():
    conn = None
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute('SELECT id, username, email, full_name, created_at, security_question FROM users WHERE id = %s', (session['user_id'],))
        user = dict(cur.fetchone())
        user['created_at'] = str(user['created_at'])
        return jsonify({'success': True, 'user': user})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        close_db(conn)


@app.route('/api/verify-answer', methods=['POST'])
def verify_answer():
    conn = None
    try:
        data = request.json
        conn = get_db()
        cur = conn.cursor()
        cur.execute('SELECT * FROM users WHERE username = %s', (data['username'],))
        user = cur.fetchone()
        if not user:
            return jsonify({'success': False, 'message': 'Username not found!'}), 404
        if not user['security_answer']:
            return jsonify({'success': False, 'message': 'No security question set!'}), 400
        if not bcrypt.check_password_hash(user['security_answer'], data['answer'].lower().strip()):
            return jsonify({'success': False, 'message': '❌ Wrong answer! Try again.'}), 400
        session['reset_verified_user'] = user['id']
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        close_db(conn)


@app.route('/api/reset-password-verified', methods=['POST'])
def reset_password_verified():
    conn = None
    try:
        data = request.json
        conn = get_db()
        cur = conn.cursor()
        cur.execute('SELECT id FROM users WHERE username = %s', (data['username'],))
        user = cur.fetchone()
        if not user:
            return jsonify({'success': False, 'message': 'Username not found!'}), 404
        if session.get('reset_verified_user') != user['id']:
            return jsonify({'success': False, 'message': 'Please verify your answer first!'}), 400
        new_hash = bcrypt.generate_password_hash(data['new_password']).decode('utf-8')
        cur.execute('UPDATE users SET password_hash = %s WHERE id = %s', (new_hash, user['id']))
        conn.commit()
        session.pop('reset_verified_user', None)
        return jsonify({'success': True, 'message': 'Password reset successfully!'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        close_db(conn)

if __name__ == '__main__':
    print("🚀 FinDash starting with PostgreSQL...")
    app.run(host='0.0.0.0', debug=True, port=5000)