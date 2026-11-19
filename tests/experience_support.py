"""Shared fixtures for the Experience tests (no test cases here)."""

import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from ai_sdlc import experience_events as ev

SHA = 'a' * 64
CLOCK_TIME = '2026-11-18T22:00:00Z'


def clock():
    return CLOCK_TIME


def tool():
    return {'role': 'tool', 'name': 'ai-sdlc-lite'}


def env():
    return {'platform': 'linux', 'lite_version': '2.0.0.dev1', 'python': '3.14'}


def sample(type_name, **overrides):
    """A valid field set (without chain/identity) for each event type."""
    task = {'kind': 'task', 'task_id': 'T1', 'repo_classification': 'synthetic'}
    install = {'kind': 'installation', 'repo_classification': 'synthetic'}
    base = {
        'install.completed': dict(subject=install, actor=tool(), observer=tool(), method='tool-checked-hash',
                                  trust_level='T1', independence='none', evidence=[],
                                  data={'target': 'claude-code', 'result': 'INITIALIZED', 'file_count': 44,
                                        'manifest_sha256': SHA}),
        'install.failed': dict(subject=install, actor=tool(), observer=tool(), method='tool-reported',
                               trust_level='T0', independence='none', evidence=[],
                               data={'target': 'agents', 'reason_code': 'installation_missing', 'partial': False}),
        'task.initialized': dict(subject=task, actor={'role': 'operator'}, observer={'role': 'operator'},
                                 method='operator-recorded', trust_level='T0', independence='none', evidence=[],
                                 data={'skill_target': 'claude-code', 'context_written': True,
                                       'approval': 'PENDING'}),
        'task.approval_changed': dict(subject=task, actor={'role': 'human'}, observer={'role': 'operator'},
                                      method='human-decision-reported', trust_level='T0', independence='none',
                                      evidence=[], data={'from': 'PENDING', 'to': 'APPROVED',
                                                         'task_revision': 'r1'}),
        'verify.completed': dict(subject=task, actor=tool(), observer=tool(), method='tool-observed-git-state',
                                 trust_level='T2', independence='none',
                                 evidence=[{'kind': 'verification-report', 'ref': 'none', 'sha256': SHA}],
                                 data={'status': 'BLOCKED', 'exit_code': 2,
                                       'failure_reason_codes': ['protected_path_modified'],
                                       'modified_path_count': 2, 'report_sha256': SHA, 'registry_version': 1,
                                       'facets': {'baseline': 'operator-supplied-record', 'hash_integrity': 'none',
                                                  'custody': 'unauthenticated', 'independent_execution': 'not-verified',
                                                  'agent_assertions': 'unverified'},
                                       'checks_origin': 'agent-reported'}),
        'check.operator_run': dict(subject=task, actor={'role': 'operator'}, observer={'role': 'operator'},
                                   method='operator-ran', trust_level='T0', independence='same-actor-family',
                                   evidence=[], data={'check_id': 'V-1', 'exit_code': 0, 'outcome': 'pass',
                                                      'tests_total': 3, 'tests_failed': 0}),
        'human.feedback': dict(subject=task, actor={'role': 'human'}, observer={'role': 'operator'},
                               method='human-decision-reported', trust_level='T0', independence='none',
                               evidence=[], data={'decision': 'NEEDS_CHANGES', 'friction': ['docs', 'install']}),
    }[type_name]
    base = dict(base, type=type_name, environment=env())
    base.update(overrides)
    return base


def chain(count, type_name='check.operator_run'):
    """A valid in-memory chain of events (no files)."""
    events, prev = [], None
    for seq in range(1, count + 1):
        event = ev.build_event(sample(type_name), run_id='run-test-1', seq=seq, prev=prev, recorded_at=CLOCK_TIME)
        events.append(event)
        prev = event['event_id']
    return events


def to_bytes(events):
    return b''.join(ev.canonical_json(e) + b'\n' for e in events)


def git_repo(path):
    subprocess.run(['git', 'init', '-q', str(path)], check=True)
    return path


def snapshot(root):
    result = {}
    for current, dirs, files in os.walk(root, followlinks=False):
        for name in dirs + files:
            path = Path(current) / name
            info = path.lstat()
            result[path.relative_to(root).as_posix()] = (
                info.st_mode, None if path.is_dir() or path.is_symlink() else path.read_bytes(), info.st_mtime_ns)
    return result
