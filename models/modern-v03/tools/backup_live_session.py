"""Preserve current unsaved Blender data without replacing its source file."""
from pathlib import Path
from datetime import datetime, timezone
import json
import bpy

root = Path('D:/projects/claire/models/modern-v03')
backup = root.parent / 'archives' / ('live-v02-session-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '.blend')
state = {'source': bpy.data.filepath, 'was_dirty': bpy.data.is_dirty, 'backup': str(backup)}
try:
    record = bpy.app.driver_namespace.get('claire_modern_v02_preview_runtime', {})
    if record.get('instance') is not None:
        record['instance'].finish(bpy.context, restore=True)
    if bpy.context.screen and bpy.context.screen.is_animation_playing:
        bpy.ops.screen.animation_cancel(restore_frame=False)
    if bpy.context.area and bpy.context.area.type == 'CONSOLE':
        bpy.context.area.type = 'VIEW_3D'
    result = bpy.ops.wm.save_as_mainfile(filepath=str(backup), copy=True, check_existing=False)
    assert 'FINISHED' in result and backup.stat().st_size > 1024
    state['saved'] = True
except Exception as error:
    state['error'] = repr(error)
(root / 'live-session-backup.json').write_text(json.dumps(state, indent=2), encoding='utf-8')
