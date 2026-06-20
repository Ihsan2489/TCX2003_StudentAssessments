from flask import Flask, render_template, redirect, request, session, url_for, Response
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash
from decimal import Decimal, ROUND_HALF_UP
import secrets
import csv
import io
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


def create_db_session(cursor, student_id):
    session_token = secrets.token_urlsafe(32)
    cursor.execute(
        '''
        INSERT INTO sessions (
            student_id,
            session_token,
            expires_at,
            ip_address,
            user_agent
        )
        VALUES (%s, %s, DATE_ADD(NOW(), INTERVAL 8 HOUR), %s, %s)
        ''',
        (
            student_id,
            session_token,
            request.remote_addr,
            request.user_agent.string
        )
    )
    return session_token


def close_db_session(session_token):
    if not session_token:
        return

    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            '''
            UPDATE sessions
            SET logged_out_at = NOW()
            WHERE session_token = %s
            AND logged_out_at IS NULL
            ''',
            (session_token,)
        )
        connection.commit()
    except Error:
        if connection:
            connection.rollback()
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


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
                db_session_token = create_db_session(cursor, user['id'])
                connection.commit()
                session.clear()
                session['username'] = user['username']
                session['full_name'] = user.get('full_name') or user['username']
                session['email'] = user.get('email', '')
                session['db_session_token'] = db_session_token
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
    db_session_token = session.get('db_session_token')
    close_db_session(db_session_token)
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
    message = session.pop('assessment_message', '')
    attempt_result = session.pop('attempt_result', None)
    selected_task_id = attempt_result['task_id'] if attempt_result else None

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

    return render_template(
        'assessments.html',
        courses=courses,
        message=message,
        attempt_result=attempt_result,
        selected_task_id=selected_task_id
    )


@app.route('/tasks/<int:task_id>/attempts', methods=['POST'])
def submit_attempt(task_id):
    username = session.get('username')
    if not username:
        return redirect(url_for('login'))

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        connection.start_transaction()

        cursor.execute(
            'SELECT id FROM students WHERE username = %s',
            (username,)
        )
        student = cursor.fetchone()

        if not student:
            session.clear()
            return redirect(url_for('login'))

        student_id = student['id']

        # get task details, with assessment, course, enrollment
        cursor.execute(
            '''
            SELECT
                t.task_id,
                t.title AS task_title,
                t.max_score,
                a.assessment_id,
                a.due_date
            FROM tasks t
            JOIN assessments a ON a.assessment_id = t.assessment_id
            JOIN courses c ON c.course_id = a.course_id
            JOIN enrollment e ON e.course_id = c.course_id
            WHERE t.task_id = %s
            AND e.student_id = %s
            ''',
            (task_id, student_id)
        )
        task = cursor.fetchone()

        if not task:
            connection.rollback()
            session['assessment_message'] = 'Task not found or not available for your enrolled courses'
            return redirect(url_for('assessments'))

        # get number of attempts
        cursor.execute(
            '''
            SELECT COUNT(*) AS attempt_count
            FROM attempts
            WHERE student_id = %s
            AND task_id = %s
            ''',
            (student_id, task_id)
        )
        attempt_count = cursor.fetchone()['attempt_count']

        if attempt_count >= 3:
            connection.rollback()
            session['assessment_message'] = 'Attempt limit reached for this task.'
            return redirect(url_for('assessments'))

        attempt_number = attempt_count + 1

        # get questions details
        cursor.execute(
            '''
            SELECT question_id, correct_option, points
            FROM questions
            WHERE task_id = %s
            ORDER BY question_id
            ''',
            (task_id,)
        )
        questions = cursor.fetchall()

        if len(questions) != 5:
            connection.rollback()
            session['assessment_message'] = 'This task is not configured with exactly 5 questions.'
            return redirect(url_for('assessments'))

        # get the submitted answers
        submitted_answers = {}
        for question in questions:
            question_id = question['question_id']
            field_name = f'question_{question_id}'
            chosen_option = request.form.get(field_name)

            if chosen_option not in ('A', 'B', 'C', 'D'):
                connection.rollback()
                session['assessment_message'] = 'Please answer all 5 questions.'
                return redirect(url_for('assessments'))

            submitted_answers[question_id] = chosen_option

        cursor.execute(
            '''
            INSERT INTO attempts (
                student_id,
                task_id,
                attempt_number,
                submitted_at,
                status
            )
            VALUES (%s, %s, %s, NOW(), 'submitted')
            ''',
            (student_id, task_id, attempt_number)
        )

        attempt_id = cursor.lastrowid
        raw_score = Decimal('0.00')

        for question in questions:
            question_id = question['question_id']
            chosen_option = submitted_answers[question_id]
            is_correct = chosen_option == question['correct_option']
            points_awarded = question['points'] if is_correct else 0
            raw_score += Decimal(str(points_awarded))

            cursor.execute(
                '''
                INSERT INTO submitted_answers(
                    attempt_id,
                    question_id,
                    chosen_option,
                    is_correct,
                    points_awarded
                )
                VALUES(%s, %s, %s, %s, %s)
                ''',
                (attempt_id, question_id, chosen_option, is_correct, points_awarded)
            )

        cursor.execute(
            'SELECT submitted_at FROM attempts WHERE attempt_id = %s',
            (attempt_id,)
        )
        submitted_at = cursor.fetchone()['submitted_at']
        late_penalty_applied = bool(task['due_date'] and submitted_at and submitted_at > task['due_date'])
        final_score = raw_score

        if late_penalty_applied:
            final_score = raw_score * Decimal('0.90')

        final_score = final_score.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        raw_score = raw_score.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        cursor.execute(
            '''
            UPDATE attempts
            SET raw_score = %s,
                final_score = %s,
                late_penalty_applied = %s,
                status = 'graded'
            WHERE attempt_id = %s
            ''',
            (raw_score, final_score, late_penalty_applied, attempt_id)
        )

        connection.commit()

        session['assessment_message'] = (
            f'Attempt {attempt_number} submitted for {task["task_title"]}. '
            f'Score: {final_score}'
        )
        session['attempt_result'] = {
            'task_id': task_id,
            'task_title': task['task_title'],
            'attempt_number': attempt_number,
            'raw_score': str(raw_score),
            'final_score': str(final_score),
            'late_penalty_applied': late_penalty_applied
        }

    except Error as error:
        if connection:
            connection.rollback()
        session['assessment_message'] = f'Database error: {error}'
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

    return redirect(url_for('assessments'))


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

    connection = None
    cursor = None
    message = session.pop('score_message', '')
    summary = []
    submissions = []

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            'SELECT id FROM students WHERE username = %s',
            (username,)
        )
        student = cursor.fetchone()

        if not student:
            session.clear()
            return redirect(url_for('login'))

        student_id = student['id']

        cursor.execute(
            '''
            SELECT
                COUNT(att.attempt_id) AS total_attempts,
                COALESCE(AVG(att.final_score), 0) AS average_score,
                COALESCE(SUM(CASE WHEN att.late_penalty_applied = TRUE THEN 1 ELSE 0 END), 0) AS late_count
            FROM attempts att
            JOIN tasks t ON t.task_id = att.task_id
            JOIN assessments a ON a.assessment_id = t.assessment_id
            JOIN enrollment e
                ON e.course_id = a.course_id
                AND e.student_id = att.student_id
            WHERE att.student_id = %s
            AND att.status = 'graded'
            ''',
            (student_id,)
        )
        stats = cursor.fetchone()

        cursor.execute(
            '''
            SELECT GROUP_CONCAT(course_code ORDER BY course_code SEPARATOR ', ') AS course_codes
            FROM enrollment e
            JOIN courses c ON c.course_id = e.course_id
            WHERE e.student_id = %s
            ''',
            (student_id,)
        )
        enrolled_courses = cursor.fetchone()

        summary = [
            {
                'label': 'Average score',
                'value': f'{float(stats["average_score"]):.2f}'
            },
            {
                'label': 'Total attempts',
                'value': stats['total_attempts']
            },
            {
                'label': 'Late penalties',
                'value': stats['late_count']
            },
            {
                'label': 'Enrolled courses',
                'value': enrolled_courses['course_codes'] or 'None'
            },
        ]

        submissions = student_submission_table(cursor, student_id)

    except Error as error:
        message = f'Database error: {error}'
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

    return render_template(
        'score.html',
        summary=summary,
        submissions=submissions,
        message=message
    )


@app.route('/score/export')
def export_score():
    username = session.get('username')
    if not username:
        return redirect(url_for('login'))

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            'SELECT id FROM students WHERE username = %s',
            (username,)
        )
        student = cursor.fetchone()

        if not student:
            session.clear()
            return redirect(url_for('login'))

        student_id = student['id']

        submissions = student_submission_table(cursor, student_id)

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Course Code', 'Assessment Title', 'Task Title', 'Questions', 'Attempt', 'Submitted', 'Raw Score', 'Penalty', 'Final Score', 'Status'])

        for submission in submissions:
            writer.writerow([
                submission['course_code'],
                submission['assessment_title'],
                submission['task_title'],
                submission['questions'],
                submission['attempt'],
                submission['submitted'],
                submission['raw_score'],
                submission['penalty'],
                submission['final_score'],
                submission['status_label']
            ])

        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=score_export.csv'}
        )

    except Error as error:
        session['score_message'] = f'Database error: {error}'
        return redirect(url_for('score'))
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

@app.route('/leaderboard')
def leaderboard():
    username = session.get('username')
    if not username:
        return redirect(url_for('login'))

    connection = None
    cursor = None
    message = ''
    courses = []

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            '''
            SELECT
                c.course_id,
                c.course_code,
                c.course_name,
                s.id AS student_id,
                s.username,
                s.full_name,
                COUNT(DISTINCT t.task_id) AS total_tasks,
                COUNT(DISTINCT CASE
                    WHEN best_task.best_score IS NOT NULL THEN t.task_id
                END) AS tasks_completed,
                COALESCE(SUM(best_task.best_score), 0) AS course_score,
                SUM(t.max_score) AS course_max_score
            FROM enrollment e
            JOIN students s ON s.id = e.student_id
            JOIN courses c ON c.course_id = e.course_id
            JOIN assessments a ON a.course_id = c.course_id
            JOIN tasks t ON t.assessment_id = a.assessment_id
            LEFT JOIN (
                SELECT
                    student_id,
                    task_id,
                    MAX(final_score) AS best_score
                FROM attempts
                WHERE status = 'graded'
                GROUP BY student_id, task_id
            ) best_task
                ON best_task.student_id = s.id
                AND best_task.task_id = t.task_id
            GROUP BY
                c.course_id,
                c.course_code,
                c.course_name,
                s.id,
                s.username,
                s.full_name
            ORDER BY
                c.course_code,
                course_score DESC,
                tasks_completed DESC,
                s.username
            '''
        )
        rows = cursor.fetchall()
        courses_by_id = {}

        for row in rows:
            course = courses_by_id.setdefault(row['course_id'], {
                'course_id': row['course_id'],
                'course_code': row['course_code'],
                'course_name': row['course_name'],
                'leaders': []
            })

            course_score = float(row['course_score'])
            course_max_score = float(row['course_max_score'])
            percentage = (course_score / course_max_score * 100) if course_max_score else 0

            course['leaders'].append({
                'rank': len(course['leaders']) + 1,
                'username': row['username'],
                'full_name': row['full_name'],
                'tasks_completed': row['tasks_completed'],
                'total_tasks': row['total_tasks'],
                'course_score': f'{course_score:.2f}',
                'course_max_score': f'{course_max_score:.2f}',
                'percentage': f'{percentage:.2f}'
            })

        for course in courses_by_id.values():
            course['leaders'] = course['leaders'][:5]
            courses.append(course)


    except Error as error:
        message = f'Database error: {error}'
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

    return render_template(
        'leaderboard.html',
        courses=courses,
        message=message
    )


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


def student_submission_table(cursor, student_id):
    cursor.execute(
        '''
        SELECT
            c.course_code,
            a.title AS assessment_title,
            t.title AS task_title,
            t.max_score,
            att.attempt_id,
            att.attempt_number,
            att.submitted_at,
            att.raw_score,
            att.final_score,
            att.late_penalty_applied,
            att.status,
            COUNT(sa.submitted_answer_id) AS answered_questions,
            COALESCE(SUM(CASE WHEN sa.is_correct = TRUE THEN 1 ELSE 0 END), 0) AS correct_answers
        FROM attempts att
        JOIN tasks t ON t.task_id = att.task_id
        JOIN assessments a ON a.assessment_id = t.assessment_id
        JOIN courses c ON c.course_id = a.course_id
        JOIN enrollment e
            ON e.course_id = c.course_id
            AND e.student_id = att.student_id
        LEFT JOIN submitted_answers sa ON sa.attempt_id = att.attempt_id
        WHERE att.student_id = %s
        AND att.status = 'graded'
        GROUP BY
            c.course_code,
            a.title,
            t.title,
            t.max_score,
            att.attempt_id,
            att.attempt_number,
            att.submitted_at,
            att.raw_score,
            att.final_score,
            att.late_penalty_applied,
            att.status
        ORDER BY att.submitted_at DESC, att.attempt_id DESC
        ''',
        (student_id,)
    )
    attempts_data = cursor.fetchall()

    submissions = []

    for row in attempts_data:
        status_label = 'Graded'
        status_class = 'full'

        if row['late_penalty_applied']:
            status_label = 'Late penalty'
            status_class = 'late'
        elif row['final_score'] < row['max_score'] and row['attempt_number'] < 3:
            status_label = 'Can retry'
            status_class = 'partial'
        elif row['attempt_number'] >= 3:
            status_label = 'Final attempt'
            status_class = 'partial'

        submissions.append({
            'course_code': row['course_code'],
            'assessment_title': row['assessment_title'],
            'task_title': row['task_title'],
            'questions': f'{row["correct_answers"]} / {row["answered_questions"]}',
            'attempt': f'{row["attempt_number"]} of 3',
            'submitted': row['submitted_at'].strftime('%d %b %Y %H:%M') if row['submitted_at'] else 'Not submitted',
            'raw_score': f'{float(row["raw_score"]):.2f}' if row['raw_score'] is not None else '-',
            'penalty': '10%' if row['late_penalty_applied'] else 'None',
            'final_score': f'{float(row["final_score"]):.2f}' if row['final_score'] is not None else '-',
            'status_label': status_label,
            'status_class': status_class
        })

    return submissions
