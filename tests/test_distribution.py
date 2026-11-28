"""Distribution checks: the wheel must carry everything `init` needs, and the CLI must be discoverable."""

import importlib.util
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import install_skill as installer  # noqa: E402


def package_data_globs():
    """Globs of ai_sdlc._framework from pyproject.toml (tomllib is unavailable on Python 3.9)."""
    text = (ROOT / 'pyproject.toml').read_text(encoding='utf-8')
    block = re.search(r'\[tool\.setuptools\.package-data\]\s*"ai_sdlc\._framework"\s*=\s*\[(.*?)\n\]', text, re.S)
    assert block, 'package-data block not found'
    return re.findall(r'"([^"]+)"', block.group(1))


def covered(name, globs):
    for pattern in globs:
        if '/' not in pattern and '/' not in name and Path(name).match(pattern):
            return True
        if '/' in pattern and len(Path(name).parts) == len(Path(pattern).parts) and Path(name).match(pattern):
            return True
    return False


class PackageDataTests(unittest.TestCase):
    def test_every_bundled_framework_file_is_packaged(self):
        content, _ = installer.bundle_content()
        names = sorted(n[len('framework/'):] for n in content if n.startswith('framework/'))
        self.assertGreater(len(names), 30)
        globs = package_data_globs()
        # RESULT.md in the bundle is the reusable template, packaged as templates/RESULT.md.
        missing = [n for n in names if n != 'RESULT.md' and not covered(n, globs)]
        self.assertEqual(missing, [], 'bundle files absent from pyproject package-data')
        self.assertTrue(covered('templates/RESULT.md', globs))

    def test_scripts_the_cli_executes_are_packaged(self):
        globs = package_data_globs()
        for name in ('scripts/verify_scope.py', 'scripts/install_skill.py', '.agents/skills/ai-sdlc-lite/SKILL.md'):
            self.assertTrue(covered(name, globs), name)


class VersionAndSkillTests(unittest.TestCase):
    def run_cli(self, *args):
        env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
        return subprocess.run([sys.executable, '-B', '-m', 'ai_sdlc', *args], cwd=ROOT, env=env,
                              capture_output=True, text=True)

    def test_version_flag(self):
        for flag in ('--version', '-V', 'version'):
            done = self.run_cli(flag)
            self.assertEqual(done.returncode, 0, done.stderr)
            self.assertRegex(done.stdout, r'^ai-sdlc \S+ \((source tree|installed package ai-sdlc-lite)\)\n$')
            self.assertEqual(done.stderr, '')
        self.assertEqual(self.run_cli('--version', 'extra').returncode, 2)
        self.assertIn('--version', self.run_cli('--help').stdout)

    def test_version_matches_pyproject_and_package_init(self):
        import ai_sdlc
        pyproject = (ROOT / 'pyproject.toml').read_text(encoding='utf-8')
        match = re.search(r'^version\s*=\s*"([^"]+)"', pyproject, re.M)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), ai_sdlc.__version__)
        done = self.run_cli('--version')
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertTrue(done.stdout.startswith(f'ai-sdlc {ai_sdlc.__version__} '), done.stdout)

    def test_skill_names_the_cli_and_forbids_self_install(self):
        skill = (ROOT / installer.SKILL / 'SKILL.md').read_text(encoding='utf-8')
        for needle in ('ai-sdlc doctor', 'pip install --no-index --no-deps', 'Do not install packages',
                       'result-template', 'init --repo . --check'):
            self.assertIn(needle, skill)

    def test_quickstart_documents_offline_wheel_install(self):
        guide = (ROOT / 'docs' / 'QUICKSTART.md').read_text(encoding='utf-8')
        self.assertIn('pip wheel --no-build-isolation --no-deps', guide)
        self.assertIn('pip install --no-index --no-deps', guide)

    def test_skill_install_guidance_does_not_depend_on_unbundled_files(self):
        content, _ = installer.bundle_content()
        skill = content['SKILL.md'].decode('utf-8')
        self.assertNotIn('framework/docs/QUICKSTART.md', skill)
        self.assertIn('pip install --no-index --no-deps', skill)  # inline, because QUICKSTART is not in the bundle


@unittest.skipUnless(importlib.util.find_spec('setuptools'), 'setuptools is required to build the wheel')
class BuiltWheelTests(unittest.TestCase):
    def test_wheel_installs_the_skill_without_the_checkout(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            source = tmp / 'src'
            shutil.copytree(ROOT, source, ignore=shutil.ignore_patterns('.git', '__pycache__', 'build', '*.egg-info', 'dist'))
            built = subprocess.run([sys.executable, '-m', 'pip', 'wheel', '--no-build-isolation', '--no-deps',
                                    '-q', '-w', str(tmp / 'dist'), str(source)], capture_output=True, text=True)
            if built.returncode != 0:
                self.skipTest('wheel build unavailable: ' + built.stderr[-200:])
            wheel = next((tmp / 'dist').glob('*.whl'))
            site = tmp / 'site'
            with zipfile.ZipFile(wheel) as archive:
                self.assertEqual([n for n in archive.namelist() if 'website' in n or 'node_modules' in n], [])
                archive.extractall(site)
            shutil.rmtree(source)  # nothing of the checkout may remain reachable
            repo = tmp / 'project'
            repo.mkdir()
            env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
            env['PYTHONPATH'] = str(site)
            subprocess.run(['git', '-C', str(repo), 'init', '-q'], env=env, check=True)
            for command in (['doctor'], ['--version'],
                            ['init', '--repo', str(repo), '--target', 'claude-code', '--apply'],
                            ['init', '--repo', str(repo), '--target', 'claude-code', '--check']):
                done = subprocess.run([sys.executable, '-B', '-m', 'ai_sdlc', *command], cwd=tmp, env=env,
                                      capture_output=True, text=True)
                self.assertEqual(done.returncode, 0, ' '.join(command) + done.stdout + done.stderr)
            self.assertTrue((repo / '.claude' / 'skills' / 'ai-sdlc-lite' / 'SKILL.md').is_file())


if __name__ == '__main__':
    unittest.main()
