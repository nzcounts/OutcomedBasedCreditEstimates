"""Check the recorded source archive hashes before fitting."""
from pathlib import Path
import hashlib, os
base=Path(__file__).resolve().parents[1]
data=Path(os.environ.get('MEPS_DATA_DIR',str(base/'data'/'raw')))
for line in (base/'data/SOURCE_DATA_SHA256.txt').read_text().splitlines():
    expected,name=line.split(None,1)
    p=data/name
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    if h.hexdigest()!=expected:raise SystemExit('Input hash mismatch: '+name)
    print('PASS',name)
