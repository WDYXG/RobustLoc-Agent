"""Read-only integrity audit; emit a write-once delivery snapshot."""
import json
import subprocess
from pathlib import Path

from v5.researcher.io import ROOT, check_hashes, file_hash, read, write_new


def main():
    checks = {}
    prior = read(ROOT / 'v5/PREVIOUS_FREEZE.json')
    checks['historical_files_unchanged'] = check_hashes(prior['files'])
    assert checks['historical_files_unchanged'] == prior['count'] == 4083
    for policy in ('scripted', 'codex'):
        folder = ROOT / f'v5/runs/paired-v2-{policy}-001'
        transport = read(folder / 'transport_manifest.json')
        for field in ('scientific_sources', 'transport_sources'):
            checks[f'{policy}_{field}'] = check_hashes(transport[field])
        manifest = read(folder / 'scientific/manifest.json')
        checks[f'{policy}_scientific_manifest_sources'] = check_hashes(manifest['source_hashes'])
        outputs = read(folder / 'scientific/output_hashes.json')
        checks[f'{policy}_outputs'] = check_hashes({
            (folder / 'scientific' / p).relative_to(ROOT).as_posix(): h
            for p, h in outputs.items()})
        assert read(folder / 'audit.json')['passed']
        assert len(read(folder / 'scientific/ledger.json')) == 12
    folder = ROOT / 'v5/runs/paired-v2-codex-001'
    resume = read(folder / 'RESUME_MANIFEST.json')
    checks['resume_sources'] = check_hashes(resume['source_hashes'])
    checks['preinterruption_artifacts_unchanged'] = check_hashes(resume['preexisting_artifact_hashes'])
    resume_audit = read(folder / 'RESUME_AUDIT.json')
    assert resume_audit['passed'] and resume_audit['captured_completed_turns'] == 11
    folder = ROOT / 'v5/runs/comparison-v3-001'
    final = read(folder / 'manifest.json')
    checks['report_evaluator_sources'] = check_hashes(final['sources'])
    checks['report_evaluator_inputs'] = check_hashes(final['inputs'])
    checks['report_evaluator_outputs'] = check_hashes({
        (folder / p).relative_to(ROOT).as_posix(): h
        for p, h in read(folder / 'output_hashes.json').items()})
    published = subprocess.check_output(
        ['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z', '--', 'v5'],
        cwd=ROOT).decode('utf-8').split('\0')
    paths = sorted(set(p for p in published if p))
    assert 'v5/runs/diagnostics/cli_capabilities.json' not in paths
    target = ROOT / 'v5/runs/DELIVERY_AUDIT.json'
    hashes = {p: file_hash(ROOT / p) for p in paths if ROOT / p != target}
    write_new(target, {
        'schema': 'phase5-final-delivery-integrity-v1',
        'baseline_commit': prior['baseline_commit'], 'passed': True,
        'checks': checks, 'files_excluding_this_manifest': hashes,
        'scope': 'Byte integrity and retained audit assertions; not new mathematical validation.',
    })
    print(json.dumps({'passed': True, 'checks': checks, 'delivery_files': len(hashes)}))


if __name__ == '__main__':
    main()
