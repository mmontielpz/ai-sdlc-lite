#!/usr/bin/env python3
"""Install a self-contained project Skill using Python's standard library and Git."""

import argparse
import base64
import copy
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import shlex
from urllib.parse import unquote, urlsplit


SOURCE = Path(__file__).resolve().parents[1]
SKILL = Path('.agents/skills/ai-sdlc-lite')
MANIFEST = '.install-manifest.json'
CONTEXT = Path('.ai-sdlc-lite/task-context.json')
CONFIG_BACKUP = '.ai-sdlc-lite-settings-backup.json'
PERMISSION_BACKUP = '.ai-sdlc-lite-permission-backup.json'
DOCUMENTS = ('WORKFLOW.md', 'README.md', 'AGENTS.md', 'TASK.md',
             'CHECKLIST.md', 'RESULT.md')
LINK = re.compile(r'\[[^\]\n]*\]\(([^)\s]+)\)')


class Blocked(Exception):
    pass


def digest(content):
    return hashlib.sha256(content).hexdigest()


def run(args, cwd):
    result = subprocess.run(args, cwd=cwd, capture_output=True, text=True,
                            timeout=20)
    if result.returncode:
        raise Blocked(f'{args[0]} exited {result.returncode}: {result.stderr.strip()}')
    return result.stdout.strip()


def target_root(value):
    target = Path(value).expanduser().resolve(strict=True)
    if not target.is_dir():
        raise Blocked('Target must be a repository directory.')
    root = Path(run(['git', 'rev-parse', '--show-toplevel'], target)).resolve()
    if root == SOURCE or root.is_relative_to(SOURCE) or SOURCE.is_relative_to(root):
        raise Blocked('Framework and target repositories must be separate.')
    print(f'Target repository: {root}')
    if target != root:
        print(f'Resolved target subdirectory {target} to Git root {root}')
    status = run(['git', 'status', '--short', '--untracked-files=all'], root)
    print('Existing uncommitted changes:\n' + (status or 'CLEAN'))
    return root


def no_symlinks(root, path):
    """Never follow destination symlinks, including dangling ancestors."""
    relative = path.relative_to(root)
    current = root
    for part in relative.parts:
        current /= part
        if current.is_symlink():
            raise Blocked(f'Symlink refused: {current}')


def workspace(root):
    """Inspect instruction locations only; never read ancestor instruction content."""
    ancestors = []
    for directory in (root, *root.parents):
        path = directory / 'AGENTS.md'
        if path.exists() or path.is_symlink():
            kind = 'ROOT' if directory == root else 'PARENT'
            print(f'{kind} instructions detected (not read): {path}')
            if directory != root:
                ancestors.append(path)
    writable = os.access(root, os.W_OK)
    print(f'Workspace writable: {writable}')
    print('WRITE PREFLIGHT: PASS; edits may be proposed.' if writable else
          'WRITE PREFLIGHT: BLOCKED; read-only workspace. Do not propose edits; '
          'report the limitation or reopen a writable workspace.')
    print('Parent-file path approval: BLOCKED for automatic configuration; '
          'directory grants are broader than one instruction file.')
    context = root / CONTEXT
    no_symlinks(root, context)
    if context.is_file():
        record = json.loads(context.read_text(encoding='utf-8'))
        if not isinstance(record, dict):
            raise Blocked('Invalid task-context record.')
        for key in ('contract', 'checklist', 'result'):
            path = local_path(root, record.get(key, ''))
            if not path.is_file():
                raise Blocked(f'Task context has missing {key}: {path}')
            print(f'Task {key}: {path}')
        print('Task approval: UNVERIFIED; original contract and owner decision govern.')
    else:
        print('Task context: NOT INITIALIZED; non-blocking. Use the user request as the '
              'bounded task; no earlier task or approval is inferred.')
    print('Launch: ' + shlex.join(['copilot', '-C', str(root)]))
    return ancestors


def preflight(root):
    """Report bounded metadata, never secret values or inferred production safety."""
    print(f'Working directory: {Path.cwd()}; execution target: {root}')
    print(f'Installed Skill: {(root / SKILL / "SKILL.md").is_file()}')
    for name in ('copilot', 'node', 'npm'):
        executable = shutil.which(name)
        if executable:
            args = [executable, '--no-auto-update', '--version'] if name == 'copilot' else [executable, '--version']
            try:
                print(f'Tool {name}: ' + run(args, root).splitlines()[0])
            except (Blocked, IndexError, OSError, subprocess.SubprocessError):
                print(f'Tool {name}: FOUND; version UNKNOWN')
        else:
            print(f'Tool {name}: UNAVAILABLE')
    browsers = [name for name in ('chromium', 'chromium-browser', 'google-chrome', 'firefox') if shutil.which(name)]
    print('Browser executables on PATH: ' + (', '.join(browsers) or 'NONE DETECTED; project browser availability UNKNOWN'))
    package = root / 'package.json'
    no_symlinks(root, package)
    if package.is_file():
        document = json.loads(package.read_text(encoding='utf-8-sig'))
        scripts = document.get('scripts', {})
        if not isinstance(scripts, dict):
            raise Blocked('package.json scripts is not an object.')
        print('Declared npm script names: ' + ', '.join(sorted(scripts)))
        print('Test availability: ' + ('test script declared; runtime UNVERIFIED' if 'test' in scripts else 'UNKNOWN'))
    else:
        print('Node project/test commands: UNKNOWN; no root package.json inspected.')
    print('Verification commands: only those explicitly named in the approved plan; none executed by preflight.')
    print('Production/credential exposure: UNKNOWN; inspected workspace metadata and package.json only, no secrets read.')
    print('Access: metadata reads in target; planned edits, artifacts and network need task-specific review.')
    print('Separate authorization: production/deployment, secrets/credentials, dependencies, privileged/destructive '
          'operations, security changes, Git push/publication and scope expansion.')


def profile_configuration(root, home_value, plan_value, consent, dry_run, rollback=False):
    """Store literal command grants by repository; file rules apply only to a printed invocation."""
    if not home_value or not Path(home_value).expanduser().is_absolute():
        raise Blocked('An explicit absolute --copilot-home is required.')
    home = Path(home_value).expanduser()
    no_symlinks(Path(home.anchor), home)
    if not home.is_dir() or home.resolve() == (Path.home() / '.copilot').resolve():
        raise Blocked('Use an existing dedicated Copilot home; default global grants are refused.')
    backup = home / PERMISSION_BACKUP
    no_symlinks(home, backup)
    paths = [home / 'permissions-config.json', home / 'settings.json']
    for path in paths:
        no_symlinks(home, path)
    before = {path.name: path.read_bytes() if path.exists() else None for path in paths}
    if rollback:
        record = json.loads(backup.read_text())
        if record.get('target') != str(root):
            raise Blocked('Permission backup belongs to another target.')
        if not isinstance(record.get('files'), dict) or set(record['files']) != {p.name for p in paths}:
            raise Blocked('Invalid permission backup inventory.')
        if any((digest(before[name]) if before[name] is not None else None) != item['after']
               for name, item in record['files'].items()):
            raise Blocked('Configuration changed later; preserve it and the permission backup.')
        print('RESTORE original permissions-config.json and settings.json; remove permission backup.')
        if not dry_run:
            for name, item in record['files'].items():
                if name not in {p.name for p in paths}:
                    raise Blocked('Unsafe permission backup filename.')
                path = home / name
                if item['before'] is None:
                    path.unlink()
                else:
                    path.write_bytes(base64.b64decode(item['before'], validate=True))
            backup.unlink()
        print('READY: permission configuration rollback' + (' preview.' if dry_run else ' complete.'))
        return 0
    if not plan_value:
        raise Blocked('--permission-plan is required.')
    copilot = shutil.which('copilot')
    if not copilot:
        raise Blocked('Copilot CLI unavailable; no permission changes.')
    version = run([copilot, '--no-auto-update', '--version'], root)
    help_text = run([copilot, '--no-auto-update', 'help', 'permissions'], root)
    if not re.search(r'\b1\.0\.109\b', version) or not all(x in help_text for x in ('--allow-tool', 'read(path?)', 'write(path?)')):
        raise Blocked('Permission configuration compatibility is restricted to CLI 1.0.109; no grants applied.')
    if not (root / '.git').is_dir():
        raise Blocked('Worktree/submodule permission scoping requires separate qualification.')
    if any(os.environ.get(k, '').lower() not in ('', '0', 'false', 'off', 'no')
           for k in ('COPILOT_ALLOW_ALL', 'COPILOT_ASSISTED_APPROVAL')):
        raise Blocked('Inherited automatic approval mode conflicts with narrow setup.')
    plan_path = local_path(root, plan_value)
    plan = json.loads(plan_path.read_text(encoding='utf-8'))
    if not isinstance(plan, dict):
        raise Blocked('Permission plan must be a JSON object.')
    permissions = json.loads(before['permissions-config.json']) if before['permissions-config.json'] is not None else {}
    settings = json.loads(before['settings.json']) if before['settings.json'] is not None else {}
    if not isinstance(permissions, dict) or not isinstance(settings, dict):
        raise Blocked('Configuration must contain JSON objects; JSONC needs manual review.')
    print(f'Existing configuration: {len(settings)} setting keys; values withheld; unrelated settings preserved.')
    if settings.get('defaultPermissionMode', 'manual') != 'manual' or settings.get('defaultMode', 'interactive') == 'autopilot':
        raise Blocked('Existing automatic permission/mode settings require owner review; unchanged.')
    locations = permissions.setdefault('locations', {})
    existing = locations.get(str(root), {})
    if existing.get('tool_approvals') or existing.get('allowed_directories'):
        raise Blocked('Target already has grants; review or roll back them before creating a new profile.')
    commands, flags, fingerprints, omitted = [], [], {}, []
    for field, kind in (('read_files', 'read'), ('edit_files', 'write')):
        values = plan.get(field, [])
        if not isinstance(values, list):
            raise Blocked(f'{field} must be a list of exact files.')
        for value in values:
            path = local_path(root, value)
            if any(c in str(path) for c in '*?[]()\n\r') or not path.is_file():
                raise Blocked('File rules require existing literal file paths without glob/pattern characters.')
            if (any(part in {'.git', '.github', '.agents', '.copilot', '.ai-sdlc-lite'} for part in path.relative_to(root).parts)
                    or path.name.startswith('.env') or path.suffix in ('.key', '.pem')
                    or path.name in {'.npmrc', '.netrc', '.pypirc'}
                    or any(word in path.name.lower() for word in ('secret', 'credential', 'id_rsa', 'id_ed25519'))
                    or (kind == 'write' and path.name in {'package.json', 'package-lock.json', 'npm-shrinkwrap.json',
                                                        'AGENTS.md', 'CLAUDE.md', 'GEMINI.md', 'SECURITY.md', '.gitignore'})):
                raise Blocked('Secret/security/dependency-control files are not auto-authorized.')
            flags.append(f'--allow-tool={kind}({path})')
            fingerprints[value] = digest(path.read_bytes())
    package_path = root / 'package.json'
    no_symlinks(root, package_path)
    scripts = plan.get('scripts', [])
    if not isinstance(scripts, list):
        raise Blocked('scripts must be a list of named npm scripts.')
    if scripts:
        package_bytes = package_path.read_bytes()
        package = json.loads(package_bytes)
        fingerprints['package.json'] = digest(package_bytes)
        print('Package/hook review SHA-256: ' + fingerprints['package.json'])
        for name in scripts:
            if name not in ('lint', 'build', 'test'):
                omitted.append(str(name) + ': preview/browser/cleanup effects cannot be confined by a command name')
                continue
            if not isinstance(package.get('scripts', {}).get(name), str):
                raise Blocked(f'Missing npm script: {name}')
            commands.append('npm run ' + name)
    locations[str(root)] = {**existing, 'tool_approvals': [{'kind': 'commands', 'commandIdentifiers': sorted(set(commands))}]} if commands else existing
    new_settings = copy.deepcopy(settings)
    sandbox = new_settings.setdefault('sandbox', {})
    sandbox['enabled'], sandbox['allowBypass'] = True, False
    after = {'permissions-config.json': (json.dumps(permissions, indent=2) + '\n').encode(),
             'settings.json': (json.dumps(new_settings, indent=2) + '\n').encode()}
    proposal = {'target': str(root), 'version': version.splitlines()[0], 'plan_sha256': digest(plan_path.read_bytes()),
                'file_hashes': fingerprints, 'commands': sorted(set(commands)), 'session_flags': flags,
                'before': {k: digest(v) if v is not None else None for k, v in before.items()},
                'after': {k: digest(v) for k, v in after.items()}}
    token = digest(json.dumps(proposal, sort_keys=True).encode())
    print('Execution-plan proposal (owner declarations; exposure is not verified):')
    print('  Scope/files: ' + json.dumps(sorted(fingerprints)))
    print('  Operations: ' + json.dumps(sorted(set(commands))))
    for field in ('production_exposure', 'credential_exposure', 'filesystem_access', 'network_access', 'risks'):
        print(f'  {field}: ' + json.dumps(plan.get(field, 'UNKNOWN')))
    print('  Approval reference supplied: ' + str(bool(plan.get('approval_reference'))))
    print('  Delivery acceptance: PENDING; setup does not approve implementation.')
    for name, content in after.items():
        print(f'  WRITE {home / name} sha256={digest(content)}; preserve unrelated values')
    print('  SET sandbox.enabled=true; sandbox.allowBypass=false; runtime enforcement remains UNVERIFIED.')
    print(f'  BACK UP exact original bytes privately to {backup}')
    print('  Repository grants: literal npm commands only; no directory/write/interpreter grants.')
    print('  Session-only file rules: ' + json.dumps(flags))
    print('  LIMITATION: saved repository commands persist until guarded rollback; no automatic task expiry.')
    print('  LIMITATION: file rules cover built-in tools only, not shell effects or repository confinement.')
    print('  UNGRANTED: arbitrary verification commands, including Python unittest; no interpreter approximation.')
    print('  Native permission prompt count: UNKNOWN unless a complete operator count or CLI trace is available.')
    for reason in omitted:
        print('  UNGRANTED: ' + reason)
    print('  UNGRANTED: production, secrets, dependencies, push/publication, security changes; other requests may prompt.')
    print('  Script rules do not confine their effects; review lifecycle hooks/config and reapprove changed scope.')
    print('CONSENT TOKEN: ' + token)
    print('Launch: ' + shlex.join(['env', f'COPILOT_HOME={home}', 'copilot', '--no-auto-update', '-C', str(root), *flags]))
    if dry_run or not consent:
        print('READY: preview only; apply with --consent-config TOKEN after separate plan/config review.')
        return 0
    if consent != token or not isinstance(plan.get('approval_reference'), str) or not plan['approval_reference'].strip():
        raise Blocked('Consent token mismatch or missing explicit plan approval reference; no configuration changed.')
    if commands and (plan.get('reviewed_package_sha256') != fingerprints['package.json']
                     or plan.get('production_exposure') != 'NONE_DECLARED'
                     or plan.get('credential_exposure') != 'NONE_DECLARED'):
        raise Blocked('Command grants require matching reviewed package/hook hash and explicit no-production/no-credential declarations.')
    if backup.exists() or (home / CONFIG_BACKUP).exists():
        raise Blocked('Existing backup conflicts; restore/review it first.')
    record = {'target': str(root), 'proposal': proposal, 'files': {
        name: {'before': base64.b64encode(before[name]).decode() if before[name] is not None else None,
               'after': digest(content)} for name, content in after.items()}}
    with os.fdopen(os.open(backup, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600), 'w') as stream:
        json.dump(record, stream)
    for name, content in after.items():
        path = home / name
        if path.exists():
            path.write_bytes(content)
        else:
            with os.fdopen(os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600), 'wb') as stream:
                stream.write(content)
    print('READY: narrow configuration stored; runtime matching, sandbox enforcement and prompt reduction UNVERIFIED.')
    return 0


def local_path(root, value):
    if not isinstance(value, str) or not value or '\\' in value:
        raise Blocked('A nonempty repository-relative path is required.')
    relative = PurePosixPath(value)
    if relative.is_absolute() or '..' in relative.parts:
        raise Blocked('Task context must remain inside the target repository.')
    path = root / relative
    no_symlinks(root, path)
    if path == root / SKILL or path.is_relative_to(root / SKILL):
        raise Blocked('Bundled references cannot be active task records.')
    return path


def initialize_task(root, task_id, contract, dry_run):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}', task_id):
        raise Blocked('Task ID must contain only letters, digits, underscores or hyphens.')
    directory = root / 'tasks' / task_id
    no_symlinks(root, directory)
    record = {'task_id': task_id, 'contract': contract or f'tasks/{task_id}/TASK.md',
              'checklist': f'tasks/{task_id}/CHECKLIST.md',
              'result': f'tasks/{task_id}/RESULT.md'}
    existing_contract = local_path(root, record['contract'])
    if contract and not existing_contract.is_file():
        raise Blocked('Explicit existing task contract must be a regular in-repository file.')
    marker = root / CONTEXT
    no_symlinks(root, marker)
    if marker.exists():
        if json.loads(marker.read_text()) != record:
            raise Blocked('Existing active task context differs; preserve it for owner review.')
        if not all(local_path(root, record[key]).is_file() for key in ('contract', 'checklist', 'result')):
            raise Blocked('Existing task context is incomplete; no automatic repair.')
        print('READY: existing task context preserved, including subsequent record edits.')
        return 0
    additions = {}
    for name in ('TASK.md', 'CHECKLIST.md', 'RESULT.md'):
        if name == 'TASK.md' and contract:
            continue
        path = directory / name
        if path.exists():
            raise Blocked(f'Existing task record refused: {path}')
        text = (SOURCE / name).read_text(encoding='utf-8')
        # Rebase only the shared README link; task records link to each other locally.
        readme = os.path.relpath(root / SKILL / 'framework/README.md', directory).replace(os.sep, '/')
        text = text.replace('](README.md)', f']({readme})').replace('<unique ID>', task_id)
        if name == 'CHECKLIST.md' and contract:
            ref = os.path.relpath(existing_contract, directory).replace(os.sep, '/')
            text = text.replace('](TASK.md)', f']({ref})')
        additions[path] = text.encode()
    if not (root / SKILL / 'framework/README.md').is_file():
        raise Blocked('Install the project Skill before initializing task context.')
    for path, content in additions.items():
        print(f'  CREATE {path} sha256={digest(content)}')
    marker_bytes = (json.dumps(record, indent=2) + '\n').encode()
    print(f'  CREATE {marker} sha256={digest(marker_bytes)}')
    print('Task approval: PENDING for new templates; existing approvals are not inferred or changed.')
    if not dry_run:
        for path, content in {**additions, marker: marker_bytes}.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open('xb') as stream:
                stream.write(content)
    print('READY: task-context preview.' if dry_run else 'READY: task context initialized; no implementation approved.')
    return 0


def configure_copilot(root, home_value, files, dry_run, rollback=False):
    """Opt-in sandbox settings only. Never change CLI tool/path approvals."""
    if not home_value or not Path(home_value).expanduser().is_absolute():
        raise Blocked('Configuration requires an explicit absolute --copilot-home path.')
    home = Path(home_value).expanduser()
    no_symlinks(Path(home.anchor), home)
    if not home.is_dir():
        raise Blocked('Explicit Copilot home must already exist.')
    settings, backup = home / 'settings.json', home / CONFIG_BACKUP
    no_symlinks(home, settings)
    no_symlinks(home, backup)
    before = settings.read_bytes() if settings.exists() else None
    if rollback:
        if not backup.is_file():
            raise Blocked('No configuration backup exists.')
        record = json.loads(backup.read_text())
        if record.get('target') != str(root) or digest(before or b'') != record.get('after_sha256'):
            raise Blocked('Settings changed since configuration; preserve settings and backup.')
        original = base64.b64decode(record['before'], validate=True) if record['before'] is not None else None
        print(f'  RESTORE {settings} from {backup}; remove backup after restoration')
        if not dry_run:
            if original is None:
                settings.unlink()
            else:
                settings.write_bytes(original)
            backup.unlink()
        print('READY: configuration rollback preview.' if dry_run else 'READY: original settings restored.')
        return 0
    document = json.loads(before.decode('utf-8-sig')) if before is not None else {}
    if not isinstance(document, dict):
        raise Blocked('Settings must be a JSON object; JSONC requires manual review.')
    after = copy.deepcopy(document)
    sandbox = after.setdefault('sandbox', {})
    if not isinstance(sandbox, dict):
        raise Blocked('Existing sandbox settings are not an object.')
    sandbox['enabled'] = True
    sandbox['allowBypass'] = False
    if files:
        allowed = workspace(root)
        paths = []
        for value in files:
            path = Path(value).expanduser()
            if not path.is_absolute() or path not in allowed or path.is_symlink() or not path.is_file():
                raise Blocked('Only explicitly named regular ancestor AGENTS.md files are supported.')
            paths.append(str(path))
        policy = sandbox.setdefault('userPolicy', {}).setdefault('filesystem', {})
        existing = policy.setdefault('readonlyPaths', [])
        if not isinstance(existing, list) or any(not isinstance(x, str) for x in existing):
            raise Blocked('Existing readonlyPaths is not a string list.')
        policy['readonlyPaths'] = list(dict.fromkeys([*existing, *paths]))
    content = (json.dumps(after, indent=2) + '\n').encode()
    if backup.exists():
        record = json.loads(backup.read_text())
        if record.get('target') == str(root) and record.get('after_sha256') == digest(before or b'') and after == document:
            print('READY: matching settings and backup preserved without writes.')
            return 0
        raise Blocked('Existing configuration backup conflicts; roll back or review first.')
    print(f'Configuration scope: {home} (applies whenever this COPILOT_HOME is used)')
    print('  SET sandbox.enabled=true; sandbox.allowBypass=false')
    if files:
        print('  APPEND sandbox.userPolicy.filesystem.readonlyPaths: ' + json.dumps(paths))
    print(f'  BACK UP {settings} to {backup}; original settings existed={before is not None}')
    print(f'  WRITE {settings} sha256={digest(content)}; unrelated settings preserved')
    print('Parent CLI path prompts: BLOCKED for automatic single-file grants; unchanged.')
    if not dry_run:
        record = {'target': str(root), 'before': base64.b64encode(before).decode() if before is not None else None,
                  'after_sha256': digest(content)}
        with os.fdopen(os.open(backup, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600), 'w') as stream:
            json.dump(record, stream)
        if settings.exists():
            settings.write_bytes(content)
        else:
            with os.fdopen(os.open(settings, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600), 'wb') as stream:
                stream.write(content)
    print('READY: configuration preview.' if dry_run else
          'READY: sandbox settings saved; host support and enforcement UNVERIFIED. '
          'No tool or directory approvals were granted.')
    print('Launch: ' + shlex.join(['env', f'COPILOT_HOME={home}', 'copilot', '-C', str(root)]))
    return 0


def payload():
    """Copy the local Markdown link closure without changing canonical bytes."""
    pending = [SOURCE / name for name in (*DOCUMENTS, 'LICENSE')]
    bundled = {}
    while pending:
        path = pending.pop()
        if not path.is_relative_to(SOURCE):
            raise Blocked(f'Framework link escapes source: {path}')
        no_symlinks(SOURCE, path)
        relative = path.relative_to(SOURCE).as_posix()
        if relative in bundled:
            continue
        if not path.is_file():
            raise Blocked(f'Missing framework dependency: {relative}')
        content = path.read_bytes()
        bundled[relative] = content
        if path.suffix == '.md':
            for link in LINK.findall(content.decode('utf-8')):
                url = urlsplit(link)
                if url.scheme or url.netloc or not url.path:
                    continue
                linked = Path(unquote(url.path))
                if linked.is_absolute():
                    raise Blocked(f'Absolute framework link refused: {link}')
                # Resolve dot segments without following symlinks.
                pending.append(Path(os.path.abspath(path.parent / linked)))
    entry = (SOURCE / SKILL / 'SKILL.md').read_text(encoding='utf-8')
    for name in DOCUMENTS:
        old = f'](../../../{name})'
        if entry.count(old) != 1:
            raise Blocked(f'Unexpected Skill reference: {name}')
        entry = entry.replace(old, f'](framework/{name})')
    entry += ('\nThe framework/ files are bundled reference material, not target-root '
              'instructions or active task records. Work in the target Git root, '
              'read its own instructions first, and agree on active task/result '
              'paths outside this installed bundle. Do not edit bundled references.\n')
    entry += ('\nBefore asking for earlier task context, check for '
              '`.ai-sdlc-lite/task-context.json` in the target Git root. If present, '
              'read its named contract, checklist and result. Otherwise follow the '
              'Zero-friction defaults and use the request as the task; never '
              'reconstruct a missing approval from conversation assumptions or '
              'bundled templates.\n')
    return {'SKILL.md': entry.encode('utf-8'),
            **{f'framework/{name}': data for name, data in sorted(bundled.items())}}


def inventory(destination):
    files = set()
    for path in destination.rglob('*'):
        no_symlinks(destination, path)
        if path.is_file():
            files.add(path.relative_to(destination).as_posix())
        elif not path.is_dir():
            raise Blocked(f'Non-regular installation entry: {path}')
    return files


def read_manifest(destination):
    path = destination / MANIFEST
    no_symlinks(destination, path)
    if not path.is_file():
        raise Blocked('Existing destination has no installer ownership manifest.')
    record = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(record, dict):
        raise Blocked('Invalid installer manifest.')
    files = record.get('files')
    required = {'SKILL.md', 'framework/LICENSE', *(f'framework/{name}' for name in DOCUMENTS)}
    if record.get('format') != 1 or not isinstance(files, dict) or not required <= files.keys():
        raise Blocked('Invalid installer manifest.')
    for name, sha in files.items():
        relative = PurePosixPath(name)
        if (relative.is_absolute() or '..' in relative.parts or '\\' in name
                or relative.as_posix() != name
                or not (name == 'SKILL.md' or name.startswith('framework/'))
                or not isinstance(sha, str) or not re.fullmatch('[0-9a-f]{64}', sha)):
            raise Blocked('Unsafe installer manifest entry.')
        no_symlinks(destination, destination / name)
    for name in files:
        if any(parent.as_posix() in files for parent in PurePosixPath(name).parents):
            raise Blocked('Ambiguous installer manifest: a file is also a parent path.')
    return files


def uninstall(destination, dry_run):
    if not destination.exists():
        print('READY: no installation exists; nothing to roll back.')
        return 0
    owned = read_manifest(destination)
    present = inventory(destination)
    retained = sorted(present - set(owned) - {MANIFEST})
    directories = {destination}
    for name in owned:
        directories.update(parent for parent in (destination / name).parents
                           if parent == destination or parent.is_relative_to(destination))
    # Empty directories created later are user-owned too, not deletion authority.
    retained.extend(path.relative_to(destination).as_posix() + '/'
                    for path in destination.rglob('*') if path.is_dir() and path not in directories)
    removable = []
    for name, sha in sorted(owned.items()):
        path = destination / name
        if path.exists():
            if path.is_file() and digest(path.read_bytes()) == sha:
                removable.append(path)
            else:
                retained.append(name)
    print('Uninstall preview (unchanged manifest-owned files only):')
    print('Configuration restoration: NOT PERFORMED by Skill uninstall.')
    for path in removable:
        print(f'  REMOVE {path}')
    print(f'  {"KEEP" if retained else "REMOVE"} {destination / MANIFEST}')
    empty_directories = sorted((path for path in directories if path.is_dir()),
                               key=lambda path: (-len(path.parts), path.as_posix())) if not retained else []
    for directory in empty_directories:
        print(f'  RMDIR {directory} (only if empty after owned files are removed)')
    for name in sorted(retained):
        print(f'  PRESERVE {destination / name}')
    if not dry_run:
        removal_scope = [*removable, *empty_directories]
        if not retained:
            removal_scope.append(destination / MANIFEST)
        if any(not os.access(path.parent, os.W_OK | os.X_OK) for path in removal_scope):
            raise Blocked('Removal scope is read-only or unwritable; no removals attempted.')
        for path in removable:
            path.unlink()
        if not retained:
            (destination / MANIFEST).unlink()
            for directory in empty_directories:
                if directory.is_dir() and not any(directory.iterdir()):
                    directory.rmdir()
    if retained:
        print('BLOCKED: edited or unowned files preserved; ownership manifest retained.')
        return 1
    print('READY: rollback preview complete.' if dry_run else
          'READY: installed files removed; empty installation directories removed.')
    return 0


def readiness(root, destination):
    print(f'Installed Skill: {destination}')
    print('References: all six entry links and bundled local dependencies resolve.')
    copilot = shutil.which('copilot')
    if not copilot:
        raise Blocked('Installation complete; Copilot CLI is unavailable on PATH.')
    print('Copilot: ' + run([copilot, '--no-auto-update', '--version'], root).splitlines()[0])
    skills = json.loads(run([copilot, '--no-auto-update', 'skill', 'list', '--json'], root))
    if not isinstance(skills, list) or any(not isinstance(item, dict) for item in skills):
        raise Blocked('Installation complete; unexpected Copilot Skill listing format.')
    matches = [item for item in skills if item.get('name') == 'ai-sdlc-lite']
    if (len(matches) != 1 or matches[0].get('source') != 'project'
            or not matches[0].get('enabled')
            or Path(matches[0].get('path', '')).resolve() != destination):
        raise Blocked('Installation complete; enabled project Skill discovery not verified.')
    print('READY: Copilot discovers the enabled project Skill. No task or permission is approved.')
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', required=True, help='Explicit target Git repository or subdirectory')
    parser.add_argument('--dry-run', action='store_true', help='Preview without writing target files')
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument('--uninstall', action='store_true', help='Remove only unchanged installer-created files')
    actions.add_argument('--check', action='store_true', help='Read-only workspace and installed Skill check')
    actions.add_argument('--init-task', metavar='ID', help='Initialize pending task records or reference a named existing contract')
    actions.add_argument('--configure-copilot', action='store_true', help='Opt in to sandbox settings; no CLI permission grants')
    actions.add_argument('--rollback-config', action='store_true', help='Restore settings only if unchanged since opt-in')
    parser.add_argument('--task-contract', help='Existing repository-relative task contract; requires --init-task')
    parser.add_argument('--copilot-home', help='Explicit absolute configuration directory for opt-in/rollback')
    parser.add_argument('--read-instruction', action='append', default=[], help='Exact ancestor AGENTS.md sandbox read-only path; requires opt-in')
    parser.add_argument('--permission-plan', help='Repository-relative JSON plan for narrow commands and session file rules')
    parser.add_argument('--consent-config', help='Apply the exact permission preview token; separate from task approval')
    args = parser.parse_args(argv)
    try:
        root = target_root(args.target)
        if args.task_contract and not args.init_task:
            raise Blocked('--task-contract requires --init-task.')
        if args.read_instruction and not args.configure_copilot:
            raise Blocked('--read-instruction requires --configure-copilot.')
        if (args.permission_plan or args.consent_config) and not args.configure_copilot:
            raise Blocked('Permission plans/consent require --configure-copilot.')
        if args.consent_config and not args.permission_plan:
            raise Blocked('--consent-config requires --permission-plan.')
        if args.permission_plan and args.read_instruction:
            raise Blocked('Parent-path sandbox settings require the separate existing configuration workflow.')
        if args.copilot_home and not (args.configure_copilot or args.rollback_config):
            raise Blocked('--copilot-home is only used by explicit configuration actions; use COPILOT_HOME for CLI checks.')
        # Recovery validates its own ownership evidence before any removal/restore.
        # It must not depend on active task records, package JSON or development tools.
        if args.uninstall:
            destination = root / SKILL
            no_symlinks(root, destination)
            return uninstall(destination, args.dry_run)
        if args.rollback_config:
            if args.copilot_home and (Path(args.copilot_home).expanduser() / PERMISSION_BACKUP).exists():
                return profile_configuration(root, args.copilot_home, None, None, args.dry_run, rollback=True)
            return configure_copilot(root, args.copilot_home, [], args.dry_run, rollback=True)
        workspace(root)
        preflight(root)
        if args.permission_plan:
            return profile_configuration(root, args.copilot_home, args.permission_plan,
                                         args.consent_config, args.dry_run)
        if (args.configure_copilot and args.copilot_home
                and (Path(args.copilot_home).expanduser() / PERMISSION_BACKUP).exists()):
            raise Blocked('Permission configuration owns this transaction; roll it back before sandbox-only changes.')
        if args.configure_copilot:
            return configure_copilot(root, args.copilot_home, args.read_instruction,
                                     args.dry_run)
        if args.init_task:
            return initialize_task(root, args.init_task, args.task_contract, args.dry_run)
        destination = root / SKILL
        no_symlinks(root, destination)
        if args.check:
            if not (destination / 'SKILL.md').is_file():
                raise Blocked('Project Skill not installed.')
            owned = read_manifest(destination)
            if inventory(destination) != set(owned) | {MANIFEST} or any(
                    digest((destination / name).read_bytes()) != sha for name, sha in owned.items()):
                raise Blocked('Installed Skill differs from its ownership manifest.')
            return readiness(root, destination)
        content = payload()
        hashes = {name: digest(data) for name, data in sorted(content.items())}
        manifest = json.dumps({'format': 1, 'files': hashes}, indent=2, sort_keys=True).encode() + b'\n'
        content[MANIFEST] = manifest
        exists = destination.exists()
        if exists:
            if not destination.is_dir():
                raise Blocked('Skill destination is not a directory.')
            if read_manifest(destination) != hashes or inventory(destination) != set(content):
                raise Blocked('Existing installation differs; no automatic overwrite or upgrade.')
            if any((destination / name).read_bytes() != data for name, data in content.items()):
                raise Blocked('Existing installation has edited files; no overwrite.')
        print('Exact installation preview:')
        for name, data in sorted(content.items()):
            print(f'  {"UNCHANGED" if exists else "CREATE"} {destination / name} sha256={digest(data)}')
        if args.dry_run:
            print('READY: preview only; CLI discovery and installation not exercised.')
            return 0
        if not exists:
            destination.mkdir(parents=True, exist_ok=False)
            # Write ownership first so an interrupted installation can be rolled back.
            for name in [MANIFEST, *sorted(hashes)]:
                data = content[name]
                path = destination / name
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open('xb') as stream:
                    stream.write(data)
        return readiness(root, destination)
    except (Blocked, OSError, ValueError, TypeError, AttributeError, KeyError, subprocess.SubprocessError) as error:
        print(f'BLOCKED: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
