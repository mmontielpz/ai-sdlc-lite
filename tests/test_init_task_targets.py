"""--init-task resolves the installed Skill target (legacy, Claude Code, both) and fails closed otherwise."""

from contextlib import redirect_stdout, redirect_stderr
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from ai_sdlc import initializer as init

spec = importlib.util.spec_from_file_location('install_skill_f1', ROOT / 'scripts/install_skill.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)

LEGACY = '.agents/skills/ai-sdlc-lite'
CLAUDE = '.claude/skills/ai-sdlc-lite'


def snapshot(root):
    return {p.relative_to(root).as_posix(): (p.read_bytes() if p.is_file() else None)
            for p in sorted(root.rglob('*')) if '.git' not in p.relative_to(root).parts}


class InitTaskTargetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='ai-sdlc-f1-')
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name) / 'repo'
        subprocess.run(['git', 'init', '-q', str(self.repo)], check=True)

    def install(self, *targets):
        for target in targets:
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(init.main(['--repo', str(self.repo), '--target', target, '--apply']), 0)

    def init_task(self, *extra, task='DEMO'):
        out = io.StringIO()
        with redirect_stdout(out), redirect_stderr(out):
            code = installer.main(['--target', str(self.repo), '--init-task', task, *extra])
        return code, out.getvalue()

    def assert_refused_without_writes(self, *extra, text=None):
        before = snapshot(self.repo)
        code, out = self.init_task(*extra)
        self.assertEqual(code, 1, out)
        if text:
            self.assertIn(text, out)
        self.assertEqual(before, snapshot(self.repo))
        self.assertFalse((self.repo / '.ai-sdlc-lite').exists())
        self.assertFalse((self.repo / 'tasks').exists())

    def readme_link_target(self):
        text = (self.repo / 'tasks/DEMO/CHECKLIST.md').read_text()
        # the shared README link is rebased onto the selected installed bundle
        links = [l for l in text.split('](')[1:] if l.split(')')[0].endswith('framework/README.md')]
        self.assertTrue(links, text)
        link = links[0].split(')')[0]
        self.assertTrue((self.repo / 'tasks/DEMO' / link).resolve().is_file())
        return link

    def test_claude_only_installation_is_accepted(self):
        self.install('claude-code')
        self.assertEqual(self.init_task('--dry-run')[0], 0)
        self.assertFalse((self.repo / 'tasks').exists())
        code, out = self.init_task()
        self.assertEqual(code, 0, out)
        self.assertIn('**Decision:** PENDING', (self.repo / 'tasks/DEMO/TASK.md').read_text())
        self.assertIn(CLAUDE, self.readme_link_target())
        self.assertFalse((self.repo / '.agents').exists())
        self.assertFalse((self.repo / 'CLAUDE.md').exists())
        context = json.loads((self.repo / '.ai-sdlc-lite/task-context.json').read_text())
        self.assertEqual(context['contract'], 'tasks/DEMO/TASK.md')

    def test_legacy_only_installation_still_works_and_is_unchanged(self):
        self.install('agents')
        code, out = self.init_task()
        self.assertEqual(code, 0, out)
        self.assertIn(LEGACY, self.readme_link_target())
        self.assertFalse((self.repo / '.claude').exists())

    def test_both_valid_targets_prefer_legacy_deterministically(self):
        self.install('agents', 'claude-code')
        self.assertEqual(self.init_task()[0], 0)
        first = (self.repo / 'tasks/DEMO/CHECKLIST.md').read_bytes()
        self.assertIn(LEGACY, self.readme_link_target())
        self.assertEqual(self.init_task()[0], 0)  # idempotent re-run
        self.assertEqual(first, (self.repo / 'tasks/DEMO/CHECKLIST.md').read_bytes())

    def test_neither_installation_is_refused(self):
        self.assert_refused_without_writes(text='Install the project Skill')

    def test_tampered_claude_installation_is_refused(self):
        self.install('claude-code')
        (self.repo / CLAUDE / 'framework/README.md').write_bytes(b'tampered\n')
        self.assert_refused_without_writes(text='differs from its ownership manifest')

    def test_partial_claude_installation_is_refused(self):
        self.install('claude-code')
        (self.repo / CLAUDE / 'framework/WORKFLOW.md').unlink()
        self.assert_refused_without_writes()

    def test_extra_file_in_claude_installation_is_refused(self):
        self.install('claude-code')
        (self.repo / CLAUDE / 'extra.md').write_text('x\n')
        self.assert_refused_without_writes(text='differs from its ownership manifest')

    def test_bare_directory_without_manifest_is_refused(self):
        (self.repo / CLAUDE / 'framework').mkdir(parents=True)
        (self.repo / CLAUDE / 'framework/README.md').write_text('forged\n')
        self.assert_refused_without_writes(text='ownership manifest')

    def test_invalid_claude_target_is_refused_even_if_legacy_is_valid(self):
        self.install('agents', 'claude-code')
        (self.repo / CLAUDE / 'SKILL.md').write_bytes(b'tampered\n')
        self.assert_refused_without_writes(text='differs from its ownership manifest')

    def test_symlinked_destination_is_refused(self):
        outside = Path(self.temp.name) / 'outside'
        outside.mkdir()
        (self.repo / '.claude').symlink_to(outside, target_is_directory=True)
        before = list(outside.iterdir())
        self.assert_refused_without_writes(text='Symlink refused')
        self.assertEqual(before, list(outside.iterdir()))

    def test_bundled_task_contracts_rejected_for_both_targets(self):
        self.install('agents', 'claude-code')
        for base in ('.agents', '.claude'):
            self.assert_refused_without_writes('--task-contract', base + '/skills/ai-sdlc-lite/framework/TASK.md',
                                               text='Bundled references cannot be active task records')

    def test_bundled_task_contract_rejected_with_claude_only(self):
        self.install('claude-code')
        self.assert_refused_without_writes('--task-contract', CLAUDE + '/framework/TASK.md',
                                           text='Bundled references cannot be active task records')

    def test_existing_task_context_is_preserved_and_existing_contract_referenced(self):
        self.install('claude-code')
        (self.repo / 'TASK.md').write_text('Owner contract.\n')
        before = (self.repo / 'TASK.md').read_bytes()
        self.assertEqual(self.init_task('--task-contract', 'TASK.md', task='EXISTING')[0], 0)
        self.assertEqual(before, (self.repo / 'TASK.md').read_bytes())
        context = json.loads((self.repo / '.ai-sdlc-lite/task-context.json').read_text())
        self.assertEqual(context['contract'], 'TASK.md')
        snap = snapshot(self.repo)
        self.assertEqual(self.init_task('--task-contract', 'TASK.md', task='EXISTING')[0], 0)
        self.assertEqual(snap, snapshot(self.repo))
        self.assertEqual(self.init_task(task='OTHER')[0], 1)  # conflicting context still refused
        self.assertEqual(snap, snapshot(self.repo))


if __name__ == '__main__':
    unittest.main()
