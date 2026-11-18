"""Additive Claude Code install target: identical bundle at .claude/skills; legacy target unchanged."""

from contextlib import redirect_stdout, redirect_stderr
import importlib.util
import io
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from ai_sdlc import initializer as init

LEGACY = '.agents/skills/ai-sdlc-lite'
CLAUDE = '.claude/skills/ai-sdlc-lite'


def tree(root):
    return {p.relative_to(root).as_posix(): (p.read_bytes() if p.is_file() else None)
            for p in sorted(root.rglob('*')) if '.git/' not in p.as_posix() + '/' and p.name != '.git'}


class ClaudeTargetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='ai-sdlc-claude-target-')
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name) / 'repo'
        subprocess.run(['git', 'init', '-q', str(self.repo)], check=True)
        (self.repo / 'AGENTS.md').write_text('Preserve project rules.\n')
        self.installer = init._installer()
        self.content, self.hashes = self.installer.bundle_content()

    def invoke(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err), \
                patch('subprocess.run', side_effect=AssertionError('subprocess forbidden')), \
                patch.object(socket, 'socket', side_effect=AssertionError('network forbidden')):
            code = init.main(['--repo', str(self.repo), *args])
        return code, out.getvalue(), err.getvalue()

    def uninstall(self, *args):
        spec = importlib.util.spec_from_file_location('install_skill_u', ROOT / 'scripts/install_skill.py')
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        out = io.StringIO()
        with redirect_stdout(out), redirect_stderr(out):
            code = mod.main(['--target', str(self.repo), '--uninstall', *args])
        return code, out.getvalue()

    def test_target_mapping_and_default(self):
        self.assertEqual(self.installer.SKILL.as_posix(), LEGACY)
        self.assertEqual({k: v.as_posix() for k, v in self.installer.SKILL_TARGETS.items()},
                         {'agents': LEGACY, 'claude-code': CLAUDE})

    def test_preview_writes_nothing_and_names_claude_paths(self):
        before = tree(self.repo)
        code, out, _ = self.invoke('--target', 'claude-code')
        self.assertEqual(code, 0)
        self.assertIn('RESULT: PREVIEW', out)
        self.assertIn('"%s/SKILL.md"' % CLAUDE, out)
        self.assertNotIn('"' + LEGACY + '/', out)  # the bundle's own nested reference copy is not a destination
        self.assertEqual(before, tree(self.repo))
        self.assertFalse((self.repo / '.claude').exists())

    def test_apply_installs_identical_nested_bundle_without_claude_md(self):
        self.assertEqual(self.invoke('--target', 'claude-code', '--apply')[0], 0)
        base = self.repo / CLAUDE
        self.assertEqual(len(self.content), 44)  # 43 payload files + the ownership manifest
        installed = {p.relative_to(base).as_posix() for p in base.rglob('*') if p.is_file()}
        self.assertEqual(installed, set(self.content))
        for name, data in self.content.items():
            self.assertEqual((base / name).read_bytes(), data)
        self.assertTrue((base / 'framework/AGENTS.md').is_file())
        self.assertFalse((self.repo / 'CLAUDE.md').exists())
        self.assertFalse((self.repo / '.agents').exists())
        self.assertEqual((self.repo / 'AGENTS.md').read_text(), 'Preserve project rules.\n')
        self.assertEqual(sorted(p.name for p in (self.repo / '.claude').iterdir()), ['skills'])

    def test_bundle_bytes_equal_across_targets(self):
        self.invoke('--apply')
        self.invoke('--target', 'claude-code', '--apply')
        self.assertEqual(tree(self.repo / LEGACY), tree(self.repo / CLAUDE))

    def test_default_still_installs_legacy_only(self):
        self.assertEqual(self.invoke('--apply')[0], 0)
        self.assertTrue((self.repo / LEGACY / 'SKILL.md').is_file())
        self.assertFalse((self.repo / '.claude').exists())
        self.assertEqual(self.invoke('--target', 'agents', '--check')[0], 0)

    def test_idempotent_apply_and_check_and_targets_independent(self):
        self.invoke('--target', 'claude-code', '--apply')
        before = tree(self.repo)
        self.assertEqual(self.invoke('--target', 'claude-code', '--apply')[1].splitlines()[-1], 'RESULT: UNCHANGED')
        self.assertEqual(self.invoke('--target', 'claude-code', '--check')[1].splitlines()[-1], 'RESULT: CHECK_OK')
        self.assertEqual(before, tree(self.repo))
        code, _, err = self.invoke('--check')  # legacy target is not installed
        self.assertEqual(code, 2)
        self.assertIn('installation_missing', err)

    def test_conflicts_are_refused_without_overwrite(self):
        skill = self.repo / CLAUDE
        skill.mkdir(parents=True)
        (skill / 'SKILL.md').write_text('user skill\n')
        before = tree(self.repo)
        code, _, err = self.invoke('--target', 'claude-code', '--apply')
        self.assertNotEqual(code, 0)
        self.assertIn('reason=', err)
        self.assertEqual(before, tree(self.repo))

    def test_symlinked_claude_directory_is_refused(self):
        outside = Path(self.temp.name) / 'outside'
        outside.mkdir()
        (self.repo / '.claude').symlink_to(outside, target_is_directory=True)
        code, _, _ = self.invoke('--target', 'claude-code', '--apply')
        self.assertNotEqual(code, 0)
        self.assertEqual(list(outside.iterdir()), [])

    def test_manifest_tamper_detected_by_check(self):
        self.invoke('--target', 'claude-code', '--apply')
        (self.repo / CLAUDE / 'SKILL.md').write_bytes(b'tampered\n')
        code, _, err = self.invoke('--target', 'claude-code', '--check')
        self.assertEqual(code, 2)
        self.assertIn('reason=', err)

    def test_invalid_target_and_duplicate_flag_are_usage_errors(self):
        for args in (('--target', 'codex'), ('--target',), ('--target', 'claude-code', '--target', 'agents')):
            code, _, err = self.invoke(*args)
            self.assertEqual(code, 2, args)
            self.assertIn('BLOCKED: usage', err)

    def test_uninstall_claude_target_is_clean_and_leaves_legacy(self):
        self.invoke('--apply')
        self.invoke('--target', 'claude-code', '--apply')
        legacy_before = tree(self.repo / LEGACY)
        self.assertEqual(self.uninstall('--skill-target', 'claude-code', '--dry-run')[0], 0)
        self.assertTrue((self.repo / CLAUDE / 'SKILL.md').is_file())
        self.assertEqual(self.uninstall('--skill-target', 'claude-code')[0], 0)
        self.assertFalse((self.repo / CLAUDE).exists())
        self.assertEqual(legacy_before, tree(self.repo / LEGACY))

    def test_uninstall_preserves_edited_claude_files(self):
        self.invoke('--target', 'claude-code', '--apply')
        (self.repo / CLAUDE / 'SKILL.md').write_bytes(b'edited\n')
        self.assertEqual(self.uninstall('--skill-target', 'claude-code')[0], 1)
        self.assertEqual((self.repo / CLAUDE / 'SKILL.md').read_bytes(), b'edited\n')

    def test_skill_target_flag_requires_uninstall(self):
        spec = importlib.util.spec_from_file_location('install_skill_v', ROOT / 'scripts/install_skill.py')
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        out = io.StringIO()
        with redirect_stdout(out), redirect_stderr(out):
            code = mod.main(['--target', str(self.repo), '--skill-target', 'claude-code', '--dry-run'])
        self.assertEqual(code, 1)
        self.assertFalse((self.repo / '.claude').exists())


if __name__ == '__main__':
    unittest.main()
