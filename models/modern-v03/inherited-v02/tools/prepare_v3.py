"""Prepare independent V3 source files; never writes V2."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
assert root.name == 'modern-v03'
for path in root.rglob('*.py'):
    if path == Path(__file__).resolve():
        continue
    text = path.read_text(encoding='utf-8')
    text = text.replace('modern-v02', 'modern-v03').replace('modern_v02', 'modern_v03')
    text = text.replace('CLAIREMODERN', 'CLAIREV3').replace('claire_modern.', 'claire_v3.')
    path.write_text(text, encoding='utf-8')

# Keep old rebuild recipes, but the V3 entrypoint upgrades the saved V2 geometry.
builder = root / 'build_modern_scene.py'
builder.rename(root / 'build_geometry_base.py')
builder.write_text('''"""Reproducible V3 build from the preserved V2 model, including header corrections."""
from pathlib import Path
import runpy
import bpy
root = Path(__file__).resolve().parent
source = root.parent / 'modern-v02' / 'claire-modern-v02.blend'
bpy.ops.wm.open_mainfile(filepath=str(source), use_scripts=False)
runpy.run_path(str(root / 'tools' / 'upgrade_motion.py'), run_name='__main__')
''', encoding='utf-8')

# Separate GUI helper from its original main program; target PID is verified.
old = (root / 'tools' / 'load_ready_model.py').read_text(encoding='utf-8')
prefix = old.split("if '--probe-console' in sys.argv:")[0]
prefix = prefix.replace('pid.value==35936', 'pid.value==int(sys.argv[1])')
body = '''
if __name__ == '__main__':
    action = sys.argv[2]
    script = ROOT / 'tools' / ('backup_live_session.py' if action == 'backup' else 'open_v3_live.py')
    report = ROOT / ('live-session-backup.json' if action == 'backup' else 'live-v3-ready.json')
    before_time = time.time()
    console_command("exec(compile(open(r'%s',encoding='utf-8').read(),'<claire-v3-session>','exec'))" % str(script).replace('\\\\','/'))
    for _ in range(40):
        time.sleep(.5)
        if report.exists() and report.stat().st_mtime >= before_time:
            state = json.loads(report.read_text(encoding='utf-8'))
            if state.get('error'): raise RuntimeError(state['error'])
            print(json.dumps(state, ensure_ascii=False)); break
    else: raise RuntimeError('Blender did not confirm operation')
'''
(root / 'tools' / 'desktop_session.py').write_text(prefix + body, encoding='utf-8')
