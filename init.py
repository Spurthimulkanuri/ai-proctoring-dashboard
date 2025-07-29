import sqlite3

conn = sqlite3.connect('exam.db')  # same name used in app.py
c = conn.cursor()

# Create exam_logs table
c.execute('''
CREATE TABLE IF NOT EXISTS exam_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_name TEXT,
    subject TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    violations INTEGER DEFAULT 0,
    cheating_type TEXT
)
''')

conn.commit()
conn.close()

print("✅ exam_logs table created.")

