"""Scope controls prove bounded fault detection, never language/visual quality."""
import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import check_scope as scope
from compare_evals import compare, scope_suites
from summarize_scope_trials import summarize


def good_product(case, destination):
    shutil.copytree(scope.fixture_root(case) / "product", destination)
    if case == "narrow-spacing":
        (destination / "settings.css").write_text('.actions { margin-top: var(--space-4); }\n')
    elif case == "empty-state-copy-only":
        locale = json.loads((destination / "locales/ko.json").read_text())
        locale.update(empty_title='“{query}”에 맞는 자료가 없습니다.', empty_body='다른 검색어로 찾아보세요.', empty_name='{query}에 맞는 자료 없음')
        scope.write_json(destination / "locales/ko.json", locale)
    elif case == "master-page-consistency":
        rule = '.comparison-table th, .comparison-table td { padding-block: 10px; }\n'
        (destination / "compare.css").write_text(rule)
        design = (destination / "DESIGN.md").read_text()
        before, _, after = scope.exception_section(design)
        (destination / "DESIGN.md").write_text(before + scope.START + '\ncompare.html에서 행 비교를 쉽게 하도록 셀 간격을 줄인다.\n```css\n' + rule + '```\n' + scope.END + after)
    return destination


def synthetic_result(case, variant, run_id):
    suite = scope_suites()[case + '-v1']
    return {"schema": 1, "suite": suite["id"], "run_id": run_id, "variant": variant,
            "fixture": {"id": case, "sha256": "a" * 64}, "task_sha256": "b" * 64,
            "model": "synthetic-test-context", "settings": {"invocation_mode": "snapshot-direct", "reasoning": "test"},
            "skill_revision": "test-revision-" + variant,
            "cases": [{"id": case, "checks": [{"id": key, "kind": kind, "status": "pass", "evidence": {"text": "Synthetic contract observation for harness tests only."}} for key, kind in suite["cases"][case].items()]}]}


class ScopeSourceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def product(self, case):
        return good_product(case, self.root / case)

    def statuses(self, case, product):
        return {check['id']: check['status'] for check in scope.inspect_source(case, product)['checks']}

    def test_known_good_source_controls(self):
        for case in scope.CASES:
            with self.subTest(case=case):
                self.assertEqual(set(self.statuses(case, self.product(case)).values()), {'pass'})

    def test_css_comments_and_whitespace_do_not_force_exact_bytes(self):
        product = self.product('narrow-spacing')
        (product / 'settings.css').write_text('/* targeted spacing */\n.actions\n { margin-top : var(--space-4) ; }')
        self.assertEqual(self.statuses('narrow-spacing', product)['allowed-scope'], 'pass')

    def test_read_only_rejects_write_new_file_and_file_mode(self):
        product = self.product('audit-read-only')
        self.assertEqual(self.statuses('audit-read-only', product)['product-files-unchanged'], 'pass')
        original = (product / 'index.html').read_text()
        (product / 'index.html').write_text(original.replace('배송 대기', '완료'))
        self.assertEqual(self.statuses('audit-read-only', product)['product-files-unchanged'], 'fail')
        (product / 'index.html').write_text(original)
        (product / 'report.md').write_text('Unrequested audit product write')
        self.assertEqual(self.statuses('audit-read-only', product)['product-files-unchanged'], 'fail')
        (product / 'report.md').unlink()
        if os.name != 'nt':
            (product / 'index.html').chmod(0o755)
            self.assertEqual(self.statuses('audit-read-only', product)['product-files-unchanged'], 'fail')

    @unittest.skipIf(os.name == 'nt', 'Creating Windows symlinks requires developer-mode privileges.')
    def test_product_root_symlink_cannot_hide_read_only_writes(self):
        product = self.product('audit-read-only')
        shutil.rmtree(product)
        product.symlink_to(scope.fixture_root('audit-read-only') / 'product', target_is_directory=True)
        self.assertEqual(scope.inventory(product)['.']['type'], 'symlink')
        self.assertEqual(len(scope.inventory(product)), 1)
        self.assertEqual(self.statuses('audit-read-only', product)['product-files-unchanged'], 'fail')

    def test_read_only_rejects_added_directory(self):
        product = self.product('audit-read-only')
        (product / 'new-directory').mkdir()
        self.assertEqual(self.statuses('audit-read-only', product)['product-files-unchanged'], 'fail')

    def test_narrow_scope_rejects_shared_token_and_local_shadow(self):
        product = self.product('narrow-spacing')
        tokens = (product / 'tokens.css').read_text()
        (product / 'tokens.css').write_text(tokens.replace('#235942', '#8736b5'))
        self.assertEqual(self.statuses('narrow-spacing', product)['allowed-scope'], 'fail')
        (product / 'tokens.css').write_text(tokens)
        (product / 'settings.css').write_text('.actions { margin-top: var(--space-4); } :root { --brand: #8736b5; }')
        self.assertEqual(self.statuses('narrow-spacing', product)['allowed-scope'], 'fail')

    def test_locale_rejects_interpolation_key_and_known_fabricated_action(self):
        product = self.product('empty-state-copy-only')
        good = json.loads((product / 'locales/ko.json').read_text())
        for mutation in (lambda obj: obj.update(empty_name='자료 없음'),
                         lambda obj: obj.update(new_key='추가'),
                         lambda obj: obj.update(empty_body='필터 초기화 버튼을 눌러 다시 시도하세요.')):
            current = copy.deepcopy(good)
            mutation(current)
            scope.write_json(product / 'locales/ko.json', current)
            self.assertEqual(self.statuses('empty-state-copy-only', product)['locale-aria-contract'], 'fail')

    def test_locale_rejects_aria_mutation_even_when_strings_are_valid(self):
        product = self.product('empty-state-copy-only')
        index = product / 'index.html'
        index.write_text(index.read_text().replace('aria-labelledby="empty-title"', 'aria-labelledby="missing-title"'))
        self.assertEqual(self.statuses('empty-state-copy-only', product)['locale-aria-contract'], 'fail')

    def test_master_rejects_shared_token_and_design_disagreement(self):
        product = self.product('master-page-consistency')
        tokens = (product / 'tokens.css').read_text()
        (product / 'tokens.css').write_text(tokens.replace('--cell-space: 16px', '--cell-space: 10px'))
        self.assertEqual(self.statuses('master-page-consistency', product)['allowed-scope'], 'fail')
        (product / 'tokens.css').write_text(tokens)
        design = product / 'DESIGN.md'
        design.write_text(design.read_text().replace('padding-block: 10px', 'padding-block: 8px'))
        self.assertEqual(self.statuses('master-page-consistency', product)['design-record-matches'], 'fail')

    def test_prepare_is_fresh_and_collect_keeps_missing_review_incomplete(self):
        trial = self.root / 'trial'
        scope.prepare('narrow-spacing', trial)
        with self.assertRaises(FileExistsError):
            scope.prepare('narrow-spacing', trial)
        scope.write_json(trial / 'invocation.json', {key: value for key, value in synthetic_result('narrow-spacing', 'candidate', 'collect-trial').items() if key in ('run_id', 'variant', 'model', 'settings', 'skill_revision')})
        run = scope.collect('narrow-spacing', trial)
        statuses = {check['id']: check['status'] for check in run['cases'][0]['checks']}
        self.assertEqual(statuses, {'allowed-scope': 'fail', 'spacing-and-state': 'not-run', 'narrow-focus-review': 'not-run'})
        baseline = synthetic_result('narrow-spacing', 'baseline', 'baseline-trial')
        baseline['fixture'], baseline['task_sha256'] = run['fixture'], run['task_sha256']
        outcome = compare(baseline, run, candidate_root=trial, suite=scope_suites()['narrow-spacing-v1'])
        self.assertEqual(outcome['verdict'], 'changes-required')
        self.assertTrue(outcome['not_run'])
        (trial / 'product/settings.css').write_text('.actions { margin-top: var(--space-4); }')
        run = scope.collect('narrow-spacing', trial)
        self.assertEqual(compare(baseline, run, candidate_root=trial, suite=scope_suites()['narrow-spacing-v1'])['verdict'], 'incomplete')

    def test_concrete_review_failure_is_kept_when_other_images_are_missing(self):
        case = 'narrow-spacing'
        trial = self.root / 'failed-review'
        scope.prepare(case, trial)
        scope.write_json(trial / 'invocation.json', synthetic_result(case, 'candidate', 'failed-review-trial'))
        (trial / 'agent-output.md').write_text('Synthetic actual response for collector regression testing.')
        (trial / 'review.md').write_text('A concrete failure was observed; the remaining images could not be inspected.')
        scope.write_json(trial / 'review.json', {'narrow-focus-review': {'status': 'fail', 'evidence': {'path': 'review.md'}, 'reviewed_images': []}})
        check = scope.collect(case, trial)['cases'][0]['checks'][-1]
        self.assertEqual(check['status'], 'fail')
        self.assertIn('unavailable', check['reason'])

    def test_review_pass_without_inspected_images_cannot_pass(self):
        case = 'narrow-spacing'
        trial = self.root / 'trial'
        scope.prepare(case, trial)
        (trial / 'product/settings.css').write_text('.actions { margin-top: var(--space-4); }')
        invocation = synthetic_result(case, 'candidate', 'review-trial')
        scope.write_json(trial / 'invocation.json', invocation)
        (trial / 'agent-output.md').write_text('Actual final output placeholder for this synthetic harness test.')
        (trial / 'review.md').write_text('Synthetic reviewer record; absent image must prevent pass.')
        scope.write_json(trial / 'review.json', {'narrow-focus-review': {'status': 'pass', 'evidence': {'path': 'review.md'}, 'reviewed_images': ['images/' + name for name in scope.IMAGES[case]]}})
        self.assertEqual(scope.collect(case, trial)['cases'][0]['checks'][-1]['status'], 'not-run')


class ScopeSummaryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.manifest = {'schema': 1, 'repetitions': 2, 'host_coverage': {mode: {'status': 'not-run', 'reason': 'Synthetic snapshot tests do not exercise actual host invocation.'} for mode in ('installed-host-explicit', 'automatic-discovery')}, 'trials': []}
        for case in scope.CASES:
            for repeat in (1, 2):
                for variant in ('baseline', 'candidate'):
                    name = f'{case}-{repeat}-{variant}'
                    directory = self.root / name
                    directory.mkdir()
                    scope.write_json(directory / 'result.json', synthetic_result(case, variant, name))
                    scope.write_json(directory / 'launch.json', {'request': {'fork_turns': 'none'}, 'response': {'task_name': name}})
                    (directory / 'agent-output.md').write_text('Synthetic final output for summary contract tests only.')
                    self.manifest['trials'].append({'case': case, 'repeat': repeat, 'variant': variant, 'native_agent_id': name, 'result': name + '/result.json', 'launch': name + '/launch.json', 'output': name + '/agent-output.md'})

    def test_sixteen_contexts_produce_eight_pairs_without_averages(self):
        result = summarize(self.manifest, self.root)
        self.assertEqual(result['verdict'], 'pass', result)
        self.assertEqual((result['loaded_trials'], len(result['pairs'])), (16, 8))
        self.assertTrue(all(not pair['improvements'] for pair in result['pairs']))

    def test_missing_trial_duplicate_context_and_missing_launch_are_incomplete(self):
        for mutation in (lambda obj: obj['trials'].pop(),
                         lambda obj: obj['trials'][1].update(native_agent_id=obj['trials'][0]['native_agent_id']),
                         lambda obj: obj['trials'][0].update(launch='absent.json')):
            with self.subTest(mutation=mutation):
                manifest = copy.deepcopy(self.manifest)
                mutation(manifest)
                self.assertEqual(summarize(manifest, self.root)['verdict'], 'incomplete')

    def test_global_condition_mismatch_is_incomplete_even_when_each_pair_matches(self):
        for entry in self.manifest['trials'][-2:]:
            path = self.root / entry['result']
            run = json.loads(path.read_text())
            run['settings']['reasoning'] = 'different-condition'
            scope.write_json(path, run)
        self.assertEqual(summarize(self.manifest, self.root)['verdict'], 'incomplete')

    def test_fixture_and_task_must_match_between_repetitions(self):
        for entry in self.manifest['trials'][2:4]:
            path = self.root / entry['result']
            run = json.loads(path.read_text())
            run['task_sha256'] = 'c' * 64
            scope.write_json(path, run)
        result = summarize(self.manifest, self.root)
        self.assertEqual(result['verdict'], 'incomplete')
        self.assertTrue(any('between repetitions' in error for error in result['errors']))

    def test_concrete_failure_wins_over_an_unrelated_missing_trial(self):
        entry = self.manifest['trials'][1]
        path = self.root / entry['result']
        run = json.loads(path.read_text())
        run['cases'][0]['checks'][0]['status'] = 'fail'
        scope.write_json(path, run)
        self.manifest['trials'].pop()
        outcome = summarize(self.manifest, self.root)
        self.assertEqual(outcome['verdict'], 'changes-required')
        self.assertTrue(outcome['missing'])

    def test_candidate_failure_survives_its_own_missing_baseline(self):
        entry = self.manifest['trials'][1]
        path = self.root / entry['result']
        run = json.loads(path.read_text())
        run['cases'][0]['checks'][0]['status'] = 'fail'
        scope.write_json(path, run)
        self.manifest['trials'].pop(0)
        outcome = summarize(self.manifest, self.root)
        self.assertEqual(outcome['verdict'], 'changes-required')
        pair = outcome['pairs'][0]
        self.assertEqual(pair['verdict'], 'changes-required')
        self.assertEqual(pair['comparison_verdict'], 'incomplete')
        self.assertTrue(pair['candidate_failures'])
        self.assertEqual(pair['regressions'], [])
        self.assertTrue(outcome['missing'])

    def test_candidate_failure_survives_missing_launch_metadata(self):
        entry = self.manifest['trials'][1]
        path = self.root / entry['result']
        run = json.loads(path.read_text())
        run['cases'][0]['checks'][0]['status'] = 'fail'
        scope.write_json(path, run)
        entry['launch'] = 'not-recorded.json'
        outcome = summarize(self.manifest, self.root)
        self.assertEqual(outcome['verdict'], 'changes-required')
        self.assertTrue(outcome['errors'])
        self.assertTrue(outcome['missing'])

    def test_followup_and_claimed_host_discovery_are_rejected(self):
        entry = self.manifest['trials'][0]
        scope.write_json(self.root / entry['launch'], {'request': {'fork_turns': 'all'}, 'response': {'task_name': entry['native_agent_id']}})
        self.manifest['host_coverage']['automatic-discovery']['status'] = 'pass'
        result = summarize(self.manifest, self.root)
        self.assertEqual(result['verdict'], 'incomplete')
        self.assertTrue(any('fork_turns' in error for error in result['errors']))
        self.assertTrue(any('automatic-discovery' in error for error in result['errors']))

    def test_malformed_host_coverage_preserves_complete_trial_pairs(self):
        for mode in ('installed-host-explicit', 'automatic-discovery'):
            for coverage in (None, [], 'not-run', 1, True, {}):
                with self.subTest(mode=mode, coverage=coverage):
                    manifest = copy.deepcopy(self.manifest)
                    manifest['host_coverage'][mode] = coverage
                    result = summarize(manifest, self.root)
                    self.assertEqual(result['verdict'], 'incomplete')
                    self.assertEqual((result['loaded_trials'], len(result['pairs'])), (16, 8))
                    self.assertTrue(all(pair['verdict'] == 'pass' for pair in result['pairs']))
                    self.assertTrue(any(mode in error for error in result['errors']))

    def test_candidate_failure_survives_malformed_host_coverage(self):
        entry = self.manifest['trials'][1]
        path = self.root / entry['result']
        run = json.loads(path.read_text())
        run['cases'][0]['checks'][0]['status'] = 'fail'
        scope.write_json(path, run)
        self.manifest['host_coverage']['automatic-discovery'] = None
        self.manifest['trials'].pop(0)
        result = summarize(self.manifest, self.root)
        self.assertEqual(result['verdict'], 'changes-required')
        self.assertTrue(any('automatic-discovery' in error for error in result['errors']))
        self.assertTrue(result['missing'])
        pair = result['pairs'][0]
        self.assertTrue(pair['candidate_failures'])
        self.assertEqual(pair['comparison_verdict'], 'incomplete')
        self.assertEqual(pair['regressions'], [])
        self.assertEqual(pair['improvements'], [])

    def test_malformed_host_coverage_cli_outputs_incomplete_json(self):
        self.manifest['host_coverage']['installed-host-explicit'] = None
        manifest_path = self.root / 'manifest.json'
        output_path = self.root / 'summary.json'
        scope.write_json(manifest_path, self.manifest)
        completed = subprocess.run(
            [sys.executable, '-B', str(ROOT / 'scripts/summarize_scope_trials.py'),
             str(manifest_path), '--output', str(output_path)],
            text=True, capture_output=True, timeout=10, check=False,
        )
        self.assertEqual(completed.returncode, 3, completed.stderr)
        self.assertEqual(completed.stderr, '')
        result = json.loads(completed.stdout)
        self.assertEqual(result['verdict'], 'incomplete')
        self.assertEqual(len(result['pairs']), 8)
        self.assertTrue(any('installed-host-explicit' in error for error in result['errors']))
        self.assertEqual(output_path.read_text(), completed.stdout)


if __name__ == '__main__':
    unittest.main()
