"""Render the corrected paper headers from the saved Blender model."""
from pathlib import Path
import json
import bpy
root = Path('D:/projects/claire-vinyl-preview/modern-v03')
for key in ('about','projects','world'):
    body=bpy.data.objects['Independent '+key+' insert']
    title=bpy.data.objects['Readable top title '+key]
    # Validate the specific correction before producing review images.
    body_top=max(v.co.z+body.location.z for v in body.data.vertices)
    assert abs(body_top-1.435)<.001
    assert max(v.co.z for v in title.data.vertices)<body_top
    assert min(v.co.z for v in title.data.vertices)>1.135
assert not any(o.name.startswith(('Raised title tab support','Exposed title tab ')) for o in bpy.data.objects)
scene=bpy.context.scene
scene.cycles.samples=64
scene.render.resolution_x=1600;scene.render.resolution_y=900
scene.render.resolution_percentage=100
prefs=bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type='OPTIX';prefs.get_devices()
for d in prefs.devices:d.use=d.type!='CPU'
scene.cycles.device='GPU'
for frame,name in [(135,'hero-idle.png'),(163,'hero-hover-projects.png')]:
    scene.frame_set(frame)
    scene.render.filepath=str(root/name)
    bpy.ops.render.render(write_still=True)
manifest_path=root/'model-manifest.json'
manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
manifest['objects']=len(bpy.data.objects)
manifest['header_design']='single continuous paper sheet with printed upper header'
manifest_path.write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print('HEADERS_CONNECTED_AND_RENDERED')
