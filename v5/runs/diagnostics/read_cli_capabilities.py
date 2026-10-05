"""Read only public CLI model/usage metadata, never credentials or config files."""
import json
import queue
import shutil
import subprocess
import threading
import time
from pathlib import Path


def main():
    p = subprocess.Popen([shutil.which('codex'), 'app-server', '--stdio'], stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, encoding='utf-8',
                         creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    q = queue.Queue()
    def reader():
        for line in p.stdout:
            try: q.put(json.loads(line))
            except ValueError: pass
    threading.Thread(target=reader,daemon=True).start()
    def send(o):
        p.stdin.write(json.dumps(o)+'\n');p.stdin.flush()
    def receive(identifier):
        until=time.monotonic()+25
        while time.monotonic()<until:
            obj=q.get(timeout=max(.01,until-time.monotonic()))
            if obj.get('id')==identifier:return obj
        raise TimeoutError('metadata request timed out')
    try:
        send({'id':1,'method':'initialize','params':{'clientInfo':{'name':'phase5-readonly-preflight','version':'1'}}})
        receive(1);send({'method':'initialized','params':{}})
        send({'id':2,'method':'account/rateLimits/read','params':{}})
        limits=receive(2)
        send({'id':3,'method':'model/list','params':{'limit':50,'includeHidden':False}})
        models=receive(3)
        result={'rate_limits':limits.get('result',limits.get('error')),
                'models':[{k:r.get(k) for k in ('model','isDefault','defaultReasoningEffort')}
                          for r in models.get('result',{}).get('data',[])],
                'model_error':models.get('error'),'inference_calls':0,'credentials_read':False}
        # Keep no account identifiers, reset-credit identifiers, or auth fields.
        if isinstance(result['rate_limits'],dict):
            result['rate_limits']={k:v for k,v in result['rate_limits'].items()
                                   if k in ('rateLimits','rateLimitsByLimitId','ordinaryUsageAllowed')}
        destination=Path(__file__).with_name('cli_capabilities.json')
        with destination.open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
        print(json.dumps(result,indent=2))
    finally:
        p.terminate();p.wait(timeout=10)


if __name__=='__main__':main()
