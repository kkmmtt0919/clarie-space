"""Load in Blender's Python Console, then explicitly call protected_open(target).

This module has no automatic GUI or data-changing actions. The function saves an
independent backup of the current in-memory session before opening the new file.
"""
from datetime import datetime, timezone
from pathlib import Path
import json
import bpy


def protected_open(target):
    target = Path(target).resolve()
    workspace = Path("D:/projects/claire-vinyl-preview").resolve()
    if not target.is_relative_to(workspace):
        raise ValueError("Target must be within the Claire workspace.")
    if target.suffix.lower() != ".blend" or not target.is_file() or target.stat().st_size < 1024:
        raise ValueError("Target is not a completed Blender file.")

    backup_dir = target.parent / "session-backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    source = bpy.data.filepath
    basename = Path(source).stem if source else "untitled-session"
    backup = backup_dir / (basename + "-before-modern-" + stamp + ".blend")
    report = backup_dir / ("session-switch-" + stamp + ".json")
    state = {"source": source, "backup": str(backup), "target": str(target), "stage": "started"}

    def write_report():
        report.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

    write_report()
    try:
        # Console must have been opened from the 3D viewport. Restoring it here
        # prevents preserving the temporary Console editor in the backup UI.
        if bpy.context.area and bpy.context.area.type == "CONSOLE":
            bpy.context.area.type = "VIEW_3D"
        saved = bpy.ops.wm.save_as_mainfile(filepath=str(backup), copy=True, check_existing=False)
        if "FINISHED" not in saved or not backup.is_file() or backup.stat().st_size < 1024:
            raise RuntimeError("Current-session backup did not finish; target was not opened.")
        state["stage"] = "backup-saved"
        state["backup_size"] = backup.stat().st_size
        write_report()
        opened = bpy.ops.wm.open_mainfile(filepath=str(target), load_ui=True, use_scripts=False)
        if "FINISHED" not in opened:
            raise RuntimeError("New file could not be opened. Current session is preserved in backup.")
        state["stage"] = "target-opened"
        write_report()
        return state
    except Exception as error:
        state["error"] = repr(error)
        write_report()
        raise
