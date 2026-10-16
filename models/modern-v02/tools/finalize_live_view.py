"""Set the delivered model's review UI, without changing model geometry."""
from pathlib import Path
import json
import bpy

root = Path('D:/projects/claire-vinyl-preview/modern-v02')
target = root / 'claire-modern-v02.blend'
assert Path(bpy.data.filepath).resolve() == target.resolve()
assert bpy.context.scene.get('claire_model_version') == 'modern-v02'
bpy.context.scene.frame_set(135)
area = bpy.context.area
area.type = 'VIEW_3D'
space = area.spaces.active
space.show_region_ui = True
space.region_3d.view_perspective = 'CAMERA'
space.region_3d.view_camera_zoom = 7
space.region_3d.view_camera_offset = (.075, 0)
space.shading.type = 'MATERIAL'
space.shading.use_scene_lights = True
space.shading.use_scene_world = True
space.overlay.show_overlays = False
result = bpy.ops.wm.save_as_mainfile(filepath=str(target), check_existing=False)
assert 'FINISHED' in result
(root / 'live-preview-ready.json').write_text(json.dumps({
    'file': bpy.data.filepath, 'frame': bpy.context.scene.frame_current,
    'runtime_registered': hasattr(bpy.types, 'CLAIREMODERN_PT_motion_preview'),
    'saved': True
}, indent=2), encoding='utf-8')
