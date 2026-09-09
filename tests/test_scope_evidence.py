"""Evidence freshness controls; synthetic records make no visual-quality claim."""
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from uuid import UUID

from test_scope_checks import ROOT, compare, good_product, scope, scope_suites, synthetic_result


class ScopeEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def recorded_trial(self, case, name='trial'):
        trial = self.root / name
        scope.prepare(case, trial)
        shutil.rmtree(trial / 'product')
        good_product(case, trial / 'product')
        scope.write_json(trial / 'invocation.json', synthetic_result(case, 'candidate', name))
        (trial / 'agent-output.md').write_text('Synthetic actual response for evidence contract tests.')
        (trial / 'review.md').write_text('Synthetic reviewer observed the saved captures and response.')
        (trial / 'images').mkdir()
        images = ['images/' + name for name in scope.IMAGES[case]]
        for image in images:
            (trial / image).write_bytes(b'Synthetic image artifact: ' + image.encode())
        suite = scope_suites()[case + '-v1']['cases'][case]
        binding = scope.observation_binding(case, trial)
        browser = {'schema': 2, 'case': case, 'binding': binding,
                   'product_after_sha256': binding['product_sha256'],
                   'observations': {'images': images, 'image_sha256': {
                       name: self.file_digest(trial / name) for name in images}}, 'checks': [
            {'id': key, 'kind': kind, 'status': 'pass', 'evidence': {
                'path': 'browser.json', 'text': 'Synthetic browser contract observation completed.'}}
            for key, kind in suite.items() if kind == 'behavior' and key not in scope.SOURCE_IDS[case]
        ]}
        scope.write_json(trial / 'browser.json', browser)
        review = {'schema': 2, 'binding': copy.deepcopy(binding),
                  'browser_sha256': self.file_digest(trial / 'browser.json'),
                  'reviewed_files': {name: self.file_digest(trial / name)
                                     for name in images + ['review.md', 'agent-output.md']},
                  'checks': {
            key: {'status': 'pass', 'evidence': {'path': 'review.md'}, 'reviewed_images': images}
            for key, kind in suite.items() if kind == 'quality'
        }}
        scope.write_json(trial / 'review.json', review)
        return trial

    @staticmethod
    def file_digest(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    @staticmethod
    def alter_json(path, mutate):
        record = json.loads(path.read_text())
        mutate(record)
        scope.write_json(path, record)

    def checks(self, case, trial):
        return {check['id']: check for check in scope.collect(case, trial)['cases'][0]['checks']}

    def assert_stale(self, check, reason_fragment):
        self.assertEqual(check['status'], 'not-run', check)
        self.assertIn(reason_fragment.lower(), check['reason'].lower())

    def test_current_bound_evidence_passes_for_every_case(self):
        for case in scope.CASES:
            with self.subTest(case=case):
                trial = self.recorded_trial(case, case)
                self.assertEqual({check['status'] for check in self.checks(case, trial).values()}, {'pass'})

    def test_trial_identity_is_stable_and_unique_even_for_identical_products(self):
        first = self.recorded_trial('narrow-spacing', 'first')
        second = self.recorded_trial('narrow-spacing', 'second')
        one = scope.observation_binding('narrow-spacing', first)
        two = scope.observation_binding('narrow-spacing', second)
        self.assertEqual(one, scope.observation_binding('narrow-spacing', first))
        self.assertEqual(one['schema'], 2)
        self.assertEqual(one['case'], 'narrow-spacing')
        self.assertEqual(UUID(one['trial_id']).version, 4)
        self.assertNotEqual(one['trial_id'], two['trial_id'])
        self.assertEqual(one['product_sha256'], two['product_sha256'])
        context = json.loads((first / 'evidence-context.json').read_text())
        self.assertEqual(context, scope.evidence_context('narrow-spacing', first))
        self.assertEqual(context['schema'], 1)
        self.assertEqual(context['trial_id'], one['trial_id'])
        self.assertEqual(context['case'], one['case'])

    def test_false_copy_mutation_cannot_reuse_passing_observations(self):
        case = 'empty-state-copy-only'
        trial = self.recorded_trial(case)
        self.assertEqual({check['status'] for check in self.checks(case, trial).values()}, {'pass'})
        locale_path = trial / 'product/locales/ko.json'
        locale = json.loads(locale_path.read_text())
        locale['empty_body'] = '잠시 후 다시 열면 모든 자료가 자동으로 나타납니다.'
        scope.write_json(locale_path, locale)
        checks = self.checks(case, trial)
        self.assertEqual(checks['locale-aria-contract']['status'], 'pass')
        self.assert_stale(checks['search-and-names'], 'product')
        self.assert_stale(checks['truthful-copy-and-name'], 'product')
        candidate = scope.collect(case, trial)
        baseline = synthetic_result(case, 'baseline', 'baseline-context')
        baseline['fixture'], baseline['task_sha256'] = candidate['fixture'], candidate['task_sha256']
        outcome = compare(baseline, candidate, candidate_root=trial, suite=scope_suites()[case + '-v1'])
        self.assertEqual(outcome['verdict'], 'incomplete', outcome)
        self.assertIn('candidate/' + case + '/truthful-copy-and-name', outcome['not_run'])

    def test_css_drift_invalidates_observations_even_when_source_contract_still_passes(self):
        case = 'narrow-spacing'
        trial = self.recorded_trial(case)
        (trial / 'product/settings.css').write_text('/* saved after browser capture */\n.actions { margin-top: var(--space-4); }\n')
        checks = self.checks(case, trial)
        self.assertEqual(checks['allowed-scope']['status'], 'pass')
        self.assert_stale(checks['spacing-and-state'], 'product')
        self.assert_stale(checks['narrow-focus-review'], 'product')

    def test_changed_image_cannot_reuse_passing_review(self):
        case = 'narrow-spacing'
        trial = self.recorded_trial(case)
        self.assertEqual(self.checks(case, trial)['narrow-focus-review']['status'], 'pass')
        (trial / 'images/narrow.png').write_bytes(b'A different image now occupies the same reviewed path.')
        checks = self.checks(case, trial)
        self.assertEqual(checks['spacing-and-state']['status'], 'pass')
        self.assert_stale(checks['narrow-focus-review'], 'images/narrow.png')

    def test_missing_reviewed_image_cannot_pass(self):
        case = 'narrow-spacing'
        trial = self.recorded_trial(case)
        (trial / 'images/keyboard.png').unlink()
        self.assert_stale(self.checks(case, trial)['narrow-focus-review'], 'images/keyboard.png')

    def test_changed_review_text_and_actual_response_invalidate_review(self):
        for name in ('review.md', 'agent-output.md'):
            with self.subTest(name=name):
                trial = self.recorded_trial('narrow-spacing', name)
                (trial / name).write_text('Different content now occupies the originally reviewed file.')
                self.assert_stale(self.checks('narrow-spacing', trial)['narrow-focus-review'], name)

    def test_required_reviewed_file_digest_cannot_be_omitted(self):
        for name in ('images/wide.png', 'review.md', 'agent-output.md'):
            with self.subTest(name=name):
                trial = self.recorded_trial('narrow-spacing', name.replace('/', '-'))
                self.alter_json(trial / 'review.json', lambda review: review['reviewed_files'].pop(name))
                self.assert_stale(self.checks('narrow-spacing', trial)['narrow-focus-review'], name)

    def test_browser_from_another_trial_cannot_pass_with_identical_product(self):
        case = 'narrow-spacing'
        first, second = self.recorded_trial(case, 'first'), self.recorded_trial(case, 'second')
        shutil.copyfile(first / 'browser.json', second / 'browser.json')
        checks = self.checks(case, second)
        self.assert_stale(checks['spacing-and-state'], 'trial')
        self.assert_stale(checks['narrow-focus-review'], 'browser')

    def test_review_from_another_trial_cannot_pass_with_identical_images(self):
        case = 'narrow-spacing'
        first, second = self.recorded_trial(case, 'first'), self.recorded_trial(case, 'second')
        shutil.copyfile(first / 'review.json', second / 'review.json')
        checks = self.checks(case, second)
        self.assertEqual(checks['spacing-and-state']['status'], 'pass')
        self.assert_stale(checks['narrow-focus-review'], 'trial')

    def test_any_browser_byte_change_invalidates_the_recorded_review(self):
        case = 'narrow-spacing'
        trial = self.recorded_trial(case)
        browser_path = trial / 'browser.json'
        browser_path.write_bytes(browser_path.read_bytes() + b'\n')
        checks = self.checks(case, trial)
        self.assertEqual(checks['spacing-and-state']['status'], 'pass')
        self.assert_stale(checks['narrow-focus-review'], 'browser')

    def test_missing_browser_binding_or_legacy_schema_cannot_pass(self):
        for defect in ('binding', 'schema'):
            with self.subTest(defect=defect):
                trial = self.recorded_trial('narrow-spacing', defect)
                def mutate(browser):
                    if defect == 'binding':
                        browser.pop('binding')
                    else:
                        browser['schema'] = 1
                self.alter_json(trial / 'browser.json', mutate)
                checks = self.checks('narrow-spacing', trial)
                self.assert_stale(checks['spacing-and-state'], defect)
                self.assertEqual(checks['narrow-focus-review']['status'], 'not-run')

    def test_missing_review_binding_and_legacy_review_cannot_pass(self):
        for defect in ('binding', 'schema', 'legacy'):
            with self.subTest(defect=defect):
                trial = self.recorded_trial('narrow-spacing', defect)
                review_path = trial / 'review.json'
                review = json.loads(review_path.read_text())
                if defect == 'legacy':
                    review = review['checks']
                elif defect == 'binding':
                    review.pop('binding')
                else:
                    review['schema'] = 1
                scope.write_json(review_path, review)
                check = self.checks('narrow-spacing', trial)['narrow-focus-review']
                self.assert_stale(check, 'schema' if defect == 'legacy' else defect)

    def test_browser_before_after_product_mismatch_cannot_pass(self):
        case = 'narrow-spacing'
        trial = self.recorded_trial(case)
        self.alter_json(trial / 'browser.json', lambda browser: browser.update(product_after_sha256='f' * 64))
        self.assert_stale(self.checks(case, trial)['spacing-and-state'], 'product')

    def test_changed_task_invalidates_browser_and_review(self):
        case = 'narrow-spacing'
        trial = self.recorded_trial(case)
        task = trial / 'TASK.md'
        task.write_text(task.read_text() + '\nA different requested behavior.\n')
        checks = self.checks(case, trial)
        self.assertEqual(checks['allowed-scope']['status'], 'fail')
        self.assert_stale(checks['spacing-and-state'], 'task')
        self.assert_stale(checks['narrow-focus-review'], 'task')

    def test_evaluator_mismatch_in_each_observation_cannot_pass(self):
        for artifact, check_id in (('browser.json', 'spacing-and-state'),
                                   ('review.json', 'narrow-focus-review')):
            with self.subTest(artifact=artifact):
                trial = self.recorded_trial('narrow-spacing', artifact)
                self.alter_json(trial / artifact, lambda record: record['binding'].update(evaluator_sha256='f' * 64))
                self.assert_stale(self.checks('narrow-spacing', trial)[check_id], 'evaluator')

    def test_review_context_captures_artifacts_but_never_supplies_a_verdict(self):
        case = 'narrow-spacing'
        trial = self.recorded_trial(case)
        captured = scope.review_context(case, trial)
        self.assertEqual(captured['checks'], {})
        self.assertEqual(captured['browser_sha256'], self.file_digest(trial / 'browser.json'))
        self.assertEqual(set(captured['reviewed_files']),
                         {'images/' + name for name in scope.IMAGES[case]} | {'agent-output.md', 'review.md'})
        recorded = json.loads((trial / 'review.json').read_text())
        captured['checks'] = recorded['checks']
        scope.write_json(trial / 'review.json', captured)
        self.assertEqual(self.checks(case, trial)['narrow-focus-review']['status'], 'pass')
        (trial / 'product/settings.css').write_text('/* after browser observation */\n.actions { margin-top: var(--space-4); }\n')
        with self.assertRaisesRegex(ValueError, 'stale'):
            scope.review_context(case, trial)

    def test_image_changed_before_review_context_cannot_be_sealed(self):
        case = 'narrow-spacing'
        trial = self.recorded_trial(case)
        (trial / 'review.json').unlink()
        (trial / 'images/narrow.png').write_bytes(b'Replacement written after browser capture, before independent review.')
        with self.assertRaisesRegex(ValueError, '[Ii]mage'):
            scope.review_context(case, trial)

    def test_rehashing_replaced_image_in_review_cannot_rebind_browser_capture(self):
        case = 'narrow-spacing'
        trial = self.recorded_trial(case)
        (trial / 'images/narrow.png').write_bytes(b'A replacement image was hashed after the original browser observation.')
        self.alter_json(trial / 'review.json', lambda review: review['reviewed_files'].update({
            'images/narrow.png': self.file_digest(trial / 'images/narrow.png')}))
        self.assert_stale(self.checks(case, trial)['narrow-focus-review'], 'images/narrow.png')

    def test_custom_review_evidence_path_is_bound(self):
        case = 'narrow-spacing'
        trial = self.recorded_trial(case)
        notes = trial / 'reviewer-notes.md'
        notes.write_text('Independent review notes supplied at a custom result-relative path.')
        review = json.loads((trial / 'review.json').read_text())
        review['checks']['narrow-focus-review']['evidence']['path'] = 'reviewer-notes.md'
        review['reviewed_files']['reviewer-notes.md'] = self.file_digest(notes)
        scope.write_json(trial / 'review.json', review)
        self.assertEqual(self.checks(case, trial)['narrow-focus-review']['status'], 'pass')
        notes.write_text('Changed reviewer notes now replace the original observation.')
        self.assert_stale(self.checks(case, trial)['narrow-focus-review'], 'reviewer-notes.md')

    @unittest.skipUnless(shutil.which('node'), 'Cross-runtime parity requires the existing Node executable.')
    def test_python_and_node_bindings_agree_for_inventory_edges(self):
        for edge in ('ordinary', 'unicode-and-numeric-names', 'symlink'):
            with self.subTest(edge=edge):
                trial = self.recorded_trial('narrow-spacing', edge)
                if edge == 'unicode-and-numeric-names':
                    for name in ('2', '10', '1', '__proto__', '한글 파일.txt', '\ue000.txt', '😀.txt'):
                        (trial / 'product' / name).write_text('Unicode fixture bytes: 한글 😀\n')
                    (trial / 'product/empty-directory').mkdir()
                elif edge == 'symlink':
                    if os.name == 'nt':
                        continue
                    (trial / 'product/linked.css').symlink_to('settings.css')
                    (trial / 'product/missing-target').symlink_to('does-not-exist')
                node = subprocess.run([
                    'node', '--input-type=module', '-e',
                    "import { observationBinding } from './scripts/scope_evidence.mjs'; "
                    "const [caseId, product, trial] = process.argv.slice(1); "
                    "process.stdout.write(JSON.stringify(await observationBinding(caseId, product, trial)));",
                    'narrow-spacing', str(trial / 'product'), str(trial),
                ], cwd=ROOT, text=True, capture_output=True, timeout=10, check=False)
                self.assertEqual(node.returncode, 0, node.stderr)
                self.assertEqual(json.loads(node.stdout), scope.observation_binding('narrow-spacing', trial))

    @unittest.skipIf(os.name == 'nt', 'POSIX file mode is part of the evaluator product inventory.')
    def test_file_mode_change_invalidates_recorded_observations(self):
        case = 'narrow-spacing'
        trial = self.recorded_trial(case)
        (trial / 'product/settings.css').chmod(0o755)
        checks = self.checks(case, trial)
        self.assertEqual(checks['allowed-scope']['status'], 'fail')
        self.assert_stale(checks['spacing-and-state'], 'product')
        self.assert_stale(checks['narrow-focus-review'], 'product')

    def test_concrete_browser_failure_survives_product_drift_with_warning(self):
        case = 'narrow-spacing'
        trial = self.recorded_trial(case)
        self.alter_json(trial / 'browser.json', lambda browser: browser['checks'][0].update(
            status='fail', evidence={'path': 'browser.json', 'text': 'The saved name was lost on reload during the recorded observation.'}))
        (trial / 'product/settings.css').write_text('/* edited after a concrete failure */\n.actions { margin-top: var(--space-4); }\n')
        check = self.checks(case, trial)['spacing-and-state']
        self.assertEqual(check['status'], 'fail')
        self.assertIn('product', check['reason'].lower())
        self.assertIn('lost on reload', check['evidence']['text'])

    def test_concrete_review_failure_survives_changed_image_with_warning(self):
        case = 'narrow-spacing'
        trial = self.recorded_trial(case)
        self.alter_json(trial / 'review.json', lambda review: review['checks']['narrow-focus-review'].update(status='fail'))
        (trial / 'images/narrow.png').write_bytes(b'A replacement cannot erase the previously observed concrete failure.')
        check = self.checks(case, trial)['narrow-focus-review']
        self.assertEqual(check['status'], 'fail')
        self.assertIn('images/narrow.png', check['reason'])

    @unittest.skipIf(os.name == 'nt', 'Windows symlinks require developer-mode privileges.')
    def test_product_binding_records_symlink_without_traversing_target(self):
        case = 'audit-read-only'
        trial = self.recorded_trial(case)
        outside = self.root / 'outside'
        outside.mkdir()
        target = outside / 'unobserved.txt'
        target.write_text('Original external bytes.')
        (trial / 'product/external').symlink_to(outside, target_is_directory=True)
        first = scope.observation_binding(case, trial)
        target.write_text('Changed external bytes must not be followed by the product inventory.')
        second = scope.observation_binding(case, trial)
        self.assertEqual(first['product_sha256'], second['product_sha256'])
        (trial / 'product/external').unlink()
        self.assertNotEqual(second['product_sha256'], scope.observation_binding(case, trial)['product_sha256'])


if __name__ == '__main__':
    unittest.main()
