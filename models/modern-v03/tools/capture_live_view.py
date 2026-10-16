"""Capture only the authorized Blender window; optionally click the visible opening control."""
import sys,runpy,time,json
from pathlib import Path
from PIL import ImageGrab

root=Path(__file__).resolve().parents[1]
scope=runpy.run_path(str(root/'tools'/'desktop_session.py'),run_name='capture')
scope['focus']()
rect=scope['rect']
if '--restore-view' in sys.argv:
    send=scope['send_key']
    send(0x10);time.sleep(.1);send(0x74);time.sleep(.1);send(0x74,True);send(0x10,True);time.sleep(1)
def capture(name):
    ImageGrab.grab(bbox=(max(0,rect.left),max(0,rect.top),rect.right,rect.bottom)).save(root/name)

if '--hover' in sys.argv:
    user=scope['USER']
    def move(x,y):user.SetCursorPos(rect.left+int((rect.right-rect.left)*x),rect.top+int((rect.bottom-rect.top)*y))
    move(.72,.40)
    user.mouse_event(2,0,0,0,0);time.sleep(.08);user.mouse_event(4,0,0,0,0)
    time.sleep(.3)
    for key,x,y in [('about',.35,.305),('projects',.425,.445),('world',.51,.375)]:
        move(x,y);time.sleep(.4);capture('blender-hover-'+key+'.png')
    for x,y in ((.35,.305),(.425,.445),(.51,.375)):
        move(x,y);time.sleep(.05)
    move(.58,.70);time.sleep(.6);capture('blender-hover-returned.png')
    scope['send_key'](0x1B);time.sleep(.1);scope['send_key'](0x1B,True);time.sleep(.5)
    capture('blender-v3-ready.png')
elif '--skip' in sys.argv:
    user=scope['USER']
    user.SetCursorPos(rect.left+int((rect.right-rect.left)*.72),rect.top+int((rect.bottom-rect.top)*.192))
    user.mouse_event(2,0,0,0,0);time.sleep(.08);user.mouse_event(4,0,0,0,0)
    time.sleep(.8)
    capture('blender-v3-ready.png')
elif '--play' in sys.argv:
    user=scope['USER']
    user.SetCursorPos(rect.left+int((rect.right-rect.left)*.72),rect.top+int((rect.bottom-rect.top)*.17))
    user.mouse_event(2,0,0,0,0);time.sleep(.08);user.mouse_event(4,0,0,0,0)
    time.sleep(1)
    capture('blender-opening-in-progress.png')
    time.sleep(4)
    capture('blender-opening-finished.png')
else:capture('blender-v3-ready.png')
