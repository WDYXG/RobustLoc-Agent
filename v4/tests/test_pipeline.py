from pathlib import Path
from v4.storage import read
from v4.run import execute


def test_development_end_to_end_and_all_legacy_regressions(tmp_path):
    cfg=read(Path(__file__).resolve().parents[1]/'config.json')
    cfg.update(recovery_variants_per_problem=1,active_variants_per_problem=1,robust_active_variants=4)
    result=execute(tmp_path/'development-pipeline',cfg,development=True)
    assert result['passed'] and result['range_regressions']==43
    assert result['recovered']==4 and result['counterexample_families_verified']==4
