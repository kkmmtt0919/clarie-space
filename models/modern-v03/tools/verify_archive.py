"""Verify archive and untouched V2 against the original SHA-256 manifest."""
from pathlib import Path
import json,hashlib

root=Path(__file__).resolve().parents[1]
archive=root.parent/'archives'/'modern-v02-20261005-170425'
manifest=json.loads((archive/'manifest-sha256.json').read_text(encoding='utf-8-sig'))
for base in (archive/'modern-v02',root.parent/'modern-v02'):
    files=[p for p in base.rglob('*') if p.is_file()]
    assert len(files)==len(manifest), ('File count changed',str(base))
    for entry in manifest:
        path=base/entry['path']
        assert path.stat().st_size==entry['bytes'],str(path)
        assert hashlib.sha256(path.read_bytes()).hexdigest().upper()==entry['sha256'],str(path)
report={'passed':True,'files':len(manifest),'bytes':sum(e['bytes'] for e in manifest),'archive':str(archive),'v2_source_unchanged':True,'sha256_verified':True}
(root/'archive-verification-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report))
