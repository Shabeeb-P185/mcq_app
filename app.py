from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
import MySQLdb.cursors


app = Flask(__name__)
app.secret_key = '961834489793790522c7b0ead07be685'

# Configure MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'admin123'
app.config['MYSQL_DB'] = 'mcq'

mysql = MySQL(app)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
        user = cursor.fetchone()
        cursor.close()
        
        if user:
            session['user_id'] = user['user_id']
            session['role'] = user['role']
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('student_dashboard'))
        else:
            flash('Invalid credentials')
    
    return render_template('login.html')

@app.route('/logout', methods=['GET'])
def logout():
    session.clear()
    return redirect('http://127.0.0.1:5000/login')

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'role' in session and session['role'] == 'admin':
        return render_template('admin_dashboard.html')
    else:
        return redirect(url_for('login'))

@app.route('/student_dashboard')
def student_dashboard():
    if 'role' in session and session['role'] == 'student':
        return render_template('student_dashboard.html')
    else:
        return redirect(url_for('login'))
    
@app.route('/add_question', methods=['GET', 'POST'])
def add_question():
    if 'role' in session and session['role'] == 'admin':
        if request.method == 'POST':
            question = request.form['question']
            subject_id = request.form['subjects']
            options = [request.form[f'option{i}'] for i in range(1, 5)]
            correct_option = request.form['correct_option']
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute(
            "INSERT INTO questions (question_text, subject_id) VALUES (%s, %s)",
            (question, subject_id)
            )
            question_id = cursor.lastrowid
            
            for option in options:
                if correct_option == option:
                    is_correct = 1
                else:
                    is_correct = 0
                     
                cursor.execute(
                "INSERT INTO choices (choice_text, is_correct, question_id) VALUES (%s, %s, %s)",
                (option, is_correct, question_id)
                )
            mysql.connection.commit()
            cursor.close()
            flash('Question added successfully')
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM subjects;")
        subjects = cursor.fetchall()
        return render_template('add_question.html', subjects=subjects)
    else:
        return redirect(url_for('login'))

@app.route('/view_results')
def view_results():
    if 'role' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        if session['role'] == 'student':
            cursor.execute("SELECT ur.response_id, ur.user_id, q.question_text, c.choice_text, c.is_correct FROM user_responses ur INNER JOIN questions q ON ur.question_id = q.question_id INNER JOIN choices c ON ur.choice_id = c.choice_id WHERE ur.question_id = q.question_id AND ur.choice_id = c.choice_id;")
            responses = cursor.fetchall()
            total_marks = len(responses)
            current_mark = 0
            for response in responses:
               if response['is_correct'] == 1:
                  current_mark += 1 
                  
            cursor.close()
            return render_template('view_results.html', responses=responses, total_marks=total_marks, current_mark=current_mark)
        elif session['role'] == 'admin':
            cursor.execute("SELECT ur.response_id, ur.user_id, us.username, q.question_text, c.choice_text, c.is_correct FROM user_responses ur INNER JOIN questions q ON ur.question_id = q.question_id INNER JOIN users us ON us.user_id = ur.user_id INNER JOIN choices c ON ur.choice_id = c.choice_id WHERE ur.question_id = q.question_id AND ur.choice_id = c.choice_id;")
            responses = cursor.fetchall()
            total_marks = len(responses)
            current_mark = 0
            for response in responses:
               if response['is_correct'] == 1:
                  current_mark += 1 

            
            # format
            formatted = {}
        
            # for row in responses:
            #     question_id = row['question_id']
            #     question_text = row['question_text']
            #     username = row['username']
                
                    
            #     formatted[username]['responses'].append({
            #         'question_id': question_id,
            #         'question_text': question_text,
            #         'choices': []
            #     })
            
            # formatted_list = list(formatted.values())
            
            cursor.close()
            return render_template('admin_results.html', responses=responses, total_marks=total_marks, current_mark=current_mark)
    else:
        return redirect(url_for('login'))
 

@app.route('/take_quiz', methods=['GET', 'POST'])
def take_quiz():
    if 'role' in session and session['role'] == 'student':
        if request.method == 'POST':
            answers = request.form
            for question_id, choice_id in answers.items():
                if question_id == 'subjects':
                    continue
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute(
                    "INSERT INTO user_responses (user_id, question_id, choice_id, answered_at) VALUES (%s, %s, %s, NOW())",
                    (session['user_id'], question_id, choice_id)
                )
                mysql.connection.commit()
                cursor.close()
            flash('Quiz submitted successfully')
            return redirect(url_for('view_results'))

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT q.question_id, q.subject_id, q.question_text, c.choice_id, c.choice_text FROM questions q INNER JOIN choices c ON q.question_id = c.question_id ORDER BY q.question_id, c.choice_id;")
        questions = cursor.fetchall()
        cursor.execute("SELECT * FROM subjects;")
        subjects = cursor.fetchall()
        
        cursor.close()
        formatted = {}
        
        for row in questions:
            question_id = row['question_id']
            question_text = row['question_text']
            choice_id = row['choice_id']
            choice_text = row['choice_text']
            subject_id = row['subject_id']
            
            if question_id not in formatted:
                formatted[question_id] = {
                    'subject_id': subject_id,
                    'question_id': question_id,
                    'question_text': question_text,
                    'choices': []
                }
                
            formatted[question_id]['choices'].append({
                'choice_id': choice_id,
                'choice_text': choice_text
            })
        
        formatted_list = list(formatted.values())
        
        print(formatted_list)
        
        return render_template('quiz.html', questions=formatted_list, subjects=subjects)
    else:
        return redirect(url_for('login'))

@app.route('/quiz/<int:subject_id>', methods=['GET'])
def quiz(subject_id):
    if 'role' in session and session['role'] == 'student':
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM Questions WHERE subject_id=%s", (subject_id,))
        questions = cursor.fetchall()
        cursor.close()
        return render_template('quiz.html', questions=questions)
    else:
        return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)