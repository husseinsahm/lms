from flask import Flask, render_template, request, redirect, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'secret123'

DB_FILE = 'library.db'

# ----------------------- Database -----------------------
def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    if not os.path.exists(DB_FILE):
        conn = get_db_connection()
        c = conn.cursor()

        # Users table
        c.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT
        )
        ''')

        # Books table
        c.execute('''
        CREATE TABLE books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            author TEXT
        )
        ''')

        # Borrowed books table
        c.execute('''
        CREATE TABLE borrowed_books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            book_id INTEGER,
            borrow_date TEXT DEFAULT (datetime('now')),
            return_date TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(book_id) REFERENCES books(id)
        )
        ''')

        # Insert initial users
        c.execute("INSERT INTO users (username, password, role) VALUES ('admin', '1234', 'admin')")
        c.execute("INSERT INTO users (username, password, role) VALUES ('ahmed', '1111', 'user')")

        # Insert initial books
        c.executemany("INSERT INTO books (title, author) VALUES (?, ?)", [
            ('Python Basics', 'Mark Lutz'),
            ('Flask Web Development', 'Miguel Grinberg'),
            ('Clean Code', 'Robert C. Martin'),
            ('Automate the Boring Stuff', 'Al Sweigart')
        ])

        conn.commit()
        conn.close()

init_db()

# ----------------------- Routes -----------------------

@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password)).fetchone()
        conn.close()
        if user:
            session['user'] = username
            session['role'] = user['role']
            session['user_id'] = user['id']
            return redirect('/dashboard')
        else:
            error = "Invalid username or password"
    return render_template('login.html', error=error)

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/')

    conn = get_db_connection()
    if session['role'] == 'admin':
        books = conn.execute("SELECT * FROM books").fetchall()
        borrowed_records = conn.execute("""
        SELECT bb.id, b.title, u.username, bb.borrow_date, bb.return_date, bb.book_id
        FROM borrowed_books bb
        JOIN books b ON bb.book_id = b.id
        JOIN users u ON bb.user_id = u.id
    """).fetchall()

         # حساب حالة Availability لكل كتاب
        books_with_status = []
        for book in books:
            borrowed = any(bb['book_id'] == book['id'] and bb['return_date'] is None for bb in borrowed_records)
            books_with_status.append({
                'id': book['id'],
                'title': book['title'],
                'author': book['author'],
                'available': not borrowed
            })

        # حساب الإحصائيات
        total_books = len(books_with_status)
        available_books_count = sum(1 for b in books_with_status if b['available'])
        borrowed_books_count = total_books - available_books_count

        conn.close()
        return render_template(
            'dashboard_admin.html',
            user=session['user'],
            books=books_with_status,
            borrowed=borrowed_records,
            total_books=total_books,
            available_books=available_books_count,
            borrowed_books=borrowed_books_count
        )
    else:
        borrowed_books = conn.execute("""
            SELECT bb.id, b.title, bb.borrow_date, bb.return_date
            FROM borrowed_books bb
            JOIN books b ON bb.book_id = b.id
            WHERE bb.user_id = ?
        """, (session['user_id'],)).fetchall()

        available_books = conn.execute("""
            SELECT * FROM books 
            WHERE id NOT IN (SELECT book_id FROM borrowed_books WHERE return_date IS NULL)
        """).fetchall()
        conn.close()
        return render_template('dashboard_user.html', user=session['user'], borrowed_books=borrowed_books, available_books=available_books)

@app.route('/borrow/<int:book_id>')
def borrow(book_id):
    if 'user' not in session:
        return redirect('/')
    conn = get_db_connection()
    conn.execute("INSERT INTO borrowed_books (user_id, book_id) VALUES (?, ?)", (session['user_id'], book_id))
    conn.commit()
    conn.close()
    return redirect('/dashboard')

@app.route('/return/<int:borrow_id>')
def return_book(borrow_id):
    if 'user' not in session:
        return redirect('/')
    conn = get_db_connection()
    conn.execute("UPDATE borrowed_books SET return_date=datetime('now') WHERE id=?", (borrow_id,))
    conn.commit()
    conn.close()
    return redirect('/dashboard')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


# ---------------- Admin CRUD ----------------

# Add Book
@app.route('/admin/add_book', methods=['POST'])
def add_book():
    if 'user' not in session or session['role'] != 'admin':
        return redirect('/')
    title = request.form['title']
    author = request.form['author']
    conn = get_db_connection()
    conn.execute("INSERT INTO books (title, author) VALUES (?, ?)", (title, author))
    conn.commit()
    conn.close()
    return redirect('/dashboard')

# Edit Book
@app.route('/admin/edit_book/<int:book_id>', methods=['POST'])
def edit_book(book_id):
    if 'user' not in session or session['role'] != 'admin':
        return redirect('/')
    title = request.form['title']
    author = request.form['author']
    conn = get_db_connection()
    conn.execute("UPDATE books SET title=?, author=? WHERE id=?", (title, author, book_id))
    conn.commit()
    conn.close()
    return redirect('/dashboard')

# Delete Book
@app.route('/admin/delete_book/<int:book_id>', methods=['POST'])
def delete_book(book_id):
    if 'user' not in session or session['role'] != 'admin':
        return redirect('/')
    conn = get_db_connection()
    conn.execute("DELETE FROM books WHERE id=?", (book_id,))
    conn.commit()
    conn.close()
    return redirect('/dashboard')



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
