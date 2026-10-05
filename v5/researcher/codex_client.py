"""Real CLI transport; no fake provider, key discovery, or output substitution."""
import json
import shutil
import subprocess
import time
import re
from pathlib import Path
from .io import write_new


def cli_path():
    p = shutil.which('codex')
    if not p:
        raise RuntimeError('Codex CLI is not on PATH')
    return p


def preflight():
    try:
        p = cli_path()
        version = subprocess.run([p, '--version'], capture_output=True, text=True, encoding='utf-8', timeout=20)
        login = subprocess.run([p, 'login', 'status'], capture_output=True, text=True, encoding='utf-8', timeout=20)
        # Never read auth.json, configuration secrets, or echo environment values.
        return {'available': True, 'cli_version': version.stdout.strip(),
                'authenticated': login.returncode == 0,
                'login_status': (login.stdout + login.stderr).strip(), 'login_exit_code': login.returncode}
    except (RuntimeError, OSError, subprocess.TimeoutExpired) as exc:
        return {'available': False, 'authenticated': False, 'reason': str(exc)}


def command(workspace, schema, output):
    args = [cli_path(), 'exec', '--ignore-user-config', '--ignore-rules', '--ephemeral',
            '--skip-git-repo-check', '--sandbox', 'read-only', '--json', '--color', 'never',
            '-C', str(workspace), '--output-schema', str(schema), '-o', str(output)]
    for cfg in ['approval_policy="never"', 'project_doc_max_bytes=0', 'web_search="disabled"',
                'features.shell_tool=false', 'features.unified_exec=false', 'features.apps=false',
                'features.plugins=false', 'features.hooks=false', 'features.multi_agent=false',
                'features.browser_use=false', 'features.computer_use=false', 'features.image_generation=false',
                'features.memories=false', 'features.skill_search=false', 'features.skip_host_skill_discovery=true']:
        args += ['-c', cfg]
    return args + ['-']


def propose(prompt, workspace, schema, timeout):
    workspace = Path(workspace).resolve()
    output = workspace/'model_output.json'
    args = command(workspace, Path(schema).resolve(), output)
    write_new(workspace/'invocation.json', {'argv': args, 'model_selection': 'CLI built-in default; user configuration deliberately disabled',
              'model_id': None, 'timeout_seconds': timeout, 'sandbox': 'read-only'})
    start = time.perf_counter(); timed_out = False
    try:
        proc = subprocess.run(args, input=prompt, capture_output=True, text=True, encoding='utf-8',
                              errors='replace', timeout=timeout, cwd=workspace)
        stdout, stderr, code = proc.stdout, proc.stderr, proc.returncode
    except subprocess.TimeoutExpired as exc:
        timed_out = True; code = None
        stdout, stderr = exc.stdout or b'', exc.stderr or b''
        if isinstance(stdout, bytes): stdout = stdout.decode('utf-8', errors='replace')
        if isinstance(stderr, bytes): stderr = stderr.decode('utf-8', errors='replace')
    for name, data in [('events.jsonl', stdout), ('stderr.txt', stderr)]:
        with (workspace/name).open('x', encoding='utf-8', newline='\n') as f:
            f.write(data)
    events = []
    for line in stdout.splitlines():
        try: events.append(json.loads(line))
        except json.JSONDecodeError: pass
    usage = [e.get('usage') for e in events if e.get('type') == 'turn.completed']
    items = [e['item'] for e in events if isinstance(e.get('item'), dict)]
    forbidden = [i for i in items if i.get('type') not in ('agent_message', 'reasoning')]
    meta = {'provider': 'codex-cli', 'wall_seconds': time.perf_counter()-start,
            'returncode': code, 'timed_out': timed_out, 'usage': usage, 'dollar_cost': None,
            'dollar_cost_reason': 'no authenticated billing receipt or validated price in this experiment',
            'thread_ids': [e['thread_id'] for e in events if e.get('type') == 'thread.started'],
            'completed_turns': len(usage), 'unexpected_tool_items': len(forbidden),
            'model_id': None, 'model_id_reason': 'not inferred from the surrounding chat; fill only if transport reports it'}
    reported = re.search(r'^model:\s*(\S+)\s*$', stderr, re.MULTILINE)
    if reported:
        meta['model_id'] = reported.group(1)
        meta['model_id_reason'] = 'reported by CLI stderr header'
    if timed_out or code != 0 or not output.exists() or len(usage) != 1 or forbidden:
        return None, dict(meta, error='CLI failure, missing completion receipt, timeout or forbidden external tool use')
    try:
        proposal = json.loads(output.read_text(encoding='utf-8'))
    except (ValueError, OSError) as exc:
        return None, dict(meta, error='invalid structured output: ' + str(exc))
    return proposal, meta


def verify_receipt(workspace, proposal, meta):
    """Bind stored provider output to proposal and token usage, without inference."""
    workspace = Path(workspace)
    events = []
    for line in (workspace/'events.jsonl').read_text(encoding='utf-8').splitlines():
        try: events.append(json.loads(line))
        except json.JSONDecodeError: pass
    usage = [e.get('usage') for e in events if e.get('type') == 'turn.completed']
    ids = [e['thread_id'] for e in events if e.get('type') == 'thread.started']
    forbidden = [e['item'] for e in events if isinstance(e.get('item'),dict)
                 and e['item'].get('type') not in ('agent_message','reasoning')]
    if usage != meta['usage'] or ids != meta['thread_ids'] or len(forbidden) != meta['unexpected_tool_items']:
        raise ValueError('provider usage/thread/tool receipt mismatch')
    if proposal is not None:
        if len(usage)!=1 or not ids or forbidden or meta['timed_out'] or meta['returncode']!=0:
            raise ValueError('successful proposal lacks a clean completed provider turn')
        actual = json.loads((workspace/'model_output.json').read_text(encoding='utf-8'))
        if actual!=proposal:
            raise ValueError('stored proposal differs from actual provider output')
        messages = [e['item']['text'] for e in events if e.get('type')=='item.completed'
                    and e.get('item',{}).get('type')=='agent_message' and 'text' in e['item']]
        if not any(_same_json(m,proposal) for m in messages):
            raise ValueError('provider event stream does not contain the saved final proposal')
    return True


def _same_json(text, proposal):
    try: return json.loads(text)==proposal
    except (TypeError, ValueError): return False
