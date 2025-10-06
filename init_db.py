import sqlite3

conn = sqlite3.connect('library.db')
cursor = conn.cursor()

# جدول المستخدمين
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    role TEXT DEFAULT 'user'
)
''')

# جدول الكتب
cursor.execute('''
CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    author TEXT,
    is_borrowed INTEGER DEFAULT 0,
    borrowed_by TEXT
)
''')

# إدخال بيانات مبدئية
cursor.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES ('admin', '1234', 'admin')")
cursor.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES ('ahmed', '1111', 'user')")

cursor.executemany('INSERT INTO books (title, author) VALUES (?, ?)', [
    ('Python Basics', 'Mark Lutz'),
    ('Flask Web Development', 'Miguel Grinberg'),
    ('Clean Code', 'Robert C. Martin'),
    ('Automate the Boring Stuff', 'Al Sweigart')
])

conn.commit()
conn.close()
print("✅ Database initialized successfully.")
