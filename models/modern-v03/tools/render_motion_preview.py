"""Render actual saved motion and materials, with no .blend writes."""
from pathlib import Path
import bpy, json, sys, time

root = Path(__file__).resolve().parents[1]
scene = bpy.context.scene
assert scene.get('claire_model_version') == 'modern-v03'
mode = sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'keys'
out = root/'previews'
out.mkdir(exist_ok=True)
scene.render.resolution_percentage = 100
scene.render.resolution_x = 800
scene.render.resolution_y = 450
scene.render.image_settings.file_format = 'PNG'
scene.render.engine = 'CYCLES'
scene.cycles.samples = 12 if mode == 'keys' else 6
scene.cycles.use_denoising = True
preferences = bpy.context.preferences.addons['cycles'].preferences
try:
    preferences.compute_device_type = 'CUDA'
    preferences.get_devices()
    gpu = [device for device in preferences.devices if device.type == 'CUDA']
    for device in preferences.devices: device.use = device in gpu
    scene.cycles.device = 'GPU' if gpu else 'CPU'
except Exception:
    scene.cycles.device = 'CPU'
frames = {'bench':[135], 'keys':[1,20,45,70,90,127,135,163,223,283,417,458,520], 'opening':list(range(1,128,2)), 'hover':list(range(135,330,2))}[mode]
folder = out/mode
folder.mkdir(exist_ok=True)
started = time.perf_counter()
for index, frame in enumerate(frames):
    path = folder/f'{index:04d}-f{frame:03d}.png'
    if not path.exists():
        scene.frame_set(frame)
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
    print('PREVIEW_FRAME', mode, index+1, len(frames), frame, flush=True)
(folder/'frames.json').write_text(json.dumps({'frames':frames, 'fps':15, 'engine':'CYCLES', 'device':scene.cycles.device, 'samples':scene.cycles.samples, 'elapsed_seconds':time.perf_counter()-started},indent=2),encoding='utf-8')
print('PREVIEW_DONE',mode,flush=True)
