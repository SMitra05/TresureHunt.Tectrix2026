#!/usr/bin/env python3
import hashlib
import secrets
import sqlite3
from pathlib import Path

DB_PATH = Path('backend/data.sqlite')
MIG_DIR = Path('backend/migrations')


def hash_password(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 120000).hex()
    return digest, salt


def ensure_column(conn, table, column, ddl):
    cols = {r[1] for r in conn.execute(f'PRAGMA table_info({table})').fetchall()}
    if column not in cols:
        conn.execute(f'ALTER TABLE {table} ADD COLUMN {ddl}')


conn = sqlite3.connect(DB_PATH)
conn.execute('CREATE TABLE IF NOT EXISTS migrations (name TEXT PRIMARY KEY, applied_at TEXT DEFAULT CURRENT_TIMESTAMP)')

for migration in sorted(MIG_DIR.glob('*.sql')):
    exists = conn.execute('SELECT 1 FROM migrations WHERE name=?', (migration.name,)).fetchone()
    if exists:
        continue
    conn.executescript(migration.read_text())
    conn.execute('INSERT INTO migrations(name) VALUES (?)', (migration.name,))
    print(f'Applied {migration.name}')

ensure_column(conn, 'participants', 'password_hash', 'password_hash TEXT')
ensure_column(conn, 'participants', 'password_salt', 'password_salt TEXT')
ensure_column(conn, 'groups', 'disqualified_reason', 'disqualified_reason TEXT')
ensure_column(conn, 'groups', 'disqualified_at', 'disqualified_at TEXT')
ensure_column(conn, 'admin_users', 'password_hash', 'password_hash TEXT')
ensure_column(conn, 'admin_users', 'password_salt', 'password_salt TEXT')
ensure_column(conn, 'participant_sessions', 'expires_at', 'expires_at TEXT')
ensure_column(conn, 'admin_sessions', 'expires_at', 'expires_at TEXT')

admin = conn.execute("SELECT id, password_hash, password_salt FROM admin_users WHERE email='admin@tectrix.edu'").fetchone()
if admin and (not admin[1] or not admin[2]):
    digest, salt = hash_password('admin123')
    conn.execute('UPDATE admin_users SET password_hash=?, password_salt=? WHERE id=?', (digest, salt, admin[0]))

conn.commit()
conn.close()
print('Migrations complete')
