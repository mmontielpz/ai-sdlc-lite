"""Tests for V1-S1 first-five-minutes packaging, quickstart, and example flow."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from ai_sdlc import cli

ROOT = Path(__file__).resolve().parent.parent
EXAMPLE = ROOT / 'examples' / 'first-five-minutes'


class FirstFiveMinutesTests(unittest.TestCase):
    def test_pyproject_metadata_is_zero_dependency_and_exposes_entrypoint(self):
        text = (ROOT / 'pyproject.toml').read_text(encoding='utf-8')
        self.assertIn('name = "ai-sdlc-lite"', text)
        self.assertIn('requires-python = ">=3.9"', text)
        self.assertIn('dependencies = []', text)
        self.assertIn('ai-sdlc = "ai_sdlc.cli:main"', text)
        self.assertIn('ai_sdlc._framework', text)

    def test_quickstart_and_example_files_exist(self):
        self.assertTrue((ROOT / 'docs' / 'QUICKSTART.md').is_file())
        for rel in ('README.md', 'src/greeter.py', 'tests/test_greeter.py', 'result.pass.json', 'result.blocked.json'):
            self.assertTrue((EXAMPLE / rel).is_file(), f'missing {rel}')

    def test_cli_entrypoint_callable_directly(self):
        self.assertEqual(cli.main(['--help']), 0)

    def test_first_five_minutes_pass_and_blocked_end_to_end(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo = tmp_path / 'repo'
            evidence = tmp_path / 'evidence'
            evidence.mkdir()
            shutil.copytree(EXAMPLE, repo)

            env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
            env['HOME'] = str(tmp_path / 'home')
            Path(env['HOME']).mkdir()

            subprocess.run(['git', '-C', str(repo), 'init', '-q'], env=env, check=True)
            subprocess.run(['git', '-C', str(repo), 'config', 'user.name', 'Example User'], env=env, check=True)
            subprocess.run(['git', '-C', str(repo), 'config', 'user.email', 'example@example.invalid'], env=env, check=True)

            init_apply = subprocess.run([sys.executable, '-B', '-m', 'ai_sdlc', 'init', '--repo', str(repo), '--apply'],
                                        cwd=ROOT, env=env, capture_output=True, text=True)
            self.assertEqual(init_apply.returncode, 0, init_apply.stderr)
            self.assertIn('RESULT: INITIALIZED', init_apply.stdout)

            init_check = subprocess.run([sys.executable, '-B', '-m', 'ai_sdlc', 'init', '--repo', str(repo), '--check'],
                                        cwd=ROOT, env=env, capture_output=True, text=True)
            self.assertEqual(init_check.returncode, 0, init_check.stderr)
            self.assertIn('RESULT: CHECK_OK', init_check.stdout)

            subprocess.run(['git', '-C', str(repo), 'add', '.'], env=env, check=True)
            subprocess.run(['git', '-C', str(repo), 'commit', '-q', '-m', 'Initial baseline'], env=env, check=True)
            base_sha = subprocess.run(['git', '-C', str(repo), 'rev-parse', 'HEAD'],
                                      env=env, capture_output=True, text=True, check=True).stdout.strip()

            doctor = subprocess.run([sys.executable, '-B', '-m', 'ai_sdlc', 'doctor'],
                                    cwd=ROOT, env=env, capture_output=True, text=True)
            self.assertEqual(doctor.returncode, 0, doctor.stderr)

            status = subprocess.run([sys.executable, '-B', '-m', 'ai_sdlc', 'status', '--repo', str(repo)],
                                    cwd=ROOT, env=env, capture_output=True, text=True)
            self.assertEqual(status.returncode, 0, status.stderr)
            self.assertIn(base_sha, status.stdout)

            greeter = repo / 'src' / 'greeter.py'
            greeter.write_text(greeter.read_text(encoding='utf-8').replace('name.strip()', '(name or "").strip()'),
                               encoding='utf-8')
            test_run = subprocess.run([sys.executable, '-B', '-m', 'unittest', 'discover', '-s', 'tests'],
                                      cwd=repo, env=env, capture_output=True, text=True)
            self.assertEqual(test_run.returncode, 0, test_run.stderr)
            (evidence / 'out.txt').write_text(test_run.stdout + test_run.stderr, encoding='utf-8')

            pass_data = json.loads((repo / 'result.pass.json').read_text(encoding='utf-8'))
            pass_data['baseline_sha'] = base_sha
            pass_file = evidence / 'result.pass.json'
            pass_file.write_text(json.dumps(pass_data, indent=2), encoding='utf-8')

            pass_verify = subprocess.run([sys.executable, '-B', '-m', 'ai_sdlc', 'verify', '--repo', str(repo),
                                          '--result', str(pass_file)],
                                         cwd=ROOT, env=env, capture_output=True, text=True)
            self.assertEqual(pass_verify.returncode, 0, pass_verify.stdout + pass_verify.stderr)
            pass_report = json.loads(pass_verify.stdout)
            self.assertEqual(pass_report['status'], 'PASS')

            blocked_data = json.loads((repo / 'result.blocked.json').read_text(encoding='utf-8'))
            blocked_data['baseline_sha'] = base_sha
            blocked_file = evidence / 'result.blocked.json'
            blocked_file.write_text(json.dumps(blocked_data, indent=2), encoding='utf-8')

            blocked_verify = subprocess.run([sys.executable, '-B', '-m', 'ai_sdlc', 'verify', '--repo', str(repo),
                                             '--result', str(blocked_file)],
                                            cwd=ROOT, env=env, capture_output=True, text=True)
            self.assertEqual(blocked_verify.returncode, 2, blocked_verify.stdout + blocked_verify.stderr)
            blocked_report = json.loads(blocked_verify.stdout)
            self.assertEqual(blocked_report['status'], 'BLOCKED')
            codes = {item['code'] for item in blocked_report['failure_reasons']}
            self.assertIn('out_of_scope_modification', codes)
            self.assertIn('declared_mismatch', codes)

    def test_installed_package_layout_works_without_source_checkout(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            site_pkg = tmp_path / 'site-packages'
            shutil.copytree(ROOT / 'ai_sdlc', site_pkg / 'ai_sdlc')
            framework_dst = site_pkg / 'ai_sdlc' / '_framework'
            # Mirror the runtime directories/files declared for packaging in pyproject.toml.
            for folder in ('scripts', 'templates', '.agents', 'adapters', 'docs', 'examples', 'tasks'):
                shutil.copytree(ROOT / folder, framework_dst / folder)
            for item in ROOT.iterdir():
                if item.is_file() and (item.suffix == '.md' or item.name == 'LICENSE'):
                    shutil.copy2(item, framework_dst / item.name)

            repo = tmp_path / 'ext_repo'
            repo.mkdir()
            env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
            env['PYTHONPATH'] = str(site_pkg)
            subprocess.run(['git', '-C', str(repo), 'init', '-q'], env=env, check=True)

            doctor = subprocess.run([sys.executable, '-B', '-m', 'ai_sdlc', 'doctor'],
                                    cwd=tmp_path, env=env, capture_output=True, text=True)
            self.assertEqual(doctor.returncode, 0, doctor.stdout + doctor.stderr)

            init_preview = subprocess.run([sys.executable, '-B', '-m', 'ai_sdlc', 'init', '--repo', str(repo)],
                                          cwd=tmp_path, env=env, capture_output=True, text=True)
            self.assertEqual(init_preview.returncode, 0, init_preview.stdout + init_preview.stderr)
            self.assertIn('RESULT: PREVIEW', init_preview.stdout)
