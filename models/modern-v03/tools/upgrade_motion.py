"""Upgrade a saved V2 scene without rebuilding or discarding its corrected geometry."""
from pathlib import Path
import importlib.util
import json
import math
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
assert ROOT.name == 'modern-v03'
scene = bpy.context.scene
assert scene.get('claire_model_version') == 'modern-v02', 'Build from V2, not an already upgraded scene.'
spec = importlib.util.spec_from_file_location('claire_v3_motion', ROOT / 'claire_preview_runtime.py')
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)
names = json.loads(scene['claire_root_names'])
cards, discs, homes = runtime._roots(scene)
hinge = scene.objects[names['hinge']]
camera = scene.camera

def curves(obj):
    ad = obj.animation_data
    if not ad or not ad.action:
        return []
    if hasattr(ad.action, 'fcurves'):
        return list(ad.action.fcurves)
    return [fc for layer in ad.action.layers for strip in layer.strips for bag in strip.channelbags for fc in bag.fcurves]

def key_pose(obj, frame):
    for prop in ('location', 'rotation_euler', 'scale'):
        obj.keyframe_insert(prop, frame=frame)

def bezier_progress(t, x1=.77, y1=0., x2=.175, y2=1.):
    t = max(0., min(1., t))
    lo, hi = 0., 1.
    for _ in range(28):
        s = (lo + hi) / 2
        x = 3*(1-s)**2*s*x1 + 3*(1-s)*s*s*x2 + s**3
        if x < t: lo = s
        else: hi = s
    s = (lo + hi) / 2
    return 3*(1-s)**2*s*y1 + 3*(1-s)*s*s*y2 + s**3

# Capture exact delivered camera and disc poses before touching their animation.
scene.frame_set(1)
top_location = camera.location.copy()
top_rotation = camera.rotation_euler.to_quaternion()
top_scale = camera.data.ortho_scale
disc_start = runtime._pose(discs[0])
scene.frame_set(135)
hero_location = camera.location.copy()
hero_rotation = camera.rotation_euler.to_quaternion()
hero_scale = camera.data.ortho_scale
idle_disc = runtime._pose(discs[0])
scene.frame_set(220)
swap_start_disc = runtime._pose(discs[0])

# Preserve the existing swap exactly, moving all its keys and visibility keys.
objects = [*cards, *discs, *[obj for obj in scene.objects if obj.name.startswith('Playing marker /')]]
for obj in objects:
    for fc in curves(obj):
        for point in fc.keyframe_points:
            if point.co.x >= 220:
                point.co.x += 170
                point.handle_left.x += 170
                point.handle_right.x += 170
        fc.update()

# Remove only pre-swap card/disc keys; keep all swap values at >=390.
for obj in [*cards, *discs]:
    for fc in curves(obj):
        for index in range(len(fc.keyframe_points)-1,-1,-1):
            if fc.keyframe_points[index].co.x < 390:
                fc.keyframe_points.remove(fc.keyframe_points[index], fast=True)
        fc.update()

# Single continuous camera move, common progress for translation, quaternion and scale.
camera.animation_data_clear()
camera.data.animation_data_clear()
hinge.animation_data_clear()
camera.rotation_mode = 'QUATERNION'
for frame in range(1, 136):
    seconds = (frame - 1) / 30
    p = bezier_progress((seconds - 1.65) / 2.15)
    # A small preliminary reframe lets the opening lid stay inside the near view.
    reveal = bezier_progress((seconds - .65) / 1., .23, 1., .32, 1.)
    reframe = .12 * reveal * (1 - p)
    progress = p + reframe
    camera.location = top_location.lerp(hero_location, progress)
    anchor = (top_location + Vector((0,0,-10))).lerp(Vector((.8,.7,1.60)), progress)
    up = (anchor-camera.location).to_track_quat('-Z','Y') @ Vector((0,1,0))
    anchor += up * (.25 * reveal * (1-p))
    camera.rotation_quaternion = (anchor-camera.location).to_track_quat('-Z','Y')
    camera.data.ortho_scale = top_scale + (hero_scale - top_scale) * progress + 1.0 * reveal * (1-p)
    camera.keyframe_insert('location', frame=frame)
    camera.keyframe_insert('rotation_quaternion', frame=frame)
    camera.data.keyframe_insert('ortho_scale', frame=frame)
    if seconds <= .30:
        lid_angle = 0.
    elif seconds <= .65:
        lid_angle = 10 * bezier_progress((seconds-.30)/.35, .23, 1., .32, 1.)
    else:
        lid_angle = 10 + 68 * bezier_progress((seconds-.65)/1.2, .23, 1., .32, 1.)
    hinge.rotation_euler.x = math.radians(-lid_angle)
    hinge.keyframe_insert('rotation_euler', frame=frame)
    # Acceleration from rest: cubic integration of a smoothstep angular speed.
    u = max(0., min(1., (seconds-1.35)/.75))
    travel = .75*(u**3-.5*u**4) + max(0., seconds-2.1)
    full_travel = .375 + (4.2-2.1)
    rotation = disc_start[1].copy()
    rotation.z += (idle_disc[1].z-disc_start[1].z) * min(1., travel/full_travel)
    runtime._assign_pose(discs[0], (idle_disc[0], rotation, idle_disc[2]))
    key_pose(discs[0], frame)
for obj in (camera, camera.data, hinge):
    for fc in curves(obj):
        last = fc.keyframe_points[-1].co.y
        fc.keyframe_points.insert(520, last)
        for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'

# Bake all three demonstrations with the same exact spring used in live hover.
direction = Vector(scene['claire_hover_direction'])
for frame in range(1, 390):
    selected, elapsed = -1, 0.
    for index, start in enumerate((150, 210, 270)):
        if start <= frame <= start + 44:
            selected, elapsed = index, (frame-start)/30
            break
    for index, (card, home) in enumerate(zip(cards, homes)):
        progress = 0.
        if index == selected:
            if elapsed <= .8:
                progress, _ = runtime._spring_step(0., 0., 1., elapsed)
            else:
                value, velocity = runtime._spring_step(0., 0., 1., .8)
                progress, _ = runtime._spring_step(value, velocity, 0., elapsed-.8, runtime._RETURN_DAMPING)
        runtime._assign_pose(card, runtime._spring_pose(home, direction, progress))
        key_pose(card, frame)
    runtime._sync_spare_discs(cards, discs)
    for disc in discs[1:]: key_pose(disc, frame)
    if frame >= 135:
        p = bezier_progress((frame-350)/24)
        rotation = idle_disc[1].to_quaternion().slerp(swap_start_disc[1].to_quaternion(), p).to_euler('XYZ')
        runtime._assign_pose(discs[0], (idle_disc[0], rotation, idle_disc[2]))
        key_pose(discs[0], frame)
for obj in [*cards, *discs]:
    for fc in curves(obj):
        for kp in fc.keyframe_points:
            if kp.co.x < 390: kp.interpolation = 'LINEAR'

# Replace unsafe V2 straight-line travel with a front lane and vertical sleeve
# insertion. Keeping a disc above its neighbours before changing depth prevents
# it passing through the lid or another disc while returning to a layered stack.
for disc in discs:
    for fc in curves(disc):
        for index in range(len(fc.keyframe_points)-1,-1,-1):
            if fc.keyframe_points[index].co.x >= 390: fc.keyframe_points.remove(fc.keyframe_points[index], fast=True)
        fc.update()
card_disc_poses = []
for home in homes:
    q = home[1].to_quaternion()
    card_disc_poses.append((home[0] + q @ runtime._DISC_LOCAL, (q @ runtime._DISC_TILT).to_euler('XYZ'), home[2]))
active_q = idle_disc[1].to_quaternion()
front = scene.objects[names['player']].rotation_euler.to_quaternion() @ Vector((0,-1,0))
about_home, projects_home, world_home = card_disc_poses
about_top = about_home[0] + Vector((0,0,2.3))
about_front_top = Vector((about_home[0].x,-2.5,about_top.z))
project_top = projects_home[0] + Vector((0,0,2.6))
project_front_top = Vector((project_top.x,-2.5,project_top.z))
player_front_top = idle_disc[0] + front*1.5 + Vector((0,0,2.0))
player_front_low = idle_disc[0] + front*1.3 + Vector((0,0,.45))
outgoing = [(390,idle_disc[0],swap_start_disc[1]),(405,idle_disc[0]+front*1.3+Vector((0,0,.6)),swap_start_disc[1]),(420,about_front_top,about_home[1]),(430,about_top,about_home[1]),(440,about_home[0],about_home[1]),(520,about_home[0],about_home[1])]
incoming = [(390,projects_home[0],projects_home[1]),(440,projects_home[0],projects_home[1]),(452,project_top,projects_home[1]),(460,project_front_top,projects_home[1]),(472,player_front_top,idle_disc[1]),(482,player_front_low,idle_disc[1]),(490,idle_disc[0],idle_disc[1]),(520,idle_disc[0],idle_disc[1])]
def path_pose(waypoints, frame):
    for (a,loc_a,rot_a),(b,loc_b,rot_b) in zip(waypoints,waypoints[1:]):
        if a<=frame<=b:
            p=bezier_progress((frame-a)/(b-a),.42,0.,.58,1.)
            return loc_a.lerp(loc_b,p),rot_a.to_quaternion().slerp(rot_b.to_quaternion(),p).to_euler('XYZ'),Vector((1,1,1))
    raise ValueError(frame)
for frame in range(390,521):
    runtime._assign_pose(discs[0],path_pose(outgoing,frame))
    runtime._assign_pose(discs[1],path_pose(incoming,frame))
    runtime._assign_pose(discs[2],world_home)
    if frame>490:
        discs[1].rotation_euler.z += math.radians(60)*(frame-490)/30
    for disc in discs:key_pose(disc,frame)
for disc in discs:
    for fc in curves(disc):
        for kp in fc.keyframe_points:kp.interpolation='LINEAR'

# A small, slow widen during upper-lane travel keeps the full disc silhouette
# inside the image. Hover itself never moves the camera.
zoom_points=[(390,hero_scale),(415,15.0),(460,15.0),(490,12.5),(520,hero_scale)]
for frame in range(390,521):
    for (a,sa),(b,sb) in zip(zoom_points,zoom_points[1:]):
        if a<=frame<=b:
            p=bezier_progress((frame-a)/(b-a),.42,0.,.58,1.)
            camera.data.ortho_scale=sa+(sb-sa)*p
            camera.data.keyframe_insert('ortho_scale',frame=frame)
            break
for fc in curves(camera.data):
    for kp in fc.keyframe_points:kp.interpolation='LINEAR'

scene.timeline_markers.clear()
for frame, label in runtime._MARKERS:
    scene.timeline_markers.new(label, frame=frame)
scene.timeline_markers.new('Opening settled / 4.2s', frame=127)
scene.frame_end = 520
scene['claire_model_version'] = 'modern-v03'
scene['claire_motion_revision'] = 'opening 4.2s / velocity-preserving spring / three hover demos / safe swap lane'
scene['claire_spring_settings'] = json.dumps({'mass':1, 'stiffness':500, 'damping':30, 'return_damping':40})
scene['claire_source_model'] = str(ROOT.parent / 'modern-v02' / 'claire-modern-v02.blend')
scene['claire_active_disc'] = 'about'
scene['claire_hover_disc'] = 'none'

# Use new V3 local print assets; keep silver and iridescence as material properties.
for image in bpy.data.images:
    asset = ROOT / 'assets' / image.filepath.replace(chr(92), '/').rsplit('/', 1)[-1]
    if image.source == 'FILE' and asset.is_file():
        if image.packed_file: image.unpack(method='REMOVE')
        image.filepath = str(asset)
        image.reload()
        image.pack()
text = bpy.data.texts.get('claire_preview_runtime.py')
if text is None: text = bpy.data.texts.new('claire_preview_runtime.py')
text.clear()
text.write((ROOT/'claire_preview_runtime.py').read_text(encoding='utf-8'))
for old in list(bpy.data.texts):
    if old.name.startswith('START HERE'):
        old.name = 'START HERE — Claire modern-v03'
        old.clear()
        old.write('Claire V3 — independent from V2.\nRun claire_preview_runtime.py in Text Editor to register the Claire panel.\nOpening frames 1–127 (4.2 seconds), idle 135; hover about 163 / projects 223 / world 283; reset 374; swap 417 / 458 / 520.\nStart Hover Preview: real mouse selection with velocity-preserving spring. Esc restores the original state.\nNo webpage or audio is implemented here. V2 is preserved at ../modern-v02 and ../archives.\n')
scene.frame_set(135)
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type == 'VIEW_3D':
            space = area.spaces.active
            space.region_3d.view_perspective = 'CAMERA'
            space.show_region_ui = True
            space.shading.type = 'MATERIAL'
            space.overlay.show_overlays = False
target = ROOT/'claire-modern-v03.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(target), check_existing=False)
manifest = {'version':bpy.app.version_string, 'blend':str(target), 'source':scene['claire_source_model'], 'objects':len(scene.objects), 'disc_roots':names['discs'], 'card_roots':names['cards'], 'timeline':{m.name:m.frame for m in scene.timeline_markers}, 'opening_seconds':4.2, 'spring':json.loads(scene['claire_spring_settings']), 'web_hover_implemented':False}
(ROOT/'model-manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
print('CLAIRE_V3_SAVED', target)
