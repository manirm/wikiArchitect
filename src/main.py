import wx
import sys
import os
import ctypes
import ctypes.util
import asyncio
from src.ui.main_frame import MainFrame
from src.core.agent import WikiArchitectAgent

def set_macos_app_id():
    """Hack to set the macOS App Menu name when running from source."""
    if sys.platform != 'darwin':
        return
        
    try:
        cf_path = ctypes.util.find_library('CoreFoundation')
        if not cf_path: return
        cf = ctypes.CDLL(cf_path)
        
        # CFStringCreateWithCString
        cf.CFStringCreateWithCString.restype = ctypes.c_void_p
        cf.CFStringCreateWithCString.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_uint32]
        
        # CFBundleGetMainBundle
        cf.CFBundleGetMainBundle.restype = ctypes.c_void_p
        
        # CFBundleGetInfoDictionary
        cf.CFBundleGetInfoDictionary.restype = ctypes.c_void_p
        cf.CFBundleGetInfoDictionary.argtypes = [ctypes.c_void_p]
        
        # CFDictionarySetValue
        cf.CFDictionarySetValue.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]

        bundle = cf.CFBundleGetMainBundle()
        if not bundle: return
        
        info_dict = cf.CFBundleGetInfoDictionary(bundle)
        if not info_dict: return
        
        def cf_str(s):
            return cf.CFStringCreateWithCString(None, s.encode('utf8'), 0x08000100)

        cf.CFDictionarySetValue(info_dict, cf_str("CFBundleName"), cf_str("WikiArchitect"))
        cf.CFDictionarySetValue(info_dict, cf_str("CFBundleDisplayName"), cf_str("WikiArchitect"))
    except Exception:
        pass

class WikiArchitectApp(wx.App):
    """
    Main Application class for WikiArchitect.
    """
    def __init__(self, *args, **kwargs):
        set_macos_app_id()
        super().__init__(*args, **kwargs)

    def OnInit(self):
        # Set application identity at the absolute entry point
        self.SetAppName("WikiArchitect")
        self.SetAppDisplayName("WikiArchitect")
        
        # Initialize the theme and main frame
        self.frame = MainFrame(None, title="WikiArchitect")
        self.frame.Show()
        self.SetTopWindow(self.frame)
        return True

async def main_async():
    """Entry point for the async-enabled wxPython app."""
    # We use a custom event loop or just allow wx to handle its main loop.
    # For now, we'll use a simple wx.App and integrate async via wx.CallAfter or asyncio.run_coroutine_threadsafe.
    # However, for a simple desktop app, we'll initialize the app classically.
    
    app = WikiArchitectApp()
    app.MainLoop()

if __name__ == "__main__":
    # In a full async production app, we would use something like WxAsync.
    # For this implementation, we run the standard MainLoop.
    app = WikiArchitectApp()
    app.MainLoop()
