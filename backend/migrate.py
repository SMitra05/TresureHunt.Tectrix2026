#!/usr/bin/env python3
import sqlite3
from pathlib import Path

DB_PATH = Path('backend/data.sqlite')
MIG_DIR = Path('backend/migrations')

conn = sqlite3.connect(DB_PATH)
conn.execute('CREATE TABLE IF NOT EXISTS migrations (name TEXT PRIMARY KEY, applied_at TEXT DEFAULT CURRENT_TIMESTAMP)')

for migration in sorted(MIG_DIR.glob('*.sql')):
    exists = conn.execute('SELECT 1 FROM migrations WHERE name=?', (migration.name,)).fetchone()
    if exists:
        continue
    conn.executescript(migration.read_text())
    conn.execute('INSERT INTO migrations(name) VALUES (?)', (migration.name,))
    print(f'Applied {migration.name}')

conn.commit()
conn.close()
print('Migrations complete')
