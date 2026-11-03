"""Real BLE availability/input audit; no invented metre scale or target labels."""
import argparse
import csv
from collections import Counter
import hashlib
from pathlib import Path
from .service import observations, localize
from .study import save

URL='https://archive.ics.uci.edu/dataset/435/ble-rssi-dataset-for-indoor-localization-and-navigation'


def run(output):
    out=Path(output); out.mkdir(parents=True,exist_ok=False)
    data=Path(__file__).parent/'data'
    rows=list(csv.DictReader((data/'iBeacon_RSSI_Labeled.csv').open()))
    counts=Counter(sum(float(v)>-200 for k,v in row.items() if k.startswith('b')) for row in rows)
    # Exercise only documented missing-value handling. No coordinates are fabricated for localization.
    save(out/'audit.json',dict(source=URL,doi='10.24432/C54G80',license='CC BY 4.0',
         creators=['Mehdi Mohammadi','Ala Al-Fuqaha'],labelled_rows=len(rows),
         observed_beacon_counts=dict(sorted(counts.items())),rows_n_gt_10=sum(v for k,v in counts.items() if k>10),
         source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in data.glob('iBeacon*')},
         missing_value=-200,metre_scale_verified=False,
         conclusion='Real RSSI downloaded and audited, but no metric localization validation claimed: map has no verified metre scale; beacon array is not independent crowd reporters.',
         other_sources=[dict(url='https://data.mendeley.com/datasets/hp82nbgfy7/2',result='Public HTTP download/API returned 403 in this session'),
                        dict(url='https://zenodo.org/records/19076975',result='8 beacons; PDF fetch returned 429; not n>10')]))


if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('output'); a=p.parse_args(); run(a.output)
