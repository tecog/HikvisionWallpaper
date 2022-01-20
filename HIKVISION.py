#!pip install pypiwin32 pywin32
# import win32.lib.win32con as win32con
import pywintypes
import win32api
import _thread
import ctypes,ctypes.wintypes
from win32gui import FindWindow, FindWindowEx, ShowWindow, SendMessageTimeout, SetParent, EnumWindows, GetWindowText
from win32con import SW_HIDE, SMTO_ABORTIFHUNG, WS_POPUP, GWL_STYLE
from tkinter import BOTH,Tk,Canvas

IP = "192.168.1.222"
Username = "admin"
Password = "password"

def _MyCallback(hwnd, extra):#遍历窗口函数的回调函数（提前return退出遍历会报错）
    #当前窗口中查找图标窗口
    icon_window = FindWindowEx(hwnd, None, "SHELLDLL_DefView", None)
    if(icon_window!=0):#当前窗口包含图标窗口
        #查找静态壁纸窗口并保存
        extra[0] = FindWindowEx(None, hwnd, "WorkerW", None)


class Wallpaper:
    def __init__(self,handle):
        self.handle = handle

    def start(self):                       # 不能用join(),否则到不了mainloop,Tkinter打不开。
        _thread.start_new_thread(self.RunVideoWallpaper,())

    def RunVideoWallpaper(self):#设置视频壁纸
        if(self.handle!=0):
            #查找桌面窗口
            desktop_window_handel = FindWindow("Progman", "Program Manager")
            #设置player_window为desktop_window的子窗口
            SetParent(self.handle, desktop_window_handel)
            #核心语句，向desktop_window发送0x52C启用Active Desktop
            SendMessageTimeout(desktop_window_handel, 0x52C, 0, 0, SMTO_ABORTIFHUNG, 500)#如果报TimeOut,增加延时
            #因为有两个同类同名的WorkerW窗口，所以遍历所以顶层窗口
            workerw=[0]
            EnumWindows(_MyCallback, workerw)
            #获取player_windows名称
            player_windows_name = GetWindowText(self.handle)
            # print(player_windows_name)
            while(True):#防止win+tab导致静态壁纸窗口重新出现及将player_window发送到图标窗口的父窗口(原因不明)
                #隐藏静态壁纸窗口
                ShowWindow(workerw[0], SW_HIDE)
                #判断player_window是否在desktop_window下
                player_under_desktop = FindWindowEx(desktop_window_handel, None, "TkTopLevel", player_windows_name)
                if(player_under_desktop==0):#如果player_window位置不正确
                    #将player_window设置为desktop_window的子窗口
                    SetParent(self.handle, desktop_window_handel)

class NET_DVR_DEVICEINFO_V30(ctypes.Structure):
    _fields_ = [
            ("sSerialNumber", ctypes.c_byte*48),
            ("byAlarmInPortNum", ctypes.c_byte),
            ("byAlarmOutPortNum", ctypes.c_byte),
            ("byDiskNum", ctypes.c_byte),
            ("byDVRType", ctypes.c_byte),
            ("byChanNum", ctypes.c_byte),
            ("byStartChan", ctypes.c_byte),
            ("byAudioChanNum", ctypes.c_byte),
            ("byIPChanNum", ctypes.c_byte),
            ("byZeroChanNum", ctypes.c_byte),
            ("byMainProto", ctypes.c_byte),
            ("bySubProto", ctypes.c_byte),
            ("bySupport", ctypes.c_byte),
            ("bySupport1", ctypes.c_byte),
            ("bySupport2", ctypes.c_byte),
            ("wDevType", ctypes.c_uint16),
            ("bySupport3", ctypes.c_byte),
            ("byMultiStreamProto", ctypes.c_byte),
            ("byStartDChan", ctypes.c_byte),
            ("byStartDTalkChan", ctypes.c_byte),
            ("byHighDChanNum", ctypes.c_byte),
            ("bySupport4", ctypes.c_byte),
            ("byLanguageType", ctypes.c_byte),
            ("byVoiceInChanNum", ctypes.c_byte),
            ("byStartVoiceInChanNo", ctypes.c_byte),
            ("bySupport5", ctypes.c_byte),
            ("bySupport6", ctypes.c_byte),
            ("byMirrorChanNum", ctypes.c_byte),
            ("wStartMirrorChanNo", ctypes.c_uint16),
            ("bySupport7", ctypes.c_byte),
            ("byRes2", ctypes.c_byte),
        ]

class NET_DVR_PREVIEWINFO(ctypes.Structure):
    _fields_ = [
            ("lChannel", ctypes.c_long),
            ("dwStreamType", ctypes.c_uint32),
            ("dwLinkMode", ctypes.c_uint32),
            ("hPlayWnd", ctypes.wintypes.HWND ),
            ("bBlocked", ctypes.c_uint32),
            ("bPassbackRecord", ctypes.c_uint32),
            ("byPreviewMode", ctypes.c_byte),
            ("byStreamID", ctypes.c_byte*32),
            ("byProtoType", ctypes.c_byte),
            ("byRes1", ctypes.c_byte),
            ("byVideoCodingType", ctypes.c_byte),
            ("dwDisplayBufNum", ctypes.c_uint32),
            ("byNPQMode", ctypes.c_byte),
            ("byRecvMetaData", ctypes.c_byte),
            ("byRes", ctypes.c_byte*214),
        ]


if __name__ == "__main__":
    lib= ctypes.CDLL('lib/HCNetSDK.dll')
    lib.NET_DVR_Init()
    lib.NET_DVR_SetConnectTime(2000, 1)
    lib.NET_DVR_SetReconnect(10000, True)

    DeviceInfoTmp = NET_DVR_DEVICEINFO_V30()

    userID = lib.NET_DVR_Login_V30(
        (ctypes.c_char * 20)(*bytes(IP,'utf-8')),8000,
        (ctypes.c_char * 20)(*bytes(Username,'utf-8')),
        (ctypes.c_char * 20)(*bytes(Password,'utf-8')),
        ctypes.byref(DeviceInfoTmp))
    print("登录成功" if userID>-1 else "登陆失败")

    root = Tk()
    root.geometry("1920x1040+0+0")
    root.lift()
    root.overrideredirect(True)
    cv = Canvas(root,bg="white")
    cv.pack(fill=BOTH,expand=1)
    hCanvas = cv.winfo_id()
    win32api.SetWindowLong(hCanvas,GWL_STYLE,WS_POPUP)
    struPlayInfo = NET_DVR_PREVIEWINFO()
    ref = ctypes.wintypes.HWND()
    ref.value = int(hCanvas)
    struPlayInfo.hPlayWnd = hCanvas
    struPlayInfo.lChannel = ctypes.c_long(1)
    print("画板句柄",struPlayInfo.hPlayWnd)
    IRealPlayHandle = lib.NET_DVR_RealPlay_V40(ctypes.c_long(userID), ctypes.byref(struPlayInfo), None, None)
    print(("NET_DVR_RealPlay_V40 错误",lib.NET_DVR_GetLastError()) if IRealPlayHandle < 0 else "打开成功")
        
    p = Wallpaper(pywintypes.HANDLE(int(root.frame(), 16)))
    p.start()  
    root.mainloop()


