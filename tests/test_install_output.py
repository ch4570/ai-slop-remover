"""Exercise real installer streams with paths outside legacy output encodings."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from test_install import ROOT, snapshot


class InstallerOutputTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='lutriva-output-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()

    def run_installer(self, project, agent, encoding, *options):
        process = subprocess.run(
            [sys.executable, '-B', str(ROOT / 'install.py'), '--repo', str(project),
             '--agent', agent, *options], capture_output=True, timeout=20,
            env={**os.environ, 'PYTHONIOENCODING': encoding + ':strict'},
        )
        return process.returncode, process.stdout.decode(encoding), process.stderr.decode(encoding)

    def test_unicode_install_reinstall_dry_run_and_status_preserve_files(self):
        for agent in ('codex', 'claude'):
            for encoding in ('cp1252', 'ascii', 'utf-8'):
                with self.subTest(agent=agent, encoding=encoding):
                    project = self.root / (agent + '-' + encoding + '-한글 😺 공백-é')
                    project.mkdir()
                    expected_path = str(project).encode(encoding, 'backslashreplace').decode(encoding)
                    before = snapshot(project)
                    for option in ('--dry-run', '--status'):
                        code, output, error = self.run_installer(project, agent, encoding, option)
                        self.assertEqual((code, error), (0, ''), output + error)
                        self.assertIn(expected_path, output)
                        self.assertEqual(before, snapshot(project))
                    code, output, error = self.run_installer(project, agent, encoding)
                    self.assertEqual((code, error), (0, ''), output + error)
                    self.assertEqual(output.count('Installed '), 7)
                    self.assertIn(expected_path, output)
                    skills = project / ('.agents' if agent == 'codex' else '.claude') / 'skills'
                    self.assertEqual({p.name for p in skills.iterdir()}, {
                        'ai-slop-remover', 'ui-craft-bundle', 'ui-quality-gate',
                        'ui-slop-audit', 'ui-visual-refine', 'ux-flow-refine', 'ux-writing'})
                    installed = snapshot(project)
                    for options in ((), ('--dry-run',), ('--status',)):
                        code, output, error = self.run_installer(project, agent, encoding, *options)
                        self.assertEqual((code, error), (0, ''), output + error)
                        self.assertIn(expected_path, output)
                        self.assertEqual(installed, snapshot(project))

    def test_unicode_conflict_keeps_user_files_and_reports_a_readable_error(self):
        project = self.root / '사용자 프로젝트'
        conflict = project / '.agents/skills/ui-craft-bundle'
        conflict.mkdir(parents=True)
        (conflict / 'SKILL.md').write_text('Keep user content.', encoding='utf-8')
        before = snapshot(project)
        code, output, error = self.run_installer(project, 'codex', 'cp1252')
        self.assertEqual((code, output), (1, ''))
        self.assertIn(str(conflict).encode('cp1252', 'backslashreplace').decode('cp1252'), error)
        self.assertNotIn('Traceback', error)
        self.assertEqual(before, snapshot(project))


if __name__ == '__main__':
    unittest.main()
