google.charts.load('current', {'packages':['corechart']});

let today = new Date().toISOString().split('T')[0];
let allTransactions = [];

document.getElementById('incDate').value = today;
document.getElementById('expDate').value = today;

// Load theme
if (localStorage.getItem('theme') === 'dark') {
    document.body.classList.add('dark-mode');
    document.querySelector('.btn-theme').textContent = '☀️';
}

window.onload = function() {
    loadUser();
    loadDashboard();
    loadStatistics();
    loadRecommendations();
    loadBudgetAlerts();
    loadGoals();
    loadTransactions();
    loadBudgets();
    loadTrends();
};

async function loadUser() {
    const res = await fetch('/api/current-user');
    const data = await res.json();
    if (!data.logged_in) {
        window.location.href = '/login';
    } else {
        document.getElementById('username').textContent = 'Hi, ' + data.username;
    }
}

async function loadDashboard() {
    const res = await fetch('/api/dashboard');
    const data = await res.json();
    
    document.getElementById('totalIncome').textContent = '₹' + data.total_income.toFixed(2);
    document.getElementById('totalExpenses').textContent = '₹' + data.total_expenses.toFixed(2);
    document.getElementById('balance').textContent = '₹' + data.balance.toFixed(2);
    document.getElementById('health').textContent = data.health_score.toFixed(0);
    
    google.charts.setOnLoadCallback(() => {
        const d1 = google.visualization.arrayToDataTable([
            ['Type', 'Amount'],
            ['Income', data.total_income],
            ['Expenses', data.total_expenses]
        ]);
        new google.visualization.ColumnChart(document.getElementById('chart1'))
            .draw(d1, {colors: ['#38ef7d', '#f45c43'], legend: 'none', backgroundColor: 'transparent'});
        
        if (data.category_data.length > 0) {
            const d2 = new google.visualization.DataTable();
            d2.addColumn('string', 'Category');
            d2.addColumn('number', 'Amount');
            data.category_data.forEach(c => d2.addRow([c.category, c.total]));
            new google.visualization.PieChart(document.getElementById('chart2'))
                .draw(d2, {colors: ['#667eea', '#764ba2', '#f093fb', '#4facfe', '#43e97b', '#fa709a'], backgroundColor: 'transparent'});
        }
    });
}

async function loadStatistics() {
    const res = await fetch('/api/statistics');
    const data = await res.json();
    const s = data.statistics;
    
    document.getElementById('statTrans').textContent = s.total_transactions;
    document.getElementById('statAvgInc').textContent = '₹' + s.avg_monthly_income.toFixed(2);
    document.getElementById('statAvgExp').textContent = '₹' + s.avg_monthly_expenses.toFixed(2);
    document.getElementById('statTopCat').textContent = s.top_expense_category;
    document.getElementById('statTopAmt').textContent = '₹' + s.top_expense_amount.toFixed(2);
    document.getElementById('statDays').textContent = s.days_tracking;
    document.getElementById('statGoals').textContent = s.total_goals;
    document.getElementById('statBudgets').textContent = s.total_budgets;
    
    const change = s.month_over_month_change;
    const elem = document.getElementById('statMoM');
    if (change > 0) {
        elem.textContent = '↑ ' + change.toFixed(1) + '%';
        elem.style.color = '#ff6b6b';
    } else if (change < 0) {
        elem.textContent = '↓ ' + Math.abs(change).toFixed(1) + '%';
        elem.style.color = '#51cf66';
    } else {
        elem.textContent = '0%';
    }
}

async function loadRecommendations() {
    const res = await fetch('/api/recommendations');
    const data = await res.json();
    
    const container = document.getElementById('recommendations');
    container.innerHTML = '';
    
    if (data.recommendations.length > 0) {
        data.recommendations.forEach(r => {
            const div = document.createElement('div');
            div.className = 'rec-item ' + r.type;
            div.textContent = r.message;
            container.appendChild(div);
        });
    }
}

async function loadBudgetAlerts() {
    const res = await fetch('/api/budget-alerts');
    const data = await res.json();
    
    const container = document.getElementById('budgetAlerts');
    container.innerHTML = '';
    
    if (data.alerts.length > 0) {
        data.alerts.forEach(a => {
            const div = document.createElement('div');
            div.className = 'alert-item ' + a.type;
            div.textContent = a.message;
            container.appendChild(div);
        });
    }
}

async function loadGoals() {
    const res = await fetch('/api/goals');
    const data = await res.json();
    
    const container = document.getElementById('goalsList');
    container.innerHTML = '';
    
    if (data.goals.length === 0) {
        container.innerHTML = '<p style="text-align:center;color:#999;">No goals yet. Create your first goal above!</p>';
        return;
    }
    
    data.goals.forEach(g => {
        const div = document.createElement('div');
        const achieved = g.progress_percentage >= 100;
        div.className = 'goal-item' + (achieved ? ' goal-achieved' : '');
        
        const targetDate = new Date(g.target_date).toLocaleDateString('en-IN', {
            day: 'numeric', month: 'short', year: 'numeric'
        });
        
        div.innerHTML = `
            ${achieved ? '<div class="badge-achieved">🎉 Achieved!</div>' : ''}
            <div class="goal-header">
                <div class="goal-name">${g.goal_name}</div>
                <div class="goal-amount">₹${g.target_amount.toFixed(2)}</div>
            </div>
            <div class="goal-progress-bar">
                <div class="goal-bar" style="width: ${Math.min(g.progress_percentage, 100)}%">
                    ${g.progress_percentage.toFixed(1)}%
                </div>
            </div>
            <div class="goal-details">
                <div class="goal-detail">
                    <div class="goal-detail-label">Current Savings</div>
                    <div class="goal-detail-value">₹${g.current_savings.toFixed(2)}</div>
                </div>
                <div class="goal-detail">
                    <div class="goal-detail-label">Remaining</div>
                    <div class="goal-detail-value">₹${g.remaining_amount.toFixed(2)}</div>
                </div>
                <div class="goal-detail">
                    <div class="goal-detail-label">Target Date</div>
                    <div class="goal-detail-value">${targetDate}</div>
                </div>
                <div class="goal-detail">
                    <div class="goal-detail-label">Monthly Needed</div>
                    <div class="goal-detail-value">₹${g.monthly_savings_needed.toFixed(2)}</div>
                </div>
                <div class="goal-detail">
                    <div class="goal-detail-label">Months Left</div>
                    <div class="goal-detail-value">${g.months_remaining}</div>
                </div>
            </div>
            <div class="goal-actions">
                <button class="btn-add-savings" onclick="addSavings(${g.id})">💰 Add Savings</button>
                <button class="btn-delete" onclick="deleteGoal(${g.id})">🗑️ Delete</button>
            </div>
        `;
        container.appendChild(div);
    });
}

async function loadTransactions() {
    const res = await fetch('/api/transactions');
    const data = await res.json();
    allTransactions = data.transactions;
    displayTransactions(allTransactions);
}

function displayTransactions(trans) {
    const tbody = document.getElementById('transList');
    tbody.innerHTML = '';
    
    if (trans.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align:center">No transactions yet</td></tr>';
        return;
    }
    
    trans.forEach(t => {
        const row = document.createElement('tr');
        const typeClass = t.type === 'Income' ? 'type-income' : 'type-expense';
        const sign = t.type === 'Income' ? '+' : '-';
        row.innerHTML = `
            <td>${t.date}</td>
            <td class="${typeClass}">${t.type}</td>
            <td>${t.description}</td>
            <td class="${typeClass}">${sign}₹${t.amount.toFixed(2)}</td>
            <td><button onclick="deleteTrans('${t.type}', ${t.id})" class="btn-delete">Delete</button></td>
        `;
        tbody.appendChild(row);
    });
}

function searchTransactions() {
    const search = document.getElementById('searchTrans').value.toLowerCase();
    const filter = document.getElementById('filterType').value;
    
    let filtered = allTransactions;
    
    if (filter !== 'all') {
        filtered = filtered.filter(t => t.type === filter);
    }
    
    if (search) {
        filtered = filtered.filter(t => 
            t.description.toLowerCase().includes(search) ||
            t.date.includes(search) ||
            t.amount.toString().includes(search)
        );
    }
    
    displayTransactions(filtered);
}

async function loadBudgets() {
    const res = await fetch('/api/budgets');
    const data = await res.json();
    
    const container = document.getElementById('budgetList');
    container.innerHTML = '';
    
    if (data.budgets.length === 0) {
        container.innerHTML = '<p style="text-align:center;color:#999;">No budgets set yet</p>';
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
                <div class="budget-bar ${b.status}" style="width: ${Math.min(b.percentage, 100)}%">
                    ${b.percentage.toFixed(1)}%
                </div>
            </div>
            <div class="budget-details">
                <span>Spent: ₹${b.spent.toFixed(2)}</span>
                <span>Remaining: ₹${b.remaining.toFixed(2)}</span>
            </div>
            <button onclick="deleteBudget(${b.id})" class="btn-delete">Delete Budget</button>
        `;
        container.appendChild(div);
    });
}

async function loadTrends() {
    const res = await fetch('/api/trends');
    const data = await res.json();
    
    google.charts.setOnLoadCallback(() => {
        const d = new google.visualization.DataTable();
        d.addColumn('string', 'Month');
        d.addColumn('number', 'Income');
        d.addColumn('number', 'Expenses');
        d.addColumn('number', 'Savings');
        
        for (let i = 0; i < data.months.length; i++) {
            d.addRow([data.months[i], data.income[i], data.expenses[i], data.savings[i]]);
        }
        
        new google.visualization.LineChart(document.getElementById('chart3'))
            .draw(d, {
                curveType: 'function',
                colors: ['#38ef7d', '#f45c43', '#667eea'],
                backgroundColor: 'transparent',
                legend: {position: 'top'}
            });
    });
}

async function addIncome(e) {
    e.preventDefault();
    
    const data = {
        source: document.getElementById('incSource').value,
        amount: parseFloat(document.getElementById('incAmount').value),
        date: document.getElementById('incDate').value
    };
    
    const res = await fetch('/api/income', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    });
    
    if (res.ok) {
        alert('✅ Income added!');
        document.getElementById('incomeForm').reset();
        document.getElementById('incDate').value = today;
        loadDashboard();
        loadStatistics();
        loadRecommendations();
        loadTransactions();
    } else {
        alert('❌ Error adding income');
    }
}

async function addExpense(e) {
    e.preventDefault();
    
    const data = {
        category: document.getElementById('expCat').value,
        amount: parseFloat(document.getElementById('expAmount').value),
        description: document.getElementById('expDesc').value,
        date: document.getElementById('expDate').value
    };
    
    const res = await fetch('/api/expense', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    });
    
    if (res.ok) {
        alert('✅ Expense added!');
        document.getElementById('expenseForm').reset();
        document.getElementById('expDate').value = today;
        loadDashboard();
        loadStatistics();
        loadRecommendations();
        loadBudgetAlerts();
        loadTransactions();
        loadBudgets();
        loadTrends();
    } else {
        alert('❌ Error adding expense');
    }
}

async function setBudget(e) {
    e.preventDefault();
    
    const data = {
        category: document.getElementById('budCat').value,
        monthly_limit: parseFloat(document.getElementById('budLimit').value)
    };
    
    const res = await fetch('/api/budget', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    });
    
    if (res.ok) {
        alert('✅ Budget set!');
        document.getElementById('budgetForm').reset();
        loadStatistics();
        loadBudgetAlerts();
        loadBudgets();
    } else {
        alert('❌ Error setting budget');
    }
}

async function addGoal(e) {
    e.preventDefault();
    
    const data = {
        goal_name: document.getElementById('goalName').value,
        target_amount: parseFloat(document.getElementById('goalAmount').value),
        current_savings: parseFloat(document.getElementById('goalSavings').value),
        target_date: document.getElementById('goalDate').value
    };
    
    const res = await fetch('/api/goal', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    });
    
    if (res.ok) {
        alert('✅ Goal added!');
        document.getElementById('goalForm').reset();
        loadStatistics();
        loadGoals();
    } else {
        alert('❌ Error adding goal');
    }
}

async function addSavings(goalId) {
    const amount = prompt('Enter amount to add to savings (₹):');
    if (!amount || isNaN(amount) || parseFloat(amount) <= 0) return;
    
    const res = await fetch(`/api/goal/${goalId}/update`, {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({amount: parseFloat(amount)})
    });
    
    if (res.ok) {
        alert('✅ Savings updated!');
        loadGoals();
    } else {
        alert('❌ Error updating savings');
    }
}

async function deleteGoal(id) {
    if (!confirm('Delete this goal?')) return;
    
    const res = await fetch(`/api/goal/${id}`, {method: 'DELETE'});
    
    if (res.ok) {
        alert('✅ Goal deleted!');
        loadStatistics();
        loadGoals();
    }
}

async function deleteTrans(type, id) {
    if (!confirm('Delete this transaction?')) return;
    
    const endpoint = type === 'Income' ? `/api/income/${id}` : `/api/expense/${id}`;
    const res = await fetch(endpoint, {method: 'DELETE'});
    
    if (res.ok) {
        alert('✅ Deleted!');
        loadDashboard();
        loadStatistics();
        loadRecommendations();
        loadTransactions();
        loadBudgets();
        loadTrends();
    }
}

async function deleteBudget(id) {
    if (!confirm('Delete this budget?')) return;
    
    const res = await fetch(`/api/budget/${id}`, {method: 'DELETE'});
    
    if (res.ok) {
        alert('✅ Budget deleted!');
        loadStatistics();
        loadBudgetAlerts();
        loadBudgets();
    }
}

function toggleTheme() {
    document.body.classList.toggle('dark-mode');
    const btn = document.querySelector('.btn-theme');
    
    if (document.body.classList.contains('dark-mode')) {
        btn.textContent = '☀️';
        localStorage.setItem('theme', 'dark');
    } else {
        btn.textContent = '🌙';
        localStorage.setItem('theme', 'light');
    }
}

async function logout() {
    await fetch('/api/logout', {method: 'POST'});
    window.location.href = '/login';
}
// Page Navigation
function showPage(pageName) {
    // Hide all pages
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    
    // Remove active from all tabs
    document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
    
    // Show selected page
    document.getElementById(pageName + 'Page').classList.add('active');
    
    // Set active tab
    event.target.classList.add('active');
    
    // Load data for specific pages
    if (pageName === 'transactions') {
        loadTransactions();
        calculateTransactionSummary();
    } else if (pageName === 'goals') {
        loadGoals();
    } else if (pageName === 'budgets') {
        loadBudgets();
        loadBudgetAlerts();
    }
}

// Calculate transaction summary
function calculateTransactionSummary() {
    let totalIncome = 0;
    let totalExpense = 0;
    
    allTransactions.forEach(t => {
        if (t.type === 'Income') {
            totalIncome += t.amount;
        } else {
            totalExpense += t.amount;
        }
    });
    
    document.getElementById('sumIncome').textContent = '₹' + totalIncome.toFixed(2);
    document.getElementById('sumExpense').textContent = '₹' + totalExpense.toFixed(2);
    
    const balance = totalIncome - totalExpense;
    const balanceElem = document.getElementById('sumBalance');
    balanceElem.textContent = '₹' + balance.toFixed(2);
    balanceElem.style.color = balance >= 0 ? '#38ef7d' : '#f45c43';
}

// Export to CSV
function exportCSV() {
    if (allTransactions.length === 0) {
        alert('No transactions to export!');
        return;
    }
    
    let csv = 'Date,Type,Description,Amount\n';
    
    allTransactions.forEach(t => {
        const amount = t.type === 'Income' ? t.amount : -t.amount;
        csv += `${t.date},${t.type},"${t.description}",${amount}\n`;
    });
    
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `FinDash_Transactions_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
    
    alert('📥 CSV exported successfully!');
}
// SMS Modal Functions
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
    
    if (!smsText) {
        alert('Please paste your SMS first!');
        return;
    }
    
    try {
        const response = await fetch('/api/parse-sms', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({sms: smsText})
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Show parsed data
            const resultDiv = document.getElementById('smsResult');
            resultDiv.innerHTML = `
                <div style="border: 2px solid #4CAF50; padding: 15px; border-radius: 8px; background: #f0f9ff;">
                    <h3>✅ SMS Parsed Successfully!</h3>
                    <p><strong>Type:</strong> ${data.type === 'income' ? '💰 Income' : '💸 Expense'}</p>
                    <p><strong>Amount:</strong> ₹${data.amount}</p>
                    <p><strong>Description:</strong> ${data.description}</p>
                    <p><strong>Category:</strong> ${data.category}</p>
                    <p><strong>Date:</strong> ${data.date}</p>
                    <button onclick="addParsedTransaction('${data.type}', ${data.amount}, '${data.description}', '${data.category}', '${data.date}')" class="add-btn">
                        ✅ Add This Transaction
                    </button>
                </div>
            `;
        } else {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        alert('Failed to parse SMS: ' + error.message);
    }
}

async function addParsedTransaction(type, amount, description, category, date) {
    try {
        let response;
        
        if (type === 'income') {
            response = await fetch('/api/income', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    source: description,
                    amount: amount,
                    date: date
                })
            });
        } else {
            response = await fetch('/api/expense', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    category: category,
                    amount: amount,
                    description: description,
                    date: date,
                    day_type: new Date(date).getDay() >= 5 ? 'weekend' : 'weekday'
                })
            });
        }
        
        const data = await response.json();
        
        if (data.success) {
            alert('✅ Transaction added successfully!');
            closeSmsModal();
            location.reload(); // Refresh the entire page
        } else {
            alert('Error adding transaction');
        }
    } catch (error) {
        alert('Failed to add transaction: ' + error.message);
    }
}