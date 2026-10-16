"""Encode PNG previews with Blender's bundled FFmpeg; no external install."""
from pathlib import Path
import bpy,json

root=Path(__file__).resolve().parents[1]
for mode in ('opening','hover'):
    folder=root/'previews'/mode
    paths=sorted(folder.glob('*.png'))
    metadata=json.loads((folder/'frames.json').read_text(encoding='utf-8'))
    assert len(paths)==len(metadata['frames'])
    scene=bpy.data.scenes.new('Encode '+mode)
    bpy.context.window.scene=scene
    editor=scene.sequence_editor_create()
    strip=editor.strips.new_image(mode,filepath=str(paths[0]),channel=1,frame_start=1)
    for path in paths[1:]:strip.elements.append(path.name)
    strip.frame_final_duration=len(paths)
    scene.frame_start=1;scene.frame_end=len(paths)
    scene.render.resolution_x=800;scene.render.resolution_y=450;scene.render.resolution_percentage=100
    scene.render.fps=15
    scene.render.use_sequencer=True
    scene.render.use_compositing=False
    scene.view_settings.view_transform='Standard'
    scene.render.image_settings.media_type='VIDEO'
    scene.render.image_settings.file_format='FFMPEG'
    scene.render.ffmpeg.format='MPEG4'
    scene.render.ffmpeg.codec='H264'
    scene.render.ffmpeg.constant_rate_factor='HIGH'
    scene.render.filepath=str(root/'previews'/(mode+'-v3.mp4'))
    bpy.ops.render.render(animation=True)
    print('VIDEO_ENCODED',scene.render.filepath,flush=True)
