"""Open tested V3 only after confirming the earlier independent live backup."""
from pathlib import Path
import bpy, json
from datetime import datetime, timezone

root = Path('D:/projects/claire-vinyl-preview/modern-v03')
report = root/'live-v3-ready.json'
state = {}
try:
    saved = json.loads((root/'live-session-backup.json').read_text(encoding='utf-8'))
    assert saved.get('saved') and Path(saved['backup']).is_file(), 'Unsaved V2 backup must exist first.'
    for key in ('claire_modern_v02_preview_runtime', 'claire_modern_v03_preview_runtime'):
        record = bpy.app.driver_namespace.get(key, {})
        if record.get('instance') is not None:
            try: record['instance'].finish(bpy.context, restore=True)
            except ReferenceError: record['instance'] = None
    if bpy.context.screen and bpy.context.screen.is_animation_playing:
        bpy.ops.screen.animation_cancel(restore_frame=False)
    # Save again so any edits made during rendering are also recoverable.
    target = root/'claire-modern-v03.blend'
    assert target.is_file()
    current_backup = Path(saved['backup'])
    current_backup = root.parent/'archives'/('live-session-before-v3-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.blend')
    if bpy.context.area and bpy.context.area.type == 'CONSOLE': bpy.context.area.type = 'VIEW_3D'
    bpy.ops.wm.save_as_mainfile(filepath=str(current_backup), copy=True, check_existing=False)
    assert current_backup.is_file() and current_backup.stat().st_size > 1024
    bpy.ops.wm.open_mainfile(filepath=str(target), load_ui=True, use_scripts=False)
    assert bpy.context.scene.get('claire_model_version') == 'modern-v03'
    namespace = {'__name__':'claire_v3_live'}
    exec(compile((root/'claire_preview_runtime.py').read_text(encoding='utf-8'), '<claire-v3-runtime>', 'exec'), namespace)
    namespace['register']()
    bpy.context.scene.frame_set(135)
    if bpy.context.area and bpy.context.area.type == 'CONSOLE': bpy.context.area.type = 'VIEW_3D'
    areas = [area for screen in bpy.data.screens for area in screen.areas]
    for area in areas:
        if area.type == 'VIEW_3D':
            space = area.spaces.active
            space.show_region_ui = True
            space.region_3d.view_perspective = 'CAMERA'
            space.region_3d.view_camera_zoom = 7
            space.region_3d.view_camera_offset = (.075,0)
            space.shading.type = 'MATERIAL'
            space.shading.use_scene_lights = True
            space.shading.use_scene_world = True
            space.overlay.show_overlays = False
    state = {'file':bpy.data.filepath, 'frame':135, 'version':'modern-v03', 'runtime_registered':hasattr(bpy.types,'CLAIREV3_PT_motion_preview'), 'previous_session_backup':str(current_backup)}
except Exception as error:
    state['error'] = repr(error)
report.write_text(json.dumps(state,indent=2),encoding='utf-8')
