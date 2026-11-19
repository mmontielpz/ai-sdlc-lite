"""Targeted tests for `ai-sdlc result-template`."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def git(cwd, *args):
    return subprocess.run(
        ['git', '-c', 'user.name=t', '-c', 'user.email=t@example.invalid', *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def run_cli(*args):
    env = dict(os.environ)
    env['PYTHONPATH'] = str(ROOT)
    return subprocess.run(
        [sys.executable, '-B', '-m', 'ai_sdlc', *args],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )


class ResultTemplateTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        base = Path(self._tmp.name).resolve()
        self.repo = base / 'repo'
        self.meta = base / 'meta'
        self.repo.mkdir()
        self.meta.mkdir()
        git(self.repo, 'init', '-q')
        (self.repo / '.gitignore').write_text('*.log\n', encoding='utf-8')
        src = self.repo / 'src'
        src.mkdir()
        (src / 'app.py').write_text('x = 1\n', encoding='utf-8')
        git(self.repo, 'add', '-A')
        git(self.repo, 'commit', '-q', '-m', 'base')
        self.base_sha = git(self.repo, 'rev-parse', 'HEAD')
        (self.meta / 'out.txt').write_text('ok\n', encoding='utf-8')

    def test_clean_repo_and_untouched_template_cannot_pass(self):
        out = self.meta / 'result.json'
        res = run_cli('result-template', '--repo', str(self.repo), '--out', str(out))
        self.assertEqual(res.returncode, 0, res.stderr)
        data = json.loads(out.read_text(encoding='utf-8'))
        self.assertEqual(data['schema'], 'ai-sdlc-lite-result/1')
        self.assertEqual(data['baseline_sha'], self.base_sha)
        self.assertEqual(data['baseline_dirty_paths'], [])
        self.assertEqual(data['baseline_ignored_paths'], [])
        self.assertEqual(data['modified_paths'], [])
        self.assertEqual(data['verification'], [])
        self.assertEqual(data['claimed_status'], 'BLOCKED')
        self.assertEqual(data['execution_state'], 'in_progress')
        self.assertEqual(data['allowed_paths'], ['REPLACE-WITH-ALLOWED-GLOB'])

        verify = run_cli('verify', '--repo', str(self.repo), '--result', str(out))
        self.assertEqual(verify.returncode, 2)
        report = json.loads(verify.stdout)
        self.assertEqual(report['status'], 'BLOCKED')
        codes = {r['code'] for r in report['failure_reasons']}
        self.assertIn('missing_evidence', codes)
        self.assertIn('incomplete_execution', codes)
        self.assertEqual(git(self.repo, 'status', '--porcelain'), '')

    def test_dirty_repo_and_ignored_files(self):
        (self.repo / 'src' / 'app.py').write_text('x = 2\n', encoding='utf-8')
        (self.repo / 'debug.log').write_text('ignored\n', encoding='utf-8')
        out = self.meta / 'dirty_result.json'
        res = run_cli('result-template', '--repo', str(self.repo), '--out', str(out))
        self.assertEqual(res.returncode, 0, res.stderr)
        data = json.loads(out.read_text(encoding='utf-8'))
        self.assertEqual(data['baseline_dirty_paths'], ['src/app.py'])
        self.assertEqual(data['modified_paths'], ['src/app.py'])
        self.assertEqual(data['baseline_ignored_paths'], ['debug.log'])

    def test_valid_baseline_record_and_completed_template_verifies_pass(self):
        baseline_out = self.meta / 'baseline.json'
        base_res = run_cli('baseline', '--repo', str(self.repo), '--out', str(baseline_out))
        self.assertEqual(base_res.returncode, 0, base_res.stderr)

        (self.repo / 'src' / 'app.py').write_text('x = 2\n', encoding='utf-8')
        out = self.meta / 'result.json'
        tpl_res = run_cli(
            'result-template', '--repo', str(self.repo),
            '--out', str(out), '--baseline-record', str(baseline_out),
        )
        self.assertEqual(tpl_res.returncode, 0, tpl_res.stderr)
        data = json.loads(out.read_text(encoding='utf-8'))
        self.assertEqual(data['baseline_sha'], self.base_sha)
        self.assertEqual(data['baseline_dirty_paths'], [])
        self.assertEqual(data['modified_paths'], ['src/app.py'])

        # Untouched template still fails closed as BLOCKED.
        self.assertEqual(
            run_cli('verify', '--repo', str(self.repo), '--result', str(out), '--baseline-record', str(baseline_out)).returncode,
            2,
        )

        # Complete only the developer/agent-supplied fields and verify PASS.
        data['task_id'] = 'TPL-1'
        data['allowed_paths'] = ['src/**']
        data['verification'] = [{'command': 'python3 -m unittest', 'exit_code': 0, 'evidence': 'out.txt'}]
        data['claimed_status'] = 'PASS'
        data['execution_state'] = 'complete'
        completed = self.meta / 'completed.json'
        completed.write_text(json.dumps(data), encoding='utf-8')

        verify = run_cli(
            'verify', '--repo', str(self.repo),
            '--result', str(completed), '--baseline-record', str(baseline_out),
        )
        self.assertEqual(verify.returncode, 0, verify.stdout)
        self.assertEqual(json.loads(verify.stdout)['status'], 'PASS')

    def test_invalid_missing_and_mismatched_baseline_fail_closed(self):
        missing = self.meta / 'no_such_baseline.json'
        out = self.meta / 'r1.json'
        self.assertEqual(
            run_cli('result-template', '--repo', str(self.repo), '--out', str(out), '--baseline-record', str(missing)).returncode,
            2,
        )
        self.assertFalse(out.exists())

        tampered = self.meta / 'tampered_baseline.json'
        self.assertEqual(run_cli('baseline', '--repo', str(self.repo), '--out', str(tampered)).returncode, 0)
        obj = json.loads(tampered.read_text(encoding='utf-8'))
        obj['baseline_dirty_paths'] = ['src/app.py']
        tampered.write_text(json.dumps(obj), encoding='utf-8')
        out2 = self.meta / 'r2.json'
        res2 = run_cli('result-template', '--repo', str(self.repo), '--out', str(out2), '--baseline-record', str(tampered))
        self.assertEqual(res2.returncode, 2)
        self.assertIn('BLOCKED', res2.stderr)
        self.assertFalse(out2.exists())

        # Baseline record from an unrelated repository commit -> baseline mismatch -> BLOCKED.
        other = self.meta / 'other_repo'
        other.mkdir()
        git(other, 'init', '-q')
        (other / 'f.txt').write_text('other\n', encoding='utf-8')
        git(other, 'add', '-A')
        git(other, 'commit', '-q', '-m', 'other')
        other_baseline = self.meta / 'other_baseline.json'
        self.assertEqual(run_cli('baseline', '--repo', str(other), '--out', str(other_baseline)).returncode, 0)
        out3 = self.meta / 'r3.json'
        res3 = run_cli('result-template', '--repo', str(self.repo), '--out', str(out3), '--baseline-record', str(other_baseline))
        self.assertEqual(res3.returncode, 2)
        self.assertFalse(out3.exists())

    def test_existing_output_and_invalid_destinations_fail_closed(self):
        existing = self.meta / 'existing.json'
        existing.write_text('KEEP_ME\n', encoding='utf-8')
        res_exist = run_cli('result-template', '--repo', str(self.repo), '--out', str(existing))
        self.assertEqual(res_exist.returncode, 2)
        self.assertEqual(existing.read_text(encoding='utf-8'), 'KEEP_ME\n')

        inside_repo = self.repo / 'result.json'
        res_inside = run_cli('result-template', '--repo', str(self.repo), '--out', str(inside_repo))
        self.assertEqual(res_inside.returncode, 2)
        self.assertFalse(inside_repo.exists())

        missing_parent = self.meta / 'no_such_dir' / 'result.json'
        res_parent = run_cli('result-template', '--repo', str(self.repo), '--out', str(missing_parent))
        self.assertEqual(res_parent.returncode, 2)

        symlink_out = self.meta / 'sym_result.json'
        symlink_out.symlink_to(self.meta / 'target.json')
        res_sym = run_cli('result-template', '--repo', str(self.repo), '--out', str(symlink_out))
        self.assertEqual(res_sym.returncode, 2)
        self.assertFalse((self.meta / 'target.json').exists())


class WebsiteGeneratedArtifactTests(unittest.TestCase):
    """Website dogfood friction W-1 (build output) and W-2 (very large result contract), on a synthetic project."""

    PKG_FILES = 1500

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        base = Path(self._tmp.name).resolve()
        self.repo, self.meta = base / 'repo', base / 'meta'
        self.repo.mkdir()
        self.meta.mkdir()
        git(self.repo, 'init', '-q')
        (self.repo / '.gitignore').write_text('node_modules/\ndist/\n*.env\n', encoding='utf-8')
        (self.repo / 'web' / 'src').mkdir(parents=True)
        (self.repo / 'web' / 'src' / 'app.js').write_text('v1\n', encoding='utf-8')
        git(self.repo, 'add', '-A')
        git(self.repo, 'commit', '-q', '-m', 'base')
        for index in range(self.PKG_FILES):  # a dependency folder: thousands of ignored files
            package = self.repo / 'web' / 'node_modules' / ('pkg%d' % index)
            package.mkdir(parents=True)
            (package / 'index.js').write_text('x\n', encoding='utf-8')
        (self.repo / 'web' / 'dist').mkdir()
        (self.repo / 'web' / 'dist' / 'old.js').write_text('old\n', encoding='utf-8')
        (self.meta / 'out.txt').write_text('ok\n', encoding='utf-8')
        self.record = self.meta / 'baseline.json'
        self.assertEqual(run_cli('baseline', '--repo', str(self.repo), '--out', str(self.record)).returncode, 0)

    def template(self, name='result.json', record=True):
        out = self.meta / name
        args = ['result-template', '--repo', str(self.repo), '--out', str(out)]
        if record:
            args += ['--baseline-record', str(self.record)]
        res = run_cli(*args)
        self.assertEqual(res.returncode, 0, res.stderr)
        return res, out, json.loads(out.read_text(encoding='utf-8'))

    def build(self, name='app.abc123.js'):
        """What `npm run build` does: rewrite the source and write a new hash-named file in the ignored output."""
        (self.repo / 'web' / 'src' / 'app.js').write_text('v2\n', encoding='utf-8')
        (self.repo / 'web' / 'dist' / name).write_text('built\n', encoding='utf-8')

    def complete(self, data, **extra):
        data = dict(data, task_id='WEB-1', allowed_paths=['web/src/**'], claimed_status='PASS',
                    modified_paths=['web/src/app.js'],
                    execution_state='complete',
                    verification=[{'command': 'npm run build', 'exit_code': 0, 'evidence': 'out.txt'}])
        data.update(extra)
        path = self.meta / 'completed.json'
        if path.exists():
            path.unlink()
        path.write_text(json.dumps(data), encoding='utf-8')
        return path

    def verify(self, path, record=True):
        args = ['verify', '--repo', str(self.repo), '--result', str(path)]
        if record:
            args += ['--baseline-record', str(self.record)]
        res = run_cli(*args)
        report = json.loads(res.stdout)
        return report['status'], {r['code'] for r in report['failure_reasons']}, [r['detail'] for r in report['failure_reasons']]

    def test_w2_template_with_a_record_is_compact_and_summarizes_ignored_directories(self):
        res, out, data = self.template()
        self.assertNotIn('baseline_ignored_paths', data)  # the verifier reads the list from the record
        self.assertLess(out.stat().st_size, 4000)
        self.assertGreater(self.record.stat().st_size, 50000)  # the record keeps the complete list
        recorded = json.loads(self.record.read_text(encoding='utf-8'))
        self.assertEqual(len(recorded['baseline_ignored_paths']), self.PKG_FILES + 1)
        lines = res.stdout.splitlines()
        self.assertTrue(lines[0].startswith('wrote result template to '))
        self.assertIn('ignored paths at baseline: web/node_modules (1500), web/dist (1)', res.stdout)
        self.assertIn('ignorable_paths', res.stdout)
        self.assertIn('ignored_path_unapproved', res.stdout)

    def test_template_without_a_record_still_embeds_the_baseline_list(self):
        res, out, data = self.template('norecord.json', record=False)
        self.assertEqual(len(data['baseline_ignored_paths']), self.PKG_FILES + 1)  # the only baseline in that mode
        self.assertEqual(res.stdout.strip().splitlines()[0][:24], 'wrote result template to')
        self.assertEqual(len(res.stdout.strip().splitlines()), 1)

    def test_w1_undeclared_build_output_blocks_and_declaring_the_directory_passes(self):
        _res, _out, data = self.template()
        self.build()
        status, codes, details = self.verify(self.complete(data))
        self.assertEqual(status, 'BLOCKED')
        self.assertIn('ignored_path_unapproved', codes)
        self.assertEqual([d for d in details if d.startswith('web/dist/')], ['web/dist/app.abc123.js'])
        status, codes, _details = self.verify(self.complete(data, ignorable_paths=['web/dist/**']))
        self.assertEqual((status, codes), ('PASS', set()))

    def test_declaring_one_directory_does_not_approve_other_new_ignored_files(self):
        _res, _out, data = self.template()
        self.build()
        (self.repo / 'web' / 'local.env').write_text('SECRET=1\n', encoding='utf-8')  # ignored by *.env
        status, codes, details = self.verify(self.complete(data, ignorable_paths=['web/dist/**']))
        self.assertEqual(status, 'BLOCKED')
        self.assertIn('ignored_path_unapproved', codes)
        self.assertEqual([d for d in details if d.endswith('.env')], ['web/local.env'])
        _status, _codes, details = self.verify(self.complete(data, ignorable_paths=['web/dist/**']))
        self.assertFalse([d for d in details if d.startswith('web/dist/')])  # the declared directory is not flagged

    def test_a_contract_copy_of_the_ignored_list_is_still_cross_checked(self):
        _res, _out, data = self.template()
        self.build()
        status, codes, _details = self.verify(self.complete(data, ignorable_paths=['web/dist/**'],
                                                            baseline_ignored_paths=[]))
        self.assertEqual(status, 'BLOCKED')
        self.assertIn('baseline_record_mismatch', codes)

    def test_compact_and_legacy_contracts_verify_identically(self):
        _res, _out, compact = self.template()
        recorded = json.loads(self.record.read_text(encoding='utf-8'))['baseline_ignored_paths']
        legacy = dict(compact, baseline_ignored_paths=recorded)  # what the old template produced
        for build_name, extra in (('a.js', {}), ('b.js', {'ignorable_paths': ['web/dist/**']})):
            self.build(build_name)
            self.assertEqual(self.verify(self.complete(compact, **extra)), self.verify(self.complete(legacy, **extra)))

    def test_a_compact_template_cannot_pass_without_its_baseline_record(self):
        _res, _out, data = self.template()
        self.build()
        status, codes, _details = self.verify(self.complete(data, ignorable_paths=['web/dist/**']), record=False)
        self.assertNotEqual(status, 'PASS')  # fail closed: the ignored baseline is unknown
        self.assertIn('ignored_baseline_unknown', codes)

    def test_ignored_summary_is_deterministic_and_bounded(self):
        from ai_sdlc.result_template import summarize_ignored
        paths = ['a/b/c.js', 'a/b/d.js', 'a/x.js', 'top.log', 'z/y/1', 'z/y/2', 'z/y/3'] + ['d%d/e/f' % i for i in range(10)]
        listed, more = summarize_ignored(paths, limit=4)
        self.assertEqual(listed, [('z/y', 3), ('a/b', 2), ('.', 1), ('a', 1)])
        self.assertEqual(more, 10)
        self.assertEqual(summarize_ignored(list(reversed(paths)), limit=4), (listed, more))
        self.assertEqual(summarize_ignored([]), ([], 0))


if __name__ == '__main__':
    unittest.main()
