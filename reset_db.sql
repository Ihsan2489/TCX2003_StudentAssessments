DROP DATABASE IF EXISTS TCX2003_Project;
CREATE DATABASE TCX2003_Project;
USE TCX2003_Project;


CREATE TABLE IF NOT EXISTS students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS courses (
    course_id INT AUTO_INCREMENT PRIMARY KEY,
    course_name VARCHAR(100) NOT NULL,
    course_code VARCHAR(20) NOT NULL UNIQUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS enrollment (
    student_id INT NOT NULL, -- Reference student table 
    course_id INT NOT NULL,  -- Reference courses table 
    PRIMARY KEY (student_id, course_id), -- Composite primary key to prevent duplicate enrollments
    enrollment_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, 
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE, -- should this be restrict 
    FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE RESTRICT 
);

CREATE TABLE IF NOT EXISTS sessions (
    session_id INT AUTO_INCREMENT PRIMARY KEY, 
    student_id INT NOT NULL, -- References student table 
    -- 1. Token to identify student's activity / browser session 
    session_token VARCHAR(255) NOT NULL UNIQUE, 
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, 
    expires_at DATETIME NOT NULL, 
    logged_out_at DATETIME DEFAULT NULL, -- Added logout tracker 
    -- 3. meta data for audit / security 
    ip_address VARCHAR(45) DEFAULT NULL, 
    user_agent TEXT DEFAULT NULL,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE 
    -- 4. If student profile is deleted then delete active session as well 
);

CREATE TABLE IF NOT EXISTS assessments ( 
    assessment_id INT AUTO_INCREMENT PRIMARY KEY, 
    course_id INT NOT NULL, 
    title VARCHAR(255) NOT NULL, 
    description TEXT, 
    due_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS tasks (
    task_id INT AUTO_INCREMENT PRIMARY KEY, 
    assessment_id INT NOT NULL, 
    title VARCHAR(255) NOT NULL, 
    description TEXT,
    max_score INT NOT NULL DEFAULT 0, 
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (assessment_id) REFERENCES assessments(assessment_id) ON DELETE CASCADE
); 

CREATE TABLE IF NOT EXISTS questions (
    question_id INT AUTO_INCREMENT PRIMARY KEY,
    task_id INT NOT NULL,  
    question_text TEXT NOT NULL, 
    -- 1. columns to enter the 4 mcq options, assuming we are setting only 4 options per quesion 
    option_a VARCHAR(255) NOT NULL, 
    option_b VARCHAR(255) NOT NULL, 
    option_c VARCHAR(255) NOT NULL, 
    option_d VARCHAR(255) NOT NULL, 
    correct_option ENUM('A', 'B', 'C', 'D') NOT NULL, 
    points INT NOT NULL DEFAULT 1, 
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, 
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE 
);

CREATE TABLE IF NOT EXISTS attempts (
    attempt_id INT AUTO_INCREMENT PRIMARY KEY, 
    student_id INT NOT NULL, 
    task_id INT NOT NULL, 
    attempt_number INT NOT NULL DEFAULT 1, -- To track multiple attempts for the same task
    started_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, 
    submitted_at DATETIME DEFAULT NULL, -- For this NULL it means the attempt is still in progress 
    raw_score DECIMAL(5,2) DEFAULT NULL, -- Score before applying any late penalties or adjustments
    final_score DECIMAL(5,2) DEFAULT NULL, -- Score after applying late penalties or adjustments
    late_penalty_applied BOOLEAN DEFAULT FALSE,
    status ENUM('in_progress', 'submitted', 'graded') NOT NULL DEFAULT 'in_progress',
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE, 
    FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE,
    UNIQUE KEY unique_student_task_attempt (student_id, task_id, attempt_number) -- To prevent duplicate attempt numbers for the same student and task
    CONSTRAINT check_attempt_number CHECK (attempt_number BETWEEN 1 AND 3)
); 

-- If your MySQL version is 8.0.16 or newer, this optional constraint can also
-- enforce the 3-attempt rule at the database layer:
-- ALTER TABLE attempts
-- ADD CONSTRAINT check_attempt_number CHECK (attempt_number BETWEEN 1 AND 3);

CREATE TABLE IF NOT EXISTS submitted_answers (
    submitted_answer_id INT AUTO_INCREMENT PRIMARY KEY, 
    attempt_id INT NOT NULL,  -- To connect back to the specific student session / attempt 
    question_id INT NOT NULL, -- Which question are they answering 
    chosen_option ENUM ('A', 'B', 'C', 'D') NOT NULL,  -- The student's answer 
    is_correct BOOLEAN DEFAULT NULL,
    points_awarded INT DEFAULT NULL, -- Points awarded for this question (0 if incorrect, full points if correct, can be adjusted for partial credit in the future)
    FOREIGN KEY (attempt_id) REFERENCES attempts(attempt_id) ON DELETE CASCADE, 
    FOREIGN KEY (question_id) REFERENCES questions(question_id) ON DELETE CASCADE, 
    UNIQUE KEY unique_attempt_question (attempt_id, question_id) -- prevents answering the same question twice in 1 attempt 
); 

-- Reset-only seed data.
-- Run this after a clean database reset via reset_db.sql.
-- This file is intentionally not idempotent because course_code is unique.

INSERT INTO courses 
(course_code, course_name)
VALUES
('CS101', 'Introduction to Programming'),
('CS102', 'Database Systems'),
('CS201', 'Computing Maths');

SET @cs101_id = (SELECT course_id FROM courses WHERE course_code = 'CS101');
SET @cs102_id = (SELECT course_id FROM courses WHERE course_code = 'CS102');
SET @cs201_id = (SELECT course_id FROM courses WHERE course_code = 'CS201');

INSERT INTO assessments
(course_id, title, description, due_date)
VALUES
(@cs101_id, 'CS101 Assessment 1: Programming Basics', 'Covers variables, expressions, and conditionals.', '2026-07-15 23:59:59'),
(@cs101_id, 'CS101 Assessment 2: Control Flow', 'Covers loops, functions, and lists.', '2026-07-22 23:59:59'),
(@cs102_id, 'CS102 Assessment 1: Database Foundations', 'Covers relational concepts and SQL fundamentals.', '2026-07-18 23:59:59'),
(@cs201_id, 'CS201 Assessment 1: Logic and Sets', 'Covers propositions, sets, and basic proof ideas.', '2026-07-20 23:59:59'),
(@cs201_id, 'CS201 Assessment 2: Relations and Functions', 'Covers relations, functions, and Cartesian products.', '2026-07-27 23:59:59');

SET @cs101_a1_id = (
    SELECT assessment_id FROM assessments
    WHERE course_id = @cs101_id AND title = 'CS101 Assessment 1: Programming Basics'
);
SET @cs101_a2_id = (
    SELECT assessment_id FROM assessments
    WHERE course_id = @cs101_id AND title = 'CS101 Assessment 2: Control Flow'
);
SET @cs102_a1_id = (
    SELECT assessment_id FROM assessments
    WHERE course_id = @cs102_id AND title = 'CS102 Assessment 1: Database Foundations'
);
SET @cs201_a1_id = (
    SELECT assessment_id FROM assessments
    WHERE course_id = @cs201_id AND title = 'CS201 Assessment 1: Logic and Sets'
);
SET @cs201_a2_id = (
    SELECT assessment_id FROM assessments
    WHERE course_id = @cs201_id AND title = 'CS201 Assessment 2: Relations and Functions'
);

INSERT INTO tasks
(assessment_id, title, description, max_score)
VALUES
(@cs101_a1_id, 'Variables and Data Types', 'Answer MCQs about variables, literals, and basic data types.', 5),
(@cs101_a1_id, 'Conditionals', 'Answer MCQs about if, else, and boolean expressions.', 5),
(@cs101_a2_id, 'Loops', 'Answer MCQs about for loops, while loops, and loop control.', 5),
(@cs101_a2_id, 'Functions and Lists', 'Answer MCQs about function calls, return values, and list operations.', 5),
(@cs102_a1_id, 'Relational Model', 'Answer MCQs about tables, keys, domains, and relationships.', 5),
(@cs102_a1_id, 'SQL Basics', 'Answer MCQs about SELECT, WHERE, JOIN, and aggregation.', 5),
(@cs201_a1_id, 'Logic and Sets', 'Answer MCQs about propositions, truth values, and set operations.', 5),
(@cs201_a2_id, 'Relations and Functions', 'Answer MCQs about ordered pairs, Cartesian products, and mappings.', 5);

SET @cs101_t1_id = (
    SELECT task_id FROM tasks
    WHERE assessment_id = @cs101_a1_id AND title = 'Variables and Data Types'
);
SET @cs101_t2_id = (
    SELECT task_id FROM tasks
    WHERE assessment_id = @cs101_a1_id AND title = 'Conditionals'
);
SET @cs101_t3_id = (
    SELECT task_id FROM tasks
    WHERE assessment_id = @cs101_a2_id AND title = 'Loops'
);
SET @cs101_t4_id = (
    SELECT task_id FROM tasks
    WHERE assessment_id = @cs101_a2_id AND title = 'Functions and Lists'
);
SET @cs102_t1_id = (
    SELECT task_id FROM tasks
    WHERE assessment_id = @cs102_a1_id AND title = 'Relational Model'
);
SET @cs102_t2_id = (
    SELECT task_id FROM tasks
    WHERE assessment_id = @cs102_a1_id AND title = 'SQL Basics'
);
SET @cs201_t1_id = (
    SELECT task_id FROM tasks
    WHERE assessment_id = @cs201_a1_id AND title = 'Logic and Sets'
);
SET @cs201_t2_id = (
    SELECT task_id FROM tasks
    WHERE assessment_id = @cs201_a2_id AND title = 'Relations and Functions'
);

INSERT INTO questions
(task_id, question_text, option_a, option_b, option_c, option_d, correct_option, points)
VALUES
(@cs101_t1_id, 'Which data type is most appropriate for storing a whole number?', 'INT', 'VARCHAR', 'BOOLEAN', 'DATE', 'A', 1),
(@cs101_t1_id, 'Which value is a string literal?', '42', '''hello''', 'TRUE', '3.14', 'B', 1),
(@cs101_t1_id, 'What does assignment do in a program?', 'Compares two values', 'Stores a value in a variable', 'Deletes a variable', 'Prints every variable', 'B', 1),
(@cs101_t1_id, 'Which name is usually the best variable name?', 'x', 'data', 'student_count', 'temp2', 'C', 1),
(@cs101_t1_id, 'Which data type represents true or false?', 'INTEGER', 'BOOLEAN', 'TEXT', 'FLOAT', 'B', 1),

(@cs101_t2_id, 'Which keyword starts a basic conditional branch?', 'if', 'for', 'return', 'import', 'A', 1),
(@cs101_t2_id, 'What does an else branch represent?', 'A repeated block', 'A fallback path when earlier conditions fail', 'A function name', 'A data type', 'B', 1),
(@cs101_t2_id, 'Which expression checks whether x equals 10 in many programming languages?', 'x = 10', 'x == 10', 'x => 10', 'x <> 10', 'B', 1),
(@cs101_t2_id, 'Which operator usually means logical AND?', '&&', '++', '//', '**', 'A', 1),
(@cs101_t2_id, 'What should conditional expressions evaluate to?', 'A file', 'A table', 'A boolean result', 'A password', 'C', 1),

(@cs101_t3_id, 'Which loop is commonly used when the number of iterations is known?', 'for loop', 'if statement', 'return statement', 'import statement', 'A', 1),
(@cs101_t3_id, 'What can cause an infinite loop?', 'A condition that never becomes false', 'A list with one item', 'A variable name with letters', 'A function with parameters', 'A', 1),
(@cs101_t3_id, 'Which statement usually exits a loop early?', 'break', 'pass', 'define', 'select', 'A', 1),
(@cs101_t3_id, 'Which statement usually skips to the next loop iteration?', 'continue', 'delete', 'join', 'group', 'A', 1),
(@cs101_t3_id, 'What is the loop body?', 'The code repeated by the loop', 'The final program output', 'The database schema', 'The file name', 'A', 1),

(@cs101_t4_id, 'What is a function parameter?', 'An input value accepted by a function', 'A database row', 'A CSS rule', 'A password hash', 'A', 1),
(@cs101_t4_id, 'What does return usually do?', 'Sends a value back from a function', 'Starts a loop', 'Creates a table', 'Deletes a list', 'A', 1),
(@cs101_t4_id, 'Which operation adds an item to many list structures?', 'append', 'select', 'where', 'commit', 'A', 1),
(@cs101_t4_id, 'What is a list index commonly used for?', 'Finding an item position', 'Encrypting text', 'Opening a session', 'Changing a password', 'A', 1),
(@cs101_t4_id, 'Which function result is best described as reusable output?', 'return value', 'foreign key', 'style rule', 'route name', 'A', 1),

(@cs102_t1_id, 'What is a relation commonly represented as in a database?', 'A table', 'A stylesheet', 'A browser tab', 'A session token', 'A', 1),
(@cs102_t1_id, 'What does a primary key do?', 'Uniquely identifies a row', 'Stores every password in plain text', 'Deletes duplicate tables', 'Sorts all pages', 'A', 1),
(@cs102_t1_id, 'What is a foreign key used for?', 'Referencing a row in another table', 'Changing font size', 'Starting Flask', 'Hashing a password', 'A', 1),
(@cs102_t1_id, 'What is a domain of an attribute?', 'The set of allowed values', 'The page URL', 'The CSS class name', 'The session length only', 'A', 1),
(@cs102_t1_id, 'Which normal form reduces transitive dependency problems?', 'Third Normal Form', 'Zero Normal Form', 'Visual Form', 'Login Form', 'A', 1),

(@cs102_t2_id, 'Which SQL clause filters rows?', 'WHERE', 'ORDER BY', 'CREATE', 'DROP', 'A', 1),
(@cs102_t2_id, 'Which SQL keyword combines rows from related tables?', 'JOIN', 'STYLE', 'ROUTE', 'SESSION', 'A', 1),
(@cs102_t2_id, 'Which SQL aggregate counts rows?', 'COUNT', 'LOWER', 'TRIM', 'ROUND', 'A', 1),
(@cs102_t2_id, 'Which clause groups rows for aggregate calculations?', 'GROUP BY', 'LIMIT BY', 'SORT BY', 'FILTER BY', 'A', 1),
(@cs102_t2_id, 'Which statement retrieves data from a table?', 'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'A', 1),

(@cs201_t1_id, 'Which value can a proposition have?', 'True or false', 'Only a string', 'Only a table', 'Only a file path', 'A', 1),
(@cs201_t1_id, 'What does set intersection return?', 'Elements common to both sets', 'All possible ordered pairs', 'Only the first element', 'A password hash', 'A', 1),
(@cs201_t1_id, 'What does set union return?', 'Elements that are in either set', 'Only duplicated elements', 'Only empty values', 'Only sorted values', 'A', 1),
(@cs201_t1_id, 'What is the empty set?', 'A set with no elements', 'A set with one NULL value', 'A deleted table', 'A failed login', 'A', 1),
(@cs201_t1_id, 'What does implication usually mean?', 'If P then Q', 'P and Q are strings', 'P is a database', 'Q is a function call only', 'A', 1),

(@cs201_t2_id, 'What is a Cartesian product of sets A and B?', 'The set of ordered pairs from A and B', 'The sum of all values', 'A password table', 'A sorted list only', 'A', 1),
(@cs201_t2_id, 'What is a relation from A to B?', 'A subset of A x B', 'A CSS selector', 'A Flask route', 'A password rule', 'A', 1),
(@cs201_t2_id, 'What is a function?', 'A relation where each input has exactly one output', 'A relation with no pairs', 'Any table with a primary key', 'Any loop body', 'A', 1),
(@cs201_t2_id, 'What is an ordered pair?', 'A pair where position matters', 'A pair sorted alphabetically', 'A pair with only numbers', 'A pair of passwords', 'A', 1),
(@cs201_t2_id, 'What is the domain of a function?', 'The set of valid inputs', 'The set of CSS files', 'The current webpage', 'The SQL server port', 'A', 1);
