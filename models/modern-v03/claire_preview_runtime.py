"""Optional Blender-only motion preview for Claire modern-v03.

Open this packed text in Blender's Text Editor and choose Run Script. The Claire
sidebar panel appears only in the matching scene. No web UI or audio is created.
"""
import json
import math
import time

import bpy
from bpy.props import IntProperty
from bpy_extras import view3d_utils
from mathutils import Euler, Matrix, Vector


_VERSION = "modern-v03"
_RUNTIME_KEY = "claire_modern_v03_preview_runtime"
_HOVER_SECONDS = 0.30
_SPRING_STIFFNESS = 500.0
_SPRING_DAMPING = 30.0
_RETURN_DAMPING = 40.0


def _spring_step(value, velocity, target, seconds, damping=_SPRING_DAMPING):
    """Exact underdamped solution; independent of timer frequency and no dt clamp."""
    if seconds <= 0:
        return value, velocity
    half = damping / 2.0
    frequency = math.sqrt(_SPRING_STIFFNESS - half * half)
    displacement = value - target
    coefficient = (velocity + half * displacement) / frequency
    decay = math.exp(-half * seconds)
    cosine, sine = math.cos(frequency * seconds), math.sin(frequency * seconds)
    offset = displacement * cosine + coefficient * sine
    rate = -displacement * frequency * sine + coefficient * frequency * cosine
    return target + decay * offset, decay * (rate - half * offset)


def _spring_pose(home, direction, progress):
    """Rigid sleeve and disc share one spring progress, including small overshoot."""
    rotation = home[1].copy()
    rotation.z += math.radians(4) * progress
    scale = home[2] * (1.0 + .03 * progress)
    # Riffle around the covered right edge, rather than passing through the next
    # overlapping sleeve. The exposed left edge comes forward; the covered edge
    # retains clearance. This also gives the rigid card a believable pivot.
    pivot = Vector((1.0, 0., 0.))
    location = home[0] + home[1].to_quaternion() @ pivot - rotation.to_quaternion() @ (pivot * (1+.03*progress))
    location += Vector((0., 0., .16 * progress))
    return location, rotation, scale
_DISC_LOCAL = Vector((0.0, -0.45, -0.25))
_DISC_TILT = Euler((math.pi / 2, 0, 0)).to_quaternion()
_MARKERS = (
    (1, "Closed / Top"),
    (135, "Hero / Idle"),
    (163, "About / Spring Hover"),
    (223, "Projects / Spring Hover"),
    (283, "World / Spring Hover"),
    (374, "Compact Reset"),
    (417, "Return About"),
    (458, "Insert Projects"),
    (520, "Projects Playing"),
)


def _supported(scene):
    return scene is not None and scene.get("claire_model_version") == _VERSION


def _record():
    return bpy.app.driver_namespace.setdefault(_RUNTIME_KEY, {"instance": None})


def _pose(obj):
    return (obj.location.copy(), obj.rotation_euler.copy(), obj.scale.copy())


def _assign_pose(obj, pose):
    obj.location, obj.rotation_euler, obj.scale = pose


def _roots(scene):
    config = json.loads(scene["claire_root_names"])
    names = config["cards"]
    disc_names = config["discs"]
    if len(names) != 3 or len(disc_names) != 3:
        raise ValueError("Claire preview requires the three existing cards and discs.")
    cards = [scene.objects[name] for name in names]
    discs = [scene.objects[name] for name in disc_names]
    homes = json.loads(scene["claire_card_home_poses"])
    if len(homes) != 3:
        raise ValueError("The three card home poses are missing.")
    home_poses = [
        (Vector(item["loc"]), Euler(item["rot"], "XYZ"), Vector(item["scale"]))
        for item in homes
    ]
    return cards, discs, home_poses


def _target_pose(home, direction, selected):
    loc, rot, scale = home
    if not selected:
        return loc.copy(), rot.copy(), scale.copy()
    return _spring_pose(home, direction, 1.)


def _sync_spare_discs(cards, discs):
    # About remains in the player throughout this independent idle preview.
    for index in (1, 2):
        card = cards[index]
        quaternion = card.rotation_euler.to_quaternion()
        disc = discs[index]
        disc.location = card.location + quaternion @ _DISC_LOCAL
        disc.rotation_euler = (quaternion @ _DISC_TILT).to_euler("XYZ")
        disc.scale = card.scale.copy()


def _inside_polygon(point, polygon):
    if len(polygon) < 3:
        return False
    signs = []
    for a, b in zip(polygon, polygon[1:] + polygon[:1]):
        cross = (b.x - a.x) * (point.y - a.y) - (b.y - a.y) * (point.x - a.x)
        if abs(cross) > 0.01:
            signs.append(cross > 0)
    return not signs or all(sign == signs[0] for sign in signs)


def _local_card_corners(root):
    # Child bounds are read once; moving the hover card never shifts its trigger.
    inverse = root.matrix_world.inverted_safe()
    points = []
    for child in root.children_recursive:
        if child.type == "MESH":
            points.extend(inverse @ child.matrix_world @ Vector(p) for p in child.bound_box)
    if points:
        lo_x, hi_x = min(p.x for p in points), max(p.x for p in points)
        lo_z, hi_z = min(p.z for p in points), max(p.z for p in points)
        front = min(p.y for p in points)
    else:
        lo_x, hi_x, lo_z, hi_z, front = -1.15, 1.15, -1.15, 1.15, -0.05
    return [Vector(p) for p in (
        (lo_x, front, lo_z), (hi_x, front, lo_z),
        (hi_x, front, hi_z), (lo_x, front, hi_z),
    )]


def _pose_matrix(pose):
    loc, rot, scale = pose
    return Matrix.Translation(loc) @ rot.to_matrix().to_4x4() @ Matrix.Diagonal((*scale, 1.0))


def _stop_preview(context, restore=True):
    active = _record().get("instance")
    if active is not None:
        try:
            active.finish(context, restore=restore)
        except ReferenceError:
            # An operator cancelled by an old runtime can leave a stale RNA
            # reference. Re-registering must still recover the preview panel.
            _record()['instance'] = None


class CLAIREV3_OT_preview_frame(bpy.types.Operator):
    bl_idname = "claire_v3.preview_frame"
    bl_label = "Preview Claire Motion Frame"
    bl_description = "Show an existing timeline pose; this does not perform a webpage action"
    frame: IntProperty(default=135, min=1, max=520)

    @classmethod
    def poll(cls, context):
        return _supported(context.scene)

    def execute(self, context):
        if not _supported(context.scene):
            return {"CANCELLED"}
        _stop_preview(context)
        if context.screen and context.screen.is_animation_playing:
            bpy.ops.screen.animation_cancel(restore_frame=False)
        context.scene.frame_set(self.frame)
        context.scene["claire_hover_disc"] = {163: "about", 223: "projects", 283: "world"}.get(self.frame, "none")
        context.scene["claire_active_disc"] = "projects" if self.frame >= 490 else "about"
        return {"FINISHED"}


class CLAIREV3_OT_hover_preview(bpy.types.Operator):
    bl_idname = "claire_v3.hover_preview"
    bl_label = "Start Hover Preview"
    bl_description = "Preview card hover at frame 135; press Esc to restore the previous state"
    _timer = None
    _finished = False

    @classmethod
    def poll(cls, context):
        return _supported(context.scene) and context.area is not None and context.area.type == "VIEW_3D"

    def invoke(self, context, event):
        if not self.poll(context):
            return {"CANCELLED"}
        _stop_preview(context)
        self._scene = context.scene
        self._area = context.area
        self._region = next((r for r in context.area.regions if r.type == "WINDOW"), None)
        self._space = context.space_data
        self._rv3d = self._space.region_3d
        if self._region is None or self._rv3d is None:
            self.report({"WARNING"}, "Start hover from a normal 3D viewport.")
            return {"CANCELLED"}
        try:
            self._cards, self._discs, self._homes = _roots(self._scene)
        except (KeyError, ValueError, TypeError) as error:
            self.report({"ERROR"}, str(error))
            return {"CANCELLED"}
        self._original_frame = self._scene.frame_current
        self._original_poses = [_pose(obj) for obj in self._cards + self._discs]
        self._original_active = self._scene.get("claire_active_disc", "about")
        self._original_hover = self._scene.get("claire_hover_disc", "none")
        self._original_view = {
            "view_perspective": self._rv3d.view_perspective,
            "view_location": self._rv3d.view_location.copy(),
            "view_rotation": self._rv3d.view_rotation.copy(),
            "view_distance": self._rv3d.view_distance,
            "view_camera_zoom": self._rv3d.view_camera_zoom,
            "view_camera_offset": tuple(self._rv3d.view_camera_offset),
        }
        if context.screen and context.screen.is_animation_playing:
            bpy.ops.screen.animation_cancel(restore_frame=False)
        self._scene.frame_set(135)
        context.view_layer.update()
        self._corners = [_local_card_corners(card) for card in self._cards]
        self._home_matrices = [_pose_matrix(home) for home in self._homes]
        self._direction = Vector(self._scene.get("claire_hover_direction", (0, -1, 0)))
        self._rv3d.view_perspective = "CAMERA"
        self._scene["claire_active_disc"] = "about"
        self._scene["claire_hover_disc"] = "none"
        self._hovered = -1
        self._kind = 'hover'
        self._spring_values = [0.0] * 3
        self._spring_velocities = [0.0] * 3
        self._last_tick = time.perf_counter()
        self._start_poses = [_pose(card) for card in self._cards]
        self._target_poses = [_target_pose(home, self._direction, False) for home in self._homes]
        self._transition_started = time.perf_counter()
        self._settled = False
        self._finished = False
        self._wm = context.window_manager
        self._timer = self._wm.event_timer_add(1 / 60, window=context.window)
        _record()["instance"] = self
        self._wm.modal_handler_add(self)
        self._area.tag_redraw()
        self.report({"INFO"}, "Hover the three cards. Esc restores the previous frame. No click action or audio.")
        return {"RUNNING_MODAL"}

    def _project_polygon(self, matrix, corners):
        projected = [
            view3d_utils.location_3d_to_region_2d(self._region, self._rv3d, matrix @ corner)
            for corner in corners
        ]
        return projected if all(p is not None for p in projected) else []

    def _pick(self, context, point):
        if not (0 <= point.x < self._region.width and 0 <= point.y < self._region.height):
            return -1
        # Baseline projected regions remain fixed while the selected card moves.
        # In overlaps the closest baseline surface wins, as in a physical deck.
        candidates = []
        for index, matrix in enumerate(self._home_matrices):
            polygon = self._project_polygon(matrix, self._corners[index])
            if _inside_polygon(point, polygon):
                depth = (self._rv3d.view_matrix @ matrix.translation).z
                candidates.append((depth, index))
        if candidates:
            return max(candidates)[1]
        if self._hovered >= 0:
            card = self._cards[self._hovered]
            polygon = self._project_polygon(card.matrix_world, self._corners[self._hovered])
            if _inside_polygon(point, polygon):
                return self._hovered
        # Ray hits cover the small parts of spare discs extending beyond sleeves.
        origin = view3d_utils.region_2d_to_origin_3d(self._region, self._rv3d, point)
        direction = view3d_utils.region_2d_to_vector_3d(self._region, self._rv3d, point)
        result = self._scene.ray_cast(context.evaluated_depsgraph_get(), origin, direction)
        if result[0]:
            obj = result[4].original
            while obj is not None:
                for index, card in enumerate(self._cards):
                    if obj == card:
                        return index
                for index in (1, 2):
                    if obj == self._discs[index]:
                        return index
                obj = obj.parent
        return -1

    def _select(self, index):
        if index == self._hovered:
            return
        # Integrate to the exact input timestamp before retargeting. Preserve velocity.
        self._advance(time.perf_counter())
        self._hovered = index
        self._settled = False
        self._scene["claire_hover_disc"] = self._cards[index].get("entry_id", "none") if index >= 0 else "none"

    def _advance(self, now):
        seconds = max(0.0, now - self._last_tick)
        self._last_tick = now
        settled = True
        for i, (card, home) in enumerate(zip(self._cards, self._homes)):
            target = float(i == self._hovered)
            damping = _SPRING_DAMPING if target else _RETURN_DAMPING
            value, velocity = _spring_step(self._spring_values[i], self._spring_velocities[i], target, seconds, damping)
            if abs(value - target) < 0.0001 and abs(velocity) < 0.005:
                value, velocity = target, 0.0
            else:
                settled = False
            self._spring_values[i], self._spring_velocities[i] = value, velocity
            _assign_pose(card, _spring_pose(home, self._direction, value))
        _sync_spare_discs(self._cards, self._discs)
        self._settled = settled

    def _tick(self, context):
        if getattr(self, "_settled", False):
            self._last_tick = time.perf_counter()
            return
        self._advance(time.perf_counter())
        context.view_layer.update()
        self._area.tag_redraw()

    def modal(self, context, event):
        if self._finished:
            return {"CANCELLED"}
        if event.type == "ESC":
            self.finish(context)
            return {"CANCELLED"}
        try:
            if context.scene != self._scene or not _supported(context.scene):
                self.finish(context)
                return {"CANCELLED"}
            if event.type == "MOUSEMOVE":
                point = Vector((event.mouse_x - self._region.x, event.mouse_y - self._region.y))
                self._select(self._pick(context, point))
                return {"PASS_THROUGH"}
            # Blender 5.2 Event has no timer attribute. Exact elapsed integration
            # makes additional timer events harmless; finished operators exit above.
            if event.type == "TIMER":
                self._tick(context)
                return {"RUNNING_MODAL"}
        except (ReferenceError, RuntimeError, AttributeError):
            self.finish(context)
            return {"CANCELLED"}
        return {"PASS_THROUGH"}

    def finish(self, context, restore=True):
        if self._finished:
            return
        self._finished = True
        if self._timer is not None:
            try:
                self._wm.event_timer_remove(self._timer)
            except (ReferenceError, RuntimeError):
                pass
            self._timer = None
        if restore:
            try:
                self._scene.frame_set(self._original_frame)
                for obj, pose in zip(self._cards + self._discs, self._original_poses):
                    _assign_pose(obj, pose)
                self._scene["claire_active_disc"] = self._original_active
                self._scene["claire_hover_disc"] = self._original_hover
                for name, value in self._original_view.items():
                    setattr(self._rv3d, name, value)
                context.view_layer.update()
                self._area.tag_redraw()
            except (ReferenceError, RuntimeError, AttributeError):
                pass
        if _record().get("instance") is self:
            _record()["instance"] = None

    def cancel(self, context):
        self.finish(context)


class CLAIREV3_OT_play_opening(bpy.types.Operator):
    bl_idname = 'claire_v3.play_opening'
    bl_label = 'Play Opening / 4.2s'
    bl_description = 'Replay only the opening; Skip to Hero or Esc ends it immediately'

    @classmethod
    def poll(cls, context):
        return _supported(context.scene) and context.area is not None and context.area.type == 'VIEW_3D'

    def invoke(self, context, event):
        _stop_preview(context)
        if context.screen and context.screen.is_animation_playing:
            bpy.ops.screen.animation_cancel(restore_frame=False)
        self._scene, self._area, self._wm = context.scene, context.area, context.window_manager
        self._original_frame = self._scene.frame_current
        self._started = time.perf_counter()
        self._finished = False
        self._kind = 'opening'
        context.space_data.region_3d.view_perspective = 'CAMERA'
        self._scene.frame_set(1)
        self._timer = self._wm.event_timer_add(1/60, window=context.window)
        _record()['instance'] = self
        self._wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if self._finished: return {'CANCELLED'}
        if event.type == 'ESC':
            self.finish(context, restore=False)
            return {'FINISHED'}
        if context.scene != self._scene:
            self.finish(context)
            return {'CANCELLED'}
        if event.type == 'TIMER':
            frame = min(127, 1+int((time.perf_counter()-self._started)*30))
            self._scene.frame_set(frame)
            self._area.tag_redraw()
            if frame>=127:
                self.finish(context, restore=False)
                return {'FINISHED'}
            return {'RUNNING_MODAL'}
        return {'PASS_THROUGH'}

    def finish(self, context, restore=True):
        if self._finished: return
        self._finished = True
        self._wm.event_timer_remove(self._timer)
        self._scene.frame_set(self._original_frame if restore else 135)
        if not restore:
            self._scene['claire_active_disc'] = 'about'
            self._scene['claire_hover_disc'] = 'none'
        self._area.tag_redraw()
        if _record().get('instance') is self: _record()['instance'] = None

    def cancel(self, context):
        self.finish(context)


class CLAIREV3_OT_skip_opening(bpy.types.Operator):
    bl_idname = 'claire_v3.skip_opening'
    bl_label = 'Skip to Hero'

    @classmethod
    def poll(cls, context):
        return _supported(context.scene)

    def execute(self, context):
        _stop_preview(context)
        if context.screen and context.screen.is_animation_playing:
            bpy.ops.screen.animation_cancel(restore_frame=False)
        context.scene.frame_set(135)
        context.scene['claire_active_disc'] = 'about'
        context.scene['claire_hover_disc'] = 'none'
        return {'FINISHED'}


class CLAIREV3_OT_stop_hover(bpy.types.Operator):
    bl_idname = "claire_v3.stop_hover"
    bl_label = "Stop Hover Preview"
    bl_description = "Stop the temporary preview and restore the previous frame and transforms"

    @classmethod
    def poll(cls, context):
        return _supported(context.scene) and _record().get("instance") is not None

    def execute(self, context):
        _stop_preview(context)
        return {"FINISHED"}


class CLAIREV3_PT_motion_preview(bpy.types.Panel):
    bl_label = "Claire / Motion Preview"
    bl_idname = "CLAIREV3_PT_motion_preview"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Claire"

    @classmethod
    def poll(cls, context):
        return _supported(context.scene)

    def draw(self, context):
        layout = self.layout
        layout.label(text="Modern v03 / spring sleeves")
        layout.operator('claire_v3.play_opening', icon='PLAY')
        layout.operator('claire_v3.skip_opening', icon='FORWARD')
        column = layout.column(align=True)
        for frame, label in _MARKERS:
            button = column.operator("claire_v3.preview_frame", text=f"{frame:03d}  {label}")
            button.frame = frame
        layout.separator()
        if _record().get("instance") is None:
            layout.operator("claire_v3.hover_preview", icon="PLAY")
        else:
            layout.operator("claire_v3.stop_hover", icon="PAUSE")
            layout.label(text="Esc: restore / hover only", icon="INFO")
        layout.label(text="Frame: " + str(context.scene.frame_current))
        layout.label(text="Hover: " + context.scene.get("claire_hover_disc", "none"))
        layout.label(text="Blender motion; no audio or webpage")


_CLASSES = (
    CLAIREV3_OT_preview_frame,
    CLAIREV3_OT_hover_preview,
    CLAIREV3_OT_play_opening,
    CLAIREV3_OT_skip_opening,
    CLAIREV3_OT_stop_hover,
    CLAIREV3_PT_motion_preview,
)


def unregister():
    _stop_preview(bpy.context)
    # Keep the actual registered class objects across repeated Text Editor runs;
    # Blender's operator RNA names can differ from Python class names.
    previous_classes = list(_record().get("classes", ()))
    # Loading another .blend clears driver_namespace but can leave registered
    # UI types alive. Resolve only this runtime's own RNA names in that case.
    for cls in _CLASSES:
        if issubclass(cls, bpy.types.Operator):
            namespace, operation = cls.bl_idname.split(".", 1)
            rna_name = namespace.upper() + "_OT_" + operation
        else:
            rna_name = cls.bl_idname
        previous = getattr(bpy.types, rna_name, None)
        if previous is not None and previous not in previous_classes:
            previous_classes.append(previous)
    for cls in reversed(previous_classes):
        if getattr(cls, "is_registered", False):
            bpy.utils.unregister_class(cls)
    _record()["classes"] = ()


def register():
    unregister()
    for cls in _CLASSES:
        bpy.utils.register_class(cls)
    _record()["classes"] = _CLASSES
    print("Claire modern-v03 motion panel registered. Hover preview is optional.")


if __name__ == "__main__":
    register()
