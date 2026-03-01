#!/usr/bin/env python3
import json
import secrets
import sqlite3
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

DB_PATH = 'backend/data.sqlite'


def db_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn


class Handler(BaseHTTPRequestHandler):
    def _json(self, code, payload):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode())

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        self.send_header('Access-Control-Allow-Methods', 'GET,POST,PATCH,OPTIONS')
        self.end_headers()

    def read_body(self):
        size = int(self.headers.get('Content-Length', 0))
        raw = self.rfile.read(size) if size > 0 else b'{}'
        try:
            return json.loads(raw or b'{}')
        except json.JSONDecodeError:
            return {}

    def token(self):
        auth = self.headers.get('Authorization', '')
        if auth.startswith('Bearer '):
            return auth.split(' ', 1)[1].strip()
        return None

    def participant(self, conn):
        tok = self.token()
        if not tok:
            return None
        return conn.execute(
            'SELECT p.* FROM participant_sessions s JOIN participants p ON p.id=s.participant_id WHERE s.token=?',
            (tok,),
        ).fetchone()

    def admin(self, conn):
        tok = self.token()
        if not tok:
            return None
        return conn.execute(
            'SELECT a.* FROM admin_sessions s JOIN admin_users a ON a.id=s.admin_id WHERE s.token=?',
            (tok,),
        ).fetchone()

    def active_group(self, conn, participant_id):
        return conn.execute(
            """SELECT g.* FROM groups g
               JOIN group_members gm ON gm.group_id=g.id
               WHERE gm.participant_id=? AND gm.left_at IS NULL AND g.status!='disbanded'""",
            (participant_id,),
        ).fetchone()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        with db_conn() as conn:
            if path == '/health':
                return self._json(200, {'ok': True})

            if path == '/invitations':
                user = self.participant(conn)
                if not user:
                    return self._json(401, {'error': 'Unauthorized'})
                rows = conn.execute(
                    """SELECT gi.id, gi.status, gi.created_at, g.group_name, p.full_name invited_by
                       FROM group_invitations gi
                       JOIN groups g ON g.id=gi.group_id
                       JOIN participants p ON p.id=gi.invited_by_participant_id
                       WHERE gi.invited_participant_id=? AND gi.status='pending'
                       ORDER BY gi.id DESC""",
                    (user['id'],),
                ).fetchall()
                return self._json(200, {'invitations': [dict(r) for r in rows]})

            if path == '/admin/dashboard':
                admin = self.admin(conn)
                if not admin:
                    return self._json(401, {'error': 'Admin auth required'})
                participants = conn.execute('SELECT COUNT(*) c FROM participants').fetchone()['c']
                teams = conn.execute('SELECT COUNT(*) c FROM groups').fetchone()['c']
                active = conn.execute("SELECT COUNT(*) c FROM groups WHERE status='active'").fetchone()['c']
                solved = conn.execute('SELECT COUNT(*) c FROM submissions').fetchone()['c']
                latest = conn.execute(
                    """SELECT s.id, s.submitted_at, q.qr_number, g.group_name, p.full_name submitted_by
                       FROM submissions s
                       JOIN qr_codes q ON q.id=s.qr_code_id
                       JOIN groups g ON g.id=s.group_id
                       JOIN participants p ON p.id=s.submitted_by_participant_id
                       ORDER BY s.id DESC LIMIT 10"""
                ).fetchall()
                settings = conn.execute('SELECT * FROM game_settings WHERE id=1').fetchone()
                return self._json(
                    200,
                    {
                        'participants': participants,
                        'teams': teams,
                        'activeTeams': active,
                        'qrSolvedCount': solved,
                        'latestSubmissions': [dict(r) for r in latest],
                        'gameSettings': dict(settings) if settings else {},
                    },
                )

        return self._json(404, {'error': 'Not found'})

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        body = self.read_body()

        with db_conn() as conn:
            if path == '/auth/participant/register':
                req = ('fullName', 'department', 'collegeEmail', 'collegeRoll', 'year')
                if not all(body.get(k) for k in req):
                    return self._json(400, {'error': 'All fields required'})
                try:
                    code = f"P-{body['collegeRoll']}"
                    cur = conn.execute(
                        'INSERT INTO participants (participant_code,full_name,department,college_email,college_roll,study_year) VALUES (?,?,?,?,?,?)',
                        (code, body['fullName'], body['department'], body['collegeEmail'], body['collegeRoll'], body['year']),
                    )
                    token = secrets.token_urlsafe(24)
                    conn.execute('INSERT INTO participant_sessions (participant_id, token) VALUES (?,?)', (cur.lastrowid, token))
                    conn.commit()
                    return self._json(201, {'participantId': cur.lastrowid, 'participantCode': code, 'token': token})
                except sqlite3.IntegrityError:
                    return self._json(409, {'error': 'Email or roll already exists'})

            if path == '/auth/participant/login':
                email = body.get('collegeEmail')
                roll = body.get('collegeRoll')
                user = conn.execute(
                    'SELECT * FROM participants WHERE college_email=? OR college_roll=?', (email or '', roll or '')
                ).fetchone()
                if not user:
                    return self._json(404, {'error': 'Participant not found'})
                token = secrets.token_urlsafe(24)
                conn.execute('INSERT INTO participant_sessions (participant_id, token) VALUES (?,?)', (user['id'], token))
                conn.commit()
                return self._json(200, {'participantId': user['id'], 'participantCode': user['participant_code'], 'token': token})

            if path == '/auth/participant/logout':
                tok = self.token()
                if not tok:
                    return self._json(401, {'error': 'Unauthorized'})
                conn.execute('DELETE FROM participant_sessions WHERE token=?', (tok,))
                conn.commit()
                return self._json(200, {'ok': True})

            if path == '/groups':
                user = self.participant(conn)
                if not user:
                    return self._json(401, {'error': 'Unauthorized'})
                if self.active_group(conn, user['id']):
                    return self._json(409, {'error': 'Already in a group'})
                name = body.get('groupName')
                if not name:
                    return self._json(400, {'error': 'groupName required'})
                try:
                    cur = conn.execute('INSERT INTO groups (group_name,leader_participant_id,status) VALUES (?,?,?)', (name, user['id'], 'forming'))
                    gid = cur.lastrowid
                    conn.execute('INSERT INTO group_members (group_id,participant_id) VALUES (?,?)', (gid, user['id']))
                    conn.commit()
                    return self._json(201, {'groupId': gid, 'groupName': name})
                except sqlite3.IntegrityError:
                    return self._json(409, {'error': 'Group exists'})

            if path.startswith('/groups/') and path.endswith('/invitations'):
                user = self.participant(conn)
                if not user:
                    return self._json(401, {'error': 'Unauthorized'})
                try:
                    group_id = int(path.split('/')[2])
                except Exception:
                    return self._json(400, {'error': 'Invalid group id'})
                group = conn.execute('SELECT * FROM groups WHERE id=?', (group_id,)).fetchone()
                if not group:
                    return self._json(404, {'error': 'Group not found'})
                if group['leader_participant_id'] != user['id']:
                    return self._json(403, {'error': 'Only group leader can invite'})
                count = conn.execute('SELECT COUNT(*) c FROM group_members WHERE group_id=? AND left_at IS NULL', (group_id,)).fetchone()['c']
                if count >= 4:
                    return self._json(409, {'error': 'Group is full'})
                email = body.get('collegeEmail')
                roll = body.get('collegeRoll')
                invitee = conn.execute('SELECT * FROM participants WHERE college_email=? OR college_roll=?', (email or '', roll or '')).fetchone()
                if not invitee:
                    return self._json(404, {'error': 'Invitee not found'})
                if self.active_group(conn, invitee['id']):
                    return self._json(409, {'error': 'Invitee already in a group'})
                try:
                    cur = conn.execute(
                        'INSERT INTO group_invitations (group_id, invited_participant_id, invited_by_participant_id, status) VALUES (?,?,?,?)',
                        (group_id, invitee['id'], user['id'], 'pending'),
                    )
                    conn.commit()
                    return self._json(201, {'invitationId': cur.lastrowid})
                except sqlite3.IntegrityError:
                    return self._json(409, {'error': 'Already invited'})

            if path.startswith('/invitations/') and path.endswith('/accept'):
                user = self.participant(conn)
                if not user:
                    return self._json(401, {'error': 'Unauthorized'})
                inv_id = int(path.split('/')[2])
                inv = conn.execute('SELECT * FROM group_invitations WHERE id=?', (inv_id,)).fetchone()
                if not inv or inv['invited_participant_id'] != user['id'] or inv['status'] != 'pending':
                    return self._json(404, {'error': 'Invitation not found'})
                if self.active_group(conn, user['id']):
                    return self._json(409, {'error': 'Already in group'})
                count = conn.execute('SELECT COUNT(*) c FROM group_members WHERE group_id=? AND left_at IS NULL', (inv['group_id'],)).fetchone()['c']
                if count >= 4:
                    return self._json(409, {'error': 'Group full'})
                conn.execute('INSERT INTO group_members (group_id, participant_id) VALUES (?,?)', (inv['group_id'], user['id']))
                conn.execute('UPDATE group_invitations SET status=?, responded_at=CURRENT_TIMESTAMP WHERE id=?', ('accepted', inv_id))
                new_count = count + 1
                if new_count >= 2:
                    conn.execute("UPDATE groups SET status='active' WHERE id=?", (inv['group_id'],))
                conn.commit()
                return self._json(200, {'ok': True, 'groupId': inv['group_id']})

            if path.startswith('/invitations/') and path.endswith('/reject'):
                user = self.participant(conn)
                if not user:
                    return self._json(401, {'error': 'Unauthorized'})
                inv_id = int(path.split('/')[2])
                inv = conn.execute('SELECT * FROM group_invitations WHERE id=?', (inv_id,)).fetchone()
                if not inv or inv['invited_participant_id'] != user['id'] or inv['status'] != 'pending':
                    return self._json(404, {'error': 'Invitation not found'})
                conn.execute('UPDATE group_invitations SET status=?, responded_at=CURRENT_TIMESTAMP WHERE id=?', ('rejected', inv_id))
                conn.commit()
                return self._json(200, {'ok': True})

            if path == '/qr/scan':
                user = self.participant(conn)
                if not user:
                    return self._json(401, {'error': 'Unauthorized'})
                qr = conn.execute('SELECT * FROM qr_codes WHERE token=? AND is_active=1', (body.get('token'),)).fetchone()
                if not qr:
                    return self._json(404, {'error': 'Invalid token'})
                return self._json(200, {'qrNumber': qr['qr_number'], 'question': qr['question_text'], 'isFinal': bool(qr['is_final'])})

            if path == '/submissions':
                user = self.participant(conn)
                if not user:
                    return self._json(401, {'error': 'Unauthorized'})
                for k in ('qrNumber', 'answer', 'explanation'):
                    if not body.get(k):
                        return self._json(400, {'error': 'All fields required'})
                group = self.active_group(conn, user['id'])
                if not group:
                    return self._json(400, {'error': 'Join a group first'})
                gid = group['id']
                count = conn.execute('SELECT COUNT(*) c FROM group_members WHERE group_id=? AND left_at IS NULL', (gid,)).fetchone()['c']
                if count < 2:
                    return self._json(409, {'error': 'Need at least 2 members'})
                setting = conn.execute('SELECT * FROM game_settings WHERE id=1').fetchone()
                if setting and (setting['close_submissions'] or setting['status'] != 'running'):
                    return self._json(409, {'error': 'Submissions are closed'})
                qr = conn.execute('SELECT * FROM qr_codes WHERE qr_number=?', (body['qrNumber'],)).fetchone()
                if not qr:
                    return self._json(404, {'error': 'QR not found'})
                try:
                    conn.execute(
                        'INSERT INTO submissions (group_id,qr_code_id,submitted_by_participant_id,answer_text,explanation_text) VALUES (?,?,?,?,?)',
                        (gid, qr['id'], user['id'], body['answer'], body['explanation']),
                    )
                    conn.commit()
                except sqlite3.IntegrityError:
                    return self._json(409, {'error': 'Already submitted this QR'})

                if qr['is_final']:
                    unsolved = conn.execute(
                        'SELECT COUNT(*) c FROM qr_codes q WHERE q.is_final=0 AND NOT EXISTS (SELECT 1 FROM submissions s WHERE s.group_id=? AND s.qr_code_id=q.id)',
                        (gid,),
                    ).fetchone()['c']
                    if unsolved > 0:
                        return self._json(409, {'error': 'Solve other QR answers before final QR'})
                    return self._json(200, {'message': 'Congratulations, you successfully caught the murderer.'})

                return self._json(201, {'ok': True})

            if path == '/admin/login':
                admin = conn.execute('SELECT * FROM admin_users WHERE email=? AND password=?', (body.get('email'), body.get('password'))).fetchone()
                if not admin:
                    return self._json(401, {'error': 'Invalid credentials'})
                token = secrets.token_urlsafe(24)
                conn.execute('INSERT INTO admin_sessions (admin_id, token) VALUES (?,?)', (admin['id'], token))
                conn.commit()
                return self._json(200, {'adminId': admin['id'], 'name': admin['full_name'], 'token': token})

            if path == '/admin/logout':
                token = self.token()
                if not token:
                    return self._json(401, {'error': 'Admin auth required'})
                conn.execute('DELETE FROM admin_sessions WHERE token=?', (token,))
                conn.commit()
                return self._json(200, {'ok': True})

            if path == '/admin/broadcast':
                admin = self.admin(conn)
                if not admin:
                    return self._json(401, {'error': 'Admin auth required'})
                msg = body.get('message')
                if not msg:
                    return self._json(400, {'error': 'message required'})
                conn.execute('UPDATE game_settings SET broadcast_message=?, updated_at=CURRENT_TIMESTAMP WHERE id=1', (msg,))
                conn.commit()
                return self._json(200, {'ok': True, 'message': msg})

        return self._json(404, {'error': 'Not found'})

    def do_PATCH(self):
        path = urlparse(self.path).path
        body = self.read_body()
        with db_conn() as conn:
            if path == '/admin/game/state':
                admin = self.admin(conn)
                if not admin:
                    return self._json(401, {'error': 'Admin auth required'})
                status = body.get('status')
                close = body.get('closeSubmissions')
                if status and status not in ('running', 'paused', 'closed'):
                    return self._json(400, {'error': 'invalid status'})
                current = conn.execute('SELECT * FROM game_settings WHERE id=1').fetchone()
                next_status = status if status is not None else current['status']
                next_close = int(close) if isinstance(close, bool) else current['close_submissions']
                conn.execute(
                    'UPDATE game_settings SET status=?, close_submissions=?, updated_at=CURRENT_TIMESTAMP WHERE id=1',
                    (next_status, next_close),
                )
                conn.commit()
                return self._json(200, {'ok': True, 'status': next_status, 'closeSubmissions': bool(next_close)})

            if path == '/admin/game/final-qr':
                admin = self.admin(conn)
                if not admin:
                    return self._json(401, {'error': 'Admin auth required'})
                qr_num = body.get('qrNumber')
                qr = conn.execute('SELECT * FROM qr_codes WHERE qr_number=?', (qr_num,)).fetchone()
                if not qr:
                    return self._json(404, {'error': 'QR not found'})
                conn.execute('UPDATE qr_codes SET is_final=0')
                conn.execute('UPDATE qr_codes SET is_final=1 WHERE id=?', (qr['id'],))
                conn.execute('UPDATE game_settings SET final_qr_code_id=?, updated_at=CURRENT_TIMESTAMP WHERE id=1', (qr['id'],))
                conn.commit()
                return self._json(200, {'ok': True, 'finalQr': qr_num})

        return self._json(404, {'error': 'Not found'})


def run():
    server = HTTPServer(('0.0.0.0', 4000), Handler)
    print('Backend running on http://localhost:4000')
    server.serve_forever()


if __name__ == '__main__':
    run()
