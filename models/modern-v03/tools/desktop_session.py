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
    if pid.value==int(sys.argv[1]) and USER.IsWindowVisible(hwnd):
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
        send_key(vk);time.sleep(.025);send_key(vk,True)
        if modifiers&1:send_key(0x10,True)
        time.sleep(.004)

def console_command(command):
    focus();send_key(0x10);time.sleep(.12);send_key(0x73);time.sleep(.12);send_key(0x73,True);time.sleep(.12);send_key(0x10,True);time.sleep(2.0)
    USER.SetCursorPos(rect.left+int((rect.right-rect.left)*.30),rect.top+int((rect.bottom-rect.top)*.89))
    USER.mouse_event(2,0,0,0,0);time.sleep(.12);USER.mouse_event(4,0,0,0,0);time.sleep(.5)
    # Changing editor type inside a Console command can retain its input buffer.
    send_key(0x11);send_key(0x41);time.sleep(.08);send_key(0x41,True);send_key(0x11,True)
    send_key(0x08);time.sleep(.08);send_key(0x08,True);time.sleep(.1)
    text_ascii(command);time.sleep(.2);send_key(0x0D);time.sleep(.1);send_key(0x0D,True)


if __name__ == '__main__':
    action = sys.argv[2]
    scripts={'backup':'backup_live_session.py','open':'open_v3_live.py','qa':'live_preview_check.py'}
    reports={'backup':'live-session-backup.json','open':'live-v3-ready.json','qa':'live-playback-report.json'}
    script = ROOT / 'tools' / scripts[action]
    report = ROOT / reports[action]
    before_time = time.time()
    console_command("exec(open(r'%s',encoding='utf-8').read())" % str(script).replace('\\','/'))
    for _ in range(40):
        time.sleep(.5)
        if report.exists() and report.stat().st_mtime >= before_time:
            state = json.loads(report.read_text(encoding='utf-8'))
            if state.get('error'): raise RuntimeError(state['error'])
            print(json.dumps(state, ensure_ascii=False)); break
    else: raise RuntimeError('Blender did not confirm operation')
