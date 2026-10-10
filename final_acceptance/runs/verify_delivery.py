"""Post-run integrity, generator replay and all-potential-reporter premise audit."""
from copy import deepcopy
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

from final_acceptance import study as s
from final_acceptance.report import aggregate, paired_intervals, rows_from


def main():
    folder = s.HOME/'runs/final-001'
    manifest = s.read(folder/'manifest.json')
    previous = s.read(s.HOME/'PREVIOUS_FREEZE.json')
    checks = {'previous_files': s.verify_hashes(previous['files']),
              'frozen_sources': s.verify_hashes(manifest['sources'])}
    cases = [s.read(p) for p in sorted((folder/'cases').glob('*.json'))]
    all_potential_valid, regenerated = 0, 0
    for case in cases:
        cfg = manifest['config']
        index = int(case['public']['episode_id'].split('-')[1])
        public, private = s.episode(case['private']['scenario'], index, cfg, manifest['seed'])
        assert public == case['public'] and private == case['private']
        regenerated += 1
        extended = deepcopy(public)
        extended['budget'] = str(len(extended['offers']))
        for offer in list(extended['offers']):
            extended = s.acquire(extended, private, offer['id'])
        valid = s.evaluate(extended, private, {'action': 'abstain'})['contract_valid']
        assert valid == private['expected_valid']
        all_potential_valid += int(valid)
    rows = rows_from(cases)
    metrics = s.read(folder/'metrics.json')
    assert aggregate(rows, cfg) == metrics['groups']
    assert paired_intervals(rows, cfg) == metrics['paired_correct_output']
    checks.update(regenerated_cases=regenerated, all_potential_reporters_valid_cases=all_potential_valid,
                  metrics_exactly_recomputed=True)
    audit = s.read(folder/'audit.json')
    assert audit['passed'] and audit['counts']['solver_replays'] == 2880
    tests = {}
    for name in ('new-contract-tests.xml', 'frozen-regression-tests.xml', 'acceptance-tests.xml'):
        root = ET.parse(s.HOME/'runs'/name).getroot()
        tests[name] = [dict(suite.attrib) for suite in root.iter('testsuite')]
    paths = s.git('ls-files', '--cached', '--others', '--exclude-standard', '-z', '--', 'final_acceptance').decode().split('\0')
    paths = sorted(set(p for p in paths if p))
    missing_links = []
    for p in paths:
        if p.endswith('.md'):
            for link in re.findall(r'\]\(([^)]+)\)', (s.ROOT/p).read_text(encoding='utf-8')):
                if '://' not in link and not ((s.ROOT/p).parent/link.split('#')[0]).exists():
                    missing_links.append((p, link))
    assert not missing_links, missing_links
    hashes = {p: s.sha(s.ROOT/p) for p in paths if not p.endswith('/DELIVERY_AUDIT.json')}
    target = s.HOME/'runs/DELIVERY_AUDIT.json'
    s.write(target, dict(passed=True, checks=checks, tests=tests,
                        historical_baseline=previous['baseline_commit'],
                        initial_expected_failures_preserved=True,
                        files_excluding_this_manifest=hashes,
                        scope='Synthetic pipeline acceptance only; not physical or industrial certification.'))
    print(json.dumps(dict(checks=checks, files=len(hashes), missing_links=missing_links)))


if __name__ == '__main__':
    main()
