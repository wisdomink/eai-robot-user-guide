"""Account/session contracts for SQLite and Moto DynamoDB; no live services."""

import hashlib
import importlib
import sys
import unittest
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import boto3
from fastapi import FastAPI
from fastapi.testclient import TestClient
from moto import mock_aws

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.admin import COOKIE_NAME, get_admin_storage, router
from app.services.admin_service import AdminStorage


@contextmanager
def storage_for(backend):
    with TemporaryDirectory() as directory:
        if backend == 'sqlite':
            yield AdminStorage(Path(directory) / 'admin.sqlite3')
        else:
            with mock_aws():
                table = boto3.resource('dynamodb', region_name='us-east-1').create_table(
                    TableName='admin-test', BillingMode='PAY_PER_REQUEST',
                    KeySchema=[{'AttributeName': 'pk', 'KeyType': 'HASH'}, {'AttributeName': 'sk', 'KeyType': 'RANGE'}],
                    AttributeDefinitions=[{'AttributeName': name, 'AttributeType': 'S'} for name in ('pk', 'sk')],
                )
                yield AdminStorage(table=table)


class AdminStorageTests(unittest.TestCase):
    def test_persistence_password_hashes_and_login_history(self):
        for backend in ('sqlite', 'dynamodb'):
            with self.subTest(backend=backend), storage_for(backend) as storage:
                admin = storage.login('admin', 'root123!', '127.0.0.1')
                self.assertEqual(admin['user']['role'], 'admin')
                created = storage.create_user('operator', 'initial123!')
                self.assertEqual(created['role'], 'user')
                self.assertNotIn('password_hash', created)
                saved = storage._get('USER', 'operator')
                self.assertNotIn('initial123!', saved['password_hash'])
                self.assertEqual(len(saved['password_hash'].split('$')[0]), 32)
                with self.assertRaises(FileExistsError):
                    storage.create_user('operator', 'different123!')
                self.assertIsNone(storage.login('operator', 'wrong', '127.0.0.2'))
                self.assertIsNone(storage.login('missing', 'initial123!', '127.0.0.3'))
                session = storage.login('operator', 'initial123!', '127.0.0.4')
                stored = storage._get('SESSION', hashlib.sha256(session['token'].encode()).hexdigest())
                self.assertNotIn('token', stored)
                restarted = AdminStorage(storage._path, table=storage._table)
                self.assertEqual(restarted.session(session['token'])['user']['username'], 'operator')
                self.assertEqual(len(restarted.list_users()), 2)
                self.assertEqual(restarted._get('USER', 'admin')['created_at'], admin['user']['created_at'])
                rows = restarted.login_logs(username='operator')['logs']
                self.assertEqual([row['success'] for row in rows], [True, False])
                self.assertEqual(rows[0]['ip'], '127.0.0.4')
                self.assertIsNotNone(restarted.list_users()[1]['last_login_at'])
                self.assertNotIn('initial123!', str(restarted.login_logs()))

    def test_disable_reset_logout_and_expiry_revoke_sessions(self):
        for backend in ('sqlite', 'dynamodb'):
            with self.subTest(backend=backend), storage_for(backend) as storage:
                storage.create_user('operator', 'initial123!')
                first = storage.login('operator', 'initial123!', '')
                second = storage.login('operator', 'initial123!', '')
                storage.update_user('operator', enabled=False)
                self.assertIsNone(storage.session(first['token']))
                self.assertIsNone(storage.session(second['token']))
                self.assertIsNone(storage.login('operator', 'initial123!', ''))
                storage.update_user('operator', enabled=True)
                self.assertIsNone(storage.session(first['token']))
                active = storage.login('operator', 'initial123!', '')
                old_version = storage._get('USER', 'operator')['auth_version']
                storage.update_user('operator', password='changed123!')
                self.assertIsNone(storage._update_user('operator', {'last_login_at': 'stale'}, expected_version=old_version))
                self.assertIsNone(storage.session(active['token']))
                self.assertIsNone(storage.login('operator', 'initial123!', ''))
                active = storage.login('operator', 'changed123!', '')
                storage.logout(active['token'])
                self.assertIsNone(storage.session(active['token']))
                active = storage.login('operator', 'changed123!', '')
                with patch('app.services.admin_service.time.time', return_value=active['expires_at'] + 1):
                    self.assertIsNone(storage.session(active['token']))
                self.assertIsNone(storage.session('forged'))
                with self.assertRaises(ValueError):
                    storage.update_user('admin', enabled=False)
                with self.assertRaises(ValueError):
                    storage.update_user('admin', password='changed123!')

    def test_log_filter_and_cursor_pagination(self):
        for backend in ('sqlite', 'dynamodb'):
            with self.subTest(backend=backend), storage_for(backend) as storage:
                storage.create_user('operator', 'initial123!')
                for username in ('admin', 'operator', 'missing', 'operator', 'admin', 'operator'):
                    storage.login(username, 'incorrect', '127.0.0.1')
                for username, count in [('', 6), ('operator', 3), ('absent', 0)]:
                    rows, after = [], None
                    while True:
                        page = storage.login_logs(limit=2, after=after, username=username)
                        self.assertLessEqual(len(page['logs']), 2)
                        rows.extend(page['logs'])
                        after = page['after']
                        if not after:
                            break
                    self.assertEqual(len(rows), count)
                    self.assertEqual(len({row['timestamp'] for row in rows}), count)
                    self.assertEqual([row['timestamp'] for row in rows], sorted([row['timestamp'] for row in rows], reverse=True))
                    if username:
                        self.assertTrue(all(row['username'] == username for row in rows))


class AdminHttpTests(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.storage = AdminStorage(Path(directory.name) / 'admin.sqlite3')
        self.app = FastAPI()
        self.app.include_router(router)
        self.app.dependency_overrides[get_admin_storage] = lambda: self.storage
        self.client = TestClient(self.app)
        self.addCleanup(self.client.close)

    def login(self, username='admin', password='root123!', client=None):
        return (client or self.client).post('/api/admin/login', json={'username': username, 'password': password})

    def test_login_refresh_cookie_flags_and_logout(self):
        self.assertEqual(self.client.get('/api/admin/me').status_code, 401)
        self.assertEqual(self.login(password='bad').status_code, 401)
        response = self.login()
        self.assertEqual(response.status_code, 200)
        for attribute in ('HttpOnly', 'SameSite=strict', 'Path=/api/admin', 'Max-Age=28800'):
            self.assertIn(attribute, response.headers['set-cookie'])
        self.assertEqual(response.headers['cache-control'], 'no-store')
        self.assertNotIn('token', response.json())
        token = self.client.cookies.get(COOKIE_NAME)
        reloaded = TestClient(self.app, cookies={COOKIE_NAME: token})
        self.addCleanup(reloaded.close)
        self.assertEqual(reloaded.get('/api/admin/me').status_code, 200)
        self.assertEqual(self.client.post('/api/admin/logout').status_code, 200)
        self.assertEqual(reloaded.get('/api/admin/me').status_code, 401)
        secure = TestClient(self.app, base_url='https://testserver')
        self.addCleanup(secure.close)
        self.assertIn('Secure', self.login(client=secure).headers['set-cookie'])
        self.assertEqual(secure.get('/api/admin/me').status_code, 200)

    def test_only_admin_can_manage_accounts_and_view_logs(self):
        self.assertEqual(self.client.get('/api/admin/users').status_code, 401)
        self.login()
        response = self.client.post('/api/admin/users', json={'username': 'operator', 'password': 'initial123!'})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.client.post('/api/admin/users', json={'username': 'operator', 'password': 'initial123!'}).status_code, 409)
        self.assertEqual(self.client.post('/api/admin/users', json={'username': 'promoted', 'password': 'initial123!', 'role': 'admin'}).status_code, 422)
        self.assertEqual(self.client.post('/api/admin/users', json={'username': 'bad name', 'password': 'initial123!'}).status_code, 400)
        self.assertEqual(self.client.patch('/api/admin/users/admin', json={'enabled': False}).status_code, 400)
        self.assertEqual(self.client.patch('/api/admin/users/missing', json={'enabled': False}).status_code, 404)
        self.assertEqual(self.client.patch('/api/admin/users/operator', json={}).status_code, 400)
        self.assertEqual(self.client.patch('/api/admin/users/operator', json={'role': 'admin'}).status_code, 422)
        self.assertEqual(len(self.client.get('/api/admin/users').json()['users']), 2)
        self.assertEqual(self.client.get('/api/admin/login-logs').status_code, 200)
        self.login('operator', 'initial123!')
        self.assertEqual(self.client.get('/api/admin/me').json()['user']['role'], 'user')
        for method, path, payload in [
            ('GET', '/api/admin/users', None), ('POST', '/api/admin/users', {'username': 'another', 'password': 'initial123!'}),
            ('PATCH', '/api/admin/users/operator', {'password': 'changed123!'}), ('GET', '/api/admin/login-logs', None),
        ]:
            self.assertEqual(self.client.request(method, path, json=payload).status_code, 403)

    def test_cross_origin_requests_are_rejected(self):
        for headers in ({'Origin': 'https://untrusted.example'}, {'Origin': 'null'}, {'Sec-Fetch-Site': 'cross-site'}, {'Sec-Fetch-Site': 'same-site'}):
            response = self.client.post('/api/admin/login', json={'username': 'admin', 'password': 'root123!'}, headers=headers)
            self.assertEqual(response.status_code, 403)
        self.assertEqual(self.client.post('/api/admin/login', json={'username': 'admin', 'password': 'root123!'}, headers={'Host': 'localhost:5173', 'Origin': 'https://localhost:5173', 'Sec-Fetch-Site': 'same-origin'}).status_code, 200)

    def test_public_origin_survives_proxy_host_rewrite(self):
        public_url = 'https://robotics-instruction-manual.ff.com'
        proxy_headers = {
            'Host': 'eai-robot-alb-477631451.us-east-1.elb.amazonaws.com',
            'Origin': public_url,
            'Sec-Fetch-Site': 'same-origin',
        }
        with patch('app.admin.PUBLIC_BASE_URL', public_url):
            response = self.client.post('/api/admin/login', json={'username': 'admin', 'password': 'root123!'}, headers=proxy_headers)
            self.assertEqual(response.status_code, 200)
            self.assertIn('Secure', response.headers['set-cookie'])
            # Use HTTPS so the test client sends the Secure cookie on subsequent calls.
            secure = TestClient(self.app, base_url=public_url, cookies={COOKIE_NAME: self.client.cookies.get(COOKIE_NAME)})
            self.addCleanup(secure.close)
            self.assertEqual(secure.get('/api/admin/me', headers=proxy_headers).status_code, 200)
            self.assertEqual(secure.get('/api/admin/users', headers=proxy_headers).status_code, 200)
            self.assertEqual(secure.post('/api/admin/logout', headers=proxy_headers).status_code, 200)
            for origin in [public_url + '.untrusted.example', public_url + ':8443', public_url.replace('https:', 'http:'), 'null', 'https://[invalid']:
                with self.subTest(origin=origin):
                    response = self.client.post('/api/admin/login', json={'username': 'admin', 'password': 'root123!'}, headers={**proxy_headers, 'Origin': origin})
                    self.assertEqual(response.status_code, 403)
            for site in ['cross-site', 'same-site']:
                self.assertEqual(self.client.post('/api/admin/login', json={'username': 'admin', 'password': 'root123!'}, headers={**proxy_headers, 'Sec-Fetch-Site': site}).status_code, 403)
        with patch('app.admin.PUBLIC_BASE_URL', ''):
            response = self.client.post('/api/admin/login', json={'username': 'admin', 'password': 'root123!'}, headers={**proxy_headers, 'X-Forwarded-Host': 'robotics-instruction-manual.ff.com'})
            self.assertEqual(response.status_code, 403)

    def test_existing_business_api_remains_public(self):
        with patch('app.core.logging_config.setup_logging'), \
             patch('app.core.openai_http.configure_agents_default_openai_client'), \
             patch('app.core.openai_http.create_async_openai_client'):
            main = importlib.import_module('app.main')
        client = TestClient(main.app)
        self.addCleanup(client.close)
        with patch.object(main.recommendation_storage, 'list_recommendations', return_value=[]), \
             patch.object(main.lead_storage, 'list_leads', return_value=[]):
            self.assertEqual(client.get('/api/get-recommendations').status_code, 200)
            self.assertEqual(client.get('/api/get-leads').status_code, 200)


if __name__ == '__main__':
    unittest.main()
