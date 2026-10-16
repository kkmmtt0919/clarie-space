"""Decode exported videos with Blender's bundled movie reader."""
from pathlib import Path
import bpy,json
root=Path(__file__).resolve().parents[1]
reports={}
for mode in ('opening','hover'):
    path=root/'previews'/(mode+'-v3.mp4')
    expected=len(json.loads((root/'previews'/mode/'frames.json').read_text(encoding='utf-8'))['frames'])
    scene=bpy.data.scenes.new('Verify '+mode)
    movie=scene.sequence_editor_create().strips.new_movie(mode,filepath=str(path),channel=1,frame_start=1)
    assert movie.frame_final_duration==expected
    reports[mode]={'path':str(path),'frames':movie.frame_final_duration,'expected_frames':expected,'bytes':path.stat().st_size,'decoded':True}
(root/'video-validation-report.json').write_text(json.dumps(reports,indent=2),encoding='utf-8')
print('VIDEOS_VERIFIED',json.dumps(reports))
