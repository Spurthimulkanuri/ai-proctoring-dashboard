import sqlite3

conn = sqlite3.connect('database.db')
c = conn.cursor()

# Add missing columns to users table
try:
    c.execute("ALTER TABLE users ADD COLUMN branch TEXT")
except:
    pass

try:
    c.execute("ALTER TABLE users ADD COLUMN year TEXT")
except:
    pass

try:
    c.execute("ALTER TABLE users ADD COLUMN subject TEXT")
except:
    pass

conn.commit()
conn.close()

print("✅ users table updated with branch, year, subject columns.")

