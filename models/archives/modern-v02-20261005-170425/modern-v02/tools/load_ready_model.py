"""Explicit desktop action: preserve user's Blender session, open model, register preview.
Uses only the Blender process requested by the user; no clipboard is read or written.
"""
import ctypes, time, json, sys
from ctypes import wintypes
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
USER=ctypes.windll.user32
try: USER.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
except Exception: pass
ULONG_PTR=ctypes.c_ulonglong if ctypes.sizeof(ctypes.c_void_p)==8 else ctypes.c_ulong
class KEYBDINPUT(ctypes.Structure):
    _fields_=[('wVk',wintypes.WORD),('wScan',wintypes.WORD),('dwFlags',wintypes.DWORD),('time',wintypes.DWORD),('dwExtraInfo',ULONG_PTR)]
class MOUSEINPUT(ctypes.Structure):
    _fields_=[('dx',wintypes.LONG),('dy',wintypes.LONG),('mouseData',wintypes.DWORD),('dwFlags',wintypes.DWORD),('time',wintypes.DWORD),('dwExtraInfo',ULONG_PTR)]
class HARDWAREINPUT(ctypes.Structure):
    _fields_=[('uMsg',wintypes.DWORD),('wParamL',wintypes.WORD),('wParamH',wintypes.WORD)]
class INPUTUNION(ctypes.Union):
    _fields_=[('ki',KEYBDINPUT),('mi',MOUSEINPUT),('hi',HARDWAREINPUT)]
class INPUT(ctypes.Structure):
    _fields_=[('type',wintypes.DWORD),('u',INPUTUNION)]
USER.SendInput.argtypes=(wintypes.UINT,ctypes.POINTER(INPUT),ctypes.c_int)
USER.SendInput.restype=wintypes.UINT
USER.GetForegroundWindow.restype=wintypes.HWND
USER.SetForegroundWindow.argtypes=(wintypes.HWND,)
USER.ShowWindow.argtypes=(wintypes.HWND,ctypes.c_int)
USER.GetWindowRect.argtypes=(wintypes.HWND,ctypes.POINTER(wintypes.RECT))
USER.GetWindowThreadProcessId.argtypes=(wintypes.HWND,ctypes.POINTER(wintypes.DWORD))
windows=[]
CALLBACK=ctypes.WINFUNCTYPE(wintypes.BOOL,wintypes.HWND,wintypes.LPARAM)
@CALLBACK
def enum(hwnd,param):
    pid=wintypes.DWORD();USER.GetWindowThreadProcessId(hwnd,ctypes.byref(pid))
    if pid.value==35936 and USER.IsWindowVisible(hwnd):
        txt=ctypes.create_unicode_buffer(1024);USER.GetWindowTextW(hwnd,txt,1024)
        rect=wintypes.RECT();USER.GetWindowRect(hwnd,ctypes.byref(rect))
        if rect.right-rect.left>500:windows.append((hwnd,txt.value,rect))
    return True
USER.EnumWindows(enum,0)
if len(windows)!=1:raise RuntimeError('Expected one user Blender main window; found %s'%len(windows))
hwnd,title,rect=windows[0]

def send_key(vk,up=False):
    scan=USER.MapVirtualKeyW(vk,0)
    x=INPUT(type=1);x.u.ki=KEYBDINPUT(0,scan,8|(2 if up else 0),0,0)
    if USER.SendInput(1,ctypes.byref(x),ctypes.sizeof(INPUT))!=1:raise RuntimeError('Keyboard event failed')

def focus():
    USER.ShowWindow(hwnd,9)
    foreground=USER.GetForegroundWindow()
    current_thread=ctypes.windll.kernel32.GetCurrentThreadId()
    fore_thread=USER.GetWindowThreadProcessId(foreground,None)
    blender_thread=USER.GetWindowThreadProcessId(hwnd,None)
    attached=[]
    for tid in set([fore_thread,blender_thread]):
        if tid and tid!=current_thread and USER.AttachThreadInput(current_thread,tid,True):attached.append(tid)
    try:
        USER.BringWindowToTop(hwnd)
        USER.SetForegroundWindow(hwnd)
        USER.SetActiveWindow(hwnd)
    finally:
        for tid in attached:USER.AttachThreadInput(current_thread,tid,False)
    time.sleep(.4)
    if USER.GetForegroundWindow()!=hwnd:raise RuntimeError('Blender is not foreground; refusing keyboard input')
    USER.GetWindowRect(hwnd,ctypes.byref(rect))
    USER.SetCursorPos(rect.left+int((rect.right-rect.left)*.36),rect.top+int((rect.bottom-rect.top)*.42))
    time.sleep(.2)

def text_unicode(text):
    for char in text:
        down=INPUT(type=1);down.u.ki=KEYBDINPUT(0,ord(char),4,0,0)
        up=INPUT(type=1);up.u.ki=KEYBDINPUT(0,ord(char),6,0,0)
        pair=(INPUT*2)(down,up)
        if USER.SendInput(2,pair,ctypes.sizeof(INPUT))!=2:raise RuntimeError('Unicode text input failed')

def text_ascii(text):
    # Blender consumes raw scan-code events rather than VK_PACKET/WM_CHAR.
    for char in text:
        key=USER.VkKeyScanW(ord(char))
        if key==-1 or ord(char)>127:raise RuntimeError('Only known ASCII commands may be typed')
        vk=key&255; modifiers=(key>>8)&255
        if modifiers & 6:raise RuntimeError('Unexpected keyboard-layout modifier')
        if modifiers&1:send_key(0x10);time.sleep(.008)
        send_key(vk);time.sleep(.008);send_key(vk,True)
        if modifiers&1:send_key(0x10,True)
        time.sleep(.004)

def console_command(command):
    focus();send_key(0x10);time.sleep(.12);send_key(0x73);time.sleep(.12);send_key(0x73,True);time.sleep(.12);send_key(0x10,True);time.sleep(.7)
    # Changing editor type inside a Console command can retain its input buffer.
    send_key(0x11);send_key(0x41);time.sleep(.08);send_key(0x41,True);send_key(0x11,True)
    send_key(0x08);time.sleep(.08);send_key(0x08,True);time.sleep(.1)
    text_ascii(command);time.sleep(.2);send_key(0x0D);time.sleep(.1);send_key(0x0D,True)

if '--probe-console' in sys.argv:
    focus()
    probe=str(ROOT/'console-probe.json').replace('\\','/')
    text_ascii("open(r'%s','w').write(__import__('json').dumps({'area':bpy.context.area.type,'file':bpy.data.filepath}))"%probe)
    time.sleep(.2);send_key(0x0D);time.sleep(.1);send_key(0x0D,True);time.sleep(2)
    from PIL import ImageGrab
    ImageGrab.grab(bbox=(max(0,rect.left),max(0,rect.top),rect.right,rect.bottom)).save(str(ROOT/'blender-probe-check.png'))
    print('Probe delivered', 'confirmed' if (ROOT/'console-probe.json').exists() else 'unconfirmed')
    print('Window',rect.left,rect.top,rect.right,rect.bottom)
    raise SystemExit(0)

if '--configure-preview' in sys.argv:
    config=str(ROOT/'tools/finalize_live_view.py').replace('\\','/')
    console_command("exec(compile(open(r'%s',encoding='utf-8').read(),'<preview-ui>','exec'))"%config)
    time.sleep(3)
    print('Review UI', (ROOT/'live-preview-ready.json').read_text(encoding='utf-8') if (ROOT/'live-preview-ready.json').exists() else 'unconfirmed')
    raise SystemExit(0)

if '--attach-titles' in sys.argv:
    config=str(ROOT/'tools/attach_card_headers.py').replace('\\','/')
    before_time=time.time()
    console_command("exec(compile(open(r'%s',encoding='utf-8').read(),'<attach-headers>','exec'))"%config)
    report_path=ROOT/'attached-headers-report.json'
    for _ in range(20):
        time.sleep(.5)
        if report_path.exists() and report_path.stat().st_mtime>=before_time:
            print('Connected headers',report_path.read_text(encoding='utf-8'));break
    else:raise RuntimeError('Header correction was not confirmed')
    raise SystemExit(0)

if '--click-claire' in sys.argv:
    focus()
    USER.SetCursorPos(rect.left+int((rect.right-rect.left)*.813),rect.top+int((rect.bottom-rect.top)*.322))
    time.sleep(.2);USER.mouse_event(2,0,0,0,0);time.sleep(.1);USER.mouse_event(4,0,0,0,0);time.sleep(1)
    from PIL import ImageGrab
    ImageGrab.grab(bbox=(max(0,rect.left),max(0,rect.top),rect.right,rect.bottom)).save(str(ROOT/'blender-claire-panel.png'))
    print('Claire panel selected')
    raise SystemExit(0)

if '--inspect' in sys.argv:
    focus()
    from PIL import ImageGrab
    ImageGrab.grab(bbox=(max(0,rect.left),max(0,rect.top),rect.right,rect.bottom)).save(str(ROOT/'blender-live-check.png'))
    print('Blender window captured only', title)
    raise SystemExit(0)

if '--console-inspect' in sys.argv:
    focus();send_key(0x10);time.sleep(.15);send_key(0x73);time.sleep(.15);send_key(0x73,True);time.sleep(.15);send_key(0x10,True);time.sleep(5)
    from PIL import ImageGrab
    ImageGrab.grab(bbox=(max(0,rect.left),max(0,rect.top),rect.right,rect.bottom)).save(str(ROOT/'blender-console-check.png'))
    print('Blender console state captured')
    raise SystemExit(0)

target=str(ROOT/'claire-modern-v02.blend').replace('\\','/')
helper=str(ROOT/'tools/protected_open_in_blender.py').replace('\\','/')
before=set((ROOT/'session-backups').glob('session-switch-*.json')) if (ROOT/'session-backups').exists() else set()
console_command("exec(compile(open(r'%s',encoding='utf-8').read(),'<protected-open>','exec')); protected_open(r'%s')"%(helper,target))
report=None
for i in range(40):
    time.sleep(.5)
    candidates=set((ROOT/'session-backups').glob('session-switch-*.json'))-before
    if candidates:
        report=max(candidates,key=lambda p:p.stat().st_mtime)
        try:
            state=json.loads(report.read_text(encoding='utf-8'))
            if state.get('error'):raise RuntimeError(state['error'])
            if state.get('stage')=='target-opened':break
        except json.JSONDecodeError:continue
else:raise RuntimeError('Blender did not confirm safe open; no success claimed')
time.sleep(2)
runtime=str(ROOT/'claire_preview_runtime.py').replace('\\','/')
nonce=str(time.time_ns())
status_path=ROOT/('live-window-status-'+nonce+'.json')
status=str(status_path).replace('\\','/')
# Known local preview script only; no global Blender script-security preference changes.
command="exec(compile(open(r'%s',encoding='utf-8').read(),'<claire-preview>','exec')); register(); bpy.context.scene.frame_set(163); bpy.context.area.type='VIEW_3D'; bpy.context.area.spaces.active.show_region_ui=True; open(r'%s','w',encoding='utf-8').write(__import__('json').dumps({'file':bpy.data.filepath,'frame':bpy.context.scene.frame_current,'version':bpy.context.scene.get('claire_model_version'),'runtime_registered':hasattr(bpy.types,'CLAIREMODERN_PT_motion_preview')}))"%(runtime,status)
console_command(command)
for i in range(20):
    time.sleep(.5)
    if status_path.exists():
        print('BLENDER_LIVE', status_path.read_text(encoding='utf-8'))
        print('SESSION_BACKUP',str(report));break
else:raise RuntimeError('New file opened but preview setup was not confirmed')
