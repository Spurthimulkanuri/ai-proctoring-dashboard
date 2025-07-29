# check_questions.py
import sqlite3

conn = sqlite3.connect('database.db')
c = conn.cursor()
c.execute("SELECT subject, branch, year, question_text FROM questions")

rows = c.fetchall()
for row in rows:
    print(f"Subject: {row[0]}, Branch: {row[1]}, Year: {row[2]}, Question: {row[3]}")

conn.close()

