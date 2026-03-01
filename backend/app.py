#!/usr/bin/env python3
import json
import sqlite3
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

DB_PATH = 'backend/data.sqlite'


def db_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


class Handler(BaseHTTPRequestHandler):
    def _json(self, code, payload):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type,x-participant-id')
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode())

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type,x-participant-id')
        self.send_header('Access-Control-Allow-Methods', 'GET,POST,PATCH,OPTIONS')
        self.end_headers()

    def read_body(self):
        size = int(self.headers.get('Content-Length', 0))
        return json.loads(self.rfile.read(size) or b'{}')

    def participant(self):
        pid = self.headers.get('x-participant-id')
        if not pid:
            return None
        with db_conn() as conn:
            return conn.execute('SELECT * FROM participants WHERE id=?', (pid,)).fetchone()

    def do_GET(self):
        path = urlparse(self.path).path
        if path == '/health':
            return self._json(200, {'ok': True})
        if path == '/admin/dashboard':
            with db_conn() as conn:
                participants = conn.execute('SELECT COUNT(*) c FROM participants').fetchone()['c']
                teams = conn.execute('SELECT COUNT(*) c FROM groups').fetchone()['c']
                active = conn.execute("SELECT COUNT(*) c FROM groups WHERE status='active'").fetchone()['c']
                solved = conn.execute('SELECT COUNT(*) c FROM submissions').fetchone()['c']
            return self._json(200, {'participants': participants, 'teams': teams, 'activeTeams': active, 'qrSolvedCount': solved})
        return self._json(404, {'error': 'Not found'})

    def do_POST(self):
        path = urlparse(self.path).path
        body = self.read_body()
        with db_conn() as conn:
            if path == '/auth/participant/register':
                req = ('fullName', 'department', 'collegeEmail', 'collegeRoll', 'year')
                if not all(body.get(k) for k in req):
                    return self._json(400, {'error': 'All fields required'})
                try:
                    cur = conn.execute(
                        'INSERT INTO participants (participant_code,full_name,department,college_email,college_roll,study_year) VALUES (?,?,?,?,?,?)',
                        (f"P-{body['collegeRoll']}", body['fullName'], body['department'], body['collegeEmail'], body['collegeRoll'], body['year'])
                    )
                    conn.commit()
                    return self._json(201, {'participantId': cur.lastrowid, 'participantCode': f"P-{body['collegeRoll']}"})
                except sqlite3.IntegrityError:
                    return self._json(409, {'error': 'Email or roll already exists'})

            if path == '/groups':
                user = self.participant()
                if not user:
                    return self._json(401, {'error': 'Unauthorized'})
                name = body.get('groupName')
                if not name:
                    return self._json(400, {'error': 'groupName required'})
                exists = conn.execute('SELECT 1 FROM group_members WHERE participant_id=? AND left_at IS NULL', (user['id'],)).fetchone()
                if exists:
                    return self._json(409, {'error': 'Already in a group'})
                try:
                    cur = conn.execute('INSERT INTO groups (group_name,leader_participant_id,status) VALUES (?,?,?)', (name, user['id'], 'forming'))
                    gid = cur.lastrowid
                    conn.execute('INSERT INTO group_members (group_id,participant_id) VALUES (?,?)', (gid, user['id']))
                    conn.commit()
                    return self._json(201, {'groupId': gid, 'groupName': name})
                except sqlite3.IntegrityError:
                    return self._json(409, {'error': 'Group exists'})

            if path == '/qr/scan':
                user = self.participant()
                if not user:
                    return self._json(401, {'error': 'Unauthorized'})
                qr = conn.execute('SELECT * FROM qr_codes WHERE token=? AND is_active=1', (body.get('token'),)).fetchone()
                if not qr:
                    return self._json(404, {'error': 'Invalid token'})
                return self._json(200, {'qrNumber': qr['qr_number'], 'question': qr['question_text'], 'isFinal': bool(qr['is_final'])})

            if path == '/submissions':
                user = self.participant()
                if not user:
                    return self._json(401, {'error': 'Unauthorized'})
                for k in ('qrNumber', 'answer', 'explanation'):
                    if not body.get(k):
                        return self._json(400, {'error': 'All fields required'})
                group = conn.execute('SELECT group_id FROM group_members WHERE participant_id=? AND left_at IS NULL', (user['id'],)).fetchone()
                if not group:
                    return self._json(400, {'error': 'Join a group first'})
                gid = group['group_id']
                cnt = conn.execute('SELECT COUNT(*) c FROM group_members WHERE group_id=? AND left_at IS NULL', (gid,)).fetchone()['c']
                if cnt < 2:
                    return self._json(409, {'error': 'Need at least 2 members'})
                qr = conn.execute('SELECT * FROM qr_codes WHERE qr_number=?', (body['qrNumber'],)).fetchone()
                if not qr:
                    return self._json(404, {'error': 'QR not found'})
                try:
                    conn.execute('INSERT INTO submissions (group_id,qr_code_id,submitted_by_participant_id,answer_text,explanation_text) VALUES (?,?,?,?,?)',
                                 (gid, qr['id'], user['id'], body['answer'], body['explanation']))
                    conn.commit()
                except sqlite3.IntegrityError:
                    return self._json(409, {'error': 'Already submitted this QR'})
                if qr['is_final']:
                    unsolved = conn.execute('SELECT COUNT(*) c FROM qr_codes q WHERE q.is_final=0 AND NOT EXISTS (SELECT 1 FROM submissions s WHERE s.group_id=? AND s.qr_code_id=q.id)', (gid,)).fetchone()['c']
                    if unsolved > 0:
                        return self._json(409, {'error': 'Solve other QR answers before final QR'})
                    return self._json(200, {'message': 'Congratulations, you successfully caught the murderer.'})
                return self._json(201, {'ok': True})

            if path == '/admin/login':
                admin = conn.execute('SELECT * FROM admin_users WHERE email=? AND password=?', (body.get('email'), body.get('password'))).fetchone()
                if not admin:
                    return self._json(401, {'error': 'Invalid credentials'})
                return self._json(200, {'adminId': admin['id'], 'name': admin['full_name']})

        return self._json(404, {'error': 'Not found'})


def run():
    server = HTTPServer(('0.0.0.0', 4000), Handler)
    print('Backend running on http://localhost:4000')
    server.serve_forever()


if __name__ == '__main__':
    run()
