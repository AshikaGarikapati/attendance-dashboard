import sqlite3

# Establish connection with a timeout of 10 seconds
conn = sqlite3.connect('attendance.db', timeout=10)
cursor = conn.cursor()

# Step 1: Create a new attendance table with the student_name column
cursor.execute('''
CREATE TABLE IF NOT EXISTS attendance_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_name TEXT NOT NULL,
    student_number TEXT NOT NULL,
    section TEXT NOT NULL,
    subject TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('Present', 'Absent')),
    date TEXT NOT NULL
)
''')

# Step 2: Copy data from the old attendance table to the new table
# Use 'Unknown' as a placeholder for student_name if the old table doesn't have this column
cursor.execute('''
INSERT INTO attendance_new (id, student_name, student_number, section, subject, status, date)
SELECT id, 'Unknown', student_number, section, subject, status, date FROM attendance
''')

# Step 3: Drop the old attendance table
cursor.execute('DROP TABLE attendance')

# Step 4: Rename the new table to the original table name
cursor.execute('ALTER TABLE attendance_new RENAME TO attendance')

# Step 5: Create the users table (unchanged)
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    student_number TEXT UNIQUE NOT NULL
)
''')

# Step 6: Create the grades table
cursor.execute('''
CREATE TABLE IF NOT EXISTS grades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_number TEXT NOT NULL,
    subject TEXT NOT NULL,
    grade TEXT NOT NULL
)
''')

# Step 7: Create the feedback table
cursor.execute('''
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    subject TEXT NOT NULL,
    comment TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)
''')

conn.commit()
conn.close()
