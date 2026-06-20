# TCX2003 Project

Flask + MySQL student assessment system for the TCX2003 project demo.

## Local Setup

```bash
python3 -m venv .venv
source .venv/bin/activate

pip install flask
pip install mysql-connector-python
```

## Database Setup

Create tables without deleting existing data:

```bash
mysql -u root < schema.sql
```

Seed data is reset-only. For a clean demo database, run this from the project root:

```bash
mysql -u root < reset_db.sql
```

Use `-p` if your local MySQL root user has a password:

```bash
mysql -u root -p < reset_db.sql
```

## Seed Validation Queries

After running `reset_db.sql`, verify the seed data:

```sql
USE TCX2003_Project;

SELECT COUNT(*) AS course_count FROM courses;
SELECT COUNT(*) AS assessment_count FROM assessments;
SELECT COUNT(*) AS task_count FROM tasks;
SELECT COUNT(*) AS question_count FROM questions;

SELECT c.course_code, COUNT(a.assessment_id) AS assessment_count
FROM courses c
LEFT JOIN assessments a ON a.course_id = c.course_id
GROUP BY c.course_id, c.course_code
ORDER BY c.course_code;

SELECT c.course_code, a.title AS assessment_title, COUNT(t.task_id) AS task_count
FROM assessments a
JOIN courses c ON c.course_id = a.course_id
LEFT JOIN tasks t ON t.assessment_id = a.assessment_id
GROUP BY c.course_code, a.assessment_id, a.title
ORDER BY c.course_code, a.assessment_id;

SELECT t.task_id, t.title, COUNT(q.question_id) AS question_count
FROM tasks t
LEFT JOIN questions q ON q.task_id = t.task_id
GROUP BY t.task_id, t.title
HAVING question_count <> 5;
```

Expected counts:

```text
course_count = 3
assessment_count = 5
task_count = 8
question_count = 40
```

The final validation query should return zero rows. If it returns rows, those tasks do not have exactly 5 questions.

## Run App

```bash
flask --app flask_app run --debug
```

## Session Audit Check

After logging in and logging out, verify database-backed session tracking:

```sql
USE TCX2003_Project;

SELECT
    s.username,
    se.created_at,
    se.expires_at,
    se.logged_out_at,
    se.ip_address
FROM sessions se
JOIN students s ON s.id = se.student_id
ORDER BY se.created_at DESC
LIMIT 5;
```

## Batch Score Recalculation

After changing an assessment `due_date` directly in MySQL, recalculate stored
attempt scores for all students:

```bash
python3 recalculate_scores.py
```

To recalculate only one assessment:

```bash
python3 recalculate_scores.py --assessment-id 1
```
