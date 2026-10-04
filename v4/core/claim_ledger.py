STATUSES={'known','proved-in-project','conjectured','numerically-supported','refuted'}


def entry(identifier,status,claim,evidence,scope):
    if status not in STATUSES or not evidence or not scope: raise ValueError('claim requires status, evidence and scope')
    return dict(id=identifier,status=status,claim=claim,evidence=evidence,scope=scope)
