import importlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock, Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import sync_manuals_rag as sync
from app.core import config
from app.services import chatkit_handler as h
from app.services.manuals_index import shared_snapshot, release_filter, matches_filter, validate_manifest
from app.services.retrieval_service import RetrievalService, Evidence


class ManifestTests(unittest.TestCase):
    def test_validation_and_pairwise_filters(self):
        releases = {'master': 'r1', 'navi': 'r2'}
        manifest = dict(schema_version=1, vector_store_id='vs_shared', releases=releases)
        self.assertEqual(validate_manifest(manifest, 'vs_shared', releases), releases)
        for bad in [None, [], {}, dict(manifest, releases={}), dict(manifest, releases={'master': 1})]:
            with self.assertRaises(ValueError):
                validate_manifest(bad, 'vs_shared')
        with self.assertRaises(ValueError):
            validate_manifest(manifest, 'other')
        with self.assertRaises(ValueError):
            validate_manifest(manifest, 'vs_shared', ['ff91'])
        filters = release_filter(releases)
        self.assertTrue(matches_filter(dict(product_id='master', release_id='r1', managed_by=sync.MANAGER), filters))
        for attrs in [{}, dict(product_id='master', release_id='r2', managed_by=sync.MANAGER), dict(product_id='navi', release_id='r2')]:
            self.assertFalse(matches_filter(attrs, filters))

    def test_snapshot_rereads_atomic_manifest_and_requires_full_coverage(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest, sidebar = Path(tmp) / 'releases.json', Path(tmp) / 'sidebar.json'
            sidebar.write_text('{"master": {}, "navi": {}}')
            data = dict(schema_version=1, vector_store_id='vs_shared', releases={'master': 'r1', 'navi': 'r2'})
            with patch.multiple(config, MANUALS_INDEX_MODE='shared', OPENAI_VECTOR_STORE_MANUALS_ID='vs_shared', MANUALS_RELEASE_MANIFEST=manifest, SIDEBAR_PATH=sidebar):
                sync.atomic_save(manifest, data)
                before = shared_snapshot()
                data['releases']['master'] = 'r3'
                sync.atomic_save(manifest, data)
                self.assertEqual(before[1]['master'], 'r1')
                self.assertEqual(shared_snapshot()[1]['master'], 'r3')
                del data['releases']['navi']
                sync.atomic_save(manifest, data)
                with self.assertRaises(ValueError):
                    shared_snapshot()

    def test_comparison_uses_one_snapshot_and_filters_agent_too(self):
        plan = [h.LoopPlanItem(agent='product', product_key='master'), h.LoopPlanItem(agent='product', product_key='navi'), h.LoopPlanItem(agent='price')]
        with patch.object(h, 'shared_snapshot', return_value=('vs_shared', {'master': 'r1', 'navi': 'r2'})) as snapshot:
            passes = h._build_loop_passes_from_plan(plan)
        snapshot.assert_called_once()
        self.assertEqual(passes[0].vector_store_ids, ['vs_shared'])
        self.assertEqual(passes[0].filters, release_filter({'master': 'r1'}))
        self.assertEqual(passes[1].filters, release_filter({'navi': 'r2'}))
        self.assertIsNone(passes[2].filters)
        agent = h._build_loop_domain_agent(h.PlanOutput(input_lang='en', query_text='compare'), passes[0])
        self.assertEqual(agent.tools[0].filters, passes[0].filters)
        with patch.object(h, 'shared_snapshot', side_effect=ValueError('bad manifest')), self.assertLogs(h.logger, level='ERROR'):
            passes = h._build_loop_passes_from_plan(plan)
        self.assertEqual(passes[0].vector_store_ids, [])
        self.assertEqual(passes[1].vector_store_ids, [])
        self.assertEqual(passes[2].domain, 'price')


class SyncTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / 'pages').mkdir()
        (self.root / 'pages/start.md').write_text('## Start\nPress the power button.')
        sidebar = {p: {'title': p, 'sections': [{'pages': [{'file': 'start.md', 'slug': f'/{p}/start', 'title': 'Start'}]}]} for p in ['master', 'navi']}
        (self.root / 'sidebar.json').write_text(json.dumps(sidebar))
        self.builds = {p: sync.build_release(self.root, p) for p in sidebar}
        self.remote = []
        def attach(**kw):
            item = NS(id=kw['file_id'], attributes=kw['attributes'], status='completed')
            self.remote.append(item)
            return item
        files = Mock()
        files.list.side_effect = lambda **kw: list(self.remote)
        files.create.side_effect = attach
        files.retrieve.side_effect = lambda file_id, **kw: next(f for f in self.remote if f.id == file_id)
        self.client = Mock()
        self.client.vector_stores.files = files
        self.client.files.create.side_effect = lambda **kw: NS(id=f'file_{len(self.remote)}')
        self.client.vector_stores.search.side_effect = lambda **kw: NS(data=[f for f in self.remote if matches_filter(f.attributes, kw['filters'])][:1])
        self.manifest = self.root / 'active.json'
        self.report = {'uploads': []}

    def publish(self, builds=None, activate=True):
        return sync.publish(self.client, 'vs_shared', builds or self.builds, self.manifest, self.report, lambda: None, activate)

    def test_all_then_single_product_update_and_idempotency(self):
        first = self.publish()
        self.publish()
        self.assertEqual(self.client.files.create.call_count, 2)
        (self.root / 'pages/start.md').write_text('## Start\nUpdated procedure.')
        new = self.publish({'master': sync.build_release(self.root, 'master')})
        self.assertNotEqual(new['releases']['master'], first['releases']['master'])
        self.assertEqual(new['releases']['navi'], first['releases']['navi'])
        self.assertEqual(json.loads(self.manifest.with_suffix('.previous.json').read_text()), first)
        self.assertEqual(len(self.remote), 3)
        self.client.files.delete.assert_not_called()
        self.client.vector_stores.files.delete.assert_not_called()

    def test_staging_and_failure_never_activate(self):
        first = self.publish()
        (self.root / 'pages/start.md').write_text('New revision')
        builds = {'master': sync.build_release(self.root, 'master')}
        self.publish(builds, activate=False)
        self.assertEqual(json.loads(self.manifest.read_text()), first)
        self.client.vector_stores.search.side_effect = RuntimeError('search unavailable')
        with self.assertRaises(RuntimeError):
            self.publish(builds)
        self.assertEqual(json.loads(self.manifest.read_text()), first)
        self.assertFalse(self.manifest.with_suffix('.previous.json').exists())

    def test_failed_upload_preserves_manifest_and_journals_id(self):
        first = self.publish()
        (self.root / 'pages/start.md').write_text('New revision')
        self.client.vector_stores.files.create.side_effect = RuntimeError('attach failed')
        with self.assertRaises(RuntimeError):
            self.publish({'master': sync.build_release(self.root, 'master')})
        self.assertEqual(json.loads(self.manifest.read_text()), first)
        self.assertEqual(len(self.report['uploads']), 3)

    def test_conflicting_duplicate_or_failed_release_rejected(self):
        self.publish()
        release, pages = self.builds['master']
        self.remote.append(self.remote[0])
        with self.assertRaises(ValueError):
            sync.inspect_release(self.client, 'vs_shared', 'master', release, pages)
        self.remote.pop()
        self.remote[0].status = 'failed'
        with self.assertRaises(ValueError):
            sync.inspect_release(self.client, 'vs_shared', 'master', release, pages)

    def test_identity_covers_language_and_product_and_required_metadata(self):
        release, pages = self.builds['master']
        self.assertNotEqual(release, self.builds['navi'][0])
        self.assertNotEqual(release, sync.build_release(self.root, 'master', 'zh')[0])
        self.assertNotEqual(pages['start.md']['name'], self.builds['navi'][1]['start.md']['name'])
        self.assertEqual(set(pages['start.md']['attributes']), {'managed_by', 'product_id', 'source_path', 'page_slug', 'language', 'content_hash', 'release_id'})


class SharedSearchTests(unittest.IsolatedAsyncioTestCase):
    async def test_remote_filter_and_local_defense(self):
        attrs = dict(product_id='master', release_id='r1', managed_by=sync.MANAGER)
        hits = [NS(file_id=str(i), filename='unique.md', attributes=a, score=.9, content=[NS(type='text', text='evidence')]) for i, a in enumerate([attrs, {}, dict(attrs, release_id='old')])]
        search = AsyncMock(return_value=NS(data=hits))
        service = RetrievalService(NS(vector_stores=NS(search=search)))
        filters = release_filter({'master': 'r1'})
        result = await service.search('charge', vector_store_id='vs_shared', filters=filters)
        self.assertEqual([h.file_id for h in result], ['0'])
        self.assertEqual(search.await_args.kwargs['filters'], filters)

    async def test_site_search_uses_slug_and_active_versions_only(self):
        with patch('app.core.logging_config.setup_logging'), patch('app.core.openai_http.configure_agents_default_openai_client'), patch('app.core.openai_http.create_async_openai_client'):
            main = importlib.import_module('app.main')
        hit = Evidence('f1', 'hashed-name.md', '## Charging\nPlug in.', .9, {'page_slug': '/master/start'}, 'vs_shared')
        service = Mock(search=AsyncMock(return_value=[hit]))
        with patch.object(main, '_retrieval', service), patch.object(main, 'shared_snapshot', return_value=('vs_shared', {'master': 'r1', 'navi': 'r2'})), patch.object(main, '_FILE_INFO_MAP', {'/master/start': {'slug': '/master/start', 'title': 'Start', 'sectionId': 'start'}}):
            response = await main.search_endpoint(q='charge', limit=10)
        service.search.assert_awaited_once()
        self.assertEqual(service.search.await_args.kwargs['vector_store_id'], 'vs_shared')
        self.assertEqual(service.search.await_args.kwargs['filters'], release_filter({'master': 'r1', 'navi': 'r2'}))
        self.assertEqual(response['results'][0]['pageSlug'], '/master/start')
        service.search.reset_mock()
        with patch.object(main, '_retrieval', service), patch.object(main, 'shared_snapshot', side_effect=ValueError('invalid')), self.assertLogs(main.logger, level='ERROR'):
            response = await main.search_endpoint(q='charge', limit=10)
        self.assertEqual(response['results'], [])
        self.assertIn('error', response)
        service.search.assert_not_called()


if __name__ == '__main__':
    unittest.main()
