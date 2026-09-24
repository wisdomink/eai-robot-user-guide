"""DynamoDB integration tests against Moto; never calls a real AWS account."""
import asyncio
import base64
import os
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import boto3
from botocore.exceptions import ClientError
from chatkit.store import NotFoundError
from chatkit.types import ThreadMetadata, UserMessageItem, AssistantMessageItem, AssistantMessageContent
from app.services.chat_store import DynamoDBStore
from moto import mock_aws


class ChatStoreTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.mock = mock_aws()
        self.mock.start()
        self.addCleanup(self.mock.stop)
        self.table = boto3.resource('dynamodb', region_name='us-east-1').create_table(
            TableName='test-chat', BillingMode='PAY_PER_REQUEST',
            AttributeDefinitions=[{'AttributeName': k, 'AttributeType': 'S'} for k in ['pk', 'sk', 'gpk', 'gsk']],
            KeySchema=[{'AttributeName': 'pk', 'KeyType': 'HASH'}, {'AttributeName': 'sk', 'KeyType': 'RANGE'}],
            GlobalSecondaryIndexes=[{'IndexName': 'threads-by-created', 'KeySchema': [
                {'AttributeName': 'gpk', 'KeyType': 'HASH'}, {'AttributeName': 'gsk', 'KeyType': 'RANGE'}],
                'Projection': {'ProjectionType': 'ALL'}}],
        )
        self.store = DynamoDBStore('test-chat', table=self.table)
        self.now = datetime.now(timezone.utc)

    def user(self, i=0, text='你好'):
        return UserMessageItem(id=f'u{i}', thread_id='t', created_at=self.now + timedelta(seconds=i),
                               content=[{'type': 'input_text', 'text': text}], inference_options={})

    async def seed(self):
        await self.store.save_thread(ThreadMetadata(id='t', title='Chat', created_at=self.now), {})

    async def test_restart_roundtrip_and_continuation(self):
        await self.seed()
        user = self.user()
        assistant = AssistantMessageItem(id='a', thread_id='t', created_at=self.now + timedelta(seconds=1),
                                         content=[AssistantMessageContent(text='你好！')])
        await self.store.add_thread_item('t', user, {})
        await self.store.add_thread_item('t', assistant, {})
        trace = {'timestamp': self.now.isoformat(), 'score': .91, 'nodes': [{'agent': 'Output'}]}
        await self.store.add_trace('t', trace)
        await self.store.set_language('t', 'zh')
        # A fresh store has no in-process cache and uses the same persisted table.
        fresh = DynamoDBStore('test-chat', 'us-east-1')
        self.assertEqual((await fresh.load_thread('t', {})).title, 'Chat')
        page = await fresh.load_thread_items('t', None, 10, 'asc', {})
        self.assertEqual(page.data, [user, assistant])
        self.assertEqual(await fresh.load_traces('t'), [trace])
        self.assertEqual(await fresh.get_language('t'), 'zh')
        self.assertEqual(await fresh.history_summary('t'), {'item_count': 2, 'first_message': '你好', 'agents': ['Output']})
        await fresh.add_thread_item('t', self.user(2), {})
        self.assertEqual((await self.store.history_summary('t'))['item_count'], 3)

    async def test_idempotency_update_pagination_and_delete(self):
        await self.seed()
        for i in range(5):
            await self.store.add_thread_item('t', self.user(i), {})
        await self.store.add_thread_item('t', self.user(0), {})
        await self.store.save_item('t', self.user(0, 'updated'), {})
        self.assertEqual((await self.store.load_item('t', 'u0', {})).content[0].text, 'updated')
        ids = []
        after = None
        while True:
            page = await self.store.load_thread_items('t', after, 2, 'asc', {})
            ids.extend(i.id for i in page.data)
            if not page.has_more:
                break
            after = page.after
        self.assertEqual(ids, ['u0', 'u1', 'u2', 'u3', 'u4'])
        page = await self.store.load_thread_items('t', None, 2, 'desc', {})
        self.assertEqual([i.id for i in page.data], ['u4', 'u3'])
        await self.store.delete_thread_item('t', 'u1', {})
        with self.assertRaises(NotFoundError):
            await self.store.load_item('t', 'u1', {})
        await self.store.delete_thread('t', {})
        with self.assertRaises(NotFoundError):
            await self.store.load_thread('t', {})
        self.assertEqual(self.table.scan()['Items'], [])

    async def test_thread_index_pagination_and_isolation(self):
        for i in range(4):
            await self.store.save_thread(ThreadMetadata(id=str(i), created_at=self.now + timedelta(seconds=i)), {})
        first = await self.store.load_threads(2, None, 'desc', {})
        second = await self.store.load_threads(2, first.after, 'desc', {})
        self.assertEqual([t.id for t in first.data + second.data], ['3', '2', '1', '0'])
        self.assertFalse(second.has_more)
        self.assertEqual((await self.store.load_thread_items('other', None, 2, 'asc', {})).data, [])

    async def test_large_payload_chunks_and_database_page_boundary(self):
        await self.seed()
        # Incompressible enough to exceed the 400 KB DynamoDB item limit.
        large = base64.b64encode(os.urandom(500_000)).decode()
        await self.store.add_thread_item('t', self.user(0, large), {})
        fresh = DynamoDBStore('test-chat', 'us-east-1')
        self.assertEqual((await fresh.load_item('t', 'u0', {})).content[0].text, large)
        # More than DynamoDB's 1 MB response limit must still fill a logical page.
        for i in range(1, 7):
            await self.store.add_thread_item('t', self.user(i, base64.b64encode(os.urandom(210_000)).decode()), {})
        page = await fresh.load_thread_items('t', None, 6, 'asc', {})
        self.assertEqual(len(page.data), 6)
        self.assertTrue(page.has_more)
        self.assertEqual(len((await fresh.load_thread_items('t', page.after, 6, 'asc', {})).data), 1)
        await fresh.delete_thread('t', {})
        self.assertEqual(self.table.scan()['Items'], [])

    async def test_failure_does_not_silently_succeed_or_replace_old_payload(self):
        await self.seed()
        await self.store.save_item('t', self.user(0, 'old'), {})
        real_put = self.table.put_item
        def fail_chunk(**kwargs):
            if kwargs['Item']['sk'].startswith('CHUNK#'):
                raise ClientError({'Error': {'Code': 'ProvisionedThroughputExceededException', 'Message': 'test'}}, 'PutItem')
            return real_put(**kwargs)
        with patch.object(self.table, 'put_item', side_effect=fail_chunk), self.assertLogs('front', level='ERROR'):
            with self.assertRaises(ClientError):
                await self.store.save_item('t', self.user(0, base64.b64encode(os.urandom(500_000)).decode()), {})
        self.assertEqual((await self.store.load_item('t', 'u0', {})).content[0].text, 'old')

    async def test_history_http_after_restart(self):
        from fastapi.testclient import TestClient
        from app import main
        await self.seed()
        for i in range(3):
            await self.store.add_thread_item('t', self.user(i), {})
        with patch.object(main.chatkit_server, 'store', DynamoDBStore('test-chat', 'us-east-1')):
            client = TestClient(main.app)
            response = await asyncio.to_thread(client.get, '/api/chat-history')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['threads'][0]['item_count'], 3)
            response = await asyncio.to_thread(client.get, '/api/chat-history/t?limit=2')
            body = response.json()
            self.assertTrue(body['has_more'])
            response = await asyncio.to_thread(client.get, '/api/chat-history/t', params={'after': body['after']})
            self.assertEqual(len(response.json()['items']), 1)
            response = await asyncio.to_thread(client.get, '/api/chat-history/missing')
            self.assertEqual(response.status_code, 404)
            response = await asyncio.to_thread(client.get, '/api/chat-history?order=bad')
            self.assertEqual(response.status_code, 422)


if __name__ == '__main__':
    unittest.main()
