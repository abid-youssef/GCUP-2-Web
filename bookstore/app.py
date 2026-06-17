import os
import secrets
import sqlite3
import subprocess

from flask import Flask, jsonify, redirect, render_template, request, session

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(32))

DB_PATH = '/app/data.db'
ENV_STORE = '/app/instance'


_NATIVE = (type, object)


def _populate(obj, data):
    for k, v in data.items():
        if isinstance(v, dict):
            node = getattr(obj, k, None)
            if node is None or node in _NATIVE:
                continue
            _populate(node, v)
        elif not k.startswith('__'):
            setattr(obj, k, v)


class SortConfig:
    field = 'title'
    order = 'asc'


class SearchConfig:
    allowed_genres = ['fiction', 'science', 'history', 'biography']

    def __init__(self):
        self.genre = ''
        self.sort = SortConfig()

    def is_allowed(self):
        return self.genre in type(self).allowed_genres


def get_db():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db


def init_db():
    if os.path.exists(DB_PATH):
        return
    db = get_db()
    db.executescript("""
        CREATE TABLE books (
            id      INTEGER PRIMARY KEY,
            title   TEXT,
            author  TEXT,
            genre   TEXT
        );
        CREATE TABLE admin (
            id       INTEGER PRIMARY KEY,
            username TEXT,
            password TEXT
        );
        INSERT INTO books VALUES (1,  'Dune',                        'Frank Herbert',       'fiction');
        INSERT INTO books VALUES (2,  'Foundation',                  'Isaac Asimov',        'fiction');
        INSERT INTO books VALUES (3,  'Neuromancer',                 'William Gibson',      'fiction');
        INSERT INTO books VALUES (4,  'The Left Hand of Darkness',   'Ursula K. Le Guin',   'fiction');
        INSERT INTO books VALUES (5,  'A Brief History of Time',     'Stephen Hawking',     'science');
        INSERT INTO books VALUES (6,  'The Selfish Gene',            'Richard Dawkins',     'science');
        INSERT INTO books VALUES (7,  'Cosmos',                      'Carl Sagan',          'science');
        INSERT INTO books VALUES (8,  'The Double Helix',            'James D. Watson',     'science');
        INSERT INTO books VALUES (9,  'Sapiens',                     'Yuval Noah Harari',   'history');
        INSERT INTO books VALUES (10, 'Guns Germs and Steel',        'Jared Diamond',       'history');
        INSERT INTO books VALUES (11, 'The Art of War',              'Sun Tzu',             'history');
        INSERT INTO books VALUES (12, 'The Diary of a Young Girl',   'Anne Frank',          'biography');
        INSERT INTO books VALUES (13, 'Long Walk to Freedom',        'Nelson Mandela',      'biography');
        INSERT INTO books VALUES (14, 'Leonardo da Vinci',           'Walter Isaacson',     'biography');
        INSERT INTO admin VALUES (1, 'admin', '2a7a27c730d17896473c31dbbd167f0c');
    """)
    db.commit()
    db.close()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/books')
def list_books():
    db = get_db()
    genre = session.get('genre', '')
    sort_field = session.get('sort_field', 'title')
    sort_order = session.get('sort_order', 'asc')
    if sort_field not in ('title', 'author', 'id'):
        sort_field = 'title'
    if sort_order not in ('asc', 'desc'):
        sort_order = 'asc'
    if genre:
        rows = db.execute(
            f"SELECT id, title, author FROM books WHERE genre='{genre}'"
            f' ORDER BY {sort_field} {sort_order}'
        ).fetchall()
    else:
        rows = db.execute(
            f'SELECT id, title, author FROM books ORDER BY {sort_field} {sort_order}'
        ).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])


@app.route('/api/prefs', methods=['POST'])
def update_prefs():
    cfg = SearchConfig()
    _populate(cfg, request.get_json(force=True))
    if cfg.genre and not cfg.is_allowed():
        return jsonify({'error': 'invalid genre'}), 400
    sort_field = getattr(cfg.sort, 'field', 'title')
    sort_order = getattr(cfg.sort, 'order', 'asc')
    if sort_field not in ('title', 'author', 'id'):
        sort_field = 'title'
    if sort_order not in ('asc', 'desc'):
        sort_order = 'asc'
    session['genre'] = cfg.genre
    session['sort_field'] = sort_field
    session['sort_order'] = sort_order
    return jsonify({'ok': True})


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    db = get_db()
    u = request.form.get('username')
    p = request.form.get('password')
    row = db.execute(
        'SELECT * FROM admin WHERE username=? AND password=?', (u, p)
    ).fetchone()
    db.close()
    if row:
        session['role'] = 'admin'
        session['env_id'] = secrets.token_hex(8)
        return jsonify({'ok': True})
    return jsonify({'error': 'invalid credentials'}), 401


@app.route('/admin/backup', methods=['GET', 'POST'])
def admin_backup():
    if session.get('role') != 'admin':
        return redirect('/login')

    if request.method == 'GET':
        return render_template('admin.html')

    action = request.form.get('action')
    uid = session['env_id']
    env_file = os.path.join(ENV_STORE, f'{uid}.env')

    if action == 'save':
        from dotenv import set_key
        set_key(env_file, 'BACKUP_SERVER', request.form.get('backup_server', ''))
        set_key(env_file, 'ARCHIVE_PATH', request.form.get('archive_path', ''))
        return jsonify({'ok': True})

    if action == 'run':
        from dotenv import dotenv_values
        vals = {k: v for k, v in dotenv_values(env_file).items() if v is not None}
        env = {k: v for k, v in os.environ.items() if k != 'SECRET_KEY'}
        env.update(vals)
        result = subprocess.run(
            ['/usr/local/bin/python3', '/app/backup.py'],
            env=env, capture_output=True, text=True, timeout=10
        )
        return jsonify({'output': result.stdout + result.stderr})

    return jsonify({'error': 'unknown action'}), 400


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
