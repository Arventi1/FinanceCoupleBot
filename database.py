import sqlite3
from datetime import datetime, date, timedelta
from config import DB_PATH, MY_USER_ID, GIRLFRIEND_USER_ID

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Таблица пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT
        )
    ''')
    
    # Таблица транзакций
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            type TEXT CHECK(type IN ('income', 'expense')),
            amount REAL,
            category TEXT,
            description TEXT,
            date DATE DEFAULT CURRENT_DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Таблица планов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT,
            description TEXT,
            date DATE,
            time TEXT,
            notification_enabled BOOLEAN DEFAULT 1,
            notification_time TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Таблица покупок
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS planned_purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            item_name TEXT,
            estimated_cost REAL,
            priority TEXT CHECK(priority IN ('low', 'medium', 'high')),
            target_date DATE,
            notes TEXT,
            status TEXT DEFAULT 'planned',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def add_user(user_id, username, full_name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        'INSERT OR IGNORE INTO users (id, username, full_name) VALUES (?, ?, ?)',
        (user_id, username, full_name)
    )
    conn.commit()
    conn.close()

def add_transaction(user_id, trans_type, amount, category, description=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO transactions (user_id, type, amount, category, description, date)
        VALUES (?, ?, ?, ?, ?, DATE('now'))
    ''', (user_id, trans_type, amount, category, description))
    conn.commit()
    conn.close()

def add_plan(user_id, title, description, plan_date, time=None, notification_time=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO plans (user_id, title, description, date, time, notification_time)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, title, description, plan_date, time, notification_time))
    conn.commit()
    conn.close()

def add_planned_purchase(user_id, item_name, estimated_cost, priority, target_date=None, notes=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO planned_purchases (user_id, item_name, estimated_cost, priority, target_date, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, item_name, estimated_cost, priority, target_date, notes))
    conn.commit()
    conn.close()

def get_transactions(user_id, period='today'):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if period == 'today':
        query = """
            SELECT type, amount, category, description, 
                   strftime('%H:%M', created_at) as time
            FROM transactions 
            WHERE user_id = ? AND date = DATE('now') 
            ORDER BY created_at DESC
        """
        cursor.execute(query, (user_id,))
    elif period == 'week':
        query = """
            SELECT type, amount, category, description, date,
                   strftime('%H:%M', created_at) as time
            FROM transactions 
            WHERE user_id = ? AND date >= DATE('now', '-7 days') 
            ORDER BY date DESC, created_at DESC
        """
        cursor.execute(query, (user_id,))
    elif period == 'month':
        query = """
            SELECT type, amount, category, description, date,
                   strftime('%H:%M', created_at) as time
            FROM transactions 
            WHERE user_id = ? AND strftime('%Y-%m', date) = strftime('%Y-%m', 'now') 
            ORDER BY date DESC, created_at DESC
        """
        cursor.execute(query, (user_id,))
    
    results = cursor.fetchall()
    conn.close()
    return results

def get_period_statistics(user_id, period='month'):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if period == 'today':
        cursor.execute('''
            SELECT 
                SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) as total_income,
                SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) as total_expense,
                COUNT(*) as count
            FROM transactions 
            WHERE user_id = ? AND date = DATE('now')
        ''', (user_id,))
    elif period == 'week':
        cursor.execute('''
            SELECT 
                SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) as total_income,
                SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) as total_expense,
                COUNT(*) as count
            FROM transactions 
            WHERE user_id = ? AND date >= DATE('now', '-7 days')
        ''', (user_id,))
    elif period == 'month':
        cursor.execute('''
            SELECT 
                SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) as total_income,
                SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) as total_expense,
                COUNT(*) as count
            FROM transactions 
            WHERE user_id = ? AND strftime('%Y-%m', date) = strftime('%Y-%m', 'now')
        ''', (user_id,))
    elif period == 'all':
        cursor.execute('''
            SELECT 
                SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) as total_income,
                SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) as total_expense,
                COUNT(*) as count
            FROM transactions 
            WHERE user_id = ?
        ''', (user_id,))
    
    result = cursor.fetchone()
    conn.close()
    return result

def get_partner_transactions(user_id, period='today'):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if user_id == MY_USER_ID:
        partner_id = GIRLFRIEND_USER_ID
    else:
        partner_id = MY_USER_ID
    
    if period == 'today':
        cursor.execute('''
            SELECT category, SUM(amount), COUNT(*)
            FROM transactions 
            WHERE user_id = ? 
            AND type = 'expense'
            AND date = DATE('now')
            GROUP BY category
            ORDER BY SUM(amount) DESC
        ''', (partner_id,))
    elif period == 'month':
        cursor.execute('''
            SELECT category, SUM(amount), COUNT(*)
            FROM transactions 
            WHERE user_id = ? 
            AND type = 'expense'
            AND strftime('%Y-%m', date) = strftime('%Y-%m', 'now')
            GROUP BY category
            ORDER BY SUM(amount) DESC
        ''', (partner_id,))
    
    results = cursor.fetchall()
    conn.close()
    return results

def get_daily_plans(user_id, target_date=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if not target_date:
        target_date = date.today().isoformat()
    
    cursor.execute('''
        SELECT * FROM plans 
        WHERE user_id = ? AND date = ? 
        ORDER BY time
    ''', (user_id, target_date))
    
    results = cursor.fetchall()
    conn.close()
    return results

def get_planned_purchases(user_id, status='planned'):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM planned_purchases 
        WHERE user_id = ? AND status = ?
        ORDER BY 
            CASE priority 
                WHEN 'high' THEN 1
                WHEN 'medium' THEN 2
                WHEN 'low' THEN 3
            END,
            target_date
    ''', (user_id, status))
    
    results = cursor.fetchall()
    conn.close()
    return results

def get_today_reminders():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT p.*, u.username 
        FROM plans p
        JOIN users u ON p.user_id = u.id
        WHERE p.date = DATE('now') 
        AND p.notification_enabled = 1
        AND p.notification_time IS NOT NULL
    ''')
    
    results = cursor.fetchall()
    conn.close()
    return results

def get_common_categories_statistics():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            category,
            SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) as total_expense,
            COUNT(*) as transaction_count
        FROM transactions 
        WHERE strftime('%Y-%m', date) = strftime('%Y-%m', 'now')
        AND user_id IN (?, ?)
        GROUP BY category
        ORDER BY total_expense DESC
        LIMIT 10
    ''', (MY_USER_ID, GIRLFRIEND_USER_ID))
    
    results = cursor.fetchall()
    conn.close()
    return results

def get_daily_combined_expenses(target_date=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if not target_date:
        target_date = date.today().isoformat()
    
    cursor.execute('''
        SELECT 
            u.full_name,
            t.category,
            t.amount,
            t.description,
            t.created_at
        FROM transactions t
        JOIN users u ON t.user_id = u.id
        WHERE t.date = ? 
        AND t.type = 'expense'
        AND t.user_id IN (?, ?)
        ORDER BY u.full_name, t.created_at DESC
    ''', (target_date, MY_USER_ID, GIRLFRIEND_USER_ID))
    
    results = cursor.fetchall()
    conn.close()
    return results

def get_monthly_comparison():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            u.full_name,
            SUM(CASE WHEN t.type = 'income' THEN amount ELSE 0 END) as total_income,
            SUM(CASE WHEN t.type = 'expense' THEN amount ELSE 0 END) as total_expense,
            (SUM(CASE WHEN t.type = 'income' THEN amount ELSE 0 END) - 
             SUM(CASE WHEN t.type = 'expense' THEN amount ELSE 0 END)) as balance
        FROM transactions t
        JOIN users u ON t.user_id = u.id
        WHERE strftime('%Y-%m', t.date) = strftime('%Y-%m', 'now')
        AND t.user_id IN (?, ?)
        GROUP BY u.full_name
    ''', (MY_USER_ID, GIRLFRIEND_USER_ID))
    
    results = cursor.fetchall()
    conn.close()
    return results

def get_shared_expenses_by_category():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            t.category,
            SUM(CASE WHEN t.user_id = ? THEN t.amount ELSE 0 END) as user1_expenses,
            SUM(CASE WHEN t.user_id = ? THEN t.amount ELSE 0 END) as user2_expenses,
            SUM(t.amount) as total
        FROM transactions t
        WHERE strftime('%Y-%m', t.date) = strftime('%Y-%m', 'now')
        AND t.type = 'expense'
        GROUP BY t.category
        ORDER BY total DESC
    ''', (MY_USER_ID, GIRLFRIEND_USER_ID))
    
    results = cursor.fetchall()
    conn.close()
    return results

def get_combined_statistics(period='month'):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if period == 'month':
        cursor.execute('''
            SELECT 
                SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) as total_income,
                SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) as total_expense,
                user_id
            FROM transactions 
            WHERE strftime('%Y-%m', date) = strftime('%Y-%m', 'now')
            GROUP BY user_id
        ''')
    
    results = cursor.fetchall()
    conn.close()
    return results

def get_recent_transactions(user_id, limit=10):
    """Получить последние транзакции"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT type, amount, category, description, 
               strftime('%Y-%m-%d %H:%M', created_at) as datetime
        FROM transactions 
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT ?
    ''', (user_id, limit))
    
    results = cursor.fetchall()
    conn.close()
    return results

def get_all_time_statistics(user_id):
    """Получить статистику за все время"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT 
            SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) as total_income,
            SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) as total_expense,
            COUNT(*) as count
        FROM transactions 
        WHERE user_id = ?
    ''', (user_id,))
    
    result = cursor.fetchone()
    conn.close()
    return result

def get_weekly_summary():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            u.full_name,
            DATE(t.date, 'weekday 0', '-6 days') as week_start,
            SUM(CASE WHEN t.type = 'income' THEN t.amount ELSE 0 END) as weekly_income,
            SUM(CASE WHEN t.type = 'expense' THEN t.amount ELSE 0 END) as weekly_expense
        FROM transactions t
        JOIN users u ON t.user_id = u.id
        WHERE t.date >= DATE('now', '-30 days')
        AND u.id IN (?, ?)
        GROUP BY u.full_name, week_start
        ORDER BY week_start DESC
        LIMIT 4
    ''', (MY_USER_ID, GIRLFRIEND_USER_ID))
    
    results = cursor.fetchall()
    conn.close()
    return results
