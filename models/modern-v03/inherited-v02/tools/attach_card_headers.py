"""Local correction: make every title the printed header of one continuous insert."""
from pathlib import Path
from datetime import datetime, timezone
import json
import bpy

root = Path('D:/projects/claire-vinyl-preview/modern-v03')
target = root / 'claire-modern-v03.blend'
assert Path(bpy.data.filepath).resolve() == target.resolve()
scene = bpy.context.scene
assert scene.get('claire_model_version') == 'modern-v03'
keys = ('about','projects','world')
for key in keys:
    assert bpy.data.objects.get('Independent '+key+' insert')
    assert bpy.data.objects.get('Readable top title '+key)
instance = bpy.app.driver_namespace.get('claire_modern_v03_preview_runtime', {}).get('instance')
if instance is not None:
    instance.finish(bpy.context, restore=True)
if bpy.context.area and bpy.context.area.type == 'CONSOLE':
    bpy.context.area.type = 'VIEW_3D'
stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
backups = root / 'session-backups'
backups.mkdir(exist_ok=True)
backup = backups / ('claire-modern-v03-before-header-fix-'+stamp+'.blend')
result = bpy.ops.wm.save_as_mainfile(filepath=str(backup), copy=True, check_existing=False)
assert 'FINISHED' in result and backup.stat().st_size > 1024
scene.frame_set(135)
report = {'backup':str(backup),'headers':[]}
for key in keys:
    body = bpy.data.objects['Independent '+key+' insert']
    # Keep the bottom, printed square, and root transform fixed.
    for vertex in body.data.vertices:
        if vertex.co.z > 0:
            vertex.co.z = 1.435 - body.location.z
    body.data.update()
    title = bpy.data.objects['Readable top title '+key]
    old_center = sum(v.co.z for v in title.data.vertices)/len(title.data.vertices)
    for vertex in title.data.vertices:
        vertex.co.z += 1.285-old_center
        vertex.co.y = -.024
    title.data.update()
    title['attached_to_continuous_insert'] = True
    title['header_center_z'] = 1.285
    plate = bpy.data.objects.get('Exposed title tab '+key)
    if plate:
        bpy.data.objects.remove(plate, do_unlink=True)
    report['headers'].append({'entry':key,'body_top':1.435,'text_bottom':1.18,'text_top':1.39})
for obj in list(bpy.data.objects):
    if obj.name.startswith('Raised title tab support'):
        bpy.data.objects.remove(obj, do_unlink=True)
bpy.context.view_layer.update()
scene['claire_header_design'] = 'continuous printed insert / no detached signs'
result = bpy.ops.wm.save_as_mainfile(filepath=str(target), check_existing=False)
assert 'FINISHED' in result
report['saved'] = True
(root / 'attached-headers-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
