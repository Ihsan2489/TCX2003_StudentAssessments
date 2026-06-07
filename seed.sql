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
