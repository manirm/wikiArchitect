import wx
import asyncio
from src.ui.main_frame import MainFrame
from src.core.agent import WikiArchitectAgent

class WikiArchitectApp(wx.App):
    """
    Main Application class for WikiArchitect.
    """
    def OnInit(self):
        # Set Application Identity for macOS and other platforms
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
