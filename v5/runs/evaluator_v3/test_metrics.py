from v5.runs.evaluator_v3.run import corrected_metrics


def row(i,status,parent='',key=None,failure=None):
    return {'id':i,'status':status,'parent_id':parent,'family':'polynomial','semantic_key':key or i,
            'ledger_advancing':status in ('proved-in-project','refuted'),'failure_kind':failure}


def test_refuted_repair_is_not_success():
    a=row('r1','refuted');b=row('r2','refuted','r1')
    m,_=corrected_metrics([a,b],{'successful_conjecture_revisions':1})
    assert m['successful_formal_revisions']==0 and m['successful_refuted_claim_repairs']==0
    assert m['failed_refuted_claim_repairs']==1 and m['legacy_successful_conjecture_revisions']==1


def test_genuine_verified_revision_is_counted():
    a=row('r1','refuted');b=row('r2','proved-in-project','r1')
    m,_=corrected_metrics([a,b],{'successful_conjecture_revisions':1})
    assert m['successful_formal_revisions']==1 and m['successful_refuted_claim_repairs']==1


def test_same_claim_proof_correction_separate_from_changed_claim():
    a=row('r1','unresolved',key='same',failure='verification-rejected')
    b=row('r2','proved-in-project','r1',key='same')
    m,_=corrected_metrics([a,b],{'successful_conjecture_revisions':0})
    assert m['successful_formal_revisions']==0 and m['successful_post_rejection_corrections']==1
