import sqlite3, bcrypt

conn = sqlite3.connect('database.db')
c = conn.cursor()

# Uncomment if table doesn't exist
c.execute('''CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    role TEXT
)''')

# Add admin
username = 'admin'
password = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, password, 'admin'))

# Add student
student = 'spurthi'
spwd = bcrypt.hashpw('shiva123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (student, spwd, 'student'))

conn.commit()
conn.close()
print("✅ Users created")

