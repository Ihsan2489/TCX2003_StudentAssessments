from flask import Flask, render_template, redirect, request, session, url_for
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash
# import re

app = Flask(__name__)
app.debug = True
app.secret_key = 'dev-secret-key'

# set mysql connection
db_config = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',
    'password': '',
    'database': 'TCX2003_Project'
}


def get_db_connection():
    return mysql.connector.connect(**db_config)


@app.route('/')
def index():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('username') and request.method == 'GET':
        return redirect(url_for('home'))

    if request.method == 'POST':
        # Get form data
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        # Validate form data
        if not username or not password:
            message = 'Please enter both username and password.'
            return render_template('login.html', message=message)

        # Check credentials against the database
        connection = None
        cursor = None
        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            cursor.execute('SELECT * FROM students WHERE username = %s', (username,))
            user = cursor.fetchone()
            if user and check_password_hash(user['password_hash'], password):
                session['username'] = user['username']
                session['full_name'] = user.get('full_name') or user['username']
                session['email'] = user.get('email', '')
                return redirect(url_for('home'))
            else:
                message = 'Invalid username or password.'
                return render_template('login.html', message=message)
        except Error as error:
            message = f'Database error: {error}'
            return render_template('login.html', message=message)
        finally:
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    message = ''
    if request.method == 'POST':
        # Get form data
        username = request.form.get('username', '').strip()
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Validate form data
        if not username or not full_name or not email or not password or not confirm_password:
            message = 'Please fill out all fields.'
        elif password != confirm_password:
            message = 'Passwords do not match.'
        else:
            # Check if username already exists
            connection = None
            cursor = None
            try:
                connection = get_db_connection()
                cursor = connection.cursor(dictionary=True)
                cursor.execute('SELECT username FROM students WHERE username = %s OR email = %s', (username, email))
                existing_user = cursor.fetchone()
                if existing_user:
                    message = 'Username or email already exists. Please choose a different one.'
                else:
                    # Hash the password and store the new user in the database
                    hashed_password = generate_password_hash(password)
                    cursor.execute(
                        'INSERT INTO students (username, full_name, email, password_hash) VALUES (%s, %s, %s, %s)',
                        (username, full_name, email, hashed_password)
                    )
                    connection.commit()
                    return redirect(url_for('login'))
            except Error as error:
                message = f'Database error: {error}'
            finally:
                if cursor:
                    cursor.close()
                if connection and connection.is_connected():
                    connection.close()
    return render_template('register.html', message=message)


@app.route('/home')
def home():
    username = session.get('username')
    if not username:
        return redirect(url_for('login'))
    user = {
        'username': username,
        'full_name': session.get('full_name', username)
    }
    return render_template('home.html', user=user)


@app.route('/assessments')
def assessments():
    return render_template('assessments.html')


@app.route('/groups')
def groups():
    return render_template('groups.html')


@app.route('/score')
def score():
    return render_template('score.html')


@app.route('/leaderboard')
def leaderboard():
    return render_template('leaderboard.html')


@app.route('/profile')
def profile():
    username = session.get('username')
    if not username:
        return redirect(url_for('login'))

    user = {
        'username': username,
        'full_name': session.get('full_name', username),
        'email': session.get('email', '')
    }

    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute('SELECT username, full_name, email FROM students WHERE username = %s', (username,))
        db_user = cursor.fetchone()
        if db_user:
            user = db_user
            session['full_name'] = db_user.get('full_name') or username
            session['email'] = db_user.get('email', '')
    except Error:
        pass
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

    return render_template('profile.html', user=user)
