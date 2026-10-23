"""Kalıcı lead kayıtları. DATABASE_URL yalnız sunucu ortamından okunur."""
import os


class StorageUnavailable(RuntimeError):
    pass


SCHEMA = '''CREATE TABLE IF NOT EXISTS mono_leads (
    id UUID PRIMARY KEY,
    isim VARCHAR(150) NOT NULL,
    eposta VARCHAR(254) NOT NULL,
    telefon VARCHAR(40) NOT NULL,
    mesaj VARCHAR(5000) NOT NULL,
    kaynak VARCHAR(20) NOT NULL,
    tarih TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
)'''


def connect():
    url = os.environ.get('DATABASE_URL', '').strip()
    if not url:
        raise StorageUnavailable('DATABASE_URL ayarlanmadı.')
    import psycopg
    from psycopg.rows import dict_row
    return psycopg.connect(url, connect_timeout=10, row_factory=dict_row,
                           options='-c statement_timeout=10000')


def prepare(conn):
    # Birden fazla Gunicorn worker ilk isteği aynı anda alabilir.
    conn.execute('SELECT pg_advisory_xact_lock(718423991)')
    conn.execute(SCHEMA)


def save_lead(data):
    with connect() as conn:
        prepare(conn)
        row = conn.execute('''INSERT INTO mono_leads
            (id, isim, eposta, telefon, mesaj, kaynak)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING RETURNING id''',
            tuple(data[key] for key in ('id', 'isim', 'eposta', 'telefon', 'mesaj', 'kaynak'))).fetchone()
        if row is None:
            existing = conn.execute('SELECT * FROM mono_leads WHERE id = %s', (data['id'],)).fetchone()
            if any(existing[key] != data[key] for key in ('isim', 'eposta', 'telefon', 'mesaj', 'kaynak')):
                raise ValueError('Bu istek kimliği başka bir kayıt için kullanılmış.')
    return data['id']


def list_leads(limit, offset):
    with connect() as conn:
        prepare(conn)
        rows = conn.execute('''SELECT id, isim, eposta, telefon, mesaj, kaynak, tarih
            FROM mono_leads ORDER BY tarih DESC, id DESC LIMIT %s OFFSET %s''',
            (limit + 1, offset)).fetchall()
    more = len(rows) > limit
    result = rows[:limit]
    for row in result:
        row['id'] = str(row['id'])
        row['tarih'] = row['tarih'].isoformat()
    return result, more
