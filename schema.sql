CREATE DATABASE IF NOT EXISTS TCX2003_Project;
USE TCX2003_Project;

CREATE TABLE students (
    username VARCHAR(50) PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE courses (
    course_id INT AUTO_INCREMENT PRIMARY KEY,
    course_name VARCHAR(100) NOT NULL
);


CREATE TABLE assessments (
    assessment_id INT AUTO_INCREMENT PRIMARY KEY,
    course_id INT,
    title VARCHAR(100),
    FOREIGN KEY (course_id) REFERENCES courses(course_id)
);


CREATE TABLE tasks (
    task_id INT AUTO_INCREMENT PRIMARY KEY,
    assessment_id INT,
    title VARCHAR(100),
    FOREIGN KEY (assessment_id) REFERENCES assessments(assessment_id)
);


CREATE TABLE attempts (
    attempt_id INT AUTO_INCREMENT PRIMARY KEY,
    student_username VARCHAR(50),
    task_id INT,
    score INT,

    FOREIGN KEY (student_username) REFERENCES students(username),
    FOREIGN KEY (task_id) REFERENCES tasks(task_id)
);
