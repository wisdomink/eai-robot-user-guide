"""Preset clicks must be scoped, current, and separate from ordinary messages."""
import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.services import chatkit_handler as handler
from app.services.fast_answer_service import FastAnswerService
from app.services.homepage_prompts_service import HomepagePromptsStorage


class PresetAnswerTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.config = self.root / 'prompts.json'
        self.faq = self.root / 'faq_en.md'
        self.faq.write_text('## Max\n\n**Path:** `/max`\n\n### 1.1 How to start?\n\nLegacy Max answer.\n')
        self.storage = HomepagePromptsStorage(self.config)
        self.write_config()
        self.answers = FastAnswerService(
            preset_faq_paths=[self.faq], memory_path=self.root / 'memory.jsonl', memory_enabled=False,
        )

    def write_config(self, *, answer='Prepared Max answer.', enabled=True):
        self.config.write_text(json.dumps({
            'global_prompts': [{'id': 'same', 'type': 'message', 'prompt': 'How to start?',
                                'reply_text': 'Global answer.', 'enabled': True}],
            'pages': [
                {'id': key, 'pattern': f'https://example.com/{key}', 'prompts': [
                    {'id': 'same', 'type': 'message', 'label': 'Start', 'prompt': 'How to start?',
                     'reply_text': answer if key == 'max' else 'Mega answer.', 'enabled': enabled},
                ]} for key in ('max', 'mega')
            ],
        }))

    def resolve(self, scope='page:max', url='https://example.com/max', prompt_id='same'):
        return self.storage.resolve_selected_prompt(prompt_id, scope, url=url)

    def answer(self, prompt, text='How to start?', url='https://example.com/max'):
        return self.answers.lookup_selected(prompt, raw_question=text, page_url=url)

    def test_same_id_in_different_scopes_returns_correct_answer(self):
        self.assertEqual(self.answer(self.resolve()).answer, 'Prepared Max answer.')
        self.assertEqual(self.answer(self.resolve('global')).answer, 'Global answer.')
        self.assertEqual(self.answer(self.resolve('page:mega', 'https://example.com/mega')).answer, 'Mega answer.')

    def test_wrong_page_host_missing_id_and_disabled_are_rejected(self):
        self.assertIsNone(self.resolve('page:max', 'https://example.com/mega'))
        self.assertIsNone(self.resolve(url='https://other.com/max'))
        self.assertIsNone(self.resolve(prompt_id='deleted'))
        self.write_config(enabled=False)
        self.assertIsNone(self.resolve())

    def test_duplicate_id_and_lead_button_are_not_faq_answers(self):
        data = json.loads(self.config.read_text())
        data['pages'][0]['prompts'] *= 2
        self.config.write_text(json.dumps(data))
        self.assertIsNone(self.resolve())
        self.write_config()
        data = json.loads(self.config.read_text())
        data['pages'][0]['prompts'][0]['type'] = 'lead_capture'
        self.config.write_text(json.dumps(data))
        self.assertIsNone(self.resolve())

    def test_answer_edits_and_question_edits_take_effect_immediately(self):
        self.write_config(answer='Updated answer.')
        self.assertEqual(self.answer(self.resolve()).answer, 'Updated answer.')
        self.assertIsNone(self.answer(self.resolve(), text='Different question'))

    def test_legacy_markdown_requires_exact_question_and_page_and_reloads(self):
        self.write_config(answer='')
        prompt = self.resolve()
        self.assertEqual(self.answer(prompt).answer, 'Legacy Max answer.')
        self.assertIsNone(self.answer(prompt, url='https://example.com/mega'))
        self.assertIsNone(self.answer({**prompt, 'prompt': 'How to start'}, text='How to start'))
        self.faq.write_text(self.faq.read_text().replace('Legacy Max answer.', 'New Markdown answer.'))
        self.assertEqual(self.answer(prompt).answer, 'New Markdown answer.')
        self.faq.write_text('')
        self.assertIsNone(self.answer(prompt))

    def test_chinese_answer_and_disabled_fast_answer(self):
        prompt = {'id': '中文问题', 'prompt': '怎么开机？', 'reply_text': '预置中文答案'}
        self.assertEqual(self.answer(prompt, text='怎么开机？').answer, '预置中文答案')
        self.answers.enabled = False
        self.assertIsNone(self.answer(prompt, text='怎么开机？'))

    def make_server(self):
        server = handler.FFRobotChatKitServer(
            store=handler.InMemoryStore(), lead_storage=Mock(), recommendation_storage=Mock(),
            homepage_prompts_storage=self.storage,
        )
        server.fast_answers = self.answers
        # Recommendations are a separate post-answer stage, not part of answer generation.
        async def recommendations(**kwargs):
            self.recommended = kwargs
            if False:
                yield
        server._stream_fast_answer_recommendation = recommendations
        self.recommended = None
        return server

    async def respond(self, server, *, selected=True, text='How to start?'):
        now = datetime.now(timezone.utc)
        thread = handler.ThreadMetadata(id='thread_test', created_at=now)
        message = handler.UserMessageItem(
            id='message_test', thread_id=thread.id, created_at=now,
            content=[{'type': 'input_text', 'text': text}], inference_options={},
        )
        context = {'page_url': 'https://example.com/max'}
        if selected:
            context.update(faq_id='same', faq_scope='page:max')
        return [event async for event in server.respond(thread, message, context)]

    async def test_click_returns_prepared_text_before_recommendation_without_model(self):
        server = self.make_server()
        with patch.object(handler.Runner, 'run', new=AsyncMock(side_effect=AssertionError('Model called'))), \
             patch.object(handler.Runner, 'run_streamed', side_effect=AssertionError('Model called')):
            events = await self.respond(server)
        answers = [e.item.content[0].text for e in events if e.type == 'thread.item.done']
        self.assertEqual(answers, ['Prepared Max answer.'])
        self.assertEqual(self.recommended['answer_text'], answers[0])

    async def test_free_input_and_disabled_button_enter_normal_plan(self):
        server = self.make_server()
        for selected in (False, True):
            if selected:
                self.write_config(enabled=False)
            with self.subTest(selected=selected), \
                 patch.object(handler.Runner, 'run', new=AsyncMock(side_effect=RuntimeError('normal plan'))), \
                 patch.object(self.answers, 'lookup', side_effect=AssertionError('Legacy fuzzy lookup called')):
                with self.assertRaisesRegex(RuntimeError, 'normal plan'):
                    await self.respond(server, selected=selected)
        self.assertIsNone(self.recommended)


if __name__ == '__main__':
    unittest.main()
