google.charts.load('current', {'packages': ['corechart']});

// Global variables
let currentUser = null;
let allTransactions = [];

// Set today's date in all date inputs
function setTodaysDate() {
    const today = new Date().toISOString().split('T')[0];
    const incomeDate = document.getElementById('incomeDate');
    if (incomeDate) incomeDate.value = today;
    const expenseDate = document.getElementById('expenseDate');
    if (expenseDate) expenseDate.value = today;
    const goalDate = document.getElementById('goalDate');
    if (goalDate) {
        const oneYearLater = new Date();
        oneYearLater.setFullYear(oneYearLater.getFullYear() + 1);
        goalDate.value = oneYearLater.toISOString().split('T')[0];
    }
}

// Load theme
if (localStorage.getItem('darkMode') === 'true') {
    document.body.classList.add('dark-mode');
}

// Start app when Google Charts is ready
google.charts.setOnLoadCallback(function() {
    loadUser();
    setTodaysDate();
    loadDashboard();
    loadStatistics();
    loadTransactions();
    loadBudgets();
    loadGoals();
    loadRecommendations();
    loadBudgetAlerts();
    loadAchievements();
    loadTrends();
    showPopupNotifications();
    checkSecurityQuestion();
});

// Load user
async function loadUser() {
    try {
        const res = await fetch('/api/current-user');
        const data = await res.json();
        if (!data.logged_in) {
            window.location.href = '/login';
        } else {
            currentUser = data.username;
            document.getElementById('username').textContent = 'Hi, ' + data.username;
        }
    } catch (e) {
        window.location.href = '/login';
    }
}

// Page navigation
function showPage(pageName, event) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));

    const page = document.getElementById(pageName);
    if (page) page.classList.add('active');

    if (event && event.target) {
        event.target.classList.add('active');
    }

    if (pageName === 'dashboard') {
        setTodaysDate();
        loadDashboard();
        loadStatistics();
        loadTrends();
    } else if (pageName === 'transactions') {
        loadTransactions();
    } else if (pageName === 'budgets') {
        loadBudgets();
    } else if (pageName === 'goals') {
        loadGoals();
    } else if (pageName === 'alerts') {
        loadRecommendations();
        loadBudgetAlerts();
        loadAchievements();
    } else if (pageName === 'analytics') {
        loadAnalytics();
    } else if (pageName === 'notifications') {
        loadNotifications();
    } else if (pageName === 'profile') {
        loadProfile();
    }
}

// Logout
async function logout() {
    await fetch('/api/logout', { method: 'POST' });
    window.location.href = '/login';
}

// Toggle dark mode
function toggleDarkMode() {
    document.body.classList.toggle('dark-mode');
    const isDark = document.body.classList.contains('dark-mode');
    localStorage.setItem('darkMode', isDark);
    const btn = document.querySelector('.btn-theme');
    if (btn) btn.textContent = isDark ? '☀️ Light Mode' : '🌙 Dark Mode';
}

// Load Dashboard
async function loadDashboard() {
    try {
        const res = await fetch('/api/dashboard');
        const data = await res.json();
        if (data.error) return;

        const income = parseFloat(data.total_income) || 0;
        const expenses = parseFloat(data.total_expenses) || 0;
        const balance = parseFloat(data.balance) || 0;
        const health = parseFloat(data.health_score) || 0;

        document.getElementById('totalIncome').textContent = '₹' + income.toFixed(2);
        document.getElementById('totalExpenses').textContent = '₹' + expenses.toFixed(2);
        document.getElementById('balance').textContent = '₹' + balance.toFixed(2);
        document.getElementById('healthScore').textContent = health.toFixed(0) + '%';

        // Chart 1: Income vs Expenses
        const chart1El = document.getElementById('chart1');
        if (chart1El) {
            chart1El.style.height = '300px';
            const d1 = google.visualization.arrayToDataTable([
                ['Type', 'Amount'],
                ['Income', income],
                ['Expenses', expenses],
                ['Balance', balance]
            ]);
            new google.visualization.ColumnChart(chart1El).draw(d1, {
                colors: ['#27ae60', '#e74c3c', '#3498db'],
                legend: { position: 'none' },
                backgroundColor: 'transparent',
                chartArea: { width: '80%', height: '75%' },
                vAxis: { format: '₹#,###' }
            });
        }

        // Chart 2: Expense Breakdown
        const chart2El = document.getElementById('chart2');
        if (chart2El) {
            chart2El.style.height = '300px';
            if (data.category_data && data.category_data.length > 0) {
                const d2 = new google.visualization.DataTable();
                d2.addColumn('string', 'Category');
                d2.addColumn('number', 'Amount');
                data.category_data.forEach(c => d2.addRow([c.category, parseFloat(c.total) || 0]));
                new google.visualization.PieChart(chart2El).draw(d2, {
                    colors: ['#e74c3c', '#3498db', '#f39c12', '#9b59b6', '#1abc9c', '#34495e', '#e67e22', '#95a5a6'],
                    backgroundColor: 'transparent',
                    pieHole: 0.4,
                    legend: { position: 'right' },
                    chartArea: { width: '90%', height: '90%' }
                });
            } else {
                chart2El.innerHTML = '<p style="text-align:center;color:#888;padding:50px;">No expense data yet. Add expenses to see breakdown!</p>';
            }
        }
    } catch (e) {
        console.error('Dashboard error:', e);
    }
}

// Load Statistics
async function loadStatistics() {
    try {
        const res = await fetch('/api/statistics');
        const data = await res.json();
        if (data.error) return;
        const s = data.statistics;
        document.getElementById('statTransactions').textContent = s.total_transactions;
        document.getElementById('statAvgIncome').textContent = '₹' + s.avg_monthly_income.toFixed(2);
        document.getElementById('statAvgExpenses').textContent = '₹' + s.avg_monthly_expenses.toFixed(2);
        document.getElementById('statTopCategory').textContent = s.top_expense_category;
        document.getElementById('statTopAmount').textContent = '₹' + s.top_expense_amount.toFixed(2);
        document.getElementById('statDaysTracking').textContent = s.days_tracking;
        document.getElementById('statGoals').textContent = s.total_goals;
        document.getElementById('statBudgets').textContent = s.total_budgets;
        const change = s.month_over_month_change;
        const el = document.getElementById('statMonthChange');
        el.textContent = (change > 0 ? '+' : '') + change.toFixed(1) + '%';
        el.style.color = change > 0 ? '#e74c3c' : '#27ae60';
    } catch (e) {
        console.error('Statistics error:', e);
    }
}

// Load Trends
async function loadTrends() {
    try {
        const res = await fetch('/api/trends');
        const data = await res.json();
        const chart3El = document.getElementById('chart3');
        if (!chart3El) return;
        chart3El.style.height = '350px';
        const d = new google.visualization.DataTable();
        d.addColumn('string', 'Month');
        d.addColumn('number', 'Income');
        d.addColumn('number', 'Expenses');
        d.addColumn('number', 'Savings');
        for (let i = 0; i < data.months.length; i++) {
            d.addRow([data.months[i], data.income[i], data.expenses[i], data.savings[i]]);
        }
        new google.visualization.LineChart(chart3El).draw(d, {
            curveType: 'function',
            colors: ['#27ae60', '#e74c3c', '#3498db'],
            backgroundColor: 'transparent',
            legend: { position: 'top' },
            chartArea: { width: '85%', height: '75%' }
        });
    } catch (e) {
        console.error('Trends error:', e);
    }
}

// Add Income
async function addIncome(event) {
    event.preventDefault();
    const source = document.getElementById('incomeSource').value;
    const amount = document.getElementById('incomeAmount').value;
    const date = document.getElementById('incomeDate').value;
    if (!confirm(`Add Income?\n\nSource: ${source}\nAmount: ₹${amount}\nDate: ${date}`)) return;
    try {
        const res = await fetch('/api/income', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ source, amount, date })
        });
        if (res.ok) {
            alert('✅ Income added!');
            document.getElementById('incomeForm').reset();
            setTodaysDate();
            loadDashboard();
            loadStatistics();
            loadTransactions();
        } else {
            alert('❌ Error adding income');
        }
    } catch (e) {
        alert('❌ Error: ' + e.message);
    }
}

// Add Expense
async function addExpense(event) {
    event.preventDefault();
    const category = document.getElementById('expenseCategory').value;
    const amount = document.getElementById('expenseAmount').value;
    const description = document.getElementById('expenseDescription').value;
    const date = document.getElementById('expenseDate').value;
    if (!confirm(`Add Expense?\n\nCategory: ${category}\nAmount: ₹${amount}\nDate: ${date}`)) return;
    try {
        const res = await fetch('/api/expense', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ category, amount, description, date })
        });
        if (res.ok) {
            alert('✅ Expense added!');
            document.getElementById('expenseForm').reset();
            setTodaysDate();
            loadDashboard();
            loadStatistics();
            loadTransactions();
            loadBudgets();
        } else {
            alert('❌ Error adding expense');
        }
    } catch (e) {
        alert('❌ Error: ' + e.message);
    }
}

// Load Transactions
async function loadTransactions() {
    try {
        const res = await fetch('/api/transactions');
        const data = await res.json();
        allTransactions = data.transactions || [];
        displayTransactions(allTransactions);
        updateTransactionSummary();
    } catch (e) {
        console.error('Transactions error:', e);
    }
}

function displayTransactions(trans) {
    const tbody = document.querySelector('#transactionsTable tbody');
    if (!tbody) return;
    tbody.innerHTML = '';
    if (trans.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:30px;color:#888;">No transactions yet. Add your first transaction!</td></tr>';
        return;
    }
    trans.forEach(t => {
        const row = document.createElement('tr');
        let timeStr = 'N/A';
        try {
            if (t.created_at) {
                const createdAt = new Date(t.created_at.replace(' ', 'T') + 'Z');
                if (!isNaN(createdAt.getTime())) {
                    timeStr = createdAt.toLocaleTimeString('en-IN', {
                        hour: '2-digit', minute: '2-digit',
                        hour12: true, timeZone: 'Asia/Kolkata'
                    });
                }
            }
        } catch (e) { timeStr = 'N/A'; }

        row.innerHTML = `
            <td>${t.date}</td>
            <td>${timeStr}</td>
            <td>${t.description}</td>
            <td class="type-${t.type.toLowerCase()}">₹${parseFloat(t.amount).toFixed(2)}</td>
            <td><span class="type-${t.type.toLowerCase()}">${t.type}</span></td>
            <td><button class="btn-delete" onclick="deleteTransaction('${t.type}', ${t.id})">Delete</button></td>
        `;
        tbody.appendChild(row);
    });
}

function updateTransactionSummary() {
    const totalIncome = allTransactions.filter(t => t.type === 'Income').reduce((s, t) => s + parseFloat(t.amount), 0);
    const totalExpenses = allTransactions.filter(t => t.type === 'Expense').reduce((s, t) => s + parseFloat(t.amount), 0);
    const summaryIncome = document.getElementById('summaryIncome');
    const summaryExpenses = document.getElementById('summaryExpenses');
    const summaryBalance = document.getElementById('summaryBalance');
    if (summaryIncome) summaryIncome.textContent = '₹' + totalIncome.toFixed(2);
    if (summaryExpenses) summaryExpenses.textContent = '₹' + totalExpenses.toFixed(2);
    if (summaryBalance) summaryBalance.textContent = '₹' + (totalIncome - totalExpenses).toFixed(2);
}

function filterTransactions() {
    const search = document.getElementById('searchTransaction').value.toLowerCase();
    const type = document.getElementById('filterType').value;
    let filtered = allTransactions;
    if (type !== 'all') filtered = filtered.filter(t => t.type.toLowerCase() === type);
    if (search) filtered = filtered.filter(t => t.description.toLowerCase().includes(search) || t.date.includes(search));
    displayTransactions(filtered);
}

function exportTransactions() {
    if (allTransactions.length === 0) { alert('No transactions to export!'); return; }
    let csv = 'Date,Type,Description,Amount\n';
    allTransactions.forEach(t => {
        csv += `${t.date},${t.type},"${t.description}",${t.amount}\n`;
    });
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `FinDash_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
}

async function deleteTransaction(type, id) {
    if (!confirm('Delete this transaction?')) return;
    const endpoint = type === 'Income' ? `/api/income/${id}` : `/api/expense/${id}`;
    const res = await fetch(endpoint, { method: 'DELETE' });
    if (res.ok) {
        alert('✅ Deleted!');
        loadDashboard();
        loadStatistics();
        loadTransactions();
        loadBudgets();
        loadTrends();
    }
}

// Budgets
async function setBudget(event) {
    event.preventDefault();
    const category = document.getElementById('budgetCategory').value;
    const amount = document.getElementById('budgetAmount').value;
    if (!confirm(`Set Budget?\n\nCategory: ${category}\nMonthly Limit: ₹${amount}`)) return;
    try {
        const res = await fetch('/api/budget', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ category, amount })
        });
        if (res.ok) {
            alert('✅ Budget set!');
            document.getElementById('budgetForm').reset();
            loadBudgets();
            loadStatistics();
        }
    } catch (e) {
        alert('❌ Error: ' + e.message);
    }
}

async function loadBudgets() {
    try {
        const res = await fetch('/api/budgets');
        const data = await res.json();
        const container = document.getElementById('budgetsList');
        if (!container) return;
        container.innerHTML = '';
        if (data.budgets.length === 0) {
            container.innerHTML = '<p style="text-align:center;padding:30px;color:#888;">No budgets set yet.</p>';
            return;
        }
        data.budgets.forEach(b => {
            const div = document.createElement('div');
            div.className = `budget-item ${b.status}`;
            div.innerHTML = `
                <div class="budget-header">
                    <span class="budget-category">${b.category}</span>
                    <span class="budget-limit">₹${b.monthly_limit.toFixed(2)}</span>
                </div>
                <div class="budget-progress">
                    <div class="budget-bar ${b.status}" style="width:${Math.min(b.percentage,100)}%">${b.percentage.toFixed(0)}%</div>
                </div>
                <div class="budget-details">
                    <span>Spent: ₹${b.spent.toFixed(2)}</span>
                    <span>Remaining: ₹${b.remaining.toFixed(2)}</span>
                </div>
                <button onclick="deleteBudget(${b.id})" class="btn-delete" style="margin-top:10px;width:100%;">Delete Budget</button>
            `;
            container.appendChild(div);
        });
    } catch (e) {
        console.error('Budgets error:', e);
    }
}

async function deleteBudget(id) {
    if (!confirm('Delete this budget?')) return;
    const res = await fetch(`/api/budget/${id}`, { method: 'DELETE' });
    if (res.ok) { alert('✅ Budget deleted!'); loadBudgets(); loadStatistics(); }
}

// Goals
async function addGoal(event) {
    event.preventDefault();
    const goal_name = document.getElementById('goalName').value;
    const target_amount = document.getElementById('goalAmount').value;
    const current_savings = document.getElementById('currentSavings').value || 0;
    const target_date = document.getElementById('goalDate').value;
    if (!confirm(`Create Goal?\n\nGoal: ${goal_name}\nTarget: ₹${target_amount}`)) return;
    try {
        const res = await fetch('/api/goal', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ goal_name, target_amount, current_savings, target_date })
        });
        if (res.ok) {
            alert('✅ Goal added!');
            document.getElementById('goalForm').reset();
            setTodaysDate();
            loadGoals();
            loadStatistics();
        }
    } catch (e) {
        alert('❌ Error: ' + e.message);
    }
}

async function loadGoals() {
    try {
        const res = await fetch('/api/goals');
        const data = await res.json();
        const container = document.getElementById('goalsList');
        if (!container) return;
        container.innerHTML = '';
        if (data.goals.length === 0) {
            container.innerHTML = '<p style="text-align:center;padding:30px;color:#888;">No goals yet.</p>';
            return;
        }
        data.goals.forEach(g => {
            const achieved = g.progress_percentage >= 100;
            const div = document.createElement('div');
            div.className = `goal-item ${achieved ? 'goal-achieved' : ''}`;
            div.innerHTML = `
                ${achieved ? '<span class="badge-achieved">🎉 Goal Achieved!</span>' : ''}
                <div class="goal-header">
                    <span class="goal-name">${g.goal_name}</span>
                    <span class="goal-amount">₹${g.target_amount.toFixed(2)}</span>
                </div>
                <div class="goal-progress-bar">
                    <div class="goal-bar" style="width:${Math.min(g.progress_percentage,100)}%">${g.progress_percentage.toFixed(0)}%</div>
                </div>
                <div class="goal-details">
                    <div class="goal-detail"><div class="goal-detail-label">Current Savings</div><div class="goal-detail-value">₹${g.current_savings.toFixed(2)}</div></div>
                    <div class="goal-detail"><div class="goal-detail-label">Remaining</div><div class="goal-detail-value">₹${g.remaining_amount.toFixed(2)}</div></div>
                    <div class="goal-detail"><div class="goal-detail-label">Target Date</div><div class="goal-detail-value">${g.target_date}</div></div>
                    <div class="goal-detail"><div class="goal-detail-label">Monthly Needed</div><div class="goal-detail-value">₹${g.monthly_savings_needed.toFixed(2)}</div></div>
                </div>
                <div class="goal-actions">
                    <button class="btn-add-savings" onclick="addSavings(${g.id})">💰 Add Savings</button>
                    <button class="btn-delete" onclick="deleteGoal(${g.id})">Delete</button>
                </div>
            `;
            container.appendChild(div);
        });
    } catch (e) {
        console.error('Goals error:', e);
    }
}

async function addSavings(id) {
    const amount = prompt('Enter amount to add:');
    if (!amount || isNaN(amount) || parseFloat(amount) <= 0) return;
    const res = await fetch(`/api/goal/${id}/update`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ amount: parseFloat(amount) })
    });
    if (res.ok) { alert('✅ Savings updated!'); loadGoals(); }
}

async function deleteGoal(id) {
    if (!confirm('Delete this goal?')) return;
    const res = await fetch(`/api/goal/${id}`, { method: 'DELETE' });
    if (res.ok) { alert('✅ Goal deleted!'); loadGoals(); loadStatistics(); }
}

// Recommendations
async function loadRecommendations() {
    try {
        const res = await fetch('/api/recommendations');
        const data = await res.json();
        const container = document.getElementById('recommendationsList');
        if (!container) return;
        container.innerHTML = '';
        if (!data.recommendations || data.recommendations.length === 0) {
            container.innerHTML = '<p style="text-align:center;padding:20px;color:#888;">No recommendations yet.</p>';
            return;
        }
        data.recommendations.forEach(r => {
            const div = document.createElement('div');
            div.className = `rec-item ${r.type}`;
            div.textContent = r.message;
            container.appendChild(div);
        });
    } catch (e) {
        console.error('Recommendations error:', e);
    }
}

// Budget Alerts
async function loadBudgetAlerts() {
    try {
        const res = await fetch('/api/budget-alerts');
        const data = await res.json();
        const container = document.getElementById('alertsList');
        if (!container) return;
        container.innerHTML = '';
        if (!data.alerts || data.alerts.length === 0) {
            container.innerHTML = '<p style="text-align:center;padding:20px;color:#888;">No budget alerts. Doing great!</p>';
            return;
        }
        data.alerts.forEach(a => {
            const div = document.createElement('div');
            div.className = `alert-item ${a.type}`;
            div.textContent = a.message;
            container.appendChild(div);
        });
    } catch (e) {
        console.error('Budget alerts error:', e);
    }
}

// Achievements
async function loadAchievements() {
    try {
        const res = await fetch('/api/achievements');
        const data = await res.json();
        const container = document.getElementById('achievementsList');
        if (!container) return;
        container.innerHTML = '';
        const colors = [
            '#27ae60', '#3498db', '#9b59b6', '#e67e22', '#e74c3c'
        ];
        const grid = document.createElement('div');
        grid.style.cssText = 'display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:15px;padding:10px 0;';
        data.achievements.forEach((a, i) => {
            const bg = colors[i % colors.length];
            const div = document.createElement('div');
            div.style.cssText = `background:${a.unlocked ? bg : '#f0f0f0'};border-radius:16px;padding:25px 15px;text-align:center;box-shadow:${a.unlocked ? '0 4px 15px rgba(0,0,0,0.15)' : 'none'};transition:transform 0.2s;`;
            div.onmouseover = () => { if (a.unlocked) div.style.transform = 'translateY(-5px)'; };
            div.onmouseout = () => { div.style.transform = 'translateY(0)'; };
            div.innerHTML = `
                <div style="font-size:2.5em;margin-bottom:10px;">${a.unlocked ? a.icon : '🔒'}</div>
                <div style="font-weight:700;font-size:0.95em;color:${a.unlocked ? 'white' : '#aaa'};margin-bottom:6px;">${a.title}</div>
                <div style="font-size:0.78em;color:${a.unlocked ? 'rgba(255,255,255,0.85)' : '#bbb'};line-height:1.4;">${a.desc}</div>
                ${a.unlocked ? '<div style="margin-top:12px;font-size:0.75em;background:rgba(255,255,255,0.25);color:white;padding:3px 10px;border-radius:20px;display:inline-block;">✅ Unlocked</div>' : ''}
            `;
            grid.appendChild(div);
        });
        container.appendChild(grid);
    } catch (e) {
        console.error('Achievements error:', e);
    }
}

// Analytics
async function loadAnalytics() {
    loadMonthlyComparison();
    loadHeatmap();
    loadCategoryTrends();
    loadWeekdayWeekend();
}

async function loadMonthlyComparison() {
    try {
        const res = await fetch('/api/analytics/monthly');
        const data = await res.json();
        const el = document.getElementById('analyticsChart1');
        if (!el) return;
        el.style.height = '350px';
        const d = new google.visualization.DataTable();
        d.addColumn('string', 'Month');
        d.addColumn('number', 'Income');
        d.addColumn('number', 'Expenses');
        for (let i = 0; i < data.months.length; i++) {
            d.addRow([data.months[i], data.income[i], data.expenses[i]]);
        }
        new google.visualization.ColumnChart(el).draw(d, {
            colors: ['#27ae60', '#e74c3c'],
            backgroundColor: 'transparent',
            legend: { position: 'top' },
            chartArea: { width: '85%', height: '75%' },
            vAxis: { format: '₹#,###' }
        });
    } catch (e) { console.error('Monthly error:', e); }
}

async function loadHeatmap() {
    try {
        const res = await fetch('/api/analytics/heatmap');
        const data = await res.json();
        const container = document.getElementById('heatmapChart');
        if (!container) return;
        const max = Math.max(...data.heatmap.map(d => d.total)) || 1;
        container.innerHTML = '';
        container.style.cssText = 'display:flex;gap:10px;flex-wrap:wrap;padding:10px 0;';
        data.heatmap.forEach(d => {
            const intensity = d.total / max;
            const color = d.total === 0 ? '#f0f0f0' : `rgba(231,76,60,${0.2 + intensity * 0.8})`;
            const textColor = intensity > 0.5 ? 'white' : '#333';
            const box = document.createElement('div');
            box.style.cssText = `flex:1;min-width:100px;padding:20px 10px;background:${color};border-radius:10px;text-align:center;`;
            box.innerHTML = `<div style="font-weight:700;font-size:0.9em;color:${textColor}">${d.day}</div><div style="font-size:1.2em;font-weight:700;color:${textColor};margin-top:5px;">₹${d.total.toFixed(0)}</div>`;
            container.appendChild(box);
        });
    } catch (e) { console.error('Heatmap error:', e); }
}

async function loadCategoryTrends() {
    try {
        const res = await fetch('/api/analytics/categories');
        const data = await res.json();
        const el = document.getElementById('categoryChart');
        if (!el) return;
        el.style.height = '350px';
        const categories = Object.keys(data.categories);
        if (categories.length === 0) {
            el.innerHTML = '<p style="text-align:center;color:#888;padding:50px;">No expense data yet.</p>';
            return;
        }
        const d = new google.visualization.DataTable();
        d.addColumn('string', 'Month');
        categories.forEach(cat => d.addColumn('number', cat));
        for (let i = 0; i < data.months.length; i++) {
            const row = [data.months[i]];
            categories.forEach(cat => row.push(data.categories[cat][i]));
            d.addRow(row);
        }
        new google.visualization.LineChart(el).draw(d, {
            curveType: 'function',
            backgroundColor: 'transparent',
            legend: { position: 'top' },
            chartArea: { width: '85%', height: '70%' },
            vAxis: { format: '₹#,###' }
        });
    } catch (e) { console.error('Category trends error:', e); }
}


async function loadWeekdayWeekend() {
    try {
        const res = await fetch('/api/analytics/weekday-weekend');
        const data = await res.json();
        if (data.error) return;

        // Option 1: Comparison Cards
        const cardsEl = document.getElementById('weekdayWeekendCards');
        if (cardsEl) {
            const total = data.weekday_total + data.weekend_total;
            const wdPct = total > 0 ? (data.weekday_total / total * 100).toFixed(0) : 0;
            const wePct = total > 0 ? (data.weekend_total / total * 100).toFixed(0) : 0;
            const higher = data.weekend_avg > data.weekday_avg ? 'weekend' : 'weekday';

            cardsEl.innerHTML = `
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:20px;">
                    <div style="background:linear-gradient(135deg,#3498db,#2980b9);border-radius:16px;padding:25px;color:white;text-align:center;box-shadow:0 4px 15px rgba(52,152,219,0.3);">
                        <div style="font-size:2em;margin-bottom:8px;">📅</div>
                        <div style="font-size:0.85em;opacity:0.85;margin-bottom:5px;text-transform:uppercase;letter-spacing:1px;">Weekdays</div>
                        <div style="font-size:1.8em;font-weight:700;margin-bottom:5px;">₹${data.weekday_total.toFixed(2)}</div>
                        <div style="font-size:0.85em;opacity:0.85;">Avg per txn: ₹${data.weekday_avg.toFixed(2)}</div>
                        <div style="font-size:0.85em;opacity:0.85;">${data.weekday_count} transactions</div>
                        <div style="margin-top:12px;background:rgba(255,255,255,0.2);border-radius:8px;padding:4px 12px;display:inline-block;font-size:0.85em;">${wdPct}% of total</div>
                    </div>
                    <div style="background:linear-gradient(135deg,#e67e22,#d35400);border-radius:16px;padding:25px;color:white;text-align:center;box-shadow:0 4px 15px rgba(230,126,34,0.3);">
                        <div style="font-size:2em;margin-bottom:8px;">🎉</div>
                        <div style="font-size:0.85em;opacity:0.85;margin-bottom:5px;text-transform:uppercase;letter-spacing:1px;">Weekends</div>
                        <div style="font-size:1.8em;font-weight:700;margin-bottom:5px;">₹${data.weekend_total.toFixed(2)}</div>
                        <div style="font-size:0.85em;opacity:0.85;">Avg per txn: ₹${data.weekend_avg.toFixed(2)}</div>
                        <div style="font-size:0.85em;opacity:0.85;">${data.weekend_count} transactions</div>
                        <div style="margin-top:12px;background:rgba(255,255,255,0.2);border-radius:8px;padding:4px 12px;display:inline-block;font-size:0.85em;">${wePct}% of total</div>
                    </div>
                </div>
                <div style="background:#f8f9fa;border-radius:12px;padding:15px;text-align:center;">
                    <div style="display:flex;border-radius:8px;overflow:hidden;height:20px;margin-bottom:10px;">
                        <div style="width:${wdPct}%;background:#3498db;transition:width 0.5s;"></div>
                        <div style="width:${wePct}%;background:#e67e22;transition:width 0.5s;"></div>
                    </div>
                    <div style="font-size:0.9em;color:#555;">
                        ${higher === 'weekend' ? '🔴 You spend <strong>more on weekends</strong> — ₹' + (data.weekend_avg - data.weekday_avg).toFixed(2) + ' more per transaction!' : '✅ You spend <strong>more on weekdays</strong> — weekend spending is controlled!'}
                    </div>
                </div>
            `;
        }

        // Option 5: Weekly Pattern Bars
        const patternEl = document.getElementById('weeklyPattern');
        if (patternEl) {
            const res2 = await fetch('/api/analytics/heatmap');
            const heatData = await res2.json();
            const max = Math.max(...heatData.heatmap.map(d => d.total), 1);

            let html = '<div style="display:flex;flex-direction:column;gap:12px;padding:10px 0;">';
            heatData.heatmap.forEach(d => {
                const isWeekend = d.day === 'Saturday' || d.day === 'Sunday';
                const pct = (d.total / max * 100).toFixed(0);
                const barColor = isWeekend ? '#e67e22' : '#3498db';
                const level = d.total === 0 ? '' : d.total < max * 0.33 ? '🟢 Low' : d.total < max * 0.66 ? '🟡 Medium' : '🔴 High';

                html += `
                    <div style="display:flex;align-items:center;gap:12px;">
                        <div style="width:90px;font-weight:${isWeekend ? '700' : '400'};color:${isWeekend ? '#e67e22' : '#333'};font-size:0.9em;flex-shrink:0;">
                            ${isWeekend ? '🎉' : '📅'} ${d.day.substring(0,3)}
                        </div>
                        <div style="flex:1;background:#f0f0f0;border-radius:6px;height:28px;overflow:hidden;position:relative;">
                            <div style="width:${pct}%;background:${barColor};height:100%;border-radius:6px;transition:width 0.5s;display:flex;align-items:center;padding-left:8px;min-width:${d.total > 0 ? '2px' : '0'};"></div>
                        </div>
                        <div style="width:90px;text-align:right;font-weight:600;font-size:0.9em;color:${isWeekend ? '#e67e22' : '#3498db'};">₹${d.total.toFixed(0)}</div>
                        <div style="width:80px;font-size:0.8em;color:#888;">${level}</div>
                    </div>
                `;
            });
            html += '</div>';
            html += '<div style="display:flex;gap:20px;margin-top:5px;justify-content:center;font-size:0.82em;color:#666;">';
            html += '<span>📅 <span style="color:#3498db;font-weight:700;">■</span> Weekday</span>';
            html += '<span>🎉 <span style="color:#e67e22;font-weight:700;">■</span> Weekend</span>';
            html += '</div>';

            patternEl.innerHTML = html;
        }
    } catch (e) {
        console.error('Weekday weekend error:', e);
    }
}

function downloadPDFReport() {
    const win = window.open('', '_blank');
    win.document.write(`<html><head><title>FinDash Report</title>
    <style>body{font-family:Arial,sans-serif;padding:30px;}h1{border-bottom:2px solid #1a1a1a;padding-bottom:10px;}table{width:100%;border-collapse:collapse;}th{background:#1a1a1a;color:white;padding:10px;}td{padding:10px;border-bottom:1px solid #eee;}.income{color:#27ae60;font-weight:bold;}.expense{color:#e74c3c;font-weight:bold;}</style>
    </head><body>
    <h1>💰 FinDash Financial Report</h1>
    <p>Generated: ${new Date().toLocaleDateString('en-IN', {day:'numeric',month:'long',year:'numeric'})} at ${new Date().toLocaleTimeString('en-IN', {hour:'2-digit',minute:'2-digit',hour12:true,timeZone:'Asia/Kolkata'})}</p>
    <h2>Summary</h2>
    <p>Total Income: <span class="income">${document.getElementById('totalIncome').textContent}</span></p>
    <p>Total Expenses: <span class="expense">${document.getElementById('totalExpenses').textContent}</span></p>
    <p>Balance: <strong>${document.getElementById('balance').textContent}</strong></p>
    <p>Financial Health: <strong>${document.getElementById('healthScore').textContent}</strong></p>
    <h2>Transactions</h2>
    <table><thead><tr><th>Date</th><th>Time</th><th>Description</th><th>Amount</th><th>Type</th></tr></thead><tbody>
    ${allTransactions.map(t => {
        let timeStr = 'N/A';
        try {
            if (t.created_at) {
                const createdAt = new Date(t.created_at.replace(' ', 'T') + 'Z');
                if (!isNaN(createdAt.getTime())) {
                    timeStr = createdAt.toLocaleTimeString('en-IN', {hour:'2-digit',minute:'2-digit',hour12:true,timeZone:'Asia/Kolkata'});
                }
            }
        } catch(e) {}
        return '<tr><td>'+t.date+'</td><td>'+timeStr+'</td><td>'+t.description+'</td><td class="'+t.type.toLowerCase()+'">₹'+parseFloat(t.amount).toFixed(2)+'</td><td>'+t.type+'</td></tr>';
    }).join('')}
    </tbody></table>
    <p style="color:#888;text-align:center;margin-top:30px;">Generated by FinDash-PFAS</p>
    </body></html>`);
    win.document.close();
    setTimeout(() => win.print(), 500);
}

// Toast Notifications
function createToastContainer() {
    if (document.getElementById('toastContainer')) return;
    const container = document.createElement('div');
    container.id = 'toastContainer';
    container.style.cssText = 'position:fixed;top:20px;right:20px;z-index:9999;display:flex;flex-direction:column;gap:10px;max-width:320px;width:100%;';
    document.body.appendChild(container);
    const style = document.createElement('style');
    style.textContent = '@keyframes slideInToast{from{transform:translateX(120%);opacity:0;}to{transform:translateX(0);opacity:1;}}@keyframes toastProgress{from{width:100%;}to{width:0%;}}';
    document.head.appendChild(style);
}

function showToast(icon, title, message, type = 'info') {
    createToastContainer();
    const colors = { danger: '#e74c3c', warning: '#f39c12', info: '#3498db', success: '#27ae60' };
    const bg = colors[type] || colors.info;
    const toast = document.createElement('div');
    toast.style.cssText = `background:${bg};color:white;padding:14px 16px;border-radius:12px;box-shadow:0 4px 20px rgba(0,0,0,0.25);display:flex;align-items:flex-start;gap:12px;position:relative;overflow:hidden;animation:slideInToast 0.3s ease;`;
    toast.innerHTML = `
        <div style="font-size:1.4em;flex-shrink:0;">${icon}</div>
        <div style="flex:1;"><div style="font-weight:700;font-size:0.95em;margin-bottom:3px;">${title}</div><div style="font-size:0.82em;opacity:0.9;line-height:1.4;">${message}</div></div>
        <div style="font-size:1.2em;opacity:0.8;cursor:pointer;" onclick="this.parentElement.remove()">×</div>
        <div style="position:absolute;bottom:0;left:0;height:3px;background:rgba(255,255,255,0.5);width:100%;animation:toastProgress 5s linear forwards;"></div>
    `;
    document.getElementById('toastContainer').appendChild(toast);
    setTimeout(() => { if (toast.parentElement) toast.remove(); }, 5000);
}

async function showPopupNotifications() {
    try {
        const res = await fetch('/api/notifications');
        const data = await res.json();
        const realNotifs = data.notifications.filter(n => n.type !== 'success');
        const countEl = document.getElementById('notifCount');
        if (countEl) countEl.textContent = realNotifs.length;
        realNotifs.forEach((n, i) => {
            setTimeout(() => showToast(n.icon, n.title, n.message, n.type), i * 800);
        });
    } catch (e) { console.error('Notifications error:', e); }
}




// Check if security question is set - remind user if not
async function checkSecurityQuestion() {
    try {
        const res = await fetch('/api/profile');
        const data = await res.json();
        if (!data.success) return;

        if (!data.user.security_question) {
            // Show reminder toast every time until set
            setTimeout(() => {
                showToast(
                    '🛡️',
                    'Set Security Question!',
                    'Go to Profile tab to set your security question for password recovery.',
                    'warning'
                );
            }, 2000);

            // Show again after 30 seconds if still on page
            setTimeout(async () => {
                const res2 = await fetch('/api/profile');
                const data2 = await res2.json();
                if (data2.success && !data2.user.security_question) {
                    showToast(
                        '⚠️',
                        'Reminder: Security Question',
                        'You still have not set your security question! Click Profile tab to set it.',
                        'danger'
                    );
                }
            }, 30000);
        }
    } catch (e) {
        console.error('Security check error:', e);
    }
}

// ============================================
// PROFILE & PASSWORD
// ============================================

async function loadProfile() {
    try {
        const res = await fetch('/api/profile');
        const data = await res.json();
        const container = document.getElementById('profileInfo');
        if (!container) return;
        const u = data.user;
        const created = new Date(u.created_at).toLocaleDateString('en-IN', {day:'numeric',month:'long',year:'numeric'});
        container.innerHTML = `
            <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:15px;padding:10px 0;">
                <div style="background:#f8f9fa;border-radius:12px;padding:20px;text-align:center;">
                    <div style="font-size:3em;margin-bottom:10px;">👤</div>
                    <div style="font-size:0.85em;color:#888;margin-bottom:4px;">USERNAME</div>
                    <div style="font-size:1.2em;font-weight:700;">${u.username}</div>
                </div>
                <div style="background:#f8f9fa;border-radius:12px;padding:20px;text-align:center;">
                    <div style="font-size:3em;margin-bottom:10px;">📧</div>
                    <div style="font-size:0.85em;color:#888;margin-bottom:4px;">EMAIL</div>
                    <div style="font-size:1.1em;font-weight:700;">${u.email || 'Not set'}</div>
                </div>
                <div style="background:#f8f9fa;border-radius:12px;padding:20px;text-align:center;">
                    <div style="font-size:3em;margin-bottom:10px;">📅</div>
                    <div style="font-size:0.85em;color:#888;margin-bottom:4px;">MEMBER SINCE</div>
                    <div style="font-size:1.1em;font-weight:700;">${created}</div>
                </div>
                <div style="background:${u.security_question ? '#eafaf1' : '#fef5e7'};border-radius:12px;padding:20px;text-align:center;">
                    <div style="font-size:3em;margin-bottom:10px;">${u.security_question ? '🛡️' : '⚠️'}</div>
                    <div style="font-size:0.85em;color:#888;margin-bottom:4px;">SECURITY</div>
                    <div style="font-size:1em;font-weight:700;color:${u.security_question ? '#27ae60' : '#e67e22'};">${u.security_question ? '✅ Question Set' : 'Not Set'}</div>
                </div>
            </div>
        `;
    } catch (e) {
        console.error('Profile error:', e);
    }
}

async function changePassword() {
    const current = document.getElementById('currentPassword').value;
    const newPass = document.getElementById('newPassword').value;
    const confirm = document.getElementById('confirmPassword').value;
    if (!current || !newPass || !confirm) { alert('Please fill all fields!'); return; }
    if (newPass !== confirm) { alert('New passwords do not match!'); return; }
    if (newPass.length < 6) { alert('New password must be at least 6 characters!'); return; }
    try {
        const res = await fetch('/api/change-password', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ current_password: current, new_password: newPass })
        });
        const data = await res.json();
        if (data.success) {
            alert('✅ ' + data.message);
            document.getElementById('currentPassword').value = '';
            document.getElementById('newPassword').value = '';
            document.getElementById('confirmPassword').value = '';
        } else {
            alert('❌ ' + data.message);
        }
    } catch (e) {
        alert('❌ Error: ' + e.message);
    }
}

async function saveSecurityQuestion() {
    const question = document.getElementById('securityQuestion').value;
    const answer = document.getElementById('securityAnswer').value.trim();
    if (!question) { alert('Please select a security question!'); return; }
    if (!answer) { alert('Please enter your answer!'); return; }
    try {
        const res = await fetch('/api/setup-security', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question, answer })
        });
        const data = await res.json();
        if (data.success) {
            alert('✅ ' + data.message);
            document.getElementById('securityQuestion').value = '';
            document.getElementById('securityAnswer').value = '';
            loadProfile();
        } else {
            alert('❌ ' + data.message);
        }
    } catch (e) {
        alert('❌ Error: ' + e.message);
    }
}

// Load Notifications Page
async function loadNotifications() {
    try {
        const res = await fetch('/api/notifications');
        const data = await res.json();
        const container = document.getElementById('notificationsList');
        if (!container) return;
        container.innerHTML = '';
        const colors = {
            'danger':  { bg: '#fdedec', border: '#e74c3c', icon_bg: '#e74c3c' },
            'warning': { bg: '#fef9e7', border: '#f39c12', icon_bg: '#f39c12' },
            'info':    { bg: '#eaf4fb', border: '#3498db', icon_bg: '#3498db' },
            'success': { bg: '#eafaf1', border: '#27ae60', icon_bg: '#27ae60' }
        };
        data.notifications.forEach(n => {
            const c = colors[n.type] || colors['info'];
            const div = document.createElement('div');
            div.style.cssText = `display:flex;align-items:center;gap:15px;padding:15px 20px;margin-bottom:12px;border-radius:12px;background:${c.bg};border-left:4px solid ${c.border};box-shadow:0 2px 8px rgba(0,0,0,0.06);`;
            div.innerHTML = `
                <div style="width:45px;height:45px;border-radius:50%;background:${c.icon_bg};display:flex;align-items:center;justify-content:center;font-size:1.3em;flex-shrink:0;">${n.icon}</div>
                <div style="flex:1;">
                    <div style="font-weight:700;color:#1a1a1a;margin-bottom:3px;">${n.title}</div>
                    <div style="font-size:0.9em;color:#555;">${n.message}</div>
                </div>
                <div style="font-size:0.8em;color:#999;white-space:nowrap;">${n.time}</div>
            `;
            container.appendChild(div);
        });
    } catch (e) {
        console.error('Notifications page error:', e);
    }
}

// SMS Modal
function showSmsModal() {
    document.getElementById('smsModal').style.display = 'block';
}

function closeSmsModal() {
    document.getElementById('smsModal').style.display = 'none';
    document.getElementById('smsText').value = '';
    document.getElementById('smsResult').innerHTML = '';
}

async function parseSms() {
    const smsText = document.getElementById('smsText').value.trim();
    if (!smsText) { alert('Please paste your SMS first!'); return; }
    try {
        const res = await fetch('/api/parse-sms', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sms: smsText })
        });
        const data = await res.json();
        if (data.success) {
            document.getElementById('smsResult').innerHTML = `
                <div style="border:2px solid #4CAF50;padding:15px;border-radius:8px;background:#f0f9ff;">
                    <h3>✅ Parsed Successfully!</h3>
                    <p><strong>Type:</strong> ${data.type}</p>
                    <p><strong>Amount:</strong> ₹${data.amount}</p>
                    <p><strong>Description:</strong> ${data.description}</p>
                    <p><strong>Date:</strong> ${data.date}</p>
                    <button onclick="addParsedTransaction('${data.type}',${data.amount},'${data.description}','${data.category||''}','${data.date}')" class="add-btn">✅ Add This Transaction</button>
                </div>`;
        } else {
            alert('Error: ' + data.error);
        }
    } catch (e) {
        alert('Failed to parse SMS');
    }
}

async function addParsedTransaction(type, amount, description, category, date) {
    if (!confirm(`Add from SMS?\nType: ${type}\nAmount: ₹${amount}`)) return;
    let res;
    if (type === 'income') {
        res = await fetch('/api/income', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ source: description, amount, date }) });
    } else {
        res = await fetch('/api/expense', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ category, amount, description, date }) });
    }
    if (res.ok) {
        alert('✅ Transaction added!');
        closeSmsModal();
        loadDashboard();
        loadStatistics();
        loadTransactions();
        loadBudgets();
    } else {
        alert('❌ Failed to add transaction');
    }
}

// Close modal on outside click
window.onclick = function(event) {
    const modal = document.getElementById('smsModal');
    if (event.target === modal) closeSmsModal();
};