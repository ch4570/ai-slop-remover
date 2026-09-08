"""Opt-in Chrome controls for bounded source and rendered scope observations."""
import difflib
import json
import os
import shutil
from pathlib import Path
import subprocess
import tempfile
import unittest

from test_scope_checks import ROOT, good_product, scope
from test_browser_checks import evidence_snapshot, png_dimensions


@unittest.skipUnless(os.environ.get('AI_SLOP_BROWSER_TESTS') == '1',
                     'Opt in with AI_SLOP_BROWSER_TESTS=1 (existing Chrome and Node 22+).')
class ScopeBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='lutriva-scope-browser-')
        cls.addClassCleanup(cls.temp.cleanup)
        cls.root = Path(cls.temp.name)
        evidence = Path(os.environ.get('AI_SLOP_BROWSER_EVIDENCE', cls.root / 'evidence'))
        evidence.mkdir(parents=True, exist_ok=True)
        cls.evidence = Path(tempfile.mkdtemp(prefix='scope-', dir=evidence))

    def run_product(self, name, case, mutation=None, chrome=None):
        product = good_product(case, self.root / name)
        if mutation:
            mutation(product)
        output = self.evidence / name
        output.mkdir()
        source = scope.inspect_source(case, product)
        scope.write_json(output / 'source-checks.json', source)
        patches = []
        initial = scope.fixture_root(case) / 'product'
        for relative in source['changes']:
            if source['before'].get(relative, {}).get('type') == source['after'].get(relative, {}).get('type') == 'file':
                patches.extend(difflib.unified_diff((initial / relative).read_text().splitlines(keepends=True),
                                                    (product / relative).read_text().splitlines(keepends=True),
                                                    fromfile='before/' + relative, tofile='after/' + relative))
        (output / 'product.patch').write_text(''.join(patches), encoding='utf-8')
        env = os.environ.copy()
        if chrome:
            env['AI_SLOP_CHROME'] = chrome
        command = ['node', str(ROOT / 'scripts/run_scope_checks.mjs'), case, str(product), str(output)]
        run = subprocess.run(command, text=True, capture_output=True, timeout=60, env=env)
        (output / 'driver.log').write_text(run.stdout + run.stderr)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        browser = json.loads((output / 'browser.json').read_text())
        self.assertEqual(browser['case'], case)
        self.browser = browser
        self.output = output
        self.source = {check['id']: check['status'] for check in source['checks']}
        checks = browser['checks']
        self.assertEqual(len(checks), len({check['id'] for check in checks}))
        suite = scope.scope_suites()[case + '-v1']['cases'][case]
        self.assertEqual({check['id'] for check in checks}, {key for key, kind in suite.items() if kind == 'behavior'} - set(scope.SOURCE_IDS[case]))
        return {check['id']: check['status'] for check in checks}

    def test_known_good_controls_preserve_source_and_browser_contracts(self):
        for case in scope.CASES:
            with self.subTest(case=case):
                checks = self.run_product('good-' + case, case)
                self.assertEqual(set(checks.values()), {'pass'}, self.browser)
                self.assertEqual(set(self.source.values()), {'pass'})
                self.assertEqual(self.browser['observations']['exceptions'], [])
                for name in scope.IMAGES[case]:
                    self.assertGreater((self.output / 'images' / name).stat().st_size, 0)
                self.assertEqual(self.browser['observations']['layout']['width'], 375)
                self.assertTrue(self.browser['observations']['focus'])

    def test_keyboard_capture_preserves_viewport_on_tall_page(self):
        # The unchanged audit page already extends below both viewport heights.
        checks = self.run_product('tall-keyboard-viewport', 'audit-read-only')
        self.assertEqual(set(checks.values()), {'pass'}, self.browser)
        self.assertEqual(set(self.source.values()), {'pass'})
        self.assertEqual(self.browser['observations']['focus'][-1]['id'], 'order-search')
        for name, height in (('wide.png', 900), ('narrow.png', 844)):
            with self.subTest(overview=name):
                self.assertGreater(png_dimensions(self.output / 'images' / name)[1], height)
        self.assertEqual(png_dimensions(self.output / 'images/keyboard.png'), (375, 844))

    def test_existing_browser_artifacts_are_preserved(self):
        env = {**os.environ, 'AI_SLOP_CHROME': str(self.root / 'absent-chrome')}
        for artifact in ('browser.json', 'images/wide.png', 'images/master-wide.png'):
            with self.subTest(artifact=artifact):
                output = self.evidence / ('existing-' + artifact.replace('/', '-'))
                target = output / artifact
                target.parent.mkdir(parents=True)
                target.write_bytes(b'Previous collection evidence must survive unchanged.')
                before = evidence_snapshot(output)
                run = subprocess.run(['node', str(ROOT / 'scripts/run_scope_checks.mjs'), 'narrow-spacing',
                                      str(scope.fixture_root('narrow-spacing') / 'product'), str(output)],
                                     capture_output=True, text=True, timeout=30, env=env)
                self.assertEqual(run.returncode, 2, run.stdout + run.stderr)
                self.assertIn('new output path', run.stderr)
                self.assertEqual(before, evidence_snapshot(output))

    def test_prepared_trial_accepts_new_browser_evidence(self):
        for unavailable in (False, True):
            with self.subTest(unavailable=unavailable):
                output = self.evidence / ('prepared-' + str(unavailable))
                scope.prepare('audit-read-only', output)
                before = {str(path.relative_to(output)): (path.read_bytes(), path.stat().st_mtime_ns)
                          for path in output.rglob('*') if path.is_file()}
                env = os.environ.copy()
                if unavailable:
                    env['AI_SLOP_CHROME'] = str(self.root / 'absent-chrome')
                command = ['node', str(ROOT / 'scripts/run_scope_checks.mjs'), 'audit-read-only',
                           str(output / 'product'), str(output)]
                run = subprocess.run(command, capture_output=True, text=True, timeout=60, env=env)
                self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
                browser = json.loads((output / 'browser.json').read_text())
                self.assertEqual({check['status'] for check in browser['checks']}, {'not-run' if unavailable else 'pass'})
                self.assertEqual(before, {name: ((output / name).read_bytes(), (output / name).stat().st_mtime_ns) for name in before})
                if unavailable:
                    self.assertTrue(browser['observations']['collectionErrors'])
                else:
                    for name in scope.IMAGES['audit-read-only']:
                        self.assertGreater((output / 'images' / name).stat().st_size, 0)
                recorded = evidence_snapshot(output)
                repeated = subprocess.run(command, capture_output=True, text=True, timeout=30, env=env)
                self.assertEqual(repeated.returncode, 2, repeated.stdout + repeated.stderr)
                self.assertIn('new output path', repeated.stderr)
                self.assertEqual(recorded, evidence_snapshot(output))

    def test_local_brand_shadow_is_rejected_after_correct_spacing(self):
        def mutate(product):
            with (product / 'settings.css').open('a') as file:
                file.write(':root { --brand: #8736b5; }\n')
        checks = self.run_product('local-brand-shadow', 'narrow-spacing', mutate)
        self.assertEqual(self.source['allowed-scope'], 'fail')
        self.assertEqual(checks['spacing-and-state'], 'fail')

    def test_broken_save_is_observed_independently_of_spacing(self):
        def mutate(product):
            path = product / 'app.js'
            path.write_text(path.read_text().replace("localStorage.setItem('display-name', field.value);", "localStorage.setItem('display-name', 'unrelated replacement');"))
        checks = self.run_product('lost-setting', 'narrow-spacing', mutate)
        self.assertEqual(checks['spacing-and-state'], 'fail')

    def test_broken_aria_link_is_observed(self):
        def mutate(product):
            path = product / 'index.html'
            path.write_text(path.read_text().replace('aria-labelledby="empty-title"', 'aria-labelledby="absent-title"'))
        checks = self.run_product('broken-aria', 'empty-state-copy-only', mutate)
        self.assertEqual(self.source['locale-aria-contract'], 'fail')
        self.assertEqual(checks['search-and-names'], 'fail')

    def test_known_fabricated_recovery_is_source_failure_without_fake_semantic_pass(self):
        def mutate(product):
            path = product / 'locales/ko.json'
            locale = json.loads(path.read_text())
            locale['empty_body'] = '필터 초기화 버튼을 눌러 다시 시도하세요.'
            scope.write_json(path, locale)
        checks = self.run_product('fabricated-recovery', 'empty-state-copy-only', mutate)
        self.assertEqual(self.source['locale-aria-contract'], 'fail')
        self.assertEqual(checks['search-and-names'], 'pass')
        self.assertNotIn('truthful-copy-and-name', checks)

    def test_shared_density_token_breaks_master(self):
        def mutate(product):
            path = product / 'tokens.css'
            path.write_text(path.read_text().replace('--cell-space: 16px', '--cell-space: 10px'))
        checks = self.run_product('shared-density-token', 'master-page-consistency', mutate)
        self.assertEqual(self.source['allowed-scope'], 'fail')
        self.assertEqual(checks['shared-master-preserved'], 'fail')
        self.assertEqual(checks['compare-density-and-actions'], 'pass')

    def test_design_disagreement_is_distinct_from_working_render(self):
        def mutate(product):
            path = product / 'DESIGN.md'
            path.write_text(path.read_text().replace('padding-block: 10px', 'padding-block: 8px'))
        checks = self.run_product('design-disagreement', 'master-page-consistency', mutate)
        self.assertEqual(self.source['design-record-matches'], 'fail')
        self.assertEqual(set(checks.values()), {'pass'})

    def test_absent_browser_reports_all_required_observations_not_run(self):
        checks = self.run_product('no-browser', 'narrow-spacing', chrome=str(self.root / 'not-installed-chrome'))
        self.assertEqual(checks, {'spacing-and-state': 'not-run'})
        self.assertTrue(self.browser['observations']['collectionErrors'])
        self.assertEqual(self.browser['observations']['images'], [])

    @unittest.skipIf(os.name == 'nt', 'Creating Windows symlinks requires developer-mode privileges.')
    def test_browser_does_not_traverse_a_replaced_product_root(self):
        def mutate(product):
            shutil.rmtree(product)
            product.symlink_to(scope.fixture_root('narrow-spacing') / 'product', target_is_directory=True)
        checks = self.run_product('replaced-product-root', 'narrow-spacing', mutate)
        self.assertEqual(checks['spacing-and-state'], 'not-run')
        self.assertIn('no browser traversal', self.browser['checks'][0]['reason'])
        self.assertEqual(self.source['allowed-scope'], 'fail')

    def test_later_navigation_failure_preserves_prior_concrete_failure(self):
        def mutate(product):
            (product / 'settings.css').write_text('.actions { margin-top: var(--space-6); }')
            with (product / 'app.js').open('a') as file:
                file.write("\nif (sessionStorage.getItem('loaded')) document.querySelector('main').remove();\nsessionStorage.setItem('loaded', 'yes');\n")
        checks = self.run_product('failure-before-unavailable-reload', 'narrow-spacing', mutate)
        self.assertEqual(checks['spacing-and-state'], 'fail')
        facts = json.loads(self.browser['checks'][0]['evidence']['text'])
        self.assertTrue(any(not fact['matches'] for fact in facts['facts']))
        self.assertIn('Fixture did not finish loading', facts['error'])


if __name__ == '__main__':
    unittest.main()
