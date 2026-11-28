"""Regressions for untracked-content access (M-03), baseline record limits (EXP-2/3) and summaries (EXP-4)."""

import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import unittest
from unittest import mock

import test_verify_scope as base

vs, run = base.vs, base.run
SECRET = 'untracked secret content\n'
SECRET_SHA = hashlib.sha256(SECRET.encode()).hexdigest()


def cli_out(*args):
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        code = vs.main(list(args))
    return code, buffer.getvalue()


@contextlib.contextmanager
def recorded_reads():
    """Resolved paths whose content the verifier opened through pathlib."""
    seen, original = [], Path.read_bytes

    def read_bytes(self):
        seen.append(self.resolve())
        return original(self)

    with mock.patch.object(Path, 'read_bytes', read_bytes):
        yield seen


class Helpers(base.Fixture):
    def record(self, *extra, name='baseline.json'):
        path = self.meta / name
        code, out = cli_out('baseline', '--repo', str(self.repo), '--out', str(path), *extra)
        self.assertEqual(code, 0, out)
        return path

    def run_with(self, data, **kwargs):
        path = self.meta / 'result.json'
        path.write_text(json.dumps(data))
        return vs.verify(self.repo, path, **kwargs)

    def dirty(self, paths, **over):
        return self.contract(baseline_dirty_paths=paths, modified_paths=paths, baseline_ignored_paths=[],
                             claimed_status='PARTIAL', **over)

    def ignore(self, *patterns):
        (self.repo / '.git' / 'info' / 'exclude').write_text(''.join(p + '\n' for p in patterns))


class UntrackedContentTests(Helpers):
    def test_default_baseline_and_verify_never_open_untracked_files(self):
        self.write('notes.txt', SECRET)
        self.write('src/app.py', 'x = 2\n')
        with recorded_reads() as reads:
            record = self.record()
            report = self.run_with(self.contract(baseline_dirty_paths=['notes.txt', 'src/app.py'],
                                                 modified_paths=['notes.txt', 'src/app.py'], baseline_ignored_paths=[],
                                                 allowed_paths=['src/**']), baseline_record=record)
        self.assertNotIn(self.repo / 'notes.txt', reads)
        self.assertIn(self.repo / 'src/app.py', reads)   # tracked dirty files are still compared
        data = json.loads(record.read_text())
        self.assertEqual(set(data['baseline_dirty_sha256']), {'src/app.py'})
        self.assertNotIn(SECRET_SHA, record.read_text())
        self.assertEqual(report['status'], 'BLOCKED')
        self.assertEqual(report['untracked_content_not_inspected'], ['notes.txt'])
        details = [r['detail'] for r in report['failure_reasons'] if r['code'] == 'out_of_scope_modification']
        self.assertEqual(details, ['notes.txt (untracked content not inspected, so it cannot be shown unchanged)'])

    def test_uninspected_path_inside_scope_is_partial_never_pass(self):
        self.write('src/new.py', SECRET)
        record = self.record()
        report = self.run_with(self.dirty(['src/new.py']), baseline_record=record)
        self.assertEqual((report['status'], report['untracked_content_not_inspected']), ('PARTIAL', ['src/new.py']))

    def test_authorization_is_needed_again_at_verify(self):
        self.write('notes.txt', SECRET)
        record = self.record('--hash-untracked')
        data = self.dirty(['notes.txt'])
        with recorded_reads() as reads:
            self.assertEqual(self.run_with(data, baseline_record=record)['status'], 'BLOCKED')
        self.assertNotIn(self.repo / 'notes.txt', reads)
        allowed = self.run_with(data, baseline_record=record, hash_untracked=True)
        self.assertEqual(allowed['status'], 'PARTIAL')
        self.assertNotIn('untracked_content_not_inspected', allowed)

    def test_authorized_verify_cannot_preserve_a_path_the_record_never_hashed(self):
        self.write('notes.txt', SECRET)
        record = self.record()
        report = self.run_with(self.dirty(['notes.txt']), baseline_record=record, hash_untracked=True)
        self.assertEqual(report['status'], 'BLOCKED')

    def test_file_that_becomes_ignored_after_the_baseline_is_not_opened(self):
        self.write('notes.txt', SECRET)
        record = self.record('--hash-untracked')
        self.ignore('notes.txt')
        with recorded_reads() as reads:
            report = self.run_with(self.dirty(['notes.txt']), baseline_record=record)
        self.assertNotIn(self.repo / 'notes.txt', reads)
        self.assertEqual(report['status'], 'BLOCKED')

    def test_file_removed_from_the_index_and_ignored_is_not_opened(self):
        run(self.repo, 'rm', '-q', '--cached', 'docs/a.md')
        self.ignore('docs/a.md')
        with recorded_reads() as reads:
            record = self.record()
        self.assertNotIn(self.repo / 'docs/a.md', reads)
        self.assertNotIn('docs/a.md', json.loads(record.read_text())['baseline_dirty_sha256'])

    def test_untracked_symlink_target_is_not_recorded(self):
        os.symlink('/nonexistent/private-target', self.repo / 'link')
        self.assertNotIn('private-target', self.record().read_text())

    def test_untracked_evidence_inside_the_repository_needs_authorization(self):
        self.write('src/app.py', 'x = 2\n')
        self.write('src/log.txt', SECRET)
        data = self.contract(modified_paths=['src/app.py', 'src/log.txt'],
                             verification=[{'command': 'c', 'exit_code': 0, 'evidence': 'src/log.txt'}])
        with recorded_reads() as reads:
            report = self.run_with(data)
        self.assertNotIn(self.repo / 'src/log.txt', reads)
        self.assertEqual(report['status'], 'BLOCKED')
        self.assertIn('missing_evidence', self.codes(report))
        self.assertEqual(self.run_with(data, hash_untracked=True)['status'], 'PASS')

    def test_tracked_evidence_inside_the_repository_is_still_hashed(self):
        report = self.run_with(self.contract(modified_paths=[],
                                             verification=[{'command': 'c', 'exit_code': 0, 'evidence': 'docs/a.md'}]))
        self.assertEqual(report['status'], 'PASS')


class BaselineLimitTests(Helpers):
    def many_ignored(self, count):
        self.ignore('deps/')
        for index in range(count):
            folder = self.repo / 'deps' / f'p{index // 500}'
            if index % 500 == 0:
                folder.mkdir(parents=True, exist_ok=True)
            (folder / f'module-file-{index}.js').touch()

    def test_large_dependency_tree_round_trips_and_new_files_are_still_detected(self):
        self.many_ignored(32000)   # above the former 20,000 limit and 1 MiB record size
        record = self.record()
        self.assertGreater(record.stat().st_size, vs.MAX_JSON)
        self.write('src/app.py', 'x = 2\n')
        data = self.contract()
        report = self.run_with(data, baseline_record=record)
        self.assertEqual((report['status'], report['failure_reasons']), ('PASS', []))
        self.write('deps/p0/injected.js', 'x\n')
        report = self.run_with(data, baseline_record=record)
        self.assertEqual(report['status'], 'BLOCKED')
        self.assertIn('ignored_path_unapproved', self.codes(report))

    def test_writer_refuses_a_record_its_reader_would_reject(self):
        out = self.meta / 'big.json'
        with mock.patch.object(vs, 'MAX_BASELINE', 100):
            code, text = cli_out('baseline', '--repo', str(self.repo), '--out', str(out))
        self.assertEqual(code, 2)
        self.assertIn('over the 100-byte limit', text)
        self.assertFalse(out.exists())

    def test_record_exactly_at_the_limit_is_readable(self):
        size = self.record().stat().st_size
        with mock.patch.object(vs, 'MAX_BASELINE', size):
            record = self.record(name='again.json')
            vs.load_sealed(record, vs.BASELINE_SCHEMA, 'baseline record')
        with mock.patch.object(vs, 'MAX_BASELINE', size - 1), self.assertRaises(vs.Blocked):
            vs.load_sealed(record, vs.BASELINE_SCHEMA, 'baseline record')

    def test_manifest_writer_enforces_the_reader_limit(self):
        out = self.meta / 'manifest.json'
        with mock.patch.object(vs, 'MAX_JSON', 10):
            self.assertEqual(cli_out('seal', '--out', str(out), str(self.meta / 'out.txt'))[0], 2)
        self.assertFalse(out.exists())

    def test_result_template_refuses_a_contract_the_verifier_would_reject(self):
        sys.path.insert(0, str(base.ROOT))
        self.addCleanup(sys.path.remove, str(base.ROOT))
        from ai_sdlc import result_template
        out = self.meta / 'template.json'
        err = io.StringIO()
        with mock.patch.object(result_template._vs, 'MAX_JSON', 100), contextlib.redirect_stderr(err):
            self.assertEqual(result_template.main(['--repo', str(self.repo), '--out', str(out)]), 2)
        self.assertIn('--baseline-record', err.getvalue())
        self.assertFalse(out.exists())


class BaselineSummaryTests(Helpers):
    def test_out_prints_a_short_summary_and_keeps_the_record_in_the_file(self):
        self.write('notes.txt', SECRET)
        out = self.meta / 'baseline.json'
        code, text = cli_out('baseline', '--repo', str(self.repo), '--out', str(out))
        self.assertEqual(code, 0)
        record = json.loads(out.read_text())
        self.assertIn(f'digest: {record["digest"]}', text)
        self.assertIn('untracked contents not read: 1', text)
        self.assertNotIn('notes.txt', text)
        self.assertLess(len(text.splitlines()), 10)
        self.assertNotIn('WARNING', text)

    def test_without_out_the_record_is_printed_as_json(self):
        code, text = cli_out('baseline', '--repo', str(self.repo))
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(text)['schema'], vs.BASELINE_SCHEMA)

    def test_truncated_listing_is_announced(self):
        self.ignore('*.log')
        self.write('a.log', 'x\n')
        self.write('b.log', 'x\n')
        with mock.patch.object(vs, 'IGNORED_CAP', 1):
            code, text = cli_out('baseline', '--repo', str(self.repo), '--out', str(self.meta / 't.json'))
        self.assertEqual(code, 0)
        self.assertIn('WARNING', text)


if __name__ == '__main__':
    unittest.main()
