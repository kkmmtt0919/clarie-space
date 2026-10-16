"""Schedule a real GUI opening playback check after leaving the Console."""
from pathlib import Path
import time,json,bpy

root=Path('D:/projects/claire-vinyl-preview/modern-v03')
assert bpy.context.scene.get('claire_model_version')=='modern-v03'
if bpy.context.area and bpy.context.area.type=='CONSOLE':bpy.context.area.type='VIEW_3D'
samples=[]
started=time.perf_counter()

def launch():
    window=next(iter(bpy.context.window_manager.windows))
    area=next(a for a in window.screen.areas if a.type=='VIEW_3D')
    region=next(r for r in area.regions if r.type=='WINDOW')
    with bpy.context.temp_override(window=window,area=area,region=region):
        result=bpy.ops.claire_v3.play_opening('INVOKE_DEFAULT')
    assert 'RUNNING_MODAL' in result
    bpy.app.timers.register(observe,first_interval=.05)
    return None

def observe():
    scene=bpy.context.scene
    samples.append({'seconds':time.perf_counter()-started,'frame':scene.frame_current})
    if time.perf_counter()-started<5.5:return .05
    state={'opening_real_gui':True,'samples':samples,'ended_frame':scene.frame_current,'passed':scene.frame_current==135 and any(1<s['frame']<127 for s in samples)}
    (root/'live-playback-report.json').write_text(json.dumps(state,indent=2),encoding='utf-8')
    return None

bpy.app.timers.register(launch,first_interval=.3)
