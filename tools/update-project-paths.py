"""Update current project references while preserving historical model archives."""
from pathlib import Path
import json
root = Path(__file__).resolve().parents[1]
mapping = {
    'D:/projects/claire-html-v03': str(root).replace('\\','/'),
    'D:/projects/claire-vinyl-preview': str(root/'models').replace('\\','/'),
    'D:/projects/claire-homepage-handoff': str(root/'docs/handoff').replace('\\','/'),
    'D:/projects/review-20261006-claire': str(root/'reviews/2026-10-06').replace('\\','/'),
    'D:/projects/generated-images': str(root/'references/legacy-generated').replace('\\','/'),
    'D:/projects/skill/emil-design-eng': str(root/'skills/emil-design-eng').replace('\\','/'),
}
files = [root/'README.md', root/'models/modern-v03/README.md',
         root/'models/modern-v03/model-manifest.json',
         root/'models/modern-v03/tools/bootstrap_live.py',
         root/'models/modern-v03/tools/backup_live_session.py']
files += list((root/'docs/handoff').rglob('*.md'))
files += [p for p in (root/'docs').glob('*.md')]
updated = []
for path in files:
    if not path.is_file():
        continue
    original = path.read_text(encoding='utf-8-sig')
    text = original
    for old,new in mapping.items():
        text = text.replace(old,new)
        text = text.replace(old.replace('/','\\'),new.replace('/','\\'))
        text = text.replace(old.replace('/','\\\\'),new.replace('/','\\\\'))
    if path.name == '交互与文字精进方案-v3.md':
        text = text.replace('../../skill/emil-design-eng/SKILL.md','../../../skills/emil-design-eng/SKILL.md')
        for skill in ('gc-minimal-zine-poster-v0-3','heytea-doodle-poster','guizang-product-video-skill'):
            text=text.replace('../../skill/'+skill+'/SKILL.md','D:/projects/skill/'+skill+'/SKILL.md')
    if text != original:
        path.write_text(text,encoding='utf-8',newline='\n')
        updated.append(str(path.relative_to(root)))
(root/'docs/path-updates-2026-10-06.json').write_text(json.dumps({
    'updated':updated,'mapping':mapping,
    'historical_archives':'models/archives, models/modern-v02 and inherited-v02 left unchanged'
},ensure_ascii=False,indent=2),encoding='utf-8')
print('UPDATED_CURRENT_REFERENCES',len(updated))
