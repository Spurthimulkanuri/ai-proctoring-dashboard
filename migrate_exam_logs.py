import sqlite3

conn = sqlite3.connect('database.db')
c = conn.cursor()

# Backup old table if exists
c.execute('ALTER TABLE exam_logs RENAME TO exam_logs_old')

# Create new table with correct schema
c.execute('''
CREATE TABLE exam_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_name TEXT,
    subject TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    violations INTEGER DEFAULT 0,
    cheating_type TEXT
)
''')

# Copy data from old table
c.execute('''
INSERT INTO exam_logs (student_name, subject, timestamp, violations)
SELECT student_name, subject, submitted_at, violations FROM exam_logs_old
''')

conn.commit()
conn.close()
print("✅ Migration complete.")

