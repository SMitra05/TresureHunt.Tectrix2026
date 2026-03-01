import json
import threading
import time
import unittest
import urllib.error
import urllib.request

from backend import app

BASE = 'http://127.0.0.1:4010'


def req(path, method='GET', data=None, token=None):
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    body = None if data is None else json.dumps(data).encode()
    request = urllib.request.Request(BASE + path, data=body, method=method, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=5) as resp:
            text = resp.read().decode() or '{}'
            return resp.status, json.loads(text)
    except urllib.error.HTTPError as err:
        text = err.read().decode() or '{}'
        return err.code, json.loads(text)


class ApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import backend.migrate  # apply migrations

        cls.server = app.create_server('127.0.0.1', 4010)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        time.sleep(0.25)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=1)

    def test_end_to_end(self):
        ts = str(int(time.time() * 1000))

        _, a = req('/auth/participant/register', 'POST', {
            'fullName': 'User A',
            'department': 'CSE',
            'collegeEmail': f'a{ts}@ex.edu',
            'collegeRoll': f'A{ts}',
            'year': '1st',
            'password': 'strongpass1',
        })
        _, b = req('/auth/participant/register', 'POST', {
            'fullName': 'User B',
            'department': 'CSE',
            'collegeEmail': f'b{ts}@ex.edu',
            'collegeRoll': f'B{ts}',
            'year': '1st',
            'password': 'strongpass1',
        })
        token_a, token_b = a['token'], b['token']

        code, group = req('/groups', 'POST', {'groupName': f'Team{ts}'}, token_a)
        self.assertEqual(code, 201)

        code, invitation = req(f"/groups/{group['groupId']}/invitations", 'POST', {'collegeEmail': f'b{ts}@ex.edu'}, token_a)
        self.assertEqual(code, 201)

        code, _ = req(f"/invitations/{invitation['invitationId']}/accept", 'POST', {}, token_b)
        self.assertEqual(code, 200)

        _, admin = req('/admin/login', 'POST', {'email': 'admin@tectrix.edu', 'password': 'admin123'})
        req('/admin/game/state', 'PATCH', {'status': 'running', 'closeSubmissions': False}, admin['token'])

        code, _ = req('/qr/scan', 'POST', {'token': 'token-qr-1'}, token_a)
        self.assertEqual(code, 200)

        code, _ = req('/submissions', 'POST', {'qrNumber': 'QR1', 'answer': 'x', 'explanation': 'y'}, token_a)
        self.assertEqual(code, 201)


    def test_validation_errors(self):
        ts = str(int(time.time() * 1000))
        code, _ = req('/auth/participant/register', 'POST', {
            'fullName': 'Weak User',
            'department': 'CSE',
            'collegeEmail': f'weak{ts}@ex.edu',
            'collegeRoll': f'W{ts}',
            'year': '1st',
            'password': '123',
        })
        self.assertEqual(code, 400)

        code, _ = req('/auth/participant/login', 'POST', {'password': 'strongpass1'})
        self.assertEqual(code, 400)

        _, admin = req('/admin/login', 'POST', {'email': 'admin@tectrix.edu', 'password': 'admin123'})
        code, _ = req('/admin/teams/not-a-number/disqualify', 'PATCH', {'reason': 'bad'}, admin['token'])
        self.assertEqual(code, 400)

    def test_admin_controls(self):
        code, admin = req('/admin/login', 'POST', {'email': 'admin@tectrix.edu', 'password': 'admin123'})
        self.assertEqual(code, 200)
        admin_token = admin['token']

        self.assertEqual(req('/admin/game/state', 'PATCH', {'status': 'paused'}, admin_token)[0], 200)
        self.assertEqual(req('/admin/game/final-qr', 'PATCH', {'qrNumber': 'QR2'}, admin_token)[0], 200)
        self.assertEqual(req('/admin/qr/QR2', 'PATCH', {'question': 'Updated?', 'isActive': True}, admin_token)[0], 200)
        self.assertEqual(req('/admin/teams/999999/disqualify', 'PATCH', {'reason': 'test'}, admin_token)[0], 404)
        self.assertEqual(req('/admin/broadcast', 'POST', {'message': 'hello'}, admin_token)[0], 202)


if __name__ == '__main__':
    unittest.main()
