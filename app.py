# app.py
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_login import login_required, current_user, login_user
from database import execute_query, natural_language_to_sql, get_table_info, initialize_database
from auth import auth, login_manager, initialize_users_table
import webbrowser
import threading
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this to a secure random key in production

# Register the auth blueprint
app.register_blueprint(auth, url_prefix='/auth')

# Initialize login manager
login_manager.init_app(app)

@app.route('/intro')
def intro():
    """Render the intro splash screen"""
    return render_template('intro.html')

@app.route('/')
def landing():
    """Show intro page for guests, redirect to main app for authenticated users"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('intro.html')

@app.route('/dashboard')
@login_required
def dashboard():
    """Render the main dashboard with database information"""
    table_info = get_table_info()
    return render_template('index.html', table_info=table_info, user=current_user)

@app.route('/query', methods=['POST'])
@login_required
def process_query():
    """Process natural language query and return results"""
    nl_query = request.form.get('nl_query', '')
    
    try:
        # Convert natural language to SQL
        sql_query = natural_language_to_sql(nl_query)
        
        # Execute the SQL query
        results, columns = execute_query(sql_query)
        
        return jsonify({
            'success': True,
            'nl_query': nl_query,
            'sql_query': sql_query,
            'results': results,
            'columns': columns
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/execute_sql', methods=['POST'])
@login_required
def execute_sql():
    """Directly execute SQL query (for advanced users)"""
    sql_query = request.form.get('sql_query', '')
    
    try:
        # Execute the SQL query
        results, columns = execute_query(sql_query)
        
        return jsonify({
            'success': True,
            'sql_query': sql_query,
            'results': results,
            'columns': columns
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/get_schema')
@login_required
def get_schema():
    """Get current database schema"""
    return jsonify(get_table_info())

def open_browser():
    """Open browser after a short delay"""
    time.sleep(1.5)  # Wait for the server to start
    webbrowser.open('http://127.0.0.1:5000')

if __name__ == '__main__':
    # Initialize database with sample data
    initialize_database()
    initialize_users_table()
    
    # Start browser in a new thread
    threading.Thread(target=open_browser).start()
    
    # Run the Flask app
    app.run(debug=True)