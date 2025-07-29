import sqlite3, bcrypt

conn = sqlite3.connect('database.db')
c = conn.cursor()

# Admin user
admin_username = 'admin'
admin_password = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
c.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)", (admin_username, admin_password, 'admin'))

# Student user
student_username = 'spurthi'
student_password = bcrypt.hashpw('shiva123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
c.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)", (student_username, student_password, 'student'))

conn.commit()
conn.close()
print("✅ Admin and student users created.")

