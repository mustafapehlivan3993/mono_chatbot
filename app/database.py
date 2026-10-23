"""Ödev sürümü: SQLite Render'ın geçici diskinde çalışır."""
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from flask import current_app

SCHEMA = '''CREATE TABLE IF NOT EXISTS mono_leads (
    id TEXT PRIMARY KEY,
    isim TEXT NOT NULL,
    eposta TEXT NOT NULL,
    telefon TEXT NOT NULL,
    mesaj TEXT NOT NULL,
    kaynak TEXT NOT NULL,
    tarih TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
)'''


@contextmanager
def connect():
    path = Path(current_app.config.get('SQLITE_PATH') or os.getenv('SQLITE_PATH')
                or Path(current_app.instance_path) / 'mono.db')
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=15)
    conn.row_factory = sqlite3.Row
    try:
        with conn:
            conn.execute(SCHEMA)
            yield conn
    finally:
        conn.close()


def save_lead(data):
    with connect() as conn:
        inserted = conn.execute('''INSERT INTO mono_leads
            (id, isim, eposta, telefon, mesaj, kaynak) VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT (id) DO NOTHING''',
            tuple(data[key] for key in ('id', 'isim', 'eposta', 'telefon', 'mesaj', 'kaynak'))).rowcount
        if not inserted:
            existing = conn.execute('SELECT * FROM mono_leads WHERE id = ?', (data['id'],)).fetchone()
            if any(existing[key] != data[key] for key in ('isim', 'eposta', 'telefon', 'mesaj', 'kaynak')):
                raise ValueError('Bu istek kimliği başka bir kayıt için kullanılmış.')
    return data['id']


def list_leads(limit, offset):
    with connect() as conn:
        rows = conn.execute('''SELECT id, isim, eposta, telefon, mesaj, kaynak, tarih
            FROM mono_leads ORDER BY tarih DESC, id DESC LIMIT ? OFFSET ?''',
            (limit + 1, offset)).fetchall()
    return [dict(row) for row in rows[:limit]], len(rows) > limit
