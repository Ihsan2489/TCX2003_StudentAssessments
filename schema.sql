CREATE DATABASE IF NOT EXISTS TCX2003_Project;
USE TCX2003_Project;

CREATE TABLE students (
    id INT AUTO_INCREMENT PRIMARY KEY,
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

CREATE TABLE enrollment (
    student_id INT NOT NULL, -- Reference student table 
    course_id INT NOT NULL,  -- Reference courses table 
    PRIMARY KEY (student_id, course_id), -- Composite primary key to prevent duplicate enrollments
    enrollment_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, 
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE, -- should this be restrict 
    FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE, -- should this be restrict instead?
);

CREATE TABLE sessions (
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

CREATE TABLE assessments ( 
    assessment_id INT AUTO_INCREMENT PRIMARY KEY, 
    course_id INT NOT NULL, 
    title VARCHAR(255) NOT NULL, 
    description TEXT, 
    due_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE
);

CREATE TABLE tasks (
    task_id INT AUTO_INCREMENT PRIMARY KEY, 
    assessment_id INT NOT NULL, 
    title VARCHAR(255) NOT NULL, 
    description TEXT,
    max_score INT NOT NULL DEFAULT 0, 
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (assessment_id) REFERENCES assessments(assessment_id) ON DELETE CASCADE
); 

CREATE TABLE questions (
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

CREATE TABLE attempts (
    attempt_id INT AUTO_INCREMENT PRIMARY KEY, 
    student_id INT NOT NULL, 
    task_id INT NOT NULL, 
    attempt_number INT NOT NULL DEFAULT 1, -- To track multiple attempts for the same task
    started_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, 
    submitted_at DATETIME DEFAULT NULL, -- For this NULL it means the attempt is still in progress 
    raw_score INT DEFAULT NULL, -- Score before applying any late penalties or adjustments
    final_score INT DEFAULT NULL, -- Score after applying late penalties or adjustments
    late_penalty_applied BOOLEAN DEFAULT FALSE,
    status ENUM('in_progress', 'submitted', 'graded') NOT NULL DEFAULT 'in_progress',
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE, 
    FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE,
    UNIQUE KEY unique_student_task_attempt (student_id, task_id, attempt_number) -- To prevent duplicate attempt numbers for the same student and task
); 

CREATE TABLE submitted_answers (
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



