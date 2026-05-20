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