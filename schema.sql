CREATE DATABASE IF NOT EXISTS TCX2003_Project;
USE TCX2003_Project;

CREATE TABLE students (
    -- 1. This handles the actual auto-incrementing math
    id INT AUTO_INCREMENT PRIMARY KEY,
    -- 2. This automatically prepends "student_" to the ID
    student_id VARCHAR(20) GENERATED ALWAYS AS (CONCAT('student_', id)) STORED,
    username VARCHAR(50) NOT NULL UNIQUE,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE courses (
    course_id INT AUTO_INCREMENT PRIMARY KEY,
    course_name VARCHAR(100) NOT NULL,
    course_code VARCHAR(20) NOT NULL UNIQUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE student_courses (
    enrollment_id INT AUTO_INCREMENT PRIMARY KEY, 
    student_id INT NOT NULL, -- Reference student table 
    course_id INT NOT NULL,  -- Reference courses table 
    enrollment_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, 
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE, -- should this be restrict 
<<<<<<< Updated upstream
    FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE, -- should this be restrict instead?
    UNIQUE KEY unique_student_course (student_id, course_id)
=======
    FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE RESTRICT    
>>>>>>> Stashed changes
);

CREATE TABLE sessions (
    session_id INT AUTO_INCREMENT PRIMARY KEY, 
    student_id INT NOT NULL, -- References student table 
    -- 1. Token to identify student's activity / browser session 
    session_token VARCHAR(255) NOT NULL UNIQUE, 
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, 
    -- 2. Assuming questions are loaded 1 by 1 on the browser, this will update everytime a student loads a new question
    last_activity DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, 
    expires_at DATETIME NOT NULL, 
    logged_out_at DATETIME DEFAULT NULL, -- Added logout tracker 
    -- 3. meta data for audit / security 
    ip_address VARCHAR(45) DEFAULT NULL, 
    user_agent TEXT DEFAULT NULL,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE 
    -- 4. If student profile is deleted then delete active session as well 
);

CREATE TABLE assessments ( 
    assessment_id INT AUTO_INCREMENT PRIMARY KEY, 
    course_id INT NOT NULL, 
    title VARCHAR(255) NOT NULL, 
    description TEXT, 
    due_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, 
    FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE
);

CREATE TABLE tasks (
    task_id INT AUTO_INCREMENT PRIMARY KEY, 
    assessment_id INT NOT NULL, 
    task_name VARCHAR(255) NOT NULL, 
    max_score INT NOT NULL DEFAULT 0, 
    FOREIGN KEY (assessment_id) REFERENCES assessments(assessment_id) ON DELETE CASCADE
); 

CREATE TABLE questions (
    question_id INT AUTO_INCREMENT PRIMARY KEY,
    task_id INT NOT NULL,  
    question_text TEXT NOT NULL, 
    -- 1. columns to enter the 4 mcq options, assuming we are setting only 4 options per quesion 
    option_1 VARCHAR(255) NOT NULL, 
    option_2 VARCHAR(255) NOT NULL, 
    option_3 VARCHAR(255) NOT NULL, 
    option_4 VARCHAR(255) NOT NULL, 
    --2. for this i'm not sure how to auto uppercase, we might need to .upper() in python before sending to SQL
    correct_option ENUM('A', 'B', 'C', 'D') NOT NULL, 
    --3. This just specifies that each question is worth 1 point by default, we can adjust this in the quesiton table 
    points INT NOT NULL DEFAULT 1, 
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, 
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE 
);

CREATE TABLE attempts (
    attempt_id INT AUTO_INCREMENT PRIMARY KEY, 
    student_id INT NOT NULL, 
    task_id INT NOT NULL, 
    started_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, 
    submitted_at DATETIME DEFAULT NULL, -- For this NULL it means the attempt is still in progress 
    score INT DEFAULT 0, 
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE, 
<<<<<<< Updated upstream
    FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE 
=======
    FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE,
    UNIQUE KEY unique_student_task_attempt (student_id, task_id, attempt_number) -- To prevent duplicate attempt numbers for the same student and task
    CONSTRAINT check_attempt_number CHECK (attempt_number BETWEEN 1 AND 3) -- Added this as safety in case Python defaults to 1 in FLASK when calculating attempt_number
>>>>>>> Stashed changes
); 

CREATE TABLE submitted_answers (
    submitted_answer_id INT AUTO_INCREMENT PRIMARY KEY, 
    attempt_id INT NOT NULL,  -- To connect back to the specific student session / attempt 
    question_id INT NOT NULL, -- Which question are they answering 
    chosen_option ENUM ('A', 'B', 'C', 'D') NOT NULL,  -- The student's answer 
    is_correct BOOLEAN DEFAULT NULL, 
    FOREIGN KEY (attempt_id) REFERENCES attempts(attempt_id) ON DELETE CASCADE, 
    FOREIGN KEY (question_id) REFERENCES questions(question_id) ON DELETE CASCADE, 
    UNIQUE KEY unique_attempt_question (attempt_id, question_id) -- prevents answering the same question twice in 1 attempt 
    
); 



