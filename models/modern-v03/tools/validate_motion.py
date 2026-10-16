"""Inspect saved motion frame by frame, plus unchanged V2 swap compatibility."""
import json
import math
from pathlib import Path
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

root = Path(__file__).resolve().parents[1]
scene = bpy.context.scene
assert scene.get('claire_model_version') == 'modern-v03'
names = json.loads(scene['claire_root_names'])
cards = [scene.objects[n] for n in names['cards']]
discs = [scene.objects[n] for n in names['discs']]
camera, hinge = scene.camera, scene.objects[names['hinge']]
scene.frame_set(135)
hero = (camera.location.copy(), camera.rotation_quaternion.copy(), camera.data.ortho_scale)
about = discs[0].location.copy()
previous = -1.
clipping = []
for frame in range(1, 128):
    scene.frame_set(frame)
    progress = (camera.location - Vector((0,0,0))).length
    assert all(math.isfinite(v) for v in camera.location)
    for name in ('Lid outer silver shell', 'Main matte silver shell'):
        obj = scene.objects[name]
        points = [world_to_camera_view(scene, camera, obj.matrix_world @ Vector(c)) for c in obj.bound_box]
        if any(p.x < -.01 or p.x > 1.01 or p.y < -.01 or p.y > 1.01 for p in points):
            clipping.append({'frame':frame, 'object':name, 'bounds':[min(p.x for p in points),max(p.x for p in points),min(p.y for p in points),max(p.y for p in points)]})
    angle = -hinge.rotation_euler.x
    assert angle >= previous - 1e-6 and angle <= math.radians(78)+1e-5
    previous = angle
scene.frame_set(127)
assert (camera.location-hero[0]).length < 1e-5
assert abs(camera.data.ortho_scale-hero[2]) < 1e-5
hover_peak = []
minimum_separation = float('inf')
for frame in range(135, 391):
    scene.frame_set(frame)
    assert (discs[0].location-about).length < 1e-5
    assert len([obj for obj in scene.objects if obj.get('is_navigation_disc')]) == 3
    for card in cards: hover_peak.append(card.scale.x)
    for i in (1,2):
        expected = cards[i].location + cards[i].rotation_euler.to_quaternion() @ Vector((0.,-.45,-.25))
        assert (discs[i].location-expected).length < 2e-5
    # Distinct sleeve root depth; exact artwork visibility is assessed in rendered frames.
    for i in range(3):
        for j in range(i+1,3):
            normal = cards[i].rotation_euler.to_quaternion() @ Vector((0,-1,0))
            gap = abs((cards[j].location-cards[i].location).dot(normal))
            minimum_separation = min(minimum_separation, gap)
swap_samples = {}
for frame in range(390,521):
    scene.frame_set(frame)
    swap_samples[frame] = [list(d.location) + list(d.rotation_euler) + list(d.scale) for d in discs]
    assert all(math.isfinite(v) for pose in swap_samples[frame] for v in pose)
    for key in ('about','projects','world'):
        obj=scene.objects['CD '+key+' solid optical substrate']
        points=[world_to_camera_view(scene,camera,obj.matrix_world@Vector(c)) for c in obj.bound_box]
        assert all(-.01<p.x<1.01 and -.01<p.y<1.01 for p in points), ('Swap disc cropped',frame,key)
    if frame<=440:
        expected=Vector(json.loads(scene['claire_card_home_poses'])[1]['loc'])+cards[1].rotation_euler.to_quaternion()@Vector((0,-.45,-.25))
        assert (discs[1].location-expected).length<1e-5
scene.frame_set(520)
assert (discs[1].location-Vector(json.loads(scene['claire_player_disc_pose'])['loc'])).length<1e-5
assert not scene.objects['Playing marker / projects'].hide_render
v3_path = root/'claire-modern-v03.blend'
bpy.ops.wm.open_mainfile(filepath=str(root.parent/'modern-v02'/'claire-modern-v02.blend'), use_scripts=False)
assert bpy.context.scene.get('claire_model_version') == 'modern-v02'
report = {'passed':not clipping, 'opening_frames_checked':127, 'opening_crop_issues':clipping, 'monotonic_lid':True, 'camera_settles_at_127':True, 'hover_frames_checked':256, 'playing_disc_fixed':True, 'spare_disc_follows':True, 'peak_scale':max(hover_peak), 'minimum_root_plane_gap':minimum_separation, 'swap_frames_checked':131, 'swap_order_and_endpoint':True, 'v2_opens':True}
(root/'motion-validation-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('CLAIRE_MOTION_CHECK',json.dumps(report))
assert not clipping, 'Camera clipping found; inspect report.'
bpy.ops.wm.open_mainfile(filepath=str(v3_path), use_scripts=False)
