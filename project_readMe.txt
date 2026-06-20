TCX2003 Project ReadMe
======================

Project summary
---------------

This project is a Flask + MySQL student assessment system.

The original TCX2003 requirement describes SQL submission and SQL auto-grading.
The professor-approved adaptation for this project is MCQ auto-grading.

The project still needs to demonstrate the original intent:

- secure student login with hashed passwords
- password change
- course enrollment
- assessments under enrolled courses
- tasks under assessments
- exactly 5 MCQ questions per task
- up to 3 attempts per task per student
- every attempt and selected answer stored
- automatic grading
- personal score display
- leaderboard
- late penalty
- CSV export


Database tables and columns
---------------------------

Database name:

- TCX2003_Project


1. students
-----------

Purpose:
Stores student account records.

Columns:

- id
  - INT AUTO_INCREMENT
  - Primary key
  - Internal student identifier

- username
  - VARCHAR(50)
  - NOT NULL
  - UNIQUE
  - Used for login

- full_name
  - VARCHAR(100)
  - NOT NULL
  - Student's display name

- email
  - VARCHAR(255)
  - NOT NULL
  - UNIQUE
  - Student email

- password_hash
  - VARCHAR(255)
  - NOT NULL
  - Stores hashed password, never plaintext password

- created_at
  - DATETIME
  - NOT NULL
  - Defaults to CURRENT_TIMESTAMP


2. courses
----------

Purpose:
Stores available courses.

Columns:

- course_id
  - INT AUTO_INCREMENT
  - Primary key

- course_name
  - VARCHAR(100)
  - NOT NULL
  - Human-readable course name

- course_code
  - VARCHAR(20)
  - NOT NULL
  - UNIQUE
  - Example: CS101, CS102, CS201

- created_at
  - DATETIME
  - NOT NULL
  - Defaults to CURRENT_TIMESTAMP


3. enrollment
-------------

Purpose:
Join table between students and courses.

This table supports the many-to-many relationship:

- one student can enroll in many courses
- one course can have many students

Columns:

- student_id
  - INT
  - NOT NULL
  - Foreign key to students.id

- course_id
  - INT
  - NOT NULL
  - Foreign key to courses.course_id

- enrollment_at
  - DATETIME
  - NOT NULL
  - Defaults to CURRENT_TIMESTAMP

Primary key:

- (student_id, course_id)

This prevents duplicate enrollment for the same student and course.


4. sessions
-----------

Purpose:
Stores login session records if session-token tracking is implemented.

Columns:

- session_id
  - INT AUTO_INCREMENT
  - Primary key

- student_id
  - INT
  - NOT NULL
  - Foreign key to students.id

- session_token
  - VARCHAR(255)
  - NOT NULL
  - UNIQUE

- created_at
  - DATETIME
  - NOT NULL
  - Defaults to CURRENT_TIMESTAMP

- expires_at
  - DATETIME
  - NOT NULL

- logged_out_at
  - DATETIME
  - Nullable

- ip_address
  - VARCHAR(45)
  - Nullable

- user_agent
  - TEXT
  - Nullable

Current implementation note:
The current Flask app uses Flask's session object. The sessions table exists in
the schema but is not fully used yet.


5. assessments
--------------

Purpose:
Stores assessments for each course.

Columns:

- assessment_id
  - INT AUTO_INCREMENT
  - Primary key

- course_id
  - INT
  - NOT NULL
  - Foreign key to courses.course_id

- title
  - VARCHAR(255)
  - NOT NULL

- description
  - TEXT
  - Nullable

- due_date
  - DATETIME
  - NOT NULL
  - Used for late penalty calculation

- created_at
  - DATETIME
  - NOT NULL
  - Defaults to CURRENT_TIMESTAMP


6. tasks
--------

Purpose:
Stores tasks under each assessment.

Columns:

- task_id
  - INT AUTO_INCREMENT
  - Primary key

- assessment_id
  - INT
  - NOT NULL
  - Foreign key to assessments.assessment_id

- title
  - VARCHAR(255)
  - NOT NULL

- description
  - TEXT
  - Nullable

- max_score
  - INT
  - NOT NULL
  - Defaults to 0
  - For current seed data, max_score is 5 because each task has 5 questions

- created_at
  - DATETIME
  - NOT NULL
  - Defaults to CURRENT_TIMESTAMP


7. questions
------------

Purpose:
Stores MCQ questions for each task.

Project rule:
Each task must have exactly 5 questions.

Columns:

- question_id
  - INT AUTO_INCREMENT
  - Primary key

- task_id
  - INT
  - NOT NULL
  - Foreign key to tasks.task_id

- question_text
  - TEXT
  - NOT NULL

- option_a
  - VARCHAR(255)
  - NOT NULL

- option_b
  - VARCHAR(255)
  - NOT NULL

- option_c
  - VARCHAR(255)
  - NOT NULL

- option_d
  - VARCHAR(255)
  - NOT NULL

- correct_option
  - ENUM('A', 'B', 'C', 'D')
  - NOT NULL
  - Correct MCQ answer

- points
  - INT
  - NOT NULL
  - Defaults to 1

- created_at
  - DATETIME
  - NOT NULL
  - Defaults to CURRENT_TIMESTAMP

- updated_at
  - DATETIME
  - NOT NULL
  - Defaults to CURRENT_TIMESTAMP and updates automatically


8. attempts
-----------

Purpose:
Stores one row per student attempt on one task.

Important rule:
Do not update an old attempt row into a new attempt.
Each new attempt creates a new row.

Columns:

- attempt_id
  - INT AUTO_INCREMENT
  - Primary key

- student_id
  - INT
  - NOT NULL
  - Foreign key to students.id

- task_id
  - INT
  - NOT NULL
  - Foreign key to tasks.task_id

- attempt_number
  - INT
  - NOT NULL
  - Defaults to 1
  - Must be assigned by backend logic as 1, 2, or 3

- started_at
  - DATETIME
  - NOT NULL
  - Defaults to CURRENT_TIMESTAMP

- submitted_at
  - DATETIME
  - Nullable
  - Null means attempt is still in progress

- raw_score
  - DECIMAL(5,2)
  - Nullable
  - Score before late penalty

- final_score
  - DECIMAL(5,2)
  - Nullable
  - Score after late penalty

- late_penalty_applied
  - BOOLEAN
  - Defaults to FALSE

- status
  - ENUM('in_progress', 'submitted', 'graded')
  - NOT NULL
  - Defaults to in_progress

Unique key:

- (student_id, task_id, attempt_number)

This prevents duplicate attempt numbers for the same student and task.

Backend must still block attempt_number greater than 3.


9. submitted_answers
--------------------

Purpose:
Stores the student's selected answer for each question in an attempt.

Project rule:
Each submitted attempt should have 5 submitted_answers rows.

Columns:

- submitted_answer_id
  - INT AUTO_INCREMENT
  - Primary key

- attempt_id
  - INT
  - NOT NULL
  - Foreign key to attempts.attempt_id

- question_id
  - INT
  - NOT NULL
  - Foreign key to questions.question_id

- chosen_option
  - ENUM('A', 'B', 'C', 'D')
  - NOT NULL

- is_correct
  - BOOLEAN
  - Nullable
  - Stores grading snapshot

- points_awarded
  - INT
  - Nullable
  - Usually 1 if correct, 0 if incorrect

Unique key:

- (attempt_id, question_id)

This prevents answering the same question twice in the same attempt.


Table relationships
-------------------

1. students to enrollment

- students.id -> enrollment.student_id
- One student can have many enrollment rows.

2. courses to enrollment

- courses.course_id -> enrollment.course_id
- One course can have many enrolled students.

3. courses to assessments

- courses.course_id -> assessments.course_id
- One course can have many assessments.

4. assessments to tasks

- assessments.assessment_id -> tasks.assessment_id
- One assessment can have many tasks.

5. tasks to questions

- tasks.task_id -> questions.task_id
- One task has exactly 5 questions by project rule.

6. students to attempts

- students.id -> attempts.student_id
- One student can have many attempts.

7. tasks to attempts

- tasks.task_id -> attempts.task_id
- One task can have many attempts from many students.

8. attempts to submitted_answers

- attempts.attempt_id -> submitted_answers.attempt_id
- One attempt should have 5 submitted answers.

9. questions to submitted_answers

- questions.question_id -> submitted_answers.question_id
- A submitted answer belongs to one question.


Relationship summary
--------------------

students M:N courses through enrollment
courses 1:M assessments
assessments 1:M tasks
tasks 1:M questions
students 1:M attempts
tasks 1:M attempts
attempts 1:M submitted_answers
questions 1:M submitted_answers


3NF explanation
---------------

The schema is defensible as 3NF because parent information is not duplicated in
child tables.

Examples:

- assessments stores course_id, not course_name
- tasks stores assessment_id, not assessment title
- questions stores task_id, not course or assessment data
- enrollment stores only student_id and course_id

Some derived grading snapshot fields are intentionally stored:

- attempts.raw_score
- attempts.final_score
- attempts.late_penalty_applied
- submitted_answers.is_correct
- submitted_answers.points_awarded

These are redundant from a strict normalization perspective, but acceptable here
because they preserve grading history and make the demo easier to explain.


Seeded tester accounts and demo data
------------------------------------

The seed data includes seven tester accounts for demo and testing.

All tester accounts are enrolled in CS101 so the course-level leaderboard can
show a top 5 ranking from one course.

All tester accounts use the same password:

- Tester123!

Important:
The password is stored in the database as a Werkzeug password hash. The plaintext
password is listed here only so the team can log in during the demo.


1. adam01
---------

Login:

- username: adam01
- password: Tester123!
- full_name: Adam tester
- email: adam01@gmail.com

Enrolled courses:

- CS101
- CS102
- CS201

Seeded attempts:

- CS102 / Relational Model
  - Attempt 1: raw_score = 2.00, final_score = 2.00
  - Attempt 2: raw_score = 5.00, final_score = 5.00

- CS101 / Variables and Data Types
  - Attempt 1: raw_score = 5.00, final_score = 5.00

Demo use:

- Shows a student enrolled in all 3 courses.
- Shows resubmission improvement from partial marks to full marks.
- Useful for demonstrating that personal scores show multiple attempts.
- Useful for leaderboard testing because Adam has a best full-mark attempt.


2. sarah02
----------

Login:

- username: sarah02
- password: Tester123!
- full_name: Sarah tester
- email: sarah02@gmail.com

Enrolled courses:

- CS101
- CS102

Seeded attempts:

- CS101 / Variables and Data Types
  - Attempt 1: raw_score = 5.00, final_score = 5.00

- CS102 / SQL Basics
  - Attempt 1: raw_score = 4.00, final_score = 4.00

Demo use:

- Shows a student with both full-mark and partial-mark attempts.
- Useful for personal score page testing.
- Useful for leaderboard comparison against Adam and Danial.


3. danial03
-----------

Login:

- username: danial03
- password: Tester123!
- full_name: Danial tester
- email: danial03@gmail.com

Enrolled courses:

- CS101
- CS102

Seeded attempts:

- CS101 / Variables and Data Types
  - Attempt 1: raw_score = 5.00
  - final_score = 4.50
  - late_penalty_applied = TRUE

- CS102 / SQL Basics
  - Attempt 1: raw_score = 5.00
  - final_score = 4.50
  - late_penalty_applied = TRUE

Demo use:

- Shows the late penalty scenario.
- Useful for explaining raw_score versus final_score.
- Useful for verifying that the score page displays late penalties correctly.
- Useful for showing a CS101 leaderboard student whose final_score is reduced
  by penalty.


4. hannah04
-----------

Login:

- username: hannah04
- password: Tester123!
- full_name: Hannah tester
- email: hannah04@gmail.com

Enrolled courses:

- CS101
- CS201

Seeded attempts:

- CS101 / Loops
  - Attempt 1: raw_score = 3.00, final_score = 3.00

- CS201 / Logic and Sets
  - Attempt 1: raw_score = 3.00, final_score = 3.00

Demo use:

- Shows a partial attempt where the student can still retry.
- Useful for verifying that assessments and scores are filtered by enrolled
  courses.


5. rayan05
----------

Login:

- username: rayan05
- password: Tester123!
- full_name: Rayan tester
- email: rayan05@gmail.com

Enrolled courses:

- CS101

Seeded attempts:

- CS101 / Conditionals
  - Attempt 1: raw_score = 2.00, final_score = 2.00
  - Attempt 2: raw_score = 3.00, final_score = 3.00
  - Attempt 3: raw_score = 4.00, final_score = 4.00

Demo use:

- Shows the 3-attempt limit.
- Useful for verifying that the assessment page disables or blocks another
  submission after 3 attempts.
- Useful for explaining why attempt_number is part of the attempts table.


6. zara06
---------

Login:

- username: zara06
- password: Tester123!
- full_name: Zara tester
- email: zara06@gmail.com

Enrolled courses:

- CS101

Seeded attempts:

- CS101 / Functions and Lists
  - Attempt 1: raw_score = 4.00, final_score = 4.00

Demo use:

- Adds another CS101 leaderboard competitor.
- Shows a partial score that can still be improved.


7. zain07
---------

Login:

- username: zain07
- password: Tester123!
- full_name: Zain tester
- email: zain07@gmail.com

Enrolled courses:

- CS101

Seeded attempts:

- CS101 / Variables and Data Types
  - Attempt 1: raw_score = 2.00, final_score = 2.00

Demo use:

- Adds another CS101 enrolled student.
- Shows a low partial score that can still be improved.


Seeded demo data counts
-----------------------

After a clean reset with reset_db.sql, the demo database should contain:

- 3 courses
- 5 assessments
- 8 tasks
- 40 questions
- 7 tester students
- 12 enrollment rows
- 14 graded attempt rows
- 70 submitted answer rows


Project and demo flows
----------------------

Flow 1: Register

1. Student opens /register.
2. Student enters username, full name, email, password, confirm password.
3. Flask validates fields.
4. Flask checks username/email uniqueness.
5. Flask hashes password using Werkzeug generate_password_hash.
6. Flask inserts student into students table.
7. Student is redirected to /login.


Flow 2: Login

1. Student opens /login.
2. Student enters username and password.
3. Flask fetches matching student by username.
4. Flask checks submitted password against students.password_hash.
5. If valid, Flask stores username, full_name, and email in session.
6. Student is redirected to /home.


Flow 3: Logout

1. Student clicks logout.
2. Flask clears the session.
3. Student is redirected to /login.


Flow 4: Add course

1. Student opens /courses.
2. Flask fetches all courses.
3. Flask checks enrollment table to mark selected courses.
4. Student clicks Add course.
5. Confirmation modal appears.
6. Student confirms.
7. Flask inserts into enrollment(student_id, course_id).
8. /courses reloads and shows the course as selected.


Flow 5: Drop course

1. Student opens /courses.
2. Student clicks Drop course for an enrolled course.
3. Confirmation modal appears.
4. Student confirms.
5. Flask deletes the row from enrollment.
6. /courses reloads and the course is no longer selected.

Design note:
Dropping a course currently removes only enrollment. It does not delete previous
attempts. This is safer for audit/history.


Flow 6: View assessments

1. Student opens /assessments.
2. Flask identifies logged-in student.
3. Flask joins enrollment -> courses -> assessments -> tasks -> questions.
4. Only assessments from enrolled courses are loaded.
5. Flask also counts previous attempts per task.
6. Page shows dropdowns for course, assessment, and task.
7. Selected task displays due date, attempt number, max score, and all 5 MCQs.


Flow 7: Submit MCQ attempt

Backend flow:

1. Student selects answers for the 5 questions.
2. Student submits task attempt.
3. Flask counts previous attempts for student_id + task_id.
4. If already 3 attempts, block submission.
5. Flask inserts one row into attempts.
6. Flask inserts five rows into submitted_answers.
7. Flask compares chosen_option to questions.correct_option.
8. Flask sets is_correct and points_awarded.
9. Flask calculates raw_score.
10. Flask checks submitted_at against assessment.due_date.
11. If late, final_score = raw_score * 0.9.
12. Flask updates attempts with score, late flag, and status='graded'.


Flow 8: View personal scores

Current page:

1. Student opens /score.
2. Flask loads graded attempts for that student from currently enrolled courses.
3. Page shows course, assessment, task, attempt number, raw_score, final_score,
   late penalty status, and submitted_at.


Flow 9: Leaderboard - planned

Project rule for this MCQ adaptation:
Leaderboard ranks students by overall course score.

Course score means:

- for each student and task, use the student's best graded attempt
- sum those best task scores across all assessments in the selected course
- rank students within that course

Expected query logic:

1. For each student and task, take MAX(final_score).
2. For each student and course, combine best task scores from all assessments
   in that course.
3. Rank students by course_score.
4. Show top 5 students per course.
5. The leaderboard dropdown should list courses, not assessments.


Flow 10: Late penalty demo - planned

1. Student submits an attempt before due date.
2. Score is shown without penalty.
3. Change assessment due_date directly in MySQL to a time before submitted_at.
4. Recalculate/regrade.
5. Score should show 10% penalty.


Flow 11: CSV export - planned

Expected export:

1. Run backend export script or route.
2. Export all student scores to CSV.
3. CSV should include student, course, assessment, task, attempt_number,
   raw_score, final_score, late_penalty_applied, and submitted_at.


Current and planned Flask functions
-----------------------------------

This section lists both:

- implemented functions currently present in flask_app.py
- planned/expected functions needed for a full-mark demo


Implemented functions
---------------------

1. get_db_connection()

Status:
Implemented.

Purpose:
Creates a MySQL connection using db_config.

Used by:
All database-backed routes.

Database tables used:
None directly. It only creates the connection.

Important behavior:

- Keeps database connection details in one place.
- Should be used by every route or helper that talks to MySQL.


2. index()

Status:
Implemented.

Route:
/

Method:
GET

Purpose:
Redirects user to /login.

Database tables used:
None.

Important behavior:

- Keeps the root URL simple.
- Avoids showing a blank page when user visits the app root.


3. login()

Status:
Implemented.

Route:
/login

Methods:
GET, POST

Purpose:
Authenticates student using username and password.

Database tables used:

- students

Important behavior:

- Validates that username and password are provided.
- Fetches the student row by username.
- Uses check_password_hash against students.password_hash.
- Stores username, full_name, and email in Flask session.
- Redirects successful login to /home.

Demo relevance:
Supports demo step 1: student should be able to login.


4. logout()

Status:
Implemented.

Route:
/logout

Method:
GET

Purpose:
Logs the student out.

Database tables used:
None in current implementation.

Important behavior:

- Clears Flask session.
- Redirects to /login.

Possible future improvement:
If sessions table is fully used, this should also update sessions.logged_out_at.


5. register()

Status:
Implemented.

Route:
/register

Methods:
GET, POST

Purpose:
Creates a student account.

Database tables used:

- students

Important behavior:

- Validates all required fields.
- Confirms password and confirm_password match.
- Checks duplicate username/email.
- Uses generate_password_hash.
- Inserts hashed password into students.password_hash.
- Redirects to /login after successful registration.

Demo relevance:
Useful for setup, but a full demo should ideally use seeded demo accounts.


6. home()

Status:
Implemented, but mostly display/static.

Route:
/home

Method:
GET

Purpose:
Shows the logged-in dashboard.

Database tables used:
None in current implementation.

Important behavior:

- Requires login.
- Displays username/full_name from session.

Expected future behavior:

- Show enrolled course count.
- Show open assessments.
- Show recent attempts.
- Show personal average.


7. assessments()

Status:
Implemented for display and task submission.

Route:
/assessments

Method:
GET

Purpose:
Shows enrolled-course assessments, tasks, attempt information, and questions.

Database tables used:

- students
- enrollment
- courses
- assessments
- tasks
- questions
- attempts

Important behavior:

- Requires login.
- Finds the logged-in student from students.
- Only shows assessments for courses the student is enrolled in.
- Joins enrollment -> courses -> assessments -> tasks -> questions.
- Counts previous attempts for each task.
- Passes nested course/assessment/task/question data to assessments.html.

Demo relevance:
Supports course-specific assessment visibility.
Prepares the UI for demo steps 3, 4, and 8.

Expected future behavior:

- Improve visual feedback after submission if needed.


8. courses()

Status:
Implemented.

Route:
/courses

Method:
GET

Purpose:
Shows all courses and whether the logged-in student is enrolled.

Database tables used:

- students
- courses
- assessments
- tasks
- enrollment

Important behavior:

- Requires login.
- Counts assessments and tasks per course.
- Marks enrolled courses as selected.
- Renders add/drop buttons based on enrollment state.


9. add_course()

Status:
Implemented.

Route:
/courses/add

Method:
POST

Purpose:
Enrolls the logged-in student in a course.

Database tables used:

- students
- courses
- enrollment

Important behavior:

- Requires login.
- Validates course_id.
- Confirms student exists.
- Confirms course exists.
- Uses INSERT IGNORE to avoid duplicate enrollment errors.
- Redirects back to /courses.


10. drop_course()

Status:
Implemented.

Route:
/courses/drop

Method:
POST

Purpose:
Drops a course enrollment for the logged-in student.

Database tables used:

- students
- courses
- enrollment

Important behavior:

- Requires login.
- Validates course_id.
- Deletes only from enrollment.
- Does not delete previous attempts or scores.

Design note:
Keeping old attempts is safer for audit/history.


11. score()

Status:
Implemented and database-backed.

Route:
/score

Method:
GET

Purpose:
Shows personal scores.

Current database tables used:

- students
- courses
- assessments
- tasks
- attempts
- enrollment
- submitted_answers

Current behavior:

- Requires login.
- Loads graded attempts for the logged-in student from currently enrolled courses.
- Shows course, assessment, task, attempt_number, submitted_at, raw_score,
  final_score, late_penalty_applied, and status.
- Should show every attempt, not only the best attempt.

Demo relevance:
Supports demo step 6: student should be able to view marks for all submissions.


12. leaderboard()

Status:
Route exists, but page is not yet database-backed.

Route:
/leaderboard

Method:
GET

Purpose:
Shows top students by overall course score.

Current database tables used:
None in current implementation.

Expected database tables:

- students
- courses
- assessments
- tasks
- attempts
- enrollment

Expected behavior:

- Load leaderboard per course.
- Use a course dropdown, not an assessment dropdown.
- For each student and task, use best final_score.
- Aggregate best task scores across all assessments in the course.
- Exclude dropped courses by joining through enrollment.
- Show top 5 students.

Demo relevance:
Supports demo step 7: show leaderboard for each course.


13. profile()

Status:
Implemented.

Route:
/profile

Methods:
GET, POST

Purpose:
Shows student profile and changes password.

Database tables used:

- students

Important behavior:

- Requires login.
- Loads profile details from students.
- Checks current password.
- Validates new password confirmation.
- Rejects new password if same as current password.
- Hashes new password.
- Updates students.password_hash.

Demo relevance:
Supports demo step 2: student should be able to change password.


14. build_assessment_tree(rows)

Status:
Implemented.

Purpose:
Converts flat SQL join rows into nested data for assessments.html.

Input shape:
One row per question.

Output shape:

courses
  assessments
    tasks
      questions

Why it is needed:
SQL joins naturally return flat rows. The UI needs nested data.

Important behavior:

- Groups rows by course_id.
- Groups assessments by assessment_id.
- Groups tasks by task_id.
- Appends questions under each task.
- Adds due_date_display for the frontend.
- Adds attempt_count, next_attempt_number, and is_locked.


Planned/expected functions
--------------------------

These functions are not all implemented yet, but they are the smallest practical
set needed to finish the project without overengineering.


15. get_current_student()

Status:
Planned helper.

Purpose:
Centralize the repeated pattern of reading the logged-in student from session and
fetching the students row.

Expected input:

- Uses session['username']

Expected output:

- Student dictionary with id, username, full_name, email
- None if not logged in or student no longer exists

Expected database tables:

- students

Why useful:
Several routes currently repeat:

- get username from session
- query students table
- clear session if student not found

This helper reduces duplication while staying simple.


16. get_next_attempt_number(student_id, task_id)

Status:
Planned helper.

Purpose:
Calculate the next attempt number for a student on a task.

Expected database tables:

- attempts

Expected behavior:

- Count existing attempts for student_id + task_id.
- If count is 0, next attempt is 1.
- If count is 1, next attempt is 2.
- If count is 2, next attempt is 3.
- If count is 3 or more, block submission.

Why important:
This enforces the project rule that each task can only be attempted 3 times.


17. calculate_late_penalty(raw_score, submitted_at, due_date)

Status:
Planned helper.

Purpose:
Calculate final_score and late_penalty_applied.

Expected input:

- raw_score
- submitted_at
- due_date

Expected output:

- final_score
- late_penalty_applied

Expected behavior:

- If submitted_at is after due_date:
  final_score = raw_score * 0.9
  late_penalty_applied = True

- Otherwise:
  final_score = raw_score
  late_penalty_applied = False

Why important:
Supports demo step 9: late submission penalty.


18. submit_attempt()

Status:
Planned route.

Expected route:
/tasks/<int:task_id>/attempts

Expected method:
POST

Purpose:
Submit one MCQ task attempt.

Expected database tables:

- students
- tasks
- assessments
- questions
- attempts
- submitted_answers

Expected behavior:

- Require login.
- Confirm task exists.
- Confirm task belongs to a course the student is enrolled in.
- Count previous attempts.
- Block if previous attempts >= 3.
- Require answers for all 5 questions.
- Insert one attempts row.
- Insert five submitted_answers rows.
- Compare chosen_option with questions.correct_option.
- Store is_correct and points_awarded.
- Calculate raw_score.
- Apply late penalty.
- Update attempts.raw_score, final_score, late_penalty_applied, submitted_at,
  and status='graded'.

Transaction requirement:
This should use a database transaction. If one answer insert fails, the attempt
should not be partially saved.

Demo relevance:
Supports demo steps 3, 4, 5, and 8.


19. grade_attempt(attempt_id)

Status:
Planned helper or backend script function.

Purpose:
Grade one attempt based on submitted answers.

Expected database tables:

- attempts
- submitted_answers
- questions
- tasks
- assessments

Expected behavior:

- Load submitted answers for attempt_id.
- Compare each submitted_answers.chosen_option with questions.correct_option.
- Set submitted_answers.is_correct.
- Set submitted_answers.points_awarded.
- Sum points_awarded into raw_score.
- Apply late penalty based on assessment.due_date.
- Update attempts row.

Design choice:
This can be called immediately by submit_attempt().
It can also be reused by a regrade script for the late penalty demo.


20. grade_ungraded_attempts()

Status:
Planned backend script or route.

Purpose:
Auto-grade attempts that have been submitted but not graded.

Expected database tables:

- attempts
- submitted_answers
- questions
- assessments

Expected behavior:

- Find attempts with status='submitted' or raw_score IS NULL.
- Call grade_attempt(attempt_id) for each.
- Finish within 30 seconds for demo data.

Demo relevance:
Maps to the original requirement's backend auto-grading script.


21. regrade_attempts_for_assessment(assessment_id)

Status:
Planned helper or backend script function.

Purpose:
Recalculate scores after the assessment due_date is changed in MySQL.

Expected database tables:

- assessments
- tasks
- attempts
- submitted_answers
- questions

Expected behavior:

- Find all attempts for tasks under the assessment.
- Recalculate raw_score from submitted answers.
- Reapply late penalty using the current assessments.due_date.
- Update attempts.final_score and late_penalty_applied.

Demo relevance:
Supports demo step 9.


22. score()

Status:
Existing route, planned database-backed implementation.

Route:
/score

Method:
GET

Purpose:
Show all scores for the logged-in student.

Expected database tables:

- students
- courses
- assessments
- tasks
- attempts

Expected behavior:

- Require login.
- Query attempts for the current student.
- Join to tasks, assessments, and courses.
- Show one row per attempt.
- Include attempt_number, submitted_at, raw_score, final_score, penalty, status.


23. leaderboard()

Status:
Existing route, planned database-backed implementation.

Route:
/leaderboard

Method:
GET

Purpose:
Show top 5 students per course.

Expected database tables:

- students
- courses
- assessments
- tasks
- attempts
- enrollment

Expected behavior:

- For each student/task, take MAX(final_score).
- Aggregate best task scores across all assessments in the selected course.
- Rank students by course_score.
- Dropdown should list courses.
- Exclude dropped courses by joining through enrollment.
- Return top 5.

Important project rule:
For the MCQ adaptation, leaderboard uses best attempt per task, then sums those
best task scores at course level.


24. export_scores()

Status:
Planned script or route.

Possible route:
/export/scores

Possible script:
export_scores.py

Purpose:
Export all scores into CSV.

Expected database tables:

- students
- courses
- assessments
- tasks
- attempts

Expected output columns:

- username
- full_name
- course_code
- course_name
- assessment_title
- task_title
- attempt_number
- submitted_at
- raw_score
- final_score
- late_penalty_applied
- status

Demo relevance:
Supports demo step 10.


25. validate_seed_data()

Status:
Planned script/helper, optional but useful.

Purpose:
Verify that the demo database is ready.

Expected checks:

- courses count is 3
- assessments count is 5
- tasks count is 8
- questions count is 40
- every task has exactly 5 questions
- demo users exist
- demo users have enrollments

Why useful:
Prevents demo failure caused by bad seed data.


26. create_demo_users()

Status:
Implemented in seed.sql and reset_db.sql as SQL seed data.

Purpose:
Create predictable demo users.

Demo users:

- adam01
- sarah02
- danial03
- hannah04
- rayan05
- zara06
- zain07

Implemented behavior:

- Insert users with hashed passwords.
- Enroll users into courses.
- Enroll every tester account in CS101 for course leaderboard demo.
- Create sample attempts for score and leaderboard demo.
- Create submitted_answers rows so each seeded attempt has 5 answer records.

Note:
This is intentionally done in SQL seed files instead of Flask application code.


Demo checklist
--------------

Preparation checklist:

- Run database reset if safe:
  mysql -u root < reset_db.sql

- Validate seed data:
  SELECT COUNT(*) FROM courses;
  SELECT COUNT(*) FROM assessments;
  SELECT COUNT(*) FROM tasks;
  SELECT COUNT(*) FROM questions;
  SELECT COUNT(*) FROM students;
  SELECT COUNT(*) FROM enrollment;
  SELECT COUNT(*) FROM attempts;
  SELECT COUNT(*) FROM submitted_answers;

- Confirm every tester is enrolled in CS101:
  SELECT s.username
  FROM students s
  JOIN enrollment e ON e.student_id = s.id
  JOIN courses c ON c.course_id = e.course_id
  WHERE c.course_code = 'CS101'
  ORDER BY s.username;

Expected result:
adam01, danial03, hannah04, rayan05, sarah02, zain07, zara06.

- Confirm every task has exactly 5 questions:
  SELECT t.task_id, t.title, COUNT(q.question_id) AS question_count
  FROM tasks t
  LEFT JOIN questions q ON q.task_id = t.task_id
  GROUP BY t.task_id, t.title
  HAVING question_count <> 5;

Expected result:
No rows.

- Run Flask:
  flask --app flask_app run --debug


Demo step checklist:

1. Login

- Open /login.
- Log in with a demo student.
- Expected: redirect to /home.

Status:
Implemented. Seed data includes demo users.


2. Change password

- Open /profile.
- Enter current password.
- Enter new password and confirmation.
- Submit.
- Log out.
- Confirm old password fails and new password works.

Status:
Implemented in current app logic.


3. Add course

- Open /courses.
- Add one course.
- Refresh page.
- Expected: course remains selected because enrollment is stored in MySQL.

Status:
Implemented.


4. View enrolled assessments

- Open /assessments.
- Expected: only assessments from enrolled courses appear.
- Dropdowns should allow course, assessment, and task selection.

Status:
Implemented for display.


5. Submit full-mark MCQ attempt

- Select a task.
- Choose all correct answers.
- Submit.
- Expected: raw_score = 5, final_score = 5.

Status:
Implemented.


6. Submit partial-mark MCQ attempt

- Select same or different task.
- Choose some incorrect answers.
- Submit.
- Expected: partial raw_score and final_score.

Status:
Implemented.


7. Show all marks

- Open /score.
- Expected: all attempts are shown.

Status:
Implemented and database-backed for currently enrolled courses.


8. Show leaderboard

- Open /leaderboard.
- Expected: course dropdown appears.
- Expected: top 5 students are ranked by overall course score.
- Expected: score is based on each student's best attempt per task across all
  assessments in that course.

Status:
Planned. Current leaderboard page is not fully database-backed.


9. Resubmit to improve score

- Return to /assessments.
- Submit a new attempt for a task with partial score.
- Expected: new attempt row appears, best score improves.

Status:
Implemented for task attempts. Leaderboard best-attempt display still needs
database integration.


10. Late penalty

- Change assessment due_date in MySQL to before submitted_at.
- Regrade or recalculate.
- Expected: final_score is raw_score * 0.9 and late_penalty_applied = TRUE.

Status:
Planned.


11. CSV export

- Run export script or endpoint.
- Expected: CSV contains all scores.

Status:
Planned.


High-priority remaining work
----------------------------

1. Finish leaderboard database integration.

Required behavior:

- use each student's best attempt per task
- aggregate task scores across all assessments in each course
- rank students by course_score
- use a course dropdown
- exclude dropped courses by joining through enrollment


2. Add late-score recalculation support.

Required behavior:

- after due_date is changed in MySQL, recompute final_score if needed
- set late_penalty_applied correctly
- keep raw_score unchanged


3. Add CSV score export.

Required output:

- student
- course_code
- assessment_title
- task_title
- attempt_number
- raw_score
- final_score
- late_penalty_applied
- submitted_at


4. Prepare final demo runbook.

Purpose:
Make the 10-minute demo predictable and easy to execute.


Important database concepts to explain in demo
---------------------------------------------

Primary key:
Uniquely identifies each row in a table.

Foreign key:
Links rows between related tables and enforces referential integrity.

Composite primary key:
Used in enrollment(student_id, course_id) to prevent duplicate enrollment.

Many-to-many relationship:
students and courses are many-to-many through enrollment.

One-to-many relationship:
courses to assessments, assessments to tasks, tasks to questions.

3NF:
The schema avoids storing parent data redundantly in child tables.

Derived data:
Scores and is_correct are stored as grading snapshots for audit and demo clarity.

Transaction:
Attempt submission should use one transaction so attempts and submitted answers
are saved together.

Late penalty:
Calculated by comparing attempts.submitted_at with assessments.due_date.

Best attempt leaderboard:
For the MCQ adaptation, leaderboard uses each student's best attempt per task,
then sums those best task scores across the selected course.
