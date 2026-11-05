"""Re-download the versioned public release and verify publisher SHA-256 values."""
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request

INDEX = 'https://data.mendeley.com/public-api/datasets/3v9mcsvcd2/files?folder_id=root&version=1'


def fetch(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'}), timeout=45).read()


def download(output):
    out = Path(output); out.mkdir(parents=True, exist_ok=False)
    data = fetch(INDEX); (out/'source-index.json').write_bytes(data)
    for item in json.loads(data):
        name = item['filename']; detail = item['content_details']
        if Path(name).name != name or not (name.endswith('.csv') or name=='APS_Positions.txt'):
            raise ValueError('Unexpected release filename')
        url = detail['download_url']
        if not url.startswith('https://data.mendeley.com/public-files/datasets/3v9mcsvcd2/files/'):
            raise ValueError('Unexpected public download host/path')
        content = fetch(url)
        if hashlib.sha256(content).hexdigest()!=detail['sha256_hash']:
            raise ValueError('Publisher hash mismatch: '+name)
        (out/name).write_bytes(content)
        print(name, len(content), 'verified', flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('output'); a=p.parse_args(); download(a.output)
