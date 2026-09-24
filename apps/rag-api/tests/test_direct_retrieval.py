import asyncio
import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock, Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.services import chatkit_handler as h
from app.services.retrieval_service import Evidence, RetrievalService
from chatkit.types import ThreadItemUpdatedEvent, AssistantMessageContentPartTextDelta


def evidence(text='The payload is 30 kg.', filename='spec.md', attrs=None, file_id='file_1'):
    return Evidence(file_id, filename, text, .9, attrs or {}, 'vs_max')


class RetrievalTests(unittest.IsolatedAsyncioTestCase):
    async def test_original_text_dedup_sort_and_product_isolation(self):
        def hit(file_id, text, score, attrs=None):
            return NS(file_id=file_id, filename='spec.md', attributes=attrs, score=score,
                      content=[NS(type='text', text=text)])
        search = AsyncMock(return_value=NS(data=[
            hit('file_low', 'Exact text with units: 30 kg.', .6),
            hit('file_high', 'First source.', .9, {'product_id': 'aegis-max'}),
            hit('file_high', 'First source.', .8),
            hit('file_wrong', 'Wrong product.', .99, {'product_id': 'navi'}),
            hit('file_empty', ' ', .7),
        ]))
        service = RetrievalService(NS(vector_stores=NS(search=search)))
        hits = await service.search(' Max payload ', vector_store_id='vs_max', product_key='aegis-max')
        self.assertEqual([x.file_id for x in hits], ['file_high', 'file_low'])
        self.assertEqual(hits[1].text, 'Exact text with units: 30 kg.')
        search.assert_awaited_once_with(vector_store_id='vs_max', query='Max payload', max_num_results=6, rewrite_query=False)
        self.assertEqual(await service.search(' ', vector_store_id='vs_max'), [])
        self.assertEqual(search.await_count, 1)

    async def test_pass_uses_focused_query_and_bounded_raw_evidence(self):
        service = Mock(search=AsyncMock(return_value=[evidence('x' * 1200), evidence('second', file_id='file_2')]))
        plan = h.PlanOutput(input_lang='en', query_text='compare Max and Mega D')
        loop = h.LoopPass('product', ['vs_max'], 'Max', 'aegis-max', 'Max payload')
        with patch.object(h, 'RETRIEVAL_MAX_CHARS_PER_PASS', 1000):
            result = await h.retrieve_loop_pass(service, plan, loop, 1)
        self.assertEqual(service.search.await_args.args, ('Max payload',))
        docs = json.loads(result.text)
        self.assertEqual(len(docs), 1)
        self.assertEqual(len(docs[0]['text']), 1000)
        self.assertTrue(docs[0]['truncated'])
        self.assertEqual(docs[0]['evidence_id'], 'E2_1')
        self.assertEqual(result.sources[0].file_id, 'file_1')

    async def test_empty_missing_and_fallback_are_distinct(self):
        service = Mock(search=AsyncMock(return_value=[]))
        plan = h.PlanOutput(input_lang='en', query_text='charge')
        result = await h.retrieve_loop_pass(service, plan, h.LoopPass('product', ['vs_max'], 'Max', 'aegis-max'), 0)
        self.assertEqual(result.status, 'empty')
        with self.assertRaises(ValueError):
            await h.retrieve_loop_pass(service, plan, h.LoopPass('product', [], 'Max', 'aegis-max'), 0)
        result = await h.retrieve_loop_pass(None, plan, h.LoopPass('fallback', [], 'fallback'), 0)
        self.assertEqual(result.status, 'fallback')

    def test_product_sources_do_not_cross_filename_collisions(self):
        with patch.object(h, 'FILE_SLUG_MAP', {
            'max/spec.md': {'slug': '/aegis-max/spec', 'title': 'Max'},
            'mega/spec.md': {'slug': '/aegis-mega-d/spec', 'title': 'Mega'},
        }):
            source = h._source_for_evidence(evidence(), 'product', 'aegis-mega-d', 'E1_1')
        self.assertEqual(source.slug, '/aegis-mega-d/spec')
        self.assertEqual(source.title, 'Mega')

    def test_news_sources_use_hit_metadata_and_reject_non_web_urls(self):
        source = h._source_for_evidence(evidence('title: Launch\nsource: https://example.com/news\npublished: 2026-09-22\n\nAnnounced.'), 'news', None, 'E1_1')
        self.assertEqual(source.url, 'https://example.com/news')
        self.assertEqual(source.published_at, '2026-09-22')
        source = h._source_for_evidence(evidence(attrs={'url': 'javascript:alert(1)'}), 'news', None, 'E1_1')
        self.assertIsNone(source.url)

    def test_plan_deduplicates_and_preserves_both_product_queries(self):
        plan = [h.LoopPlanItem(agent='product', product_key=p, query_text=p + ' payload')
                for p in ['aegis-max', 'aegis-mega-d', 'aegis-max']]
        result = h._build_loop_passes_from_plan(plan)
        self.assertEqual([r.query_text for r in result], ['aegis-max payload', 'aegis-mega-d payload'])

    def test_mixed_fallback_keeps_valid_retrieval_passes(self):
        plan = [
            h.LoopPlanItem(agent='product', product_key='aegis-max', query_text='Max payload'),
            h.LoopPlanItem(agent='fallback'),
        ]
        with patch.dict(h._SUPPORT_AGENT_CONFIGS['aegis-max'], vector_store_id='vs_max'):
            result = h._build_loop_passes_from_plan(plan)
        self.assertEqual([(item.domain, item.product_key) for item in result], [('product', 'aegis-max')])

    def test_domain_agent_uses_focused_pass_query(self):
        plan = h.PlanOutput(input_lang='en', query_text='compare Max and Mega D')
        loop = h.LoopPass(
            'product', ['vs_max'], 'Max', 'aegis-max', 'Aegis Max payload only'
        )
        agent = h._build_loop_domain_agent(plan, loop)
        self.assertIn('Aegis Max payload only', agent.instructions)
        self.assertNotIn('compare Max and Mega D', agent.instructions)


class CitationTests(unittest.TestCase):
    def setUp(self):
        self.sources = (
            h.RetrievedSource('product', 'spec.md', 'Max Specs', slug='/aegis-max/spec', evidence_id='E1_1'),
            h.RetrievedSource('news', 'news.md', 'Launch', url='https://example.com/news', evidence_id='E2_1'),
            h.RetrievedSource('price', 'price.md', 'Price', evidence_id='E3_1'),
        )

    def test_split_markers_unicode_and_unknown_citations(self):
        renderer = h._FinalSourceAppender(self.sources, 'cn')
        raw = '载荷 30 kg。[[E1_1]] News.[[E2_1]] Price.[[E3_1]] Unknown.[[E999_1]]'
        streamed = ''
        for char in raw:
            event = ThreadItemUpdatedEvent(item_id='msg', update=AssistantMessageContentPartTextDelta(content_index=0, delta=char))
            streamed += renderer.process(event).update.delta
        text, annotations = renderer.render(raw)
        self.assertEqual(streamed, text)
        self.assertNotIn('[[', text)
        self.assertEqual(len(annotations), 3)
        self.assertEqual(annotations[0].index, len('载荷 30 kg。'))
        self.assertEqual(annotations[0].source.type, 'entity')
        self.assertEqual(annotations[1].source.type, 'url')
        self.assertEqual(annotations[2].source.type, 'file')

    def test_only_used_sources_and_final_item_annotations_are_retained(self):
        renderer = h._FinalSourceAppender(self.sources, 'en')
        item = h.AssistantMessageItem(id='msg', thread_id='thread', created_at=datetime.now(),
                                      content=[h.AssistantMessageContent(text='30 kg.[[E1_1]]')])
        event = h.ThreadItemDoneEvent(item=item)
        renderer.process(event)
        renderer.process(event)
        self.assertEqual(item.content[0].text, '30 kg.')
        self.assertEqual(len(item.content[0].annotations), 1)
        self.assertEqual(renderer.render('No facts.')[1], [])

    def test_two_chunks_from_same_file_keep_distinct_evidence_ids(self):
        first = self.sources[0]
        second = h.replace(first, evidence_id='E1_2')
        self.assertEqual(len(h._merge_source_lists((first, second))), 2)


class PipelineTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.service = Mock(search=AsyncMock(return_value=[evidence()]))
        self.server = h.FFRobotChatKitServer(
            h.InMemoryStore(), lead_storage=Mock(), recommendation_storage=Mock(),
            homepage_prompts_storage=Mock(), retrieval_service=self.service,
        )
        self.server.reco_engine = Mock(evaluate_post_answer=Mock(return_value=None))
        self.server.reco_engine.build_triage_rules_prompt.return_value = ''
        self.server.reco_engine.build_purchase_intent_prompt.return_value = ''
        self.plan = h.PlanOutput(input_lang='cn', query_text='Max payload', loop_plan=[
            h.LoopPlanItem(agent='product', product_key='aegis-max', query_text='Max payload'),
        ])
        self.calls = []
        self.output_agent = None

    async def run_model(self, agent, *args, **kwargs):
        self.calls.append(agent.name)
        if 'Plan' in agent.name:
            self.assertIn('aegis-max', agent.instructions)
            return NS(final_output=self.plan)
        if 'Post-Decision' in agent.name:
            return NS(final_output=h.PostDecisionOutput())
        return NS(final_output='Legacy summary.', new_items=[])

    def run_output(self, agent, *args, **kwargs):
        self.output_agent = agent
        return Mock()

    async def stream(self, *args, **kwargs):
        yield h.ThreadItemDoneEvent(item=h.AssistantMessageItem(
            id='answer', thread_id='thread', created_at=datetime.now(timezone.utc),
            content=[h.AssistantMessageContent(text='载荷是 30 kg。[[E1_1]]')],
        ))

    async def respond(self, mode='direct'):
        now = datetime.now(timezone.utc)
        thread = h.ThreadMetadata(id='thread', created_at=now)
        message = h.UserMessageItem(id='user', thread_id='thread', created_at=now,
                                    content=[{'type': 'input_text', 'text': '载荷是多少？'}], inference_options={})
        with patch.object(h, 'CHAT_RETRIEVAL_MODE', mode), \
             patch.dict(h._SUPPORT_AGENT_CONFIGS['aegis-max'], vector_store_id='vs_max'), \
             patch.dict(h._SUPPORT_AGENT_CONFIGS['aegis-mega-d'], vector_store_id='vs_mega'), \
             patch.object(h.Runner, 'run', side_effect=self.run_model), \
             patch.object(h.Runner, 'run_streamed', side_effect=self.run_output), \
             patch.object(h, 'stream_agent_response', self.stream):
            return [e async for e in self.server.respond(thread, message, {'page_url': 'https://example.com/aegis-max/spec'})]

    async def test_direct_path_has_no_domain_model_and_preserves_post_decision(self):
        events = await self.respond()
        self.assertEqual(self.calls, ['FF Robot Plan Agent', 'FF Post-Decision Agent'])
        self.service.search.assert_awaited_once()
        self.assertIn('The payload is 30 kg.', self.output_agent.instructions)
        final = [e.item for e in events if e.type == 'thread.item.done'][0]
        self.assertEqual(final.content[0].text, '载荷是 30 kg。')
        self.assertEqual(len(final.content[0].annotations), 1)
        trace = self.server.store.agent_traces['thread'][-1]
        self.assertEqual(trace['retrieval_mode'], 'direct')
        self.assertEqual(trace['nodes'][1]['model'], None)
        self.assertEqual(trace['nodes'][1]['evidence'][0]['file_id'], 'file_1')

    async def test_clarification_stops_before_retrieval_output_and_recommendation(self):
        self.plan.clarification_question = '请问是哪款产品？'
        self.plan.loop_plan = []
        events = await self.respond()
        self.assertEqual(self.calls, ['FF Robot Plan Agent'])
        self.service.search.assert_not_called()
        self.assertIsNone(self.output_agent)
        self.assertEqual(events[-1].item.content[0].text, '请问是哪款产品？')

    async def test_parallel_partial_timeout_keeps_the_other_product_evidence(self):
        self.plan.loop_plan.append(h.LoopPlanItem(agent='product', product_key='aegis-mega-d', query_text='Mega payload'))
        active = 0
        max_active = 0
        async def search(query, **kwargs):
            nonlocal active, max_active
            active += 1
            max_active = max(max_active, active)
            try:
                await asyncio.sleep(.1 if kwargs['vector_store_id'] == 'vs_mega' else .001)
                return [evidence()]
            finally:
                active -= 1
        self.service.search.side_effect = search
        with patch.object(h, 'LOOP_PASS_TIMEOUT_SECONDS', .02):
            await self.respond()
        self.assertEqual(max_active, 2)
        self.assertEqual(active, 0)
        self.assertIn('The payload is 30 kg.', self.output_agent.instructions)
        self.assertIn('检索暂时失败', self.output_agent.instructions)
        statuses = [n['status'] for n in self.server.store.agent_traces['thread'][-1]['nodes'] if 'status' in n]
        self.assertEqual(statuses, ['ok', 'unavailable'])

    async def test_agent_mode_remains_available_for_rollback(self):
        await self.respond('agent')
        self.service.search.assert_not_called()
        self.assertTrue(any('(product)' in name for name in self.calls))
        self.assertIn('Legacy summary.', self.output_agent.instructions)

    async def test_recommendation_failure_does_not_fail_completed_answer(self):
        original = self.run_model
        async def run_model(agent, *args, **kwargs):
            if 'Post-Decision' in agent.name:
                raise RuntimeError('recommendation unavailable')
            return await original(agent, *args, **kwargs)
        self.run_model = run_model
        with self.assertLogs(h.logger, level='ERROR'):
            events = await self.respond()
        self.assertTrue(any(e.type == 'thread.item.done' for e in events))
        self.assertEqual(self.server.store.agent_traces['thread'][-1]['nodes'][-1]['output']['purchase_intent'], 'no')


class SearchEndpointTests(unittest.IsolatedAsyncioTestCase):
    async def test_search_uses_shared_retrieval_and_preserves_response_contract(self):
        import importlib
        with patch('app.core.logging_config.setup_logging'), \
             patch('app.core.openai_http.configure_agents_default_openai_client'), \
             patch('app.core.openai_http.create_async_openai_client'):
            main = importlib.import_module('app.main')
        hit = evidence('## Charging\nConnect the supplied charger.')
        service = Mock(search=AsyncMock(return_value=[hit]))
        with patch.object(main, '_retrieval', service), \
             patch.object(main, 'OPENAI_VECTOR_STORE_ROBOT_ALL_ID', 'vs_all'), \
             patch.object(main, 'OPENAI_VECTOR_STORE_AEGIS_MAX_ID', 'vs_max'), \
             patch.object(main, 'OPENAI_VECTOR_STORE_MASTER_MINI_ID', 'vs_master_mini'), \
             patch.object(main, '_FILE_INFO_MAP', {'spec.md': {'slug': '/aegis-max/spec', 'title': 'Specs', 'sectionId': 'manual'}}):
            response = await main.search_endpoint(q='charge', limit=10)
        self.assertEqual(service.search.await_count, 3)
        self.assertEqual(
            [call.kwargs['vector_store_id'] for call in service.search.await_args_list],
            ['vs_all', 'vs_max', 'vs_master_mini'],
        )
        self.assertTrue(all(call.kwargs['rewrite_query'] for call in service.search.await_args_list))
        self.assertEqual(len(response['results']), 1)
        self.assertEqual(response['results'][0]['pageSlug'], '/aegis-max/spec')
        self.assertEqual(response['results'][0]['headingAnchor'], 'charging')


if __name__ == '__main__':
    unittest.main()
