# app.py
import os, sqlite3, bcrypt, base64, io
from flask import Flask, render_template, request, redirect, url_for, jsonify, Response
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
import pandas as pd
from collections import defaultdict
from flask_socketio import SocketIO, emit, join_room
import time
import base64
import os
from fpdf import FPDF
from flask import render_template_string
from weasyprint import HTML
from dotenv import load_dotenv
load_dotenv()
from sib_api_v3_sdk import Configuration, ApiClient
from sib_api_v3_sdk.api.transactional_emails_api import TransactionalEmailsApi
from sib_api_v3_sdk.models import SendSmtpEmail, SendSmtpEmailTo, SendSmtpEmailAttachment
from flask import send_from_directory

import os
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
BREVO_API_KEY = os.getenv("BREVO_API_KEY")

app = Flask(__name__)
app.secret_key = 'shuddha_exam_secret'

socketio = SocketIO(app)  # ✅ Add this here

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

UPLOAD_FOLDER = 'static/snapshots'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# User Model
class User(UserMixin):
    def __init__(self, id, username, role, subject):
        self.id = id
        self.username = username
        self.role = role
        self.subject = subject

@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT id, username, role, subject FROM users WHERE id = ?", (user_id,))
    user = c.fetchone()
    conn.close()
    if user:
        return User(id=user[0], username=user[1], role=user[2], subject=user[3])
    return None

def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT,
        branch TEXT,
        year TEXT,
        subject TEXT
    )''')

    # Questions table
    c.execute('''CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject TEXT,
        question_text TEXT,
        option_a TEXT,
        option_b TEXT,
        option_c TEXT,
        option_d TEXT,
        correct_answer TEXT,
        branch TEXT,
        year TEXT
    )''')

    # Exam logs table with correct schema
    c.execute('''CREATE TABLE IF NOT EXISTS exam_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_name TEXT,
        subject TEXT,
        answer TEXT,
        submitted_at TEXT,
        violations INTEGER DEFAULT 0,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        cheating_type TEXT
    )''')

    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    return redirect('/login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password'].encode('utf-8')
        branch = request.form['branch']
        year = request.form['year']
        subject = request.form['subject']

        hashed = bcrypt.hashpw(password, bcrypt.gensalt()).decode('utf-8')

        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        try:
            c.execute('''INSERT INTO users (username, password, role, branch, year, subject)
                         VALUES (?, ?, 'student', ?, ?, ?)''', (username, hashed, branch, year, subject))
            conn.commit()
        except sqlite3.IntegrityError:
            return "Username already exists"
        conn.close()
        return redirect('/login')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password'].encode('utf-8')

        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT id, username, password, role, subject FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        conn.close()

        if user and bcrypt.checkpw(password, user[2].encode('utf-8')):
            user_obj = User(id=user[0], username=user[1], role=user[3], subject=user[4])
            login_user(user_obj)
            return redirect(f"/exam?subject={user[4]}" if user[3] == 'student' else '/admin')
        else:
            return "Invalid credentials"
    return render_template('login.html')
from sib_api_v3_sdk import Configuration, ApiClient
from sib_api_v3_sdk.api.transactional_emails_api import TransactionalEmailsApi
from sib_api_v3_sdk.models import SendSmtpEmail, SendSmtpEmailAttachment, SendSmtpEmailTo

def send_email_with_attachments(to_email, subject, html_body, attachments=[]):
    config = Configuration()
    config.api_key['api-key'] = BREVO_API_KEY

    api_instance = TransactionalEmailsApi(ApiClient(configuration=config))

    email = SendSmtpEmail(
        to=[SendSmtpEmailTo(email=to_email)],
        subject=subject,
        html_content=html_body,
        sender={
          "name": os.getenv("SENDER_NAME"), 
           "email": os.getenv("SENDER_EMAIL")  # spurthimulkanuri@gmail.com
        },

        attachment=attachments
    )

    try:
        response = api_instance.send_transac_email(email)
        print("✅ Email sent successfully:", response.message_id)
    except Exception as e:
        print("❌ Email sending failed:", str(e))
send_email_with_attachments(
    to_email="shivlachinki06@gmail.com",
    subject="Test Email",
    html_body="<h2>This is a test email from Brevo API</h2>",
    attachments=[]
)

@app.route('/exam')
@login_required
def exam():
    if current_user.role != 'student':
        return "Unauthorized", 403

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT branch, year FROM users WHERE username = ?", (current_user.username,))
    branch_year = c.fetchone()
    branch, year = branch_year if branch_year else (None, None)

    subject = request.args.get('subject')
    if not subject:
        return "No subject selected", 400

    c.execute("SELECT * FROM questions WHERE branch=? AND year=? AND subject=?", (branch, year, subject))
    questions = c.fetchall()
    conn.close()

    return render_template('index.html', questions=questions, subject=subject)

@app.route('/submit_exam', methods=['POST'])
@login_required
def submit_exam():
    name = current_user.username
    subject = request.form.get('subject')
    submitted_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    violations = int(request.form.get('violations', 0))

    # 1️⃣ Save student answers
    answers = []
    for key in request.form:
        if key.startswith("q"):
            answers.append(f"{key}:{request.form[key]}")
    answer_str = "; ".join(answers)

    # 2️⃣ Auto-marking logic
    correct_answers = {
        "q1": "A",
        "q2": "C",
        "q3": "B",
        "q4": "D",
        "q5": "B"
        # ➕ Add more based on your real questions
    }

    score = 0
    for key in request.form:
        if key.startswith("q"):
            student_answer = request.form[key]
            correct_answer = correct_answers.get(key)
            if student_answer == correct_answer:
                score += 1  # 1 mark per correct

    # 3️⃣ Save to DB (with marks)
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("""INSERT INTO exam_logs 
                (student_name, subject, answer, submitted_at, violations, marks) 
                VALUES (?, ?, ?, ?, ?, ?)""",
              (name, subject, answer_str, submitted_at, violations, score))
    conn.commit()
    conn.close()

    # 4️⃣ Generate CSV for admin
    conn = sqlite3.connect('database.db')
    df = pd.read_sql_query("SELECT * FROM exam_logs WHERE subject=?", conn, params=(subject,))
    conn.close()
    csv_path = f"temp_logs_{subject}.csv"
    df.to_csv(csv_path, index=False)

    # 5️⃣ Generate PDF report
    pdf_path = f"cheating_report_{subject}.pdf"
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Cheating Analysis Report", ln=True, align='C')
    pdf.cell(200, 10, txt=f"Subject: {subject}", ln=True, align='L')
    pdf.cell(200, 10, txt=f"Submitted at: {submitted_at}", ln=True, align='L')
    pdf.output(pdf_path)

    # 6️⃣ Generate plagiarism report
    plagiarism_path = f"plagiarism_report_{subject}.txt"
    with open(plagiarism_path, "w") as f:
        flagged = detect_plagiarism()
        for a, b, sim in flagged:
            f.write(f"{a} vs {b} → {sim}%\n")

    # 7️⃣ Email all reports to admin via Brevo
    config = Configuration()
    config.api_key['api-key'] = BREVO_API_KEY
    api_instance = TransactionalEmailsApi(ApiClient(config))

    email = SendSmtpEmail(
        to=[SendSmtpEmailTo(email=ADMIN_EMAIL)],
        subject=f"📝 ShuddhaExam Report - {subject}",
        html_content=f"<p>Attached are reports for <b>{subject}</b>.</p>",
        sender={"name": os.getenv("SENDER_NAME"), "email": os.getenv("SENDER_EMAIL")},
        attachment=[
            SendSmtpEmailAttachment(name="violations.csv", content=base64.b64encode(open(csv_path, "rb").read()).decode()),
            SendSmtpEmailAttachment(name="cheating_report.pdf", content=base64.b64encode(open(pdf_path, "rb").read()).decode()),
            SendSmtpEmailAttachment(name="plagiarism.txt", content=base64.b64encode(open(plagiarism_path, "rb").read()).decode())
        ]
    )

    try:
        api_instance.send_transac_email(email)
        print("📧 Email sent to admin.")
    except Exception as e:
        print("❌ Email failed:", str(e))

    # 8️⃣ Delete temporary files
    for path in [csv_path, pdf_path, plagiarism_path]:
        if os.path.exists(path):
            os.remove(path)

    return "✅ Exam submitted successfully with marks, CSV, PDF & plagiarism emailed!"



@app.route('/add_question', methods=['POST'])
@login_required
def add_question():
    if current_user.role != 'admin':
        return "Unauthorized", 403

    data = request.form
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''INSERT INTO questions (subject, question_text, option_a, option_b, option_c, option_d, correct_answer, branch, year)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (data['subject'], data['question_text'], data['option_a'], data['option_b'],
               data['option_c'], data['option_d'], data['correct_answer'], data['branch'], data['year']))
    conn.commit()
    conn.close()
    return redirect('/admin')

@app.route('/upload_excel', methods=['POST'])
@login_required
def upload_excel():
    if current_user.role != 'admin':
        return "Unauthorized", 403

    file = request.files['excel_file']
    subject = request.form['subject']
    branch = request.form['branch']
    year = request.form['year']

    df = pd.read_excel(file)
    required_cols = {'question_text', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_answer'}
    if not required_cols.issubset(df.columns):
        return "Excel format incorrect. Required columns: question_text, option_a, option_b, option_c, option_d, correct_answer", 400

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    for _, row in df.iterrows():
        c.execute('''INSERT INTO questions (subject, question_text, option_a, option_b, option_c, option_d, correct_answer, branch, year)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (subject, row['question_text'], row['option_a'], row['option_b'],
                   row['option_c'], row['option_d'], row['correct_answer'], branch, year))
    conn.commit()
    conn.close()

    return redirect('/admin')

@app.route('/view_logs')
@login_required
def view_logs():
    if current_user.role != 'admin':
        return "Unauthorized", 403

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM exam_logs")
    logs = c.fetchall()
    conn.close()
    return render_template('logs.html', logs=logs)

@app.route('/download_logs')
@login_required
def download_logs():
    if current_user.role != 'admin':
        return "Unauthorized", 403

    conn = sqlite3.connect('database.db')
    df = pd.read_sql_query("SELECT * FROM exam_logs", conn)
    conn.close()

    output = io.StringIO()
    df.to_csv(output, index=False)
    output.seek(0)

    return Response(output, mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment;filename=exam_logs.csv'})

@app.route('/analytics', methods=['GET', 'POST'])
@login_required
def analytics():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute("SELECT DISTINCT subject FROM exam_logs")
    subjects = [row[0] for row in c.fetchall()]
    selected_subject = request.form.get('subject') if request.method == 'POST' else ""
    start_date = request.form.get('start_date') if request.method == 'POST' else ""
    end_date = request.form.get('end_date') if request.method == 'POST' else ""

    query = "SELECT student_name, SUM(violations), cheating_type FROM exam_logs WHERE 1=1"
    params = []
    if selected_subject:
        query += " AND subject = ?"
        params.append(selected_subject)
    if start_date:
        query += " AND date(timestamp) >= ?"
        params.append(start_date)
    if end_date:
        query += " AND date(timestamp) <= ?"
        params.append(end_date)

    query += " GROUP BY student_name, cheating_type"
    c.execute(query, params)
    raw_data = c.fetchall()
    conn.close()

    student_totals = defaultdict(int)
    cheat_type_totals = defaultdict(int)
    for name, count, cheat_type in raw_data:
        student_totals[name] += count
        cheat_type_totals[cheat_type] += count

    return render_template('analytics.html',
                           names=list(student_totals.keys()),
                           violations=list(student_totals.values()),
                           cheat_labels=list(cheat_type_totals.keys()),
                           cheat_counts=list(cheat_type_totals.values()),
                           subjects=subjects,
                           selected_subject=selected_subject,
                           start_date=start_date,
                           end_date=end_date)

@app.route('/live')
@login_required
def live_feed():
    if current_user.role != 'admin':
        return "Unauthorized", 403

    snapshot_dir = os.path.join("static", "snapshots")
    students = [f for f in os.listdir(snapshot_dir) if f.endswith('.jpg')]
    return render_template('live_feed.html', snapshots=students)

@app.route('/upload_snapshot', methods=['POST'])
def upload_snapshot():
    data = request.get_json()
    image_data = data['image']
    student_id = data['student_id']
    violation_type = data.get('violation_type', None)

    timestamp = time.strftime("%Y%m%d-%H%M%S")
    img_data = base64.b64decode(image_data.split(",")[1])

    # Save violation image (if any)
    if violation_type:
        violation_dir = os.path.join("static", "violations")
        os.makedirs(violation_dir, exist_ok=True)
        filename = f"{student_id}_{violation_type}_{timestamp}.jpg"
        filepath = os.path.join(violation_dir, filename)
        with open(filepath, "wb") as f:
            f.write(img_data)
        return jsonify({"status": "violation_saved", "type": violation_type})

    # Save regular snapshot
    snapshot_dir = os.path.join("static", "snapshots")
    os.makedirs(snapshot_dir, exist_ok=True)
    filename = f"{student_id}_{timestamp}.jpg"
    filepath = os.path.join(snapshot_dir, filename)
    with open(filepath, "wb") as f:
        f.write(img_data)

    return jsonify({"status": "snapshot_saved"})

@app.route('/admin')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        return "Unauthorized", 403

    snapshot_dir = os.path.join('static', 'snapshots')
    snapshots = [f for f in os.listdir(snapshot_dir) if f.endswith('.jpg')]

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users")
    users = c.fetchall()
    c.execute("SELECT * FROM questions")
    questions = c.fetchall()
    conn.close()

    return render_template('admin_panel.html', users=users, questions=questions, snapshot_images=snapshots)



@app.route('/admin_chat')
@login_required
def admin_chat():
    if current_user.role != 'admin':
        return "Unauthorized", 403
    return render_template('admin_chat.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')
@app.route('/exam_chat')
@login_required
def exam_chat():
    print("Current user role:", current_user.role)
    if current_user.role != 'student':
        return "Unauthorized", 403
    return render_template('exam_chat.html')


@app.route('/delete_question/<int:id>')
@login_required
def delete_question(id):
    if current_user.role != 'admin':
        return "Unauthorized", 403

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("DELETE FROM questions WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    return redirect('/admin')
@socketio.on('join')
def handle_join(data):
    room = data['room']
    join_room(room)
    emit('message', {'sender': 'System', 'msg': f"{data['user']} joined the chat."}, to=room)
@app.route('/replay/<student_id>')
@login_required
def replay(student_id):
    violation_dir = os.path.join('static', 'violations')
    images = []

    for filename in sorted(os.listdir(violation_dir)):
        if filename.startswith(student_id):
            images.append(f"/static/violations/{filename}")

    return render_template("replay.html", images=images, student_id=student_id)

@socketio.on('send_message')
def handle_message(data):
    room = data['room']
    emit('message', {'sender': data['user'], 'msg': data['msg']}, to=room)
def parse_answers(answer_str):
    """
    Converts 'q1:A; q2:C' → {'q1': 'A', 'q2': 'C'}
    Handles answers with ":" safely.
    """
    answers = {}
    for pair in answer_str.split(";"):
        if ":" in pair:
            parts = pair.strip().split(":", 1)  # split only once
            if len(parts) == 2:
                q, a = parts
                answers[q.strip()] = a.strip()
    return answers

@app.route('/download_analytics_pdf', methods=['POST'])
@login_required
def download_analytics_pdf():
    if current_user.role != 'admin':
        return "Unauthorized", 403

    # Reuse the same logic as /analytics
    subject = request.form.get('subject', '')
    start_date = request.form.get('start_date', '')
    end_date = request.form.get('end_date', '')

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    query = "SELECT student_name, SUM(violations), cheating_type FROM exam_logs WHERE 1=1"
    params = []

    if subject:
        query += " AND subject = ?"
        params.append(subject)
    if start_date:
        query += " AND date(timestamp) >= ?"
        params.append(start_date)
    if end_date:
        query += " AND date(timestamp) <= ?"
        params.append(end_date)

    query += " GROUP BY student_name, cheating_type"
    c.execute(query, params)
    raw_data = c.fetchall()
    conn.close()

    student_totals = defaultdict(int)
    cheat_type_totals = defaultdict(int)
    for name, count, cheat_type in raw_data:
        student_totals[name] += count
        cheat_type_totals[cheat_type] += count

    # Render to HTML string
    rendered_html = render_template("analytics_pdf.html",
                                    names=list(student_totals.keys()),
                                    violations=list(student_totals.values()),
                                    cheat_labels=list(cheat_type_totals.keys()),
                                    cheat_counts=list(cheat_type_totals.values()),
                                    subject=subject, start_date=start_date, end_date=end_date)

    # Convert HTML to PDF
    pdf = HTML(string=rendered_html).write_pdf()

    return Response(pdf, mimetype='application/pdf',
                    headers={'Content-Disposition': 'attachment;filename=analytics_report.pdf'})
def compare_answers(a1, a2):
    """
    Returns similarity percentage between two answer dicts
    """
    total = 0
    matched = 0
    for qid in a1:
        if qid in a2:
            total += 1
            if a1[qid] == a2[qid]:
                matched += 1
    return (matched / total * 100) if total else 0

def detect_plagiarism():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT student_name, answer FROM exam_logs")
    rows = c.fetchall()
    conn.close()

    parsed = [(name, parse_answers(ans)) for name, ans in rows]
    flagged_pairs = []

    for i in range(len(parsed)):
        for j in range(i+1, len(parsed)):
            name1, ans1 = parsed[i]
            name2, ans2 = parsed[j]
            sim = compare_answers(ans1, ans2)
            if sim > 90:
                flagged_pairs.append((name1, name2, round(sim, 2)))

    return flagged_pairs
@app.route('/results')
@login_required
def redirect_to_results():
    subject = request.args.get("subject")
    if subject:
        return redirect(url_for("view_results", subject=subject))
    return "❌ Subject not selected", 400
@app.route('/results/<subject>')
@login_required
def view_results(subject):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # ✅ Get all students' marks sorted by score (desc)
    c.execute("""
        SELECT student_name, marks, violations
        FROM exam_logs
        WHERE subject = ?
        ORDER BY marks DESC, violations ASC
    """, (subject,))
    
    results = c.fetchall()
    conn.close()

    return render_template('results.html', results=results, subject=subject)



@app.route('/download_violations')
@login_required
def download_violations():
    if current_user.role != 'admin':
        return "Unauthorized", 403

    conn = sqlite3.connect('database.db')
    query = "SELECT student_name, subject, violations, cheating_type, submitted_at FROM exam_logs WHERE violations > 0"
    df = pd.read_sql_query(query, conn)
    conn.close()

    output = io.StringIO()
    df.to_csv(output, index=False)
    output.seek(0)

    return Response(output, mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment;filename=violation_summary.csv'})

@app.route('/plagiarism_check')
@login_required
def plagiarism_check():
    if current_user.role != 'admin':
        return "Unauthorized", 403

    flagged = detect_plagiarism()
    return render_template('plagiarism.html', flagged_pairs=flagged)

if __name__ == '__main__':
    socketio.run(app, debug=True)
