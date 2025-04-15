from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize Flask app
app = Flask(__name__)
app.secret_key = "secret"  # Secret key for session management
DB_PATH = 'database/attendance.db'  # Path to the SQLite database

# Redirect '/' to '/login'
@app.route('/')
def home():
    return redirect('/login')

# ✅ User Login + Admin Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password_input = request.form['password']

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Admin login
        if username == 'admin':
            if password_input == 'admin123':
                session['admin'] = True  # Set admin session
                return redirect('/dashboard')
            else:
                return render_template("login.html", message="❌ Invalid admin password", category="error")

        # User login
        cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        conn.close()

        if row and check_password_hash(row[0], password_input):
            session['user'] = username  # Set user session
            return redirect('/user')
        else:
            return render_template("login.html", message="❌ Invalid username or password", category="error")

    return render_template("login.html")

# ✅ User Sign Up
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])  # Hash the password
        student_number = request.form['student_number']

        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password, student_number) VALUES (?, ?, ?)",
                           (username, password, student_number))
            conn.commit()
            conn.close()
            return render_template("signup.html", message="✅ Signup successful! You can now log in.", category="success")
        except sqlite3.IntegrityError:
            return render_template("signup.html", message="❌ Username or Student ID already exists.", category="error")

    return render_template("signup.html")

# ✅ User Dashboard
@app.route('/user')
def user_dashboard():
    if 'user' not in session:
        return redirect('/login')
    return render_template('user_home.html', username=session['user'])

# ✅ Attendance Submission Form
@app.route('/submit', methods=['GET', 'POST'])
def submit():
    if 'user' not in session:
        return redirect('/login')

    if request.method == 'POST':
        data = (
            request.form['student_name'],  # Student name
            request.form['student_number'],  # Student number
            request.form['section'],  # Section
            request.form['subject'],  # Subject
            request.form['status'],  # Attendance status
            request.form['date']  # Date
        )
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO attendance (student_name, student_number, section, subject, status, date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', data)
        conn.commit()
        conn.close()
        return render_template("form.html", message="✅ Attendance submitted!", category="success", redirect_url="/user")
    return render_template('form.html')

# ✅ Admin Dashboard
@app.route('/dashboard')
def dashboard():
    if not session.get('admin'):
        return redirect('/login')

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM attendance ORDER BY date DESC")  # Fetch attendance records
    records = cursor.fetchall()
    conn.close()
    return render_template('dashboard.html', records=records)

# ✅ Delete Attendance Record
@app.route('/delete/<int:id>')
def delete_attendance(id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM attendance WHERE id = ?', (id,))  # Delete attendance by ID
    conn.commit()
    conn.close()
    return redirect('/dashboard')

# ✅ Edit Attendance Record
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_attendance(id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if request.method == 'POST':
        data = (
            request.form['student_name'],
            request.form['student_number'],
            request.form['section'],
            request.form['subject'],
            request.form['status'],
            request.form['date'],
            id
        )
        cursor.execute('''
            UPDATE attendance
            SET student_name = ?, student_number = ?, section = ?, subject = ?, status = ?, date = ?
            WHERE id = ?
        ''', data)
        conn.commit()
        conn.close()
        return redirect('/dashboard')

    cursor.execute('SELECT * FROM attendance WHERE id = ?', (id,))  # Fetch attendance record by ID
    record = cursor.fetchone()
    conn.close()

    if not record:
        return f"No record found with ID {id}", 404

    return render_template('edit_form.html', record=record)

# ✅ Add Grades
@app.route('/add-grade', methods=['GET', 'POST'])
def add_grade():
    if not session.get('admin'):
        return redirect('/')

    if request.method == 'POST':
        student_number = request.form['student_number']
        subject = request.form['subject']
        grade = request.form['grade']

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO grades (student_number, subject, grade) VALUES (?, ?, ?)',
                       (student_number, subject, grade))
        conn.commit()
        conn.close()

        return render_template("add_grade.html", message="✅ Grade added successfully!", category="success")

    return render_template("add_grade.html")

# ✅ View Grades (User)
@app.route('/grades')
def view_grades():
    if 'user' not in session:
        return redirect('/login')

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT subject, grade 
        FROM grades 
        WHERE student_number = (
            SELECT student_number 
            FROM users 
            WHERE username = ?
        )
    ''', (session['user'],))
    grades = cursor.fetchall()
    conn.close()

    return render_template("grades.html", grades=grades)

# ✅ View Grades (Admin)
@app.route('/admin-grades')
def admin_grades():
    if not session.get('admin'):
        return redirect('/')

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, student_number, subject, grade FROM grades ORDER BY student_number")  # Fetch all grades
    records = cursor.fetchall()
    conn.close()

    return render_template("admin_grades.html", grades=records)

# ✅ Delete Grade
@app.route('/delete-grade/<int:id>')
def delete_grade(id):
    if not session.get('admin'):
        return redirect('/')

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM grades WHERE id = ?", (id,))  # Delete grade by ID
    conn.commit()
    conn.close()

    return redirect('/admin-grades')

# ✅ Edit Grade
@app.route('/edit-grade/<int:id>', methods=['GET', 'POST'])
def edit_grade(id):
    if not session.get('admin'):
        return redirect('/')

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if request.method == 'POST':
        subject = request.form['subject']
        grade = request.form['grade']
        cursor.execute("UPDATE grades SET subject = ?, grade = ? WHERE id = ?", (subject, grade, id))
        conn.commit()
        conn.close()
        return redirect('/admin-grades')

    cursor.execute("SELECT id, student_number, subject, grade FROM grades WHERE id = ?", (id,))  # Fetch grade by ID
    grade_record = cursor.fetchone()
    conn.close()
    return render_template("edit_grade.html", record=grade_record)

# ✅ Submit Feedback
@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if 'user' not in session:
        return redirect('/')

    if request.method == 'POST':
        username = session['user']
        subject = request.form['subject']
        comment = request.form['comment']

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO feedback (username, subject, comment) VALUES (?, ?, ?)", (username, subject, comment))
        conn.commit()
        conn.close()

        return render_template('feedback.html', message="✅ Feedback submitted!", category="success")

    return render_template('feedback.html')

# ✅ View Feedback (Admin)
@app.route('/view-feedback')
def view_feedback():
    if not session.get('admin'):
        return redirect('/')

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, subject, comment, created_at FROM feedback ORDER BY created_at DESC")  # Fetch feedback
    feedbacks = cursor.fetchall()
    conn.close()

    return render_template('admin_feedback.html', feedbacks=feedbacks)

# ✅ Logout
@app.route('/logout')
def logout():
    session.clear()  # Clear session data
    return redirect('/login')

# ✅ Start App
if __name__ == "__main__":
    app.run(debug=True)  # Start the Flask app in debug mode
