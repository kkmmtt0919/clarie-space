"""Reproducible V3 build from the preserved V2 model, including header corrections."""
from pathlib import Path
import runpy
import bpy
root = Path(__file__).resolve().parent
source = root.parent / 'modern-v02' / 'claire-modern-v02.blend'
bpy.ops.wm.open_mainfile(filepath=str(source), use_scripts=False)
runpy.run_path(str(root / 'tools' / 'upgrade_motion.py'), run_name='__main__')
