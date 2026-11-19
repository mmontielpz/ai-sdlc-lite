"""EXP-01A: event schema, closed validation, canonical identity, strict loading (no files, no network)."""

import ast
import copy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import experience_support as sup
from ai_sdlc import experience_events as ev
from ai_sdlc.experience_events import ExperienceError

ROOT = sup.ROOT
SCHEMA = json.loads((ROOT / 'docs/experience-event.schema.json').read_text(encoding='utf-8'))
BAD = '!!bad!!'


def code_of(callable_, *args, **kwargs):
    try:
        callable_(*args, **kwargs)
    except ExperienceError as error:
        return error.code
    return None


class ValidEvents(unittest.TestCase):
    def test_each_type_builds_and_validates(self):  # V-01..V-07
        self.assertEqual(set(ev.TYPES), set(SCHEMA['data_by_type']))
        for type_name in ev.TYPES:
            event = ev.build_event(sup.sample(type_name), run_id='run-1', seq=1, prev=None, recorded_at=sup.CLOCK_TIME)
            ev.validate_event(event, expected_seq=1, previous_id=None, run_id='run-1')
            self.assertEqual(event['event_id'], ev.compute_event_id(event))

    def test_documented_examples_validate_and_chain(self):  # V-08
        examples = SCHEMA['x-examples']
        previous = None
        for number, event in enumerate(examples, 1):
            ev.validate_event(event, expected_seq=number, previous_id=previous, run_id=event['run_id'])
            previous = event['event_id']

    def test_documentation_agrees_with_code(self):
        self.assertEqual(tuple(SCHEMA['properties']['type']['enum']), ev.TYPES)
        self.assertEqual(set(SCHEMA['required']), set(ev.TOP_REQUIRED))
        self.assertEqual(set(SCHEMA['properties']), set(ev.TOP_PROPERTIES))
        self.assertEqual(set(SCHEMA['properties']['method']['enum']), set(ev.METHOD_CEILING))
        self.assertEqual(SCHEMA['x-method-ceilings'], ev.METHOD_CEILING)
        self.assertEqual(set(SCHEMA['properties']['trust_level']['enum']), {'T0', 'T1', 'T2', 'H'})
        self.assertNotIn('T3', json.dumps(SCHEMA['properties']['trust_level']['enum']))
        for type_name, (required, properties) in ev.DATA_SPECS.items():
            doc = SCHEMA['data_by_type'][type_name]
            self.assertEqual(set(doc['required']), set(required), type_name)
            self.assertEqual(set(doc['properties']), set(properties), type_name)
            self.assertFalse(doc['additionalProperties'])
        self.assertEqual(tuple(SCHEMA['data_by_type']['install.failed']['properties']['reason_code']['enum']),
                         ev.INIT_REASONS)
        subject = SCHEMA['properties']['subject']['properties']
        self.assertEqual(subject['revision']['pattern'], '^' + ev.REVISION.pattern + '$')
        self.assertEqual(SCHEMA['data_by_type']['task.approval_changed']['properties']['task_revision']['pattern'],
                         '^' + ev.REVISION.pattern + '$')
        version, registry = ev.load_registry()
        self.assertEqual(SCHEMA['x-verifier-registry-snapshot']['registry_version'], version)
        self.assertEqual(SCHEMA['x-verifier-registry-snapshot']['codes'], sorted(registry))

    def test_identity_is_canonical_and_deterministic(self):
        event = ev.build_event(sup.sample('check.operator_run'), run_id='run-1', seq=1, prev=None,
                               recorded_at=sup.CLOCK_TIME)
        shuffled = dict(reversed(list(event.items())))
        self.assertEqual(ev.canonical_json(event), ev.canonical_json(shuffled))
        self.assertEqual(ev.compute_event_id(event), ev.compute_event_id(shuffled))
        again = ev.build_event(sup.sample('check.operator_run'), run_id='run-1', seq=1, prev=None,
                               recorded_at=sup.CLOCK_TIME)
        self.assertEqual(event, again)
        self.assertRegex(event['event_id'], r'^ev-[0-9a-f]{32}$')
        self.assertEqual(ev.canonical_json({'b': 1, 'a': [1, 'x']}), b'{"a":[1,"x"],"b":1}')
        with self.assertRaises(ValueError):
            ev.canonical_json({'a': float('nan')})


def _get(root, path):
    for step in path:
        root = root[step]
    return root


class InvalidEvents(unittest.TestCase):
    def valid(self, type_name):
        return ev.build_event(sup.sample(type_name), run_id='run-1', seq=1, prev=None, recorded_at=sup.CLOCK_TIME)

    def test_closed_schema_unknown_and_missing_keys(self):  # I-01..I-03
        for type_name in ev.TYPES:
            event = self.valid(type_name)
            extra = dict(event, extra='x')
            self.assertIsNotNone(code_of(ev.validate_event, extra), type_name)
            for key in ev.TOP_REQUIRED:
                missing = {k: v for k, v in event.items() if k != key}
                self.assertIsNotNone(code_of(ev.validate_event, missing), (type_name, key))
            with_data_key = copy.deepcopy(event)
            with_data_key['data']['surprise'] = 1
            with_data_key['event_id'] = ev.compute_event_id(with_data_key)
            self.assertEqual(code_of(ev.validate_event, with_data_key), 'schema_invalid')

    def test_every_leaf_mutation_is_rejected_even_with_a_recomputed_id(self):  # I-04..I-05
        def leaves(value, path=()):
            if isinstance(value, dict):
                for key in value:
                    yield from leaves(value[key], path + (key,))
            elif isinstance(value, list):
                for index, item in enumerate(value):
                    yield from leaves(item, path + (index,))
            else:
                yield path

        def setpath(root, path, new):
            target = root
            for step in path[:-1]:
                target = target[step]
            target[path[-1]] = new

        for type_name in ev.TYPES:
            event = self.valid(type_name)
            for path in leaves(event):
                if path[0] in ('event_id', 'schema') or path == ('prev',):
                    continue
                for new in (BAD, -1, None) + (() if isinstance(_get(event, path), bool) else (True,)):
                    mutated = copy.deepcopy(event)
                    setpath(mutated, path, new)
                    self.assertIsNotNone(code_of(ev.validate_event, mutated), (type_name, path, new, 'raw'))
                    mutated['event_id'] = ev.compute_event_id(mutated)
                    code = code_of(ev.validate_event, mutated)
                    self.assertIsNotNone(code, (type_name, path, new, 'reid'))
                    self.assertNotEqual(code, 'id_mismatch', (type_name, path, new))

    def test_trust_inflation_and_disabled_levels(self):  # I-06..I-10
        run = dict(run_id='run-1', seq=1, prev=None, recorded_at=sup.CLOCK_TIME)
        self.assertEqual(code_of(ev.build_event, sup.sample('check.operator_run', trust_level='T3'), **run),
                         'trust_inflation')
        self.assertEqual(code_of(ev.build_event, sup.sample('check.operator_run', trust_level='T2'), **run),
                         'trust_inflation')
        self.assertEqual(code_of(ev.build_event, sup.sample('check.operator_run', trust_level='T1'), **run),
                         'trust_inflation')
        self.assertEqual(code_of(ev.build_event, sup.sample('human.feedback', trust_level='H'), **run),
                         'h_not_enabled')
        self.assertEqual(code_of(ev.build_event, sup.sample('task.approval_changed', trust_level='H'), **run),
                         'h_not_enabled')
        self.assertEqual(code_of(ev.build_event, sup.sample('verify.completed', trust_level='T0'), **run),
                         'schema_invalid')
        self.assertEqual(code_of(ev.build_event, sup.sample('check.operator_run', independence='ci-attested'), **run),
                         'trust_inflation')
        self.assertEqual(code_of(ev.build_event, sup.sample('check.operator_run', method='tool-observed-git-state'),
                                 **run), 'schema_invalid')  # method not allowed for the type
        self.assertEqual(code_of(ev.build_event, sup.sample('check.operator_run', method='human-decision-reported'),
                                 **run), 'schema_invalid')
        for method in ('agent-reported', 'ci-run', 'unknown'):
            self.assertIsNotNone(code_of(ev.build_event, sup.sample('check.operator_run', method=method), **run))
        # a T3 or H string is refused before any identity is computed
        raw = self.valid('check.operator_run')
        raw['trust_level'] = 'T3'
        self.assertEqual(code_of(ev.validate_event, raw), 'trust_inflation')

    def test_type_specific_actor_and_subject_rules(self):
        run = dict(run_id='run-1', seq=1, prev=None, recorded_at=sup.CLOCK_TIME)
        self.assertEqual(code_of(ev.build_event, sup.sample('install.completed', actor={'role': 'operator'}), **run),
                         'schema_invalid')
        self.assertEqual(code_of(ev.build_event, sup.sample('verify.completed', actor={'role': 'agent'}), **run),
                         'schema_invalid')
        self.assertEqual(code_of(ev.build_event, sup.sample('check.operator_run', subject={'kind': 'installation'}),
                                 **run), 'schema_invalid')
        self.assertEqual(code_of(ev.build_event, sup.sample('check.operator_run', subject={'kind': 'task'}), **run),
                         'schema_invalid')
        self.assertEqual(code_of(ev.build_event, sup.sample('install.failed', subject={
            'kind': 'installation', 'task_id': 'T1'}), **run), 'schema_invalid')
        self.assertEqual(code_of(ev.build_event, sup.sample('check.operator_run', evidence=[
            {'kind': 'verification-report', 'ref': 'none', 'sha256': sup.SHA}]), **run), 'schema_invalid')

    def test_verify_completed_rules(self):
        run = dict(run_id='run-1', seq=1, prev=None, recorded_at=sup.CLOCK_TIME)

        def verify(**data):
            base = sup.sample('verify.completed')
            base['data'] = dict(base['data'], **data)
            return base

        self.assertIsNone(code_of(ev.build_event, verify(status='PASS', exit_code=0, failure_reason_codes=[]), **run))
        self.assertEqual(code_of(ev.build_event, verify(status='PASS', exit_code=0), **run), 'schema_invalid')
        self.assertEqual(code_of(ev.build_event, verify(exit_code=1), **run), 'schema_invalid')  # BLOCKED needs 2
        self.assertEqual(code_of(ev.build_event, verify(registry_version=2), **run), 'schema_invalid')
        self.assertEqual(code_of(ev.build_event, verify(failure_reason_codes=['not_a_registry_code']), **run),
                         'schema_invalid')
        self.assertEqual(code_of(ev.build_event, verify(failure_reason_codes=['check_failed',
                                                                              'protected_path_modified']), **run), None)
        self.assertEqual(code_of(ev.build_event, verify(failure_reason_codes=['baseline_mismatch', 'check_failed']),
                                 **run), None)
        self.assertEqual(code_of(ev.build_event, verify(failure_reason_codes=['check_failed', 'check_failed']), **run),
                         'schema_invalid')
        self.assertEqual(code_of(ev.build_event, verify(failure_reason_codes=['protected_path_modified',
                                                                              'check_failed']), **run),
                         'schema_invalid')  # must be sorted
        partial = verify(status='PARTIAL', exit_code=1, failure_reason_codes=['check_failed'])
        self.assertIsNone(code_of(ev.build_event, partial, **run))
        self.assertEqual(code_of(ev.build_event, verify(status='PARTIAL', exit_code=1,
                                                        failure_reason_codes=['protected_path_modified']), **run),
                         'schema_invalid')  # that code can only be BLOCKED
        self.assertEqual(code_of(ev.build_event, verify(status='BLOCKED', exit_code=2,
                                                        failure_reason_codes=['check_failed']), **run), 'schema_invalid')
        facets = dict(verify()['data']['facets'], independent_execution='verified')
        self.assertEqual(code_of(ev.build_event, verify(facets=facets), **run), 'schema_invalid')
        self.assertEqual(code_of(ev.build_event, verify(checks_origin='tool'), **run), 'schema_invalid')
        mismatch = sup.sample('verify.completed')
        mismatch['evidence'] = [{'kind': 'verification-report', 'ref': 'none', 'sha256': 'b' * 64}]
        self.assertEqual(code_of(ev.build_event, mismatch, **run), 'schema_invalid')

    def test_other_value_rules(self):
        run = dict(run_id='run-1', seq=1, prev=None, recorded_at=sup.CLOCK_TIME)
        for stamp in ('2026-02-30T00:00:00Z', '1999-12-31T23:59:59Z', '3000-01-01T00:00:00Z', '2026-11-18 22:00:00Z'):
            self.assertEqual(code_of(ev.build_event, sup.sample('check.operator_run'), **dict(run, recorded_at=stamp)),
                             'schema_invalid', stamp)
        bad_counts = sup.sample('check.operator_run')
        bad_counts['data'] = dict(bad_counts['data'], tests_failed=9)
        self.assertEqual(code_of(ev.build_event, bad_counts, **run), 'schema_invalid')
        self.assertEqual(code_of(ev.build_event, sup.sample('check.operator_run'), **dict(run, seq=5001)),
                         'schema_invalid')
        self.assertEqual(code_of(ev.build_event, sup.sample('check.operator_run'), **dict(run, seq=0)),
                         'schema_invalid')
        unknown = dict(sup.sample('check.operator_run'), surprise=1)
        self.assertEqual(code_of(ev.build_event, unknown, **run), 'schema_invalid')
        incomplete = sup.sample('check.operator_run')
        del incomplete['data']
        self.assertEqual(code_of(ev.build_event, incomplete, **run), 'schema_invalid')

    def test_chain_position_rules(self):  # C-01..C-06 at event level
        a, b = sup.chain(2)
        self.assertIsNone(code_of(ev.validate_event, b, expected_seq=2, previous_id=a['event_id'], run_id='run-test-1'))
        for seq, prev, run in ((3, a['event_id'], 'run-test-1'), (2, None, 'run-test-1'), (2, a['event_id'], 'other'),
                               (1, a['event_id'], 'run-test-1')):
            self.assertEqual(code_of(ev.validate_event, b, expected_seq=seq, previous_id=prev, run_id=run),
                             'chain_broken', (seq, prev, run))
        edited = copy.deepcopy(b)
        edited['data']['exit_code'] = 7
        self.assertEqual(code_of(ev.validate_event, edited), 'id_mismatch')


class StringRestrictionsAreIdenticalInMemoryAndSerialized(unittest.TestCase):
    """Regression (review of PR #27): `$` in the field patterns let a trailing newline through, so
    identifiers such as "run-1\\n" were accepted by build_event AND by loads_strict (whose
    printable-ASCII check had the same flaw). Both paths must enforce the same, strict, full-string rules."""

    # (label, builder(value) -> (fields, run_id, seq, prev))
    def cases(self):
        run = dict(run_id='run-1', seq=1, prev=None)

        def nested(type_name, path, value):
            fields = sup.sample(type_name)
            target = fields
            for step in path[:-1]:
                target[step] = dict(target[step])
                target = target[step]
            target[path[-1]] = value
            return fields

        yield 'run_id', lambda v: (sup.sample('check.operator_run'), dict(run, run_id=v))
        yield 'task_id', lambda v: (nested('check.operator_run', ('subject', 'task_id'), v), run)
        yield 'task_revision (data)', lambda v: (nested('task.approval_changed', ('data', 'task_revision'), v), run)
        yield 'revision (subject)', lambda v: (nested('check.operator_run', ('subject', 'revision'), v), run)
        yield 'check_id', lambda v: (nested('check.operator_run', ('data', 'check_id'), v), run)
        yield 'lite_version', lambda v: (nested('check.operator_run', ('environment', 'lite_version'), v), run)
        yield 'python', lambda v: (nested('check.operator_run', ('environment', 'python'), v), run)
        yield 'agent_version', lambda v: (nested('check.operator_run', ('environment', 'agent_version'), v), run)
        yield 'bundle_digest', lambda v: (nested('check.operator_run', ('environment', 'bundle_digest'), v), run)
        yield 'lite_commit', lambda v: (nested('check.operator_run', ('environment', 'lite_commit'), v), run)
        yield 'manifest_sha256', lambda v: (nested('install.completed', ('data', 'manifest_sha256'), v), run)
        yield 'report_sha256', lambda v: (nested('verify.completed', ('data', 'report_sha256'), v), run)
        yield 'evidence sha256', lambda v: (nested('verify.completed', ('evidence',), [
            {'kind': 'verification-report', 'ref': 'none', 'sha256': v}]), run)
        yield 'failure code', lambda v: (nested('verify.completed', ('data', 'failure_reason_codes'), [v]), run)
        yield 'recorded_at', lambda v: (sup.sample('check.operator_run'), dict(run, recorded_at=v))
        yield 'prev', lambda v: (sup.sample('check.operator_run'), dict(run, seq=2, prev=v))

    HOSTILE = ('\n', '\r', '\t', '\x00', '\x1b', '\x7f', '\u2028', '\u202e', '\u00e9', ' ')

    def outcome_in_memory(self, fields, run):
        run = dict(run)
        run.setdefault('recorded_at', sup.CLOCK_TIME)
        return code_of(ev.build_event, fields, **run)

    def outcome_serialized(self, fields, run):
        """Same event, forced through bytes: canonical JSON -> loads_strict -> validate_event."""
        run = dict(run)
        event = {'schema': ev.SCHEMA, 'run_id': run['run_id'], 'seq': run['seq'], 'prev': run['prev'],
                 'recorded_at': run.get('recorded_at', sup.CLOCK_TIME)}
        event.update(fields)
        event['event_id'] = ev.compute_event_id(event)
        raw = ev.canonical_json(event)
        try:
            parsed = ev.loads_strict(raw)
            ev.validate_event(parsed, expected_seq=run['seq'], previous_id=run['prev'], run_id=run['run_id'])
        except ExperienceError as error:
            return error.code
        return None

    def valid_value(self, label):
        return {'run_id': 'run-1', 'task_id': 'T1', 'task_revision (data)': 'r1', 'revision (subject)': 'r1',
                'check_id': 'V-1', 'lite_version': '2.0.0', 'python': '3.14', 'agent_version': '2.1.327',
                'bundle_digest': 'a' * 64, 'lite_commit': 'b' * 40, 'manifest_sha256': 'a' * 64,
                'report_sha256': 'a' * 64, 'evidence sha256': 'a' * 64, 'failure code': 'protected_path_modified',
                'recorded_at': sup.CLOCK_TIME, 'prev': 'ev-' + 'c' * 32}[label]

    def test_trailing_and_embedded_control_characters_are_rejected_everywhere(self):
        for label, make in self.cases():
            good = self.valid_value(label)
            for suffix in self.HOSTILE:
                for value in (good + suffix, suffix + good, good[:1] + suffix + good[1:]):
                    fields, run = make(value)
                    if label == 'prev':
                        run = dict(run, seq=2, prev=value)
                    mem = self.outcome_in_memory(fields, run)
                    ser = self.outcome_serialized(fields, run)
                    self.assertIsNotNone(mem, (label, repr(value), 'in-memory accepted'))
                    self.assertIsNotNone(ser, (label, repr(value), 'serialized accepted'))

    def test_both_paths_agree_on_every_candidate(self):
        for label, make in self.cases():
            for value in ('', 'a', 'A-b_c.d', 'x' * 65, '~', '\x7e', self.valid_value(label), 'ev-' + 'f' * 32):
                fields, run = make(value)
                if label == 'prev':
                    run = dict(run, seq=2, prev=value)
                mem = self.outcome_in_memory(fields, run)
                ser = self.outcome_serialized(fields, run)
                self.assertEqual(mem is None, ser is None, (label, repr(value), mem, ser))

    def test_printable_ascii_rule_is_strict_full_string(self):
        for text in ('a\n', '\n', 'a\r\n', 'a\x00', 'a\x7f', 'caf\u00e9'):
            self.assertEqual(code_of(ev.loads_strict, ('{"a":%s}' % __import__('json').dumps(text)).encode()),
                             'forbidden_content', repr(text))
            self.assertEqual(code_of(ev.loads_strict, ('{%s:1}' % __import__('json').dumps(text)).encode()),
                             'forbidden_content', repr(text))
        self.assertEqual(ev.loads_strict(b'{"a":" ~"}'), {'a': ' ~'})

    def test_validate_event_itself_rejects_non_printable_strings(self):
        event = ev.build_event(sup.sample('check.operator_run'), run_id='run-1', seq=1, prev=None,
                               recorded_at=sup.CLOCK_TIME)
        for key in ('run_id',):
            mutated = dict(event, **{key: event[key] + '\n'})
            mutated['event_id'] = ev.compute_event_id(mutated)
            self.assertIsNotNone(code_of(ev.validate_event, mutated))
        smuggled = copy.deepcopy(event)
        smuggled['data']['check_id'] = 'V-1\n'
        smuggled['event_id'] = ev.compute_event_id(smuggled)
        self.assertIsNotNone(code_of(ev.validate_event, smuggled))


class StrictLoading(unittest.TestCase):
    def check(self, raw, code):
        self.assertEqual(code_of(ev.loads_strict, raw), code, raw[:40])

    def test_rejections(self):  # A-3..A-6
        self.check(b'{"a":1,"a":2}', 'duplicate_key')
        self.check(b'{"a":{"b":1,"b":2}}', 'duplicate_key')
        self.check(b'{"a":NaN}', 'non_finite_number')
        self.check(b'{"a":Infinity}', 'non_finite_number')
        self.check(b'{"a":-Infinity}', 'non_finite_number')
        self.check(b'{"a":1e999}', 'non_finite_number')
        self.check(b'{"a":1.5}', 'schema_invalid')
        self.check(b'{"a":%d}' % (2 ** 70), 'limit_exceeded')
        self.check(b'\xef\xbb\xbf{"a":1}', 'bad_encoding')
        self.check(b'{"a":"\xff"}', 'bad_encoding')
        self.check(b'{"a":"\xc0\xaf"}', 'bad_encoding')
        self.check(b'{"a":"\\ud800"}', 'forbidden_content')
        self.check(b'{"a":"\\u0000"}', 'forbidden_content')
        self.check(b'{"a":"\\u001b[31m"}', 'forbidden_content')
        self.check('{"a":"‮"}'.encode('utf-8'), 'forbidden_content')
        self.check('{"a":"​"}'.encode('utf-8'), 'forbidden_content')
        self.check('{"a":"café"}'.encode('utf-8'), 'forbidden_content')
        self.check('{"ké":1}'.encode('utf-8'), 'forbidden_content')
        self.check(b'{"a":', 'malformed_json')
        self.check(b'', 'malformed_json')
        self.check(b'{"a":1} trailing', 'malformed_json')
        self.check(b"{'a':1}", 'malformed_json')

    def test_depth_is_bounded_before_parsing(self):  # A-2
        self.check(b'[' * 100000 + b']' * 100000, 'depth_exceeded')
        self.check(b'[' * 9 + b']' * 9, 'depth_exceeded')
        self.assertEqual(ev.loads_strict(b'[' * 8 + b']' * 8), [[[[[[[[]]]]]]]])
        self.assertEqual(ev.loads_strict(b'{"a":"[[[[[[[[[[[[["}'), {'a': '[[[[[[[[[[[[['})  # brackets in strings

    def test_accepts_plain_documents(self):
        self.assertEqual(ev.loads_strict(b'{"a":[1,true,null,"x"],"b":{"c":-3}}'),
                         {'a': [1, True, None, 'x'], 'b': {'c': -3}})
        self.assertEqual(ev.loads_strict(b'{"n":%d}' % (2 ** 53)), {'n': 2 ** 53})


class StaticBoundaries(unittest.TestCase):
    FORBIDDEN = {'socket', 'http', 'urllib', 'ssl', 'subprocess', 'ftplib', 'smtplib', 'telnetlib', 'asyncio',
                 'multiprocessing', 'ctypes', 'pickle', 'marshal', 'shelve', 'xmlrpc', 'webbrowser', 'requests',
                 'sqlite3', 'tempfile', 'shutil'}

    def modules(self):
        for name in ('experience_events', 'experience_journal', 'experience'):
            yield name, ast.parse((ROOT / 'ai_sdlc' / (name + '.py')).read_text(encoding='utf-8'))

    def test_no_network_process_or_dynamic_execution_imports(self):  # SEC-01
        for name, tree in self.modules():
            imported, calls = set(), set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported.update(alias.name.split('.')[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imported.add(node.module.split('.')[0])
                elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    calls.add(node.func.id)
            self.assertFalse(imported & self.FORBIDDEN, (name, imported & self.FORBIDDEN))
            self.assertFalse(calls & {'eval', 'exec', 'compile', '__import__'}, (name, calls))

    def test_modules_are_flat_in_the_shipped_package(self):  # packaging (F-31)
        for name in ('experience_events', 'experience_journal', 'experience'):
            self.assertTrue((ROOT / 'ai_sdlc' / (name + '.py')).is_file())
        pyproject = (ROOT / 'pyproject.toml').read_text(encoding='utf-8')
        self.assertIn('packages = ["ai_sdlc", "ai_sdlc._framework"]', pyproject)
        self.assertFalse((ROOT / 'ai_sdlc' / 'experience').exists())


if __name__ == '__main__':
    unittest.main()
