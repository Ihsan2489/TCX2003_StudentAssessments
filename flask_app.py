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
    username = session.get('username')
    if not username:
        return redirect(url_for('login'))

    connection = None
    cursor = None
    courses = []
    message = ''

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute('SELECT id FROM students WHERE username = %s', (username,))
        student = cursor.fetchone()

        if not student:
            session.clear()
            return redirect(url_for('login'))

        cursor.execute(
            '''
            SELECT
                c.course_id,
                c.course_code,
                c.course_name,
                a.assessment_id,
                a.title AS assessment_title,
                a.description AS assessment_description,
                a.due_date,
                t.task_id,
                t.title AS task_title,
                t.description AS task_description,
                t.max_score,
                q.question_id,
                q.question_text,
                q.option_a,
                q.option_b,
                q.option_c,
                q.option_d,
                COALESCE(attempt_counts.attempt_count, 0) AS attempt_count
            FROM enrollment e
            JOIN courses c ON c.course_id = e.course_id
            JOIN assessments a ON a.course_id = c.course_id
            JOIN tasks t ON t.assessment_id = a.assessment_id
            JOIN questions q ON q.task_id = t.task_id
            LEFT JOIN(
                SELECT task_id, COUNT(*) AS attempt_count
                FROM attempts
                WHERE student_id = %s
                GROUP BY task_id
            ) attempt_counts ON attempt_counts.task_id = t.task_id
            WHERE e.student_id = %s
            ORDER BY c.course_code, a.assessment_id, t.task_id, q.question_id
            ''',
            (student['id'], student['id'])
        )

        rows = cursor.fetchall()
        courses = build_assessment_tree(rows)

    except Error as error:
        message = f'Database error: {error}'
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

    return render_template('assessments.html', courses=courses, message=message)


@app.route('/courses')
def courses():
    username = session.get('username')
    if not username:
        return redirect(url_for('login'))

    courses = []
    message = session.pop('course_message', '')
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute('SELECT id FROM students WHERE username = %s', (username,))
        student = cursor.fetchone()
        if not student:
            session.clear()
            return redirect(url_for('login'))

        cursor.execute(
            '''
            SELECT
                c.course_id,
                c.course_code,
                c.course_name,
                COUNT(DISTINCT a.assessment_id) AS assessment_count,
                COUNT(DISTINCT t.task_id) AS task_count,
                CASE WHEN e.student_id IS NULL THEN 0 ELSE 1 END AS is_enrolled
            FROM courses c
            LEFT JOIN assessments a ON a.course_id = c.course_id
            LEFT JOIN tasks t ON t.assessment_id = a.assessment_id
            LEFT JOIN enrollment e
                ON e.course_id = c.course_id
                AND e.student_id = %s
            GROUP BY c.course_id, c.course_code, c.course_name, e.student_id
            ORDER BY c.course_code
            ''',
            (student['id'],)
        )
        db_courses = cursor.fetchall()
        courses = [
            {
                'courseId': course['course_id'],
                'code': course['course_code'],
                'name': course['course_name'],
                'assessments': course['assessment_count'],
                'tasks': course['task_count'],
                'isSelected': bool(course['is_enrolled'])
            }
            for course in db_courses
        ]
    except Error as error:
        message = f'Database error: {error}'
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

    return render_template('courses.html', courses=courses, message=message)


@app.route('/courses/add', methods=['POST'])
def add_course():
    username = session.get('username')
    if not username:
        return redirect(url_for('login'))

    course_id = request.form.get('course_id', type=int)
    if not course_id:
        session['course_message'] = 'Invalid course selected.'
        return redirect(url_for('courses'))

    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute('SELECT id FROM students WHERE username = %s', (username,))
        student = cursor.fetchone()
        if not student:
            session.clear()
            return redirect(url_for('login'))

        cursor.execute('SELECT course_code FROM courses WHERE course_id = %s', (course_id,))
        course = cursor.fetchone()
        if not course:
            session['course_message'] = 'Course not found.'
            return redirect(url_for('courses'))

        cursor.execute(
            'INSERT IGNORE INTO enrollment (student_id, course_id) VALUES (%s, %s)',
            (student['id'], course_id)
        )
        connection.commit()
        session['course_message'] = f'Added {course["course_code"]}.'
    except Error as error:
        if connection:
            connection.rollback()
        session['course_message'] = f'Database error: {error}'
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

    return redirect(url_for('courses'))


@app.route('/courses/drop', methods=['POST'])
def drop_course():
    username = session.get('username')
    if not username:
        return redirect(url_for('login'))

    course_id = request.form.get('course_id', type=int)
    if not course_id:
        session['course_message'] = 'Invalid course selected.'
        return redirect(url_for('courses'))

    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute('SELECT id FROM students WHERE username = %s', (username,))
        student = cursor.fetchone()
        if not student:
            session.clear()
            return redirect(url_for('login'))

        cursor.execute('SELECT course_code FROM courses WHERE course_id = %s', (course_id,))
        course = cursor.fetchone()
        if not course:
            session['course_message'] = 'Course not found.'
            return redirect(url_for('courses'))

        cursor.execute(
            'DELETE FROM enrollment WHERE student_id = %s AND course_id = %s',
            (student['id'], course_id)
        )
        connection.commit()
        session['course_message'] = f'Dropped {course["course_code"]}.'
    except Error as error:
        if connection:
            connection.rollback()
        session['course_message'] = f'Database error: {error}'
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

    return redirect(url_for('courses'))


@app.route('/score')
def score():
    username = session.get('username')
    if not username:
        return redirect(url_for('login'))

    return render_template('score.html')


@app.route('/leaderboard')
def leaderboard():
    username = session.get('username')
    if not username:
        return redirect(url_for('login'))

    return render_template('leaderboard.html')


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    username = session.get('username')
    if not username:
        return redirect(url_for('login'))

    message = ''
    message_type = ''

    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute('SELECT username, full_name, email, password_hash FROM students WHERE username = %s', (username,))
        user = cursor.fetchone()
        
        if not user:
            session.clear()
            return redirect(url_for('login'))
        
        profile_user = {
            'username': user['username'],
            'full_name': user['full_name'],
            'email': user['email']
        }
        
        if request.method == 'POST':
            current_password = request.form.get('current_password', '')
            new_password = request.form.get('new_password', '')
            confirm_password = request.form.get('confirm_password', '')
            
            if not current_password or not new_password or not confirm_password:
                message = 'Please fill out all password fields.'
                message_type = 'error'
            elif not check_password_hash(user['password_hash'], current_password):
                message = 'Current password is incorrect.'
                message_type = 'error'
            elif new_password != confirm_password:
                message = 'New passwords do not match.'
                message_type = 'error'
            elif new_password == current_password:
                message = 'New password must be different from current password.'
                message_type = 'error'
            else:
                new_password_hash = generate_password_hash(new_password)
                
                cursor.execute(
                    'UPDATE students SET password_hash = %s WHERE username = %s',
                    (new_password_hash, username)
                )
                connection.commit()
                
                message = 'Password updated successfully.'
                message_type = 'success'
    except Error as error:
        message = f'Database error: {error}'
        message_type = 'error'
        profile_user = {
            'username': username,
            'full_name': session.get('full_name', username),
            'email': session.get('email', '')
        }
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

    return render_template('profile.html', user=profile_user, message=message, message_type=message_type)


def build_assessment_tree(rows):
    courses_by_id = {}

    for row in rows:
        course = courses_by_id.setdefault(row['course_id'], {
            'course_id': row['course_id'],
            'course_code': row['course_code'],
            'course_name': row['course_name'],
            'assessments': {}
        })

        assessment = course['assessments'].setdefault(row['assessment_id'], {
            'assessment_id': row['assessment_id'],
            'title': row['assessment_title'],
            'description': row['assessment_description'],
            'due_date': row['due_date'],
            'due_date_display': row['due_date'].strftime('%d %b %Y, %H:%M') if row['due_date'] else 'No due date',
            'tasks': {}
        })

        attempt_count = row['attempt_count']
        task = assessment['tasks'].setdefault(row['task_id'], {
            'task_id': row['task_id'],
            'title': row['task_title'],
            'description': row['task_description'],
            'max_score': row['max_score'],
            'attempt_count': attempt_count,
            'next_attempt_number': min(attempt_count + 1, 3),
            'is_locked': attempt_count >= 3,
            'questions': []
        })

        task['questions'].append({
            'question_id': row['question_id'],
            'question_text': row['question_text'],
            'option_a': row['option_a'],
            'option_b': row['option_b'],
            'option_c': row['option_c'],
            'option_d': row['option_d']
        })

    # turn all to list
    courses = list(courses_by_id.values())

    for course in courses:
        course['assessments'] = list(course['assessments'].values())
        for assessment in course['assessments']:
            assessment['tasks'] = list(assessment['tasks'].values())

    return courses
