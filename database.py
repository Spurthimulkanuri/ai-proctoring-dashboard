import sqlite3
import bcrypt

# Connect to your SQLite DB
conn = sqlite3.connect('database.db')
c = conn.cursor()

# Create tables (if not already)
c.execute('''CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    role TEXT,
    branch TEXT,
    year TEXT,
    subject TEXT
)''')

# Hash the password 'admin123'
hashed_pw = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# Insert admin user (if not exists)
c.execute("INSERT OR IGNORE INTO users (username, password, role, branch, year, subject) VALUES (?, ?, 'admin', '', '', '')", 
          ('admin', hashed_pw))

conn.commit()
conn.close()
print("✅ Admin created successfully!")

