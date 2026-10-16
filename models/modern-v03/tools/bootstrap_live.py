"""CLI startup hook: register V3 after loading it, without reopening a file in a Console context."""
from pathlib import Path
import bpy,json,os

root=Path('D:/projects/claire/models/modern-v03')
assert bpy.context.scene.get('claire_model_version')=='modern-v03'
namespace={'__name__':'claire_v3_live'}
exec(compile((root/'claire_preview_runtime.py').read_text(encoding='utf-8'),'<claire-v3-runtime>','exec'),namespace)
namespace['register']()
bpy.context.scene.frame_set(135)

def configure():
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':
                space=area.spaces.active
                space.show_region_ui=True
                space.region_3d.view_perspective='CAMERA'
                space.region_3d.view_camera_zoom=7
                space.region_3d.view_camera_offset=(.075,0)
                space.shading.type='MATERIAL'
                space.shading.use_scene_lights=True
                space.shading.use_scene_world=True
                space.overlay.show_overlays=False
    state={'file':bpy.data.filepath,'frame':135,'version':'modern-v03','runtime_registered':hasattr(bpy.types,'CLAIREV3_PT_motion_preview'),'pid':os.getpid(),'startup_mode':'file argument + Python startup hook; no live file replacement'}
    (root/'live-v3-ready.json').write_text(json.dumps(state,indent=2),encoding='utf-8')
    return None
bpy.app.timers.register(configure,first_interval=.5)
