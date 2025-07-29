# create_admin.py
import sqlite3, bcrypt

conn = sqlite3.connect('database.db')
c = conn.cursor()

username = 'admin'
password = 'admin123'
hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

c.execute("INSERT INTO users (username, password, role, branch, year) VALUES (?, ?, 'admin', '', '')", (username, hashed))

conn.commit()
conn.close()

print("✅ Admin created: username=admin, password=admin123")

