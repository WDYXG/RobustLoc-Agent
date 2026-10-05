"""Isolated, time-bounded mathematical worker. Input/output only, no file writes."""
import json
import sys
from .gate import evaluate


if __name__ == '__main__':
    request = json.load(sys.stdin)
    print(json.dumps(evaluate(request['proposal'], request['operation_limit']), ensure_ascii=False, allow_nan=False))
