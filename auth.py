# auth.py
from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from database import execute_query
import sqlite3

# Create authentication blueprint
auth = Blueprint('auth', __name__)

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, id, username, email, password):
        self.id = id
        self.username = username
        self.email = email
        self.password = password

    @staticmethod
    def get(user_id):
        conn = sqlite3.connect('database.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return User(
                id=user['id'],
                username=user['username'],
                email=user['email'],
                password=user['password']
            )
        return None

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

# Create users table
def initialize_users_table():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT NOT NULL UNIQUE,
        email TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL
    )
    ''')
    
    conn.commit()
    conn.close()

# Login route
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = sqlite3.connect('database.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            user_obj = User(
                id=user['id'],
                username=user['username'],
                email=user['email'],
                password=user['password']
            )
            login_user(user_obj)
            return redirect(url_for('dashboard'))  # Fixed: Changed 'index' to 'dashboard'
        else:
            flash('Invalid username or password.')
    
    return render_template('login.html')

# Signup route
@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match.')
            return render_template('signup.html')
        
        hashed_password = generate_password_hash(password)
        
        try:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                (username, email, hashed_password)
            )
            conn.commit()
            conn.close()
            
            flash('Account created successfully. Please log in.')
            return redirect(url_for('auth.login'))
        except sqlite3.IntegrityError:
            flash('Username or email already exists.')
            conn.close()
    
    return render_template('signup.html')

# Logout route
@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

# Profile route
@auth.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        
        conn = sqlite3.connect('database.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE id = ?", (current_user.id,))
        user = cursor.fetchone()
        
        if not check_password_hash(user['password'], current_password):
            flash('Current password is incorrect.')
            conn.close()
            return redirect(url_for('auth.profile'))
        
        try:
            if new_password:
                hashed_password = generate_password_hash(new_password)
                cursor.execute(
                    "UPDATE users SET username = ?, email = ?, password = ? WHERE id = ?",
                    (username, email, hashed_password, current_user.id)
                )
            else:
                cursor.execute(
                    "UPDATE users SET username = ?, email = ? WHERE id = ?",
                    (username, email, current_user.id)
                )
            
            conn.commit()
            conn.close()
            flash('Profile updated successfully.')
            return redirect(url_for('auth.profile'))
        except sqlite3.IntegrityError:
            conn.close()
            flash('Username or email already exists.')
    
    return render_template('profile.html', user=current_user)