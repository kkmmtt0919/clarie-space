"""Read-only Blender checks on the archived V2 model; write only a V3 report."""
from pathlib import Path
import bpy,json
root=Path(__file__).resolve().parents[1]
scene=bpy.context.scene
assert scene.get('claire_model_version')=='modern-v02'
names=json.loads(scene['claire_root_names'])
assert len(names['cards'])==len(names['discs'])==3
assert all(bpy.data.images['disc-'+key+'.png'].packed_file for key in ('about','projects','world'))
scene.frame_set(1)
assert abs(scene.objects[names['hinge']].rotation_euler.x)<1e-5
scene.frame_set(135)
report={'passed':True,'opened':bpy.data.filepath,'version':'modern-v02','cards':3,'discs':3,'textures_packed':True,'file_saved':False}
(root/'archived-model-open-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('ARCHIVED_V2_OPENED',json.dumps(report))
