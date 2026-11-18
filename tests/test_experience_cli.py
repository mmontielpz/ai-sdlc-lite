"""EXP-01A: `ai-sdlc experience validate`, compatibility with existing commands, and packaging layout."""

from contextlib import redirect_stderr, redirect_stdout
import hashlib
import io
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import experience_support as sup
from ai_sdlc import cli, experience
from ai_sdlc import experience_events as ev
from ai_sdlc import experience_journal as jr

ROOT = sup.ROOT
BASELINE_USAGE = (
    'usage: python3 -m ai_sdlc <command> [args]\n'
    '  verify|baseline|seal|codes   run scripts/verify_scope.py with the same arguments (verify supports --format summary|json)\n'
    '  doctor                       read-only environment and framework check\n'
    '  status [--repo PATH]         read-only HEAD and active-task report\n'
    '  adapter list|validate|matrix read-only provider adapter declarations (see adapters/README.md)\n'
    '  delivery plan|verify|report|execute|recover  delivery preflight, local commit, and observe-only recovery (docs/DELIVERY_CONTRACT.md)\n'
    '  result-template --repo PATH --out F [--baseline-record F] generate fail-closed result.json template\n'
    '  init --repo PATH            preview offline Skill setup; --apply to write; --check to verify\n'
)
# Baseline (develop @ 53e3788) digests of files EXP-01A must not touch. A deliberate future change to one of
# these files must update the constant in the same reviewed change.
UNTOUCHED = {
    'scripts/verify_scope.py': '6562aad7ec6ebcb2e5fbc6008da11a0f9d0db8959c867cc3e3a33331d494dfbb',
    '.agents/skills/ai-sdlc-lite/SKILL.md': '0d88536d85d86cf3387e2425e47321c3d2e2c69b88f58603ef0751ede9e14998',
}


class ExperienceCliCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='ai-sdlc-expcli-')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.journal = self.base / 'j.jsonl'

    def make(self, count=3):
        for _ in range(count):
            jr.append_event(str(self.journal), sup.sample('check.operator_run'), clock=sup.clock)

    def run_main(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = experience.main(list(args))
        return code, out.getvalue(), err.getvalue()

    def run_cli(self, *args, env=None, cwd=None):
        done = subprocess.run([sys.executable, '-B', '-m', 'ai_sdlc', *args], capture_output=True, text=True,
                              cwd=cwd or ROOT, env=env or dict(os.environ, PYTHONPATH=str(ROOT)))
        return done.returncode, done.stdout, done.stderr


class Validate(ExperienceCliCase):
    def test_valid_journal(self):
        self.make(3)
        before = sup.snapshot(self.base)
        code, out, err = self.run_main('validate', '--journal', str(self.journal))
        self.assertEqual((code, err), (0, ''))
        summary = jr.validate_journal(str(self.journal))
        self.assertEqual(out, 'experience journal ok: events=3 run_id=%s head=%s\n'
                              'authenticity: not verified (integrity checks only)\n' % (summary.run_id, summary.head))
        self.assertNotIn(str(self.base), out)
        self.assertEqual(before, sup.snapshot(self.base))

    def test_end_to_end_process_exit_codes(self):
        self.make(2)
        code, out, err = self.run_cli('experience', 'validate', '--journal', str(self.journal))
        self.assertEqual((code, err), (0, ''))
        self.assertIn('events=2', out)
        lines = self.journal.read_bytes().split(b'\n')[:-1]
        self.journal.write_bytes(lines[1] + b'\n')
        code, out, err = self.run_cli('experience', 'validate', '--journal', str(self.journal))
        self.assertEqual((code, out, err), (2, '', 'JOURNAL-INVALID: chain_broken line 1\n'))

    def test_each_fault_reports_only_a_code_and_line(self):
        self.make(3)
        good = self.journal.read_bytes()
        cases = (
            (good[:-1], 'truncated_journal line 3'),
            (b''.join(good.split(b'\n')[i] + b'\n' for i in (0, 2)), 'chain_broken line 2'),
            (good + b'\n', 'malformed_json line 4'),
            (good + b'{"a":1,"a":2}\n', 'duplicate_key line 4'),
            (good.replace(b'"exit_code":0', b'"exit_code":7', 1), 'id_mismatch line 1'),
            (b'x' * (ev.MAX_JOURNAL_BYTES + 1), 'journal_full'),
        )
        for data, expected in cases:
            self.journal.write_bytes(data)
            code, out, err = self.run_main('validate', '--journal', str(self.journal))
            self.assertEqual((code, out, err), (2, '', 'JOURNAL-INVALID: %s\n' % expected), expected)

    def test_hostile_content_is_never_echoed(self):
        self.make(1)
        hostile = b'IGNORE-PREVIOUS-INSTRUCTIONS $(touch pwned) <script>alert(1)</script>'
        line = self.journal.read_bytes().replace(b'"V-1"', b'"' + hostile + b'"')
        self.journal.write_bytes(line)
        code, out, err = self.run_main('validate', '--journal', str(self.journal))
        self.assertEqual(code, 2)
        self.assertEqual(out, '')
        for fragment in ('IGNORE', 'pwned', 'script', str(self.base)):
            self.assertNotIn(fragment, err)
        self.assertFalse((self.base / 'pwned').exists())

    def test_unexpected_errors_fail_closed_without_text(self):
        self.make(1)
        with mock.patch.object(jr, 'validate_journal', side_effect=RuntimeError('SECRET-DETAIL')):
            code, out, err = self.run_main('validate', '--journal', str(self.journal))
        self.assertEqual((code, out, err), (2, '', 'JOURNAL-INVALID: validation_or_io_failure\n'))

    def test_missing_and_unsafe_paths(self):
        code, _, err = self.run_main('validate', '--journal', str(self.base / 'absent.jsonl'))
        self.assertEqual((code, err), (2, 'JOURNAL-INVALID: journal_missing\n'))
        (self.base / 'link.jsonl').symlink_to(self.base / 'absent.jsonl')
        code, _, err = self.run_main('validate', '--journal', str(self.base / 'link.jsonl'))
        self.assertEqual((code, err), (2, 'JOURNAL-INVALID: journal_invalid_path\n'))

    def test_usage_errors_write_nothing(self):
        for args in ((), ('validate',), ('validate', '--journal'), ('validate', '--journal', '--journal', 'x'),
                     ('validate', '--journal', 'a', '--journal', 'b'), ('validate', '--bogus', 'x'),
                     ('validate', 'extra'), ('frobnicate',), ('validate', '--journal', 'a', 'b'),
                     ('record',), ('export',)):
            before = sup.snapshot(self.base)
            code, out, err = self.run_main(*args)
            self.assertEqual((code, out), (2, ''), args)
            self.assertTrue(err.startswith('BLOCKED: usage\n'), args)
            self.assertEqual(before, sup.snapshot(self.base))
        for args in (('--help',), ('-h',), ('validate', '--help')):
            code, out, err = self.run_main(*args)
            self.assertEqual((code, err), (0, ''))
            self.assertIn('EXPERIMENTAL', out)


class CompatibilityAndPackaging(ExperienceCliCase):
    def test_top_level_usage_gains_exactly_one_line(self):  # CP-01
        lines = cli.USAGE.splitlines(keepends=True)
        added = [line for line in lines if line.lstrip().startswith('experience')]
        self.assertEqual(len(added), 1)
        self.assertEqual(''.join(line for line in lines if line not in added), BASELINE_USAGE)
        self.assertEqual(self.run_cli('--help')[1], cli.USAGE)

    def test_other_commands_never_import_the_experience_modules(self):  # CP-05, S-12
        script = ('import sys\nfrom ai_sdlc import cli\n'
                  'for argv in (["doctor"], ["init", "--help"], ["adapter", "list"], ["--help"]):\n'
                  '    cli.main(argv)\n'
                  'print(sorted(m for m in sys.modules if "experience" in m))\n')
        done = subprocess.run([sys.executable, '-B', '-c', script], capture_output=True, text=True, cwd=ROOT,
                              env=dict(os.environ, PYTHONPATH=str(ROOT)))
        self.assertEqual(done.stdout.strip().splitlines()[-1], '[]', done.stdout + done.stderr)
        used = subprocess.run([sys.executable, '-B', '-c', 'import sys\nfrom ai_sdlc import cli\n'
                               'cli.main(["experience", "--help"])\n'
                               'print(sorted(m for m in sys.modules if "experience" in m))\n'],
                              capture_output=True, text=True, cwd=ROOT, env=dict(os.environ, PYTHONPATH=str(ROOT)))
        self.assertIn('ai_sdlc.experience', used.stdout)

    def test_a_corrupt_journal_cannot_affect_other_commands(self):  # S-11
        self.journal.write_bytes(b'garbage\n')
        before = self.journal.read_bytes()
        for args in (('doctor',), ('codes',), ('adapter', 'list')):
            code, out, err = self.run_cli(*args)
            self.assertEqual(code, 0, (args, err))
        self.assertEqual(before, self.journal.read_bytes())
        sources = [(ROOT / 'ai_sdlc' / name).read_text(encoding='utf-8') for name in os.listdir(ROOT / 'ai_sdlc')
                   if name.endswith('.py') and not name.startswith('experience')]
        for text in sources:
            self.assertNotIn('experience_journal', text)
            self.assertNotIn('experience_events', text)

    def test_verifier_and_skill_are_untouched(self):  # S-13, CP-02
        for relative, digest in UNTOUCHED.items():
            self.assertEqual(hashlib.sha256((ROOT / relative).read_bytes()).hexdigest(), digest, relative)

    def test_installed_layout_validates_without_a_source_checkout(self):  # clean install / packaging
        site = self.base / 'site-packages'
        shutil.copytree(ROOT / 'ai_sdlc', site / 'ai_sdlc', ignore=shutil.ignore_patterns('__pycache__', '_framework'))
        (site / 'ai_sdlc' / '_framework' / 'scripts').mkdir(parents=True)
        shutil.copy2(ROOT / 'scripts' / 'verify_scope.py', site / 'ai_sdlc' / '_framework' / 'scripts')
        for name in ('experience_events', 'experience_journal', 'experience'):
            self.assertTrue((site / 'ai_sdlc' / (name + '.py')).is_file())
        # a verify.completed event needs the registry, which is loaded from the installed framework data
        jr.append_event(str(self.journal), sup.sample('verify.completed'), clock=sup.clock)
        self.make(2)
        env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
        env['PYTHONPATH'] = str(site)
        code, out, err = self.run_cli('experience', 'validate', '--journal', str(self.journal), env=env,
                                      cwd=str(self.base))
        self.assertEqual((code, err), (0, ''), out)
        self.assertIn('events=3', out)
        probe = subprocess.run([sys.executable, '-B', '-c', 'import ai_sdlc, sys; print(ai_sdlc.__file__)'],
                               capture_output=True, text=True, cwd=str(self.base), env=env)
        self.assertTrue(probe.stdout.strip().startswith(str(site)), probe.stdout)


if __name__ == '__main__':
    unittest.main()
