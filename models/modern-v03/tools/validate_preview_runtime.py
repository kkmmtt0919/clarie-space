"""Background-only checks against the saved modern-v03 model; no .blend writes."""
import importlib.util
import json
import time
from pathlib import Path
from types import MethodType, SimpleNamespace

import bpy
from mathutils import Vector


runtime_path = Path(__file__).resolve().parent.parent / "claire_preview_runtime.py"
spec = importlib.util.spec_from_file_location("claire_runtime_validation", runtime_path)
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)
scene = bpy.context.scene
assert runtime._supported(scene), "Only run against the saved modern-v03 model."
object_names = set(bpy.data.objects.keys())
runtime.register()
runtime.register()
# Reopening a .blend can reset driver_namespace without unregistering UI types.
bpy.app.driver_namespace.pop(runtime._RUNTIME_KEY, None)
runtime.register()

old = bpy.data.scenes.new("runtime-version-guard-test")
assert not runtime.CLAIREV3_PT_motion_preview.poll(SimpleNamespace(scene=old))
assert not runtime.CLAIREV3_OT_preview_frame.poll(SimpleNamespace(scene=old))
bpy.data.scenes.remove(old)

for frame, _label in runtime._MARKERS:
    assert bpy.ops.claire_v3.preview_frame(frame=frame) == {"FINISHED"}
    assert scene.frame_current == frame
assert scene["claire_active_disc"] == "projects"
bpy.ops.claire_v3.preview_frame(frame=135)
cards, discs, homes = runtime._roots(scene)
assert [c.get("entry_id") for c in cards] == ["about", "projects", "world"]
assert len([o for o in scene.objects if o.get("is_navigation_disc")]) == 3
original_poses = [runtime._pose(obj) for obj in cards + discs]
about_initial = discs[0].matrix_world.copy()

width, height = 1920, 1080
camera = scene.camera
view_matrix = camera.matrix_world.inverted()
projection = camera.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(), x=width, y=height)
rv3d = SimpleNamespace(view_matrix=view_matrix, perspective_matrix=projection @ view_matrix)
preview = SimpleNamespace(
    _scene=scene, _cards=cards, _discs=discs, _homes=homes,
    _direction=Vector(scene["claire_hover_direction"]), _hovered=-1,
    _region=SimpleNamespace(width=width, height=height), _rv3d=rv3d,
    _area=SimpleNamespace(tag_redraw=lambda: None),
    _corners=[runtime._local_card_corners(card) for card in cards],
    _home_matrices=[runtime._pose_matrix(pose) for pose in homes],
    _finished=False, _timer=None,
    _original_frame=135, _original_poses=original_poses,
    _original_active="about", _original_hover="none", _original_view={},
    _spring_values=[0.] * 3, _spring_velocities=[0.] * 3,
    _last_tick=time.perf_counter(), _settled=True,
)
preview._advance = MethodType(runtime.CLAIREV3_OT_hover_preview._advance, preview)
preview._project_polygon = MethodType(runtime.CLAIREV3_OT_hover_preview._project_polygon, preview)
polygons = [preview._project_polygon(matrix, corners) for matrix, corners in zip(preview._home_matrices, preview._corners)]
screen_points = {}
for y in range(4, height, 8):
    for x in range(4, width, 8):
        point = Vector((x, y))
        if any(runtime._inside_polygon(point, poly) for poly in polygons):
            index = runtime.CLAIREV3_OT_hover_preview._pick(preview, bpy.context, point)
            screen_points.setdefault(index, point)
assert set(screen_points) == {0, 1, 2}, f"Every card needs an exposed stable selection region: {screen_points}"

for index in range(3):
    runtime.CLAIREV3_OT_hover_preview._select(preview, index)
    preview._last_tick = time.perf_counter() - 1
    runtime.CLAIREV3_OT_hover_preview._tick(preview, bpy.context)
    expected_loc = runtime._target_pose(homes[index], preview._direction, True)[0]
    assert (cards[index].location - expected_loc).length < 1e-5
    assert abs(cards[index].scale.x - 1.03 * homes[index][2].x) < 1e-5
    assert runtime.CLAIREV3_OT_hover_preview._pick(preview, bpy.context, screen_points[index]) == index
    assert all(abs(a - b) < 1e-5 for ra, rb in zip(discs[0].matrix_world, about_initial) for a, b in zip(ra, rb)), "Playing about disc must stay in the player."
    for spare in (1, 2):
        quaternion = cards[spare].rotation_euler.to_quaternion()
        expected = cards[spare].location + quaternion @ runtime._DISC_LOCAL
        assert (discs[spare].location - expected).length < 1e-5
        assert (discs[spare].scale - cards[spare].scale).length < 1e-5

runtime._record()["instance"] = preview
runtime.CLAIREV3_OT_hover_preview.finish(preview, bpy.context)
assert scene.frame_current == 135
assert scene["claire_hover_disc"] == "none"
assert runtime._record()["instance"] is None
for obj, pose in zip(cards + discs, original_poses):
    assert (obj.location - pose[0]).length < 1e-5
    assert (obj.scale - pose[2]).length < 1e-5
assert set(bpy.data.objects.keys()) == object_names, "Preview must never duplicate objects."

# Frame-rate independent solver, single restrained peak, immediate response.
trajectories = []
for fps in (30, 60, 144):
    value, velocity = 0., 0.
    samples = []
    for _ in range(fps):
        value, velocity = runtime._spring_step(value, velocity, 1., 1/fps)
        samples.append(value)
    trajectories.append(value)
    assert 1.05 < max(samples) < 1.09, ('Peak outside playful rigid-card range', fps, max(samples))
assert max(trajectories)-min(trajectories) < 1e-10
value, velocity = runtime._spring_step(0., 0., 1., .05)
assert value > .30 and velocity > 0, 'Hover should respond immediately'
before = (value, velocity)
assert runtime._spring_step(value, velocity, 0., 0.) == before, 'Retargeting preserves pose and speed'
value, velocity = runtime._spring_step(value, velocity, 0., .01, runtime._RETURN_DAMPING)
assert value > before[0], 'Brief continuing momentum must survive an immediate reversal'
value, velocity = runtime._spring_step(value, velocity, 0., 5., runtime._RETURN_DAMPING)
assert abs(value)+abs(velocity) < 1e-10, 'Long timer stalls must settle rather than explode'

# Real runtime retargeting must preserve every card velocity and restore all poses.
preview._finished = False
preview._hovered = -1
preview._spring_values = [0.] * 3
preview._spring_velocities = [0.] * 3
preview._last_tick = time.perf_counter()
for index in (0, 1, 2, 0, -1):
    velocities = preview._spring_velocities.copy()
    now = preview._last_tick
    original_clock = runtime.time.perf_counter
    runtime.time.perf_counter = lambda: now
    try:
        runtime.CLAIREV3_OT_hover_preview._select(preview, index)
        assert preview._spring_velocities == velocities
    finally:
        runtime.time.perf_counter = original_clock
    preview._advance(now + .05)
    bpy.context.view_layer.update()
    if index >= 0:
        assert runtime.CLAIREV3_OT_hover_preview._pick(preview, bpy.context, screen_points[index]) == index
preview._advance(preview._last_tick + 2)
for card, home in zip(cards, homes):
    assert (card.location - home[0]).length < 1e-5
runtime.CLAIREV3_OT_hover_preview.finish(preview, bpy.context)
runtime.unregister()
report = {
    "markers": [frame for frame, _ in runtime._MARKERS],
    "selectable_cards": [c.get("entry_id") for c in cards],
    "disc_count": 3,
    "spring_peak_progress": max(samples),
    "frame_rate_independent": True,
    "velocity_preserved_on_retarget": True,
    "rapid_switches": True,
    "long_stall_stable": True,
    "session_restored": True,
    "new_objects": 0,
}
(runtime_path.parent / 'runtime-validation-report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print("CLAIRE_RUNTIME_VALIDATED", json.dumps(report))
