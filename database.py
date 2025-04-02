# database.py
import sqlite3
import google.generativeai as genai
import os
from typing import Tuple, List, Dict, Any, Optional

# Configure Gemini API
GEMINI_API_KEY = "AIzaSyCp8DBUrl3mr3EIPli7H0UXgC6WZunmaNw"  # Replace with your actual API key
genai.configure(api_key=GEMINI_API_KEY)

def get_gemini_model():
    """Get the Gemini model for NL to SQL conversion"""
    return genai.GenerativeModel('gemini-1.5-pro')  # model name


def execute_query(query: str) -> Tuple[List[Dict[str, Any]], Optional[List[str]]]:
    """
    Execute an SQL query and return results and column names
    
    Args:
        query: SQL query string
    
    Returns:
        Tuple containing results and column names (if applicable)
    """
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        cursor.execute(query)
        conn.commit()
        
        # Get results for SELECT queries
        if query.strip().upper().startswith('SELECT'):
            results = [dict(row) for row in cursor.fetchall()]
            column_names = [description[0] for description in cursor.description]
            return results, column_names
        else:
            return [], None
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return [{"error": str(e)}], None
    finally:
        conn.close()

def get_table_info() -> Dict[str, List[Dict[str, str]]]:
    """
    Get information about all tables in the database
    
    Returns:
        Dictionary with table names as keys and column info as values
    """
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Get list of all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    table_info = {}
    for table in tables:
        table_name = table[0]
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        
        table_info[table_name] = [
            {
                "name": col[1],
                "type": col[2],
                "not_null": col[3],
                "primary_key": col[5]
            } for col in columns
        ]
    
    conn.close()
    return table_info

def natural_language_to_sql(nl_query: str) -> str:
    """
    Convert natural language query to SQL using Gemini API
    
    Args:
        nl_query: Natural language query string
    
    Returns:
        SQL query string
    """
    # Get table information to provide context to the model
    table_info = get_table_info()
    
    # Create prompt with database schema information
    schema_info = "Database Schema:\n"
    for table_name, columns in table_info.items():
        schema_info += f"Table: {table_name}\n"
        for col in columns:
            pk_flag = "PRIMARY KEY" if col["primary_key"] else ""
            nn_flag = "NOT NULL" if col["not_null"] else ""
            schema_info += f"  - {col['name']} ({col['type']}) {pk_flag} {nn_flag}\n"
    
    prompt = f"""
    {schema_info}
    
    Based on the database schema above, convert the following natural language query to a valid SQLite SQL statement:
    "{nl_query}"
    
    Return ONLY the SQL query with no additional text, explanations, or comments.
    """
    
    model = get_gemini_model()
    response = model.generate_content(prompt)
    
    # Extract just the SQL query from the response
    sql_query = response.text.strip()
    
    # Remove any markdown code blocks if present
    if sql_query.startswith("```sql"):
        sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
    elif sql_query.startswith("```"):
        sql_query = sql_query.replace("```", "").strip()
        
    return sql_query

def initialize_database():
    """Create some initial tables if needed"""
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Create a sample employees table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        department TEXT,
        salary REAL,
        hire_date TEXT
    )
    ''')
    
    # Create a sample departments table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS departments (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        location TEXT,
        budget REAL
    )
    ''')
    
    # Add some sample data if tables are empty
    cursor.execute("SELECT COUNT(*) FROM employees")
    if cursor.fetchone()[0] == 0:
        sample_employees = [
            (1, "John Doe", "Engineering", 85000, "2022-03-15"),
            (2, "Jane Smith", "Marketing", 75000, "2021-06-10"),
            (3, "Michael Johnson", "Engineering", 92000, "2020-11-08"),
            (4, "Emily Davis", "HR", 65000, "2023-01-20"),
            (5, "Robert Wilson", "Finance", 88000, "2021-09-12")
        ]
        cursor.executemany("INSERT INTO employees VALUES (?, ?, ?, ?, ?)", sample_employees)
    
    cursor.execute("SELECT COUNT(*) FROM departments")
    if cursor.fetchone()[0] == 0:
        sample_departments = [
            (1, "Engineering", "Building A", 1500000),
            (2, "Marketing", "Building B", 850000),
            (3, "HR", "Building A", 450000),
            (4, "Finance", "Building C", 950000)
        ]
        cursor.executemany("INSERT INTO departments VALUES (?, ?, ?, ?)", sample_departments)
    
    conn.commit()
    conn.close()