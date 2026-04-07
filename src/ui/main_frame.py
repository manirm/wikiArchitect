import wx
import wx.aui
import wx.stc
import wx.html2
import wx.adv
import os
import threading
import asyncio
from typing import List, Optional, Tuple, Dict, Any
import markdown2
from src.core.agent import WikiArchitectAgent, FileChange
from src.ui.diff_viewer import DiffViewerDialog

# --- Constants & Theme ---
DARK_BG = wx.Colour(30, 30, 30)
SIDEBAR_BG = wx.Colour(37, 37, 38)
TEXT_COLOUR = wx.Colour(204, 204, 204)
ACCENT_COLOUR = wx.Colour(0, 120, 212)

class MainFrame(wx.Frame):
    """
    Refined MainFrame for WikiArchitect.
    Integrates the LLM Agent and the DiffViewer for a complete workflow.
    """

    def __init__(self, parent, title="WikiArchitect"):
        super(MainFrame, self).__init__(parent, title=title, size=(1200, 800))
        
        # Initialize Core Agent
        self.agent = WikiArchitectAgent()
        self.current_file = None
        
        self.SetBackgroundColour(DARK_BG)
        self._mgr = wx.aui.AuiManager(self)
        
        # --- Sidebar (Top-level) ---
        self.sidebar = wx.Panel(self, style=wx.BORDER_NONE)
        self.sidebar.SetBackgroundColour(SIDEBAR_BG)
        sidebar_sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.dir_ctrl = wx.GenericDirCtrl(self.sidebar, dir=".", style=wx.DIRCTRL_SHOW_FILTERS | wx.BORDER_NONE)
        # Customizing DirCtrl tree
        tree = self.dir_ctrl.GetTreeCtrl()
        tree.SetBackgroundColour(SIDEBAR_BG)
        tree.SetForegroundColour(TEXT_COLOUR)
        
        sidebar_sizer.Add(self.dir_ctrl, 1, wx.EXPAND | wx.ALL, 5)
        self.sidebar.SetSizer(sidebar_sizer)
        
        # --- Central Workspace (Notebook) ---
        self.notebook = wx.aui.AuiNotebook(self, style=wx.aui.AUI_NB_TOP | wx.aui.AUI_NB_TAB_SPLIT | wx.aui.AUI_NB_TAB_MOVE | wx.BORDER_NONE)
        
        # Editor Tab
        self.editor = wx.stc.StyledTextCtrl(self.notebook, style=wx.BORDER_NONE)
        self._setup_editor_stc()
        self.notebook.AddPage(self.editor, "Editor")
        
        # Preview Tab (HTML WebView)
        self.preview = wx.html2.WebView.New(self.notebook)
        self.notebook.AddPage(self.preview, "Preview")
        
        # --- Right Panel (Architect Chat) ---
        self.chat_panel = wx.Panel(self, style=wx.BORDER_NONE)
        self.chat_panel.SetBackgroundColour(SIDEBAR_BG)
        chat_sizer = wx.BoxSizer(wx.VERTICAL)
        
        chat_header = wx.StaticText(self.chat_panel, label="Architect Assistant")
        chat_header.SetForegroundColour(ACCENT_COLOUR)
        
        self.chat_log = wx.TextCtrl(self.chat_panel, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.BORDER_NONE)
        self.chat_log.SetBackgroundColour(DARK_BG)
        self.chat_log.SetForegroundColour(TEXT_COLOUR)
        
        self.chat_input = wx.TextCtrl(self.chat_panel, style=wx.TE_PROCESS_ENTER | wx.BORDER_NONE)
        self.chat_input.SetBackgroundColour(DARK_BG)
        self.chat_input.SetForegroundColour(TEXT_COLOUR)
        
        chat_sizer.Add(chat_header, 0, wx.ALL, 10)
        chat_sizer.Add(self.chat_log, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)
        chat_sizer.Add(self.chat_input, 0, wx.EXPAND | wx.ALL, 10)
        self.chat_panel.SetSizer(chat_sizer)
        
        # --- AUI Panes Management ---
        self._mgr.AddPane(self.sidebar, wx.aui.AuiPaneInfo().Name("sidebar").Caption("Explorer").Left().Layer(1).Position(1).CloseButton(False).MinSize((250, -1)))
        self._mgr.AddPane(self.notebook, wx.aui.AuiPaneInfo().Name("notebook").CenterPane().PaneBorder(False))
        self._mgr.AddPane(self.chat_panel, wx.aui.AuiPaneInfo().Name("chat").Caption("Knowledge Librarian").Right().Layer(1).Position(1).MinSize((350, -1)))
        
        self._mgr.Update()
        
        # --- Menu Bar ---
        self._setup_menus()
        
        # --- Toolbar for Ingest ---
        self.toolbar = self.CreateToolBar(wx.TB_HORIZONTAL | wx.NO_BORDER)
        self.toolbar.SetBackgroundColour(SIDEBAR_BG)
        ingest_bmp = wx.ArtProvider.GetBitmap(wx.ART_ADD_BOOKMARK, wx.ART_TOOLBAR, (16, 16))
        self.toolbar.AddTool(wx.ID_ADD, "Ingest", ingest_bmp, "Ingest New Source")
        self.toolbar.Realize()

        # Final Event Binding
        self.Bind(wx.EVT_MENU, self.on_ingest, id=wx.ID_ADD)
        self.Bind(wx.EVT_MENU, self.on_exit, id=wx.ID_EXIT)
        self.Bind(wx.EVT_MENU, self.on_about, id=wx.ID_ABOUT)
        self.Bind(wx.EVT_MENU, self.on_help, id=wx.ID_HELP)

    def _setup_menus(self):
        """Creates the professional menu bar for File, Edit, and Help."""
        menubar = wx.MenuBar()
        
        # File Menu
        file_menu = wx.Menu()
        file_menu.Append(wx.ID_ADD, "&Ingest Source...\tCtrl+I", "Add a new PDF or Text source")
        file_menu.AppendSeparator()
        file_menu.Append(wx.ID_EXIT, "E&xit\tAlt+X", "Exit the application")
        menubar.Append(file_menu, "&File")
        
        # Help Menu
        help_menu = wx.Menu()
        help_menu.Append(wx.ID_HELP, "&User Guide\tF1", "Open the comprehensive documentation")
        help_menu.AppendSeparator()
        help_menu.Append(wx.ID_ABOUT, "&About WikiArchitect...", "Application details and version")
        menubar.Append(help_menu, "&Help")
        
        self.SetMenuBar(menubar)

    # --- Event Handlers ---

    def on_exit(self, event):
        self.Close()

    def on_about(self, event):
        """Displays a professional About dialog."""
        info = wx.adv.AboutDialogInfo()
        info.SetName("WikiArchitect")
        info.SetVersion("0.1.0-Alpha")
        info.SetDescription("A local-first, LLM-driven Knowledge Base Architect.\nMantain your wiki with the help of a Librarian-AI.")
        info.SetCopyright("(C) 2026 WikiArchitect Contributors")
        info.SetWebSite("https://github.com/manir/wikiArchitech")
        info.SetLicence("MIT License")
        info.AddDeveloper("The WikiArchitect Community")
        wx.adv.AboutBox(info)

    def on_help(self, event):
        """Opens the User Guide in the preview tab or OS default browser."""
        guide_path = os.path.join(os.getcwd(), "docs", "USER_GUIDE.md")
        if os.path.exists(guide_path):
            with open(guide_path, 'r') as f:
                content = f.read()
                self.editor.SetText(content)
                self.notebook.SetSelection(0) # Editor tab
                self.SetStatusText("Loaded User Guide.")
        else:
            wx.MessageBox("User Guide not found in 'docs/USER_GUIDE.md'.", "Error", wx.OK | wx.ICON_ERROR)

    def on_ingest(self, event):
        """Opens a file dialog to select a source for ingestion."""
        dlg = wx.FileDialog(self, "Select Source File", wildcard="PDF files (*.pdf)|*.pdf|Text files (*.txt)|*.txt", style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.chat_log.AppendText(f"Librarian: Ingesting {os.path.basename(path)}...\n")
            threading.Thread(target=self._run_agent_ingest, args=(path,), daemon=True).start()
        dlg.Destroy()

    def _run_agent_ingest(self, path):
        """Extracts text and calls Agent Ingest."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # 1. Extraction
        from src.core.pdf_extractor import PDFExtractor
        if path.endswith('.pdf'):
            content = PDFExtractor.extract_text(path)
        else:
            with open(path, 'r') as f:
                content = f.read()
        
        # 2. Agent Ingest Call
        response = loop.run_until_complete(self.agent.propose_ingest(content, os.path.basename(path)))
        loop.close()
        
        # Update UI
        wx.CallAfter(self._handle_agent_response, response)

    def on_file_activated(self, event):
        """Loads a file into the editor."""
        path = self.dir_ctrl.GetPath()
        if os.path.isfile(path) and (path.endswith('.md') or path.endswith('.txt')):
            self.current_file = path
            with open(path, 'r') as f:
                content = f.read()
                self.editor.SetText(content)
                self.editor.EmptyUndoBuffer()
            self.SetStatusText(f"Editing: {os.path.basename(path)}")

    def on_tab_changed(self, event):
        """Automatically updates the Preview tab when selected."""
        if self.notebook.GetPageText(event.GetSelection()) == "Preview":
            content = self.editor.GetText()
            html = markdown2.markdown(content, extras=["tables", "fenced-code-blocks", "wiki-tables"])
            # Inject some CSS for dark mode preview
            styled_html = f"<style>body {{ background: #1E1E1E; color: #CCCCCC; font-family: sans-serif; padding: 20px; }} code {{ background: #333; }}</style><body>{html}</body>"
            self.preview.SetPage(styled_html, "")

    def on_chat_send(self, event):
        """Sends user query to the agent thread."""
        query = self.chat_input.GetValue()
        if query.strip():
            self.chat_log.AppendText(f"\nArchitect: {query}\n")
            self.chat_input.ChangeValue("")
            self.chat_log.AppendText("Librarian: Consulting knowledge base...\n")
            
            # Offload LLM call to a background thread
            threading.Thread(target=self._run_agent_query, args=(query,), daemon=True).start()

    def _run_agent_query(self, query):
        """Actually calls the LLM (in a thread)."""
        # Run async coroutine in a thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        response = loop.run_until_complete(self.agent.propose_query(query))
        loop.close()
        
        # Update UI safely
        wx.CallAfter(self._handle_agent_response, response)

    def _handle_agent_response(self, response):
        """Processes the LLM response: shows summary and diff viewer if needed."""
        self.chat_log.AppendText(f"Librarian: {response.main_response or 'Analysis complete.'}\n")
        
        if response.file_changes:
            self.chat_log.AppendText(f"Librarian: Proposed {len(response.file_changes)} changes. Opening review dialog...\n")
            dlg = DiffViewerDialog(self, response.file_changes)
            if dlg.ShowModal() == wx.ID_OK:
                selected = dlg.get_selected_proposals()
                self._apply_file_changes(selected)
                self.chat_log.AppendText(f"Librarian: Successfully applied {len(selected)} changes.\n")
            dlg.Destroy()

    def _apply_file_changes(self, changes: List[FileChange]):
        """Writes the accepted changes to disk."""
        for change in changes:
            full_path = os.path.join(self.agent.base_dir, change.file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w') as f:
                f.write(change.new_content)
        # Update UI if current file changed
        if self.current_file:
            # Refresh editor if the specific file was updated
            pass 
        self.dir_ctrl.Rehash()
