"""Codex JSONL adapter tests; synthetic counts are never claimed as live billing."""
import copy
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from collect_usage import codex_usage, collect, owned_file, write_new


class CodexUsageTests(unittest.TestCase):
    def test_json_output_survives_legacy_console_and_never_overwrites(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / 'usage.json'
            buffer = io.BytesIO()
            console = io.TextIOWrapper(buffer, encoding='cp1252', errors='strict')
            value = {'source': {'path': '원시 기록.jsonl'}}
            with redirect_stdout(console):
                write_new(output, value)
            console.flush()
            self.assertEqual(json.loads(buffer.getvalue()), value)
            self.assertEqual(json.loads(output.read_bytes()), value)
            with self.assertRaises(FileExistsError):
                write_new(output, {'changed': True})
            self.assertEqual(json.loads(output.read_bytes()), value)

    def trace(self, **usage):
        return [{'type': 'thread.started', 'thread_id': 'thread-1'}, {'type': 'turn.started'},
                {'type': 'turn.completed', 'usage': dict(input_tokens=100, cached_input_tokens=40,
                  cache_write_input_tokens=10, output_tokens=20, reasoning_output_tokens=5, **usage)}]

    def test_flat_runtime_counts_include_cache_writes_and_reasoning_subsets(self):
        observed = codex_usage(self.trace(), 'cumulative')
        self.assertEqual(observed['usage_status'], 'observed')
        self.assertEqual(observed['usage'], {'input_tokens': 100, 'cached_input_tokens': 40,
            'cache_write_tokens': 10, 'output_tokens': 20, 'reasoning_output_tokens': 5})
        self.assertIsNone(observed['observed_model'])

    def test_duplicate_terminal_event_is_not_billed_twice(self):
        events = self.trace()
        events.append(copy.deepcopy(events[-1]))
        for mode in ('cumulative', 'delta'):
            self.assertEqual(codex_usage(events, mode)['usage']['input_tokens'], 100)

    def test_explicit_cumulative_and_delta_modes_differ(self):
        events = self.trace()
        events.extend([{'type': 'turn.started'}, copy.deepcopy(events[-1])])
        events[-1]['usage'].update(input_tokens=160, cached_input_tokens=60,
                                  cache_write_input_tokens=20, output_tokens=30, reasoning_output_tokens=7)
        self.assertEqual(codex_usage(events, 'cumulative')['usage']['input_tokens'], 160)
        self.assertEqual(codex_usage(events, 'delta')['usage']['input_tokens'], 260)

    def test_missing_cache_write_and_reasoning_remain_unknown(self):
        events = self.trace()
        del events[-1]['usage']['cache_write_input_tokens']
        del events[-1]['usage']['reasoning_output_tokens']
        result = codex_usage(events, 'cumulative')
        self.assertEqual(result['usage_status'], 'observed')
        self.assertIsNone(result['usage']['cache_write_tokens'])
        self.assertIsNone(result['usage']['reasoning_output_tokens'])

    def test_unfinished_turn_does_not_reuse_previous_complete_counts(self):
        for tail in ([{'type': 'turn.started'}], [{'type': 'turn.failed'}], [{'type': 'error'}]):
            with self.subTest(tail=tail):
                result = codex_usage(self.trace() + tail, 'cumulative')
                self.assertEqual(result['usage_status'], 'unavailable')
                self.assertIsNone(result['usage'])

    def test_missing_counters_are_not_zero(self):
        for key in ('input_tokens', 'cached_input_tokens', 'output_tokens'):
            events = self.trace()
            del events[-1]['usage'][key]
            self.assertEqual(codex_usage(events, 'cumulative')['usage_status'], 'unavailable')
        self.assertEqual(codex_usage([], 'cumulative')['usage_status'], 'unavailable')

    def test_later_success_cannot_hide_unmeasured_earlier_turn(self):
        for earlier in ({'type': 'turn.completed'}, {'type': 'turn.failed'}, None):
            for mode in ('delta', 'cumulative'):
                with self.subTest(earlier=earlier, mode=mode):
                    events = self.trace()[:2]
                    if earlier is not None:
                        events.append(earlier)
                    events.extend(self.trace()[1:])
                    result = codex_usage(events, mode)
                    self.assertEqual(result['usage_status'], 'unavailable')
                    self.assertIsNone(result['usage'])

    def test_counters_with_conflicting_duplicate_or_mixed_threads_are_rejected(self):
        duplicate = self.trace()
        duplicate.append(copy.deepcopy(duplicate[-1]))
        duplicate[-1]['usage']['input_tokens'] += 1
        with self.assertRaises(ValueError):
            codex_usage(duplicate, 'cumulative')
        with self.assertRaises(ValueError):
            codex_usage(self.trace() + [{'type': 'thread.started', 'thread_id': 'other'}], 'cumulative')

    def test_model_is_observed_from_metadata_not_inferred_from_requests(self):
        events = self.trace()
        events[0]['model'] = 'observed-model'
        self.assertEqual(codex_usage(events, 'cumulative')['observed_model'], 'observed-model')
        events[1]['model'] = 'another-model'
        with self.assertRaises(ValueError):
            codex_usage(events, 'cumulative')

    def test_collector_binds_trace_and_result_and_does_not_claim_child_coverage(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            result = root / 'result.json'
            result.write_text(json.dumps({'run_id': 'actual-run-id'}))
            trace = root / 'events.jsonl'
            events = self.trace()
            events.insert(2, {'type': 'item.completed', 'item': {'type': 'collab_agent_tool_call'}})
            trace.write_text('\n'.join(json.dumps(e) for e in events))
            manifest = root / 'attempts.json'
            manifest.write_text(json.dumps({'schema': 1, 'attempts': [{
                'attempt_id': 'a1', 'parent_id': None, 'trace': 'events.jsonl', 'mode': 'cumulative',
                'status': 'completed', 'provider': 'openai', 'runtime_version': 'test',
                'requested_model': 'requested-model', 'includes_children': False, 'duration_seconds': 1}]}))
            before = result.read_bytes()
            sidecar = collect(result, manifest)
            self.assertEqual(sidecar['run_id'], 'actual-run-id')
            self.assertEqual(len(sidecar['result_sha256']), 64)
            attempt = sidecar['attempts'][0]
            self.assertEqual(attempt['usage_status'], 'unavailable')
            self.assertIn('Collaboration', attempt['reason'])
            self.assertIsNone(attempt['observed_model'])
            self.assertEqual(attempt['source']['path'], 'events.jsonl')
            self.assertEqual(result.read_bytes(), before)
            with self.assertRaises(ValueError):
                owned_file(root, '../outside')


if __name__ == '__main__':
    unittest.main()
