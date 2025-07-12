from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_bcrypt import Bcrypt
import sqlite3
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = os.urandom(24)
bcrypt = Bcrypt(app)

# Database initialization
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    ''')
    
    # Create employees table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT NOT NULL,
        address TEXT NOT NULL,
        department TEXT NOT NULL
    )
    ''')
    
    # Create default admin user
    admin_exists = cursor.execute("SELECT * FROM users WHERE username = 'Anubhab'").fetchone()
    if not admin_exists:
        hashed_password = bcrypt.generate_password_hash('Anubhab123').decode('utf-8')
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", ('Anubhab', hashed_password))
    
    conn.commit()
    conn.close()

init_db()

# Database connection helper
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# Authentication middleware
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            flash('Please log in to access this page', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        if user and bcrypt.check_password_hash(user['password'], password):
            session['logged_in'] = True
            session['username'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db_connection()
    employees = conn.execute('SELECT * FROM employees').fetchall()
    conn.close()
    return render_template('dashboard.html', employees=employees)

@app.route('/add_employee', methods=['GET', 'POST'], endpoint='add_employee')
@login_required
def add_employee():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        address = request.form['address']
        department = request.form['department']
        
        conn = get_db_connection()
        try:
            conn.execute(
                'INSERT INTO employees (name, email, phone, address, department) VALUES (?, ?, ?, ?, ?)',
                (name, email, phone, address, department)
            )
            conn.commit()
            flash('Employee added successfully!', 'success')
        except sqlite3.IntegrityError:
            flash('Email already exists!', 'danger')
        finally:
            conn.close()
        
        return redirect(url_for('dashboard'))
    
    return render_template('add_employee.html')

@app.route('/edit_employee/<int:id>', methods=['GET', 'POST'], endpoint='edit_employee')
@login_required
def edit_employee(id):
    conn = get_db_connection()
    employee = conn.execute('SELECT * FROM employees WHERE id = ?', (id,)).fetchone()
    
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        address = request.form['address']
        department = request.form['department']
        
        try:
            conn.execute(
                '''UPDATE employees SET name = ?, email = ?, phone = ?, address = ?, department = ?
                WHERE id = ?''',
                (name, email, phone, address, department, id)
            )
            conn.commit()
            flash('Employee updated successfully!', 'success')
        except sqlite3.IntegrityError:
            flash('Email already exists!', 'danger')
        finally:
            conn.close()
        
        return redirect(url_for('dashboard'))
    
    conn.close()
    return render_template('edit_employee.html', employee=employee)

@app.route('/delete_employee/<int:id>', endpoint='delete_employee')
@login_required
def delete_employee(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM employees WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('Employee deleted successfully!', 'success')
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)