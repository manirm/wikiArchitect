import wx
import wx.aui
import wx.stc
import wx.html2
import wx.adv
import os
import sys
import logging
import re
import threading
from datetime import datetime
import asyncio
import urllib.parse
from typing import List, Optional, Tuple, Dict, Any
import markdown2
from src.core.agent import WikiArchitectAgent, FileChange
from src.core.graph_generator import GraphGenerator
from src.ui.diff_viewer import DiffViewerDialog
from src.core.autonomous_architect import AutonomousArchitect

# --- Constants & Theme ---
DARK_BG = wx.Colour(30, 30, 30)
SIDEBAR_BG = wx.Colour(37, 37, 38)
TEXT_COLOUR = wx.Colour(204, 204, 204)
ACCENT_COLOUR = wx.Colour(0, 120, 212)
ID_THEME_TOGGLE = 5000

LIGHT_BG = wx.Colour(251, 251, 251)
LIGHT_SIDEBAR = wx.Colour(243, 243, 243)
LIGHT_TEXT = wx.Colour(44, 44, 44)
LIGHT_ACCENT = wx.Colour(0, 95, 184)

class MainFrame(wx.Frame):
    """
    Refined MainFrame for WikiArchitect.
    Integrates the LLM Agent and the DiffViewer for a complete workflow.
    """

    def __init__(self, parent, title="WikiArchitect"):
        super(MainFrame, self).__init__(parent, title=title, size=(1200, 800))
        
        # Initialize Core Agent and State
        self.agent = WikiArchitectAgent()
        self.current_file = None
        self.theme_mode = "light"
        self.zoom_level = 1.0
        self.base_font_size = 13
        
        self.SetBackgroundColour(LIGHT_BG)
        self._mgr = wx.aui.AuiManager(self)
        
        # --- Sidebar (Top-level) ---
        self.sidebar = wx.Panel(self, style=wx.BORDER_NONE)
        self.sidebar.SetBackgroundColour(SIDEBAR_BG)
        sidebar_sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.dir_ctrl = wx.GenericDirCtrl(self.sidebar, dir="vault", style=wx.DIRCTRL_SHOW_FILTERS | wx.BORDER_NONE)
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
        
        # Knowledge Graph Tab (New!)
        self.graph_view = wx.html2.WebView.New(self.notebook)
        self.notebook.AddPage(self.graph_view, "Knowledge Graph")
        
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
        self._mgr.AddPane(self.chat_panel, wx.aui.AuiPaneInfo().Name("chat").Caption("Librarian").Right().Layer(1).Position(2).CloseButton(False).MinSize((300, -1)))
        
        self._mgr.Update()
        
        # --- Status Bar ---
        self.status_bar = self.CreateStatusBar()
        self.status_bar.SetStatusText("WikiArchitect Ready")

        # --- Startup Indexing ---
        self._start_initial_indexing()
        
        # --- Toolbar for Ingest ---
        self.toolbar = self.CreateToolBar(wx.TB_HORIZONTAL | wx.NO_BORDER)
        self.toolbar.SetBackgroundColour(SIDEBAR_BG)
        ingest_bmp = wx.ArtProvider.GetBitmap(wx.ART_ADD_BOOKMARK, wx.ART_TOOLBAR, (16, 16))
        self.toolbar.AddTool(wx.ID_ADD, "Ingest", ingest_bmp, "Ingest New Source")
        self.toolbar.Realize()

        # Final Event Binding
        self.Bind(wx.EVT_MENU, self.on_ingest, id=wx.ID_ADD)
        self.Bind(wx.EVT_MENU, self.on_save, id=wx.ID_SAVE)
        self.Bind(wx.EVT_MENU, self.on_open_wiki, id=wx.ID_OPEN)
        self.Bind(wx.EVT_MENU, self.on_exit, id=wx.ID_EXIT)
        self.Bind(wx.EVT_MENU, self.on_about, id=wx.ID_ABOUT)
        self.Bind(wx.EVT_MENU, self.on_help, id=wx.ID_HELP)
        
        # View Menu Bindings
        self.Bind(wx.EVT_MENU, self.on_toggle_theme, id=ID_THEME_TOGGLE)
        self.Bind(wx.EVT_MENU, self.on_zoom_in, id=wx.ID_ZOOM_IN)
        self.Bind(wx.EVT_MENU, self.on_zoom_out, id=wx.ID_ZOOM_OUT)
        self.Bind(wx.EVT_MENU, self.on_zoom_reset, id=wx.ID_ZOOM_FIT)
        
        # UI Component Bindings
        self.notebook.Bind(wx.aui.EVT_AUINOTEBOOK_PAGE_CHANGED, self.on_tab_changed)
        self.chat_input.Bind(wx.EVT_TEXT_ENTER, self.on_chat_send)
        self.dir_ctrl.GetTreeCtrl().Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.on_file_activated)
        
        # WebView Navigation Handling (Inter-Wiki Linking)
        self.preview.Bind(wx.html2.EVT_WEBVIEW_NAVIGATING, self.on_preview_navigating)
        self.graph_view.Bind(wx.html2.EVT_WEBVIEW_NAVIGATING, self.on_preview_navigating)

        # Initial Theme Application
        self.apply_theme("light")

    def _setup_editor_stc(self):
        """Configures the StyledTextCtrl for a modern code editing experience."""
        is_dark = self.theme_mode == "dark"
        bg = DARK_BG if is_dark else LIGHT_BG
        fg = TEXT_COLOUR if is_dark else LIGHT_TEXT
        acc = ACCENT_COLOUR if is_dark else LIGHT_ACCENT
        
        # Line numbers
        self.editor.SetMarginType(1, wx.stc.STC_MARGIN_NUMBER)
        self.editor.SetMarginWidth(1, 35)
        
        # Styles
        self.editor.StyleSetBackground(wx.stc.STC_STYLE_DEFAULT, bg)
        self.editor.StyleSetForeground(wx.stc.STC_STYLE_DEFAULT, fg)
        self.editor.StyleClearAll()
        
        # Markdown Lexer (Simplified)
        self.editor.SetLexer(wx.stc.STC_LEX_MARKDOWN)
        self.editor.StyleSetForeground(wx.stc.STC_MARKDOWN_HEADER1, acc)
        self.editor.StyleSetForeground(wx.stc.STC_MARKDOWN_HEADER2, acc)
        self.editor.StyleSetForeground(wx.stc.STC_MARKDOWN_LINK, wx.Colour(100, 150, 255) if is_dark else wx.Colour(0, 0, 238))
        
        # Caret and selection
        self.editor.SetCaretForeground(wx.WHITE if is_dark else wx.BLACK)
        self.editor.SetSelBackground(True, wx.Colour(60, 60, 60) if is_dark else wx.Colour(200, 220, 255))
        
        # Apply current zoom (STC zoom is in points)
        zoom_points = int((self.zoom_level - 1.0) * 10)
        self.editor.SetZoom(zoom_points)

    def _setup_menus(self):
        """Creates the professional menu bar for File, Edit, and Help."""
        menubar = wx.MenuBar()
        
        # File Menu
        file_menu = wx.Menu()
        file_menu.Append(wx.ID_ADD, "&Ingest Source...\tCtrl+I", "Add a new PDF or Text source")
        file_menu.Append(wx.ID_SAVE, "&Save\tCtrl+S", "Save the current file")
        file_menu.Append(wx.ID_OPEN, "&Open Wiki Folder...\tCtrl+O", "Change the active wiki directory")
        file_menu.AppendSeparator()
        file_menu.Append(wx.ID_EXIT, "&Quit\tCtrl+Q", "Exit the application")
        menubar.Append(file_menu, "&File")
        
        # Help Menu
        help_menu = wx.Menu()
        help_menu.Append(wx.ID_HELP, "&User Guide\tF1", "Open the comprehensive documentation")
        help_menu.AppendSeparator()
        help_menu.Append(wx.ID_ABOUT, "&About WikiArchitect...", "Application details and version")
        menubar.Append(help_menu, "&Help")
        
        # View Menu
        view_menu = wx.Menu()
        view_menu.Append(ID_THEME_TOGGLE, "Toggle &Theme\tCtrl+T", "Switch between Light and Dark mode")
        view_menu.AppendSeparator()
        view_menu.Append(wx.ID_ZOOM_IN, "Zoom &In\tCtrl++", "Increase font size")
        view_menu.Append(wx.ID_ZOOM_OUT, "Zoom &Out\tCtrl+-", "Decrease font size")
        view_menu.Append(wx.ID_ZOOM_FIT, "Reset &Zoom\tCtrl+0", "Reset to default size")
        menubar.Append(view_menu, "&View")
        
        self.SetMenuBar(menubar)

    # --- Event Handlers ---

    def on_exit(self, event):
        self.Close()

    def on_save(self, event):
        """Saves the current editor content to the active file."""
        if self.current_file:
            try:
                content = self.editor.GetText()
                with open(self.current_file, 'w') as f:
                    f.write(content)
                self.SetStatusText(f"Saved: {os.path.basename(self.current_file)}")
            except Exception as e:
                wx.MessageBox(f"Error saving file: {str(e)}", "Error", wx.OK | wx.ICON_ERROR)
        else:
            wx.MessageBox("No file is currently open to save.", "Info", wx.OK | wx.ICON_INFORMATION)

    def on_open_wiki(self, event):
        """Allows the user to select a new base directory for the wiki."""
        dlg = wx.DirDialog(self, "Select Your Wiki Folder", style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST)
        if dlg.ShowModal() == wx.ID_OK:
            new_path = dlg.GetPath()
            self.agent.set_base_dir(new_path)
            self.dir_ctrl.SetPath(new_path)
            self.SetStatusText(f"Switched wiki to: {new_path}")
        dlg.Destroy()

    def on_about(self, event):
        """Displays a professional About dialog."""
        info = wx.adv.AboutDialogInfo()
        info.SetName("WikiArchitect")
        info.SetVersion("0.1.3-Alpha")
        info.SetDescription("A local-first, LLM-driven Knowledge Base Architect.\nMaintain your wiki with the help of an AI Librarian Assistant.")
        info.SetCopyright("Copyright © 2026 Mohammed Maniruzzaman, PhD")
        info.SetWebSite("https://github.com/manir/wikiArchitech")
        info.SetLicence("MIT License")
        info.AddDeveloper("Mohammed Maniruzzaman, PhD")
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

    def load_file(self, path):
        """Helper to load a file into the editor, used by sidebar and links."""
        if os.path.isfile(path):
            self.current_file = path
            with open(path, 'r') as f:
                content = f.read()
                self.editor.SetText(content)
                self.editor.EmptyUndoBuffer()
            self.SetStatusText(f"Editing: {os.path.basename(path)}")
            # Refresh preview if active
            selection = self.notebook.GetSelection()
            if selection != wx.NOT_FOUND and self.notebook.GetPageText(selection) == "Preview":
                self._update_preview()

    def on_file_activated(self, event):
        """Loads a file into the editor from the sidebar."""
        path = self.dir_ctrl.GetPath()
        self.load_file(path)

    def on_preview_navigating(self, event):
        """Intercepts internal wikilinks and graph node clicks with robust matching."""
        url = event.GetURL()
        if url.startswith("wikilink:"):
            raw_page_name = url.split(":", 1)[1]
            page_name = urllib.parse.unquote(raw_page_name)
            
            # Determine search directories: Current file's owner dir, then Wiki root
            search_dirs = []
            if self.current_file:
                search_dirs.append(os.path.dirname(self.current_file))
            
            base_dir = self.agent.base_dir if hasattr(self.agent, 'base_dir') else os.getcwd()
            if base_dir not in search_dirs:
                search_dirs.append(base_dir)
            
            # Robust mapping variations
            variations = [
                f"{page_name}.md",
                f"{page_name.replace(' ', '_')}.md",
                f"{page_name.replace('-', '_')}.md",
                f"{page_name.replace('_', ' ')}.md",
                f"{page_name}.txt"
            ]
            
            found = False
            for d in search_dirs:
                for v in variations:
                    target_path = os.path.join(d, v)
                    if os.path.exists(target_path):
                        self.load_file(target_path)
                        self.notebook.SetSelection(0) # Back to Editor for clarity
                        found = True
                        break
                if found: break
            
            if not found:
                wx.MessageBox(f"File not found: {page_name} (Tried: {', '.join(variations)})", "Navigation Error", wx.OK | wx.ICON_ERROR)
            
            event.Veto() # Don't actually navigate the WebView

    def on_ingest(self, event):
        """Allows user to select a source for ingestion."""
        dlg = wx.FileDialog(self, "Select Source File", wildcard="PDF files (*.pdf)|*.pdf|Text files (*.txt)|*.txt", style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.chat_log.AppendText(f"\nLibrarian: Ingesting {os.path.basename(path)}...\n")
            threading.Thread(target=self._run_agent_ingest, args=(path,), daemon=True).start()
        dlg.Destroy()

    def _run_agent_ingest(self, path):
        """Extracts text and calls Agent Ingest in a thread."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Lazy-load to avoid main thread cost
        from src.core.pdf_extractor import PDFExtractor
        if path.endswith('.pdf'):
            content = PDFExtractor.extract_text(path)
        else:
            with open(path, 'r') as f:
                content = f.read()
        
        # Agent Ingest Call
        response = loop.run_until_complete(self.agent.propose_ingest(content, os.path.basename(path)))
        loop.close()
        wx.CallAfter(self._handle_agent_response, response)
    def on_tab_changed(self, event):
        """Automatically updates the Preview or Knowledge Graph tab when selected."""
        selection = event.GetSelection()
        if selection == wx.NOT_FOUND:
            return
            
        page_text = self.notebook.GetPageText(selection)
        if page_text == "Preview":
            self._update_preview()
        elif page_text == "Knowledge Graph":
            self._update_graph()
        event.Skip()

    def _update_graph(self):
        """Generates and loads the interactive Knowledge Graph with zoom awareness."""
        base_dir = self.agent.base_dir if hasattr(self.agent, 'base_dir') else os.getcwd()
        generator = GraphGenerator(base_dir, zoom_level=self.zoom_level)
        html = generator.generate_graph_html()
        self.graph_view.SetPage(html, "")

    def _update_preview(self):
        """Renders current content as professional HTML with WikiLinks support."""
        content = self.editor.GetText()
        
        # 1. Basic Content Conversion
        html_content = markdown2.markdown(content, extras=["fenced-code-blocks", "tables", "strike", "task_list"])
        
        # 2. [[WikiLink]] Support
        html_content = re.sub(r'\[\[([^\]|]+)(?:\|([^\]]+))?\]\]', 
                             lambda m: f'<a href="wikilink:{m.group(1)}">{m.group(2) if m.group(2) else m.group(1)}</a>', 
                             html_content)
        
        # 3. Dynamic CSS Injection
        is_dark = self.theme_mode == "dark"
        bg = "#1e1e1e" if is_dark else "#ffffff"
        text = "#e0e0e0" if is_dark else "#2c3e50"
        accent = ACCENT_COLOUR.GetAsString(wx.C2S_HTML_SYNTAX)
        code_bg = "#2d2d2d" if is_dark else "#f4f4f4"
        font_size = int(self.base_font_size * self.zoom_level)

        full_html = f"""
        <html>
        <head>
            <style>
                body {{ 
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                    line-height: 1.6; padding: 20px; background-color: {bg}; color: {text}; font-size: {font_size}px;
                    max-width: 100%; word-wrap: break-word; overflow-wrap: break-word;
                }}
                h1, h2, h3 {{ color: {accent}; margin-top: 24px; }}
                a {{ color: {accent}; text-decoration: none; font-weight: 500; }}
                code {{ background: {code_bg}; padding: 2px 4px; border-radius: 4px; font-family: monospace; }}
                pre {{ background: {code_bg}; padding: 15px; border-radius: 8px; overflow-x: auto; white-space: pre-wrap; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #444; padding: 10px; text-align: left; }}
            </style>
        </head>
        <body>{html_content}</body>
        </html>
        """
        self.preview.SetPage(full_html, "")

    def on_chat_send(self, event):
        """Sends user query to the agent thread."""
        query = self.chat_input.GetValue()
        if query.strip():
            self.chat_log.AppendText(f"\nArchitect: {query}\n")
            self.chat_input.ChangeValue("")
            self.chat_log.AppendText("Librarian: Consulting knowledge base...\n")
            threading.Thread(target=self._run_agent_query, args=(query,), daemon=True).start()

    def _run_agent_query(self, query):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        response = loop.run_until_complete(self.agent.propose_query(query))
        loop.close()
        wx.CallAfter(self._handle_agent_response, response)

    def _handle_agent_response(self, response):
        self.chat_log.AppendText(f"Librarian: {response.main_response or 'Analysis complete.'}\n")
        if response.file_changes:
            self.chat_log.AppendText(f"Librarian: Proposed {len(response.file_changes)} changes. Opening review dialog...\n")
            dlg = DiffViewerDialog(self, response.file_changes)
            if dlg.ShowModal() == wx.ID_OK:
                selected = dlg.get_selected_proposals()
                self._apply_file_changes(selected)
                self.chat_log.AppendText(f"Librarian: Successfully applied changes.\n")
            dlg.Destroy()

    def apply_theme(self, mode=None):
        if mode: self.theme_mode = mode
        is_dark = self.theme_mode == "dark"
        bg = DARK_BG if is_dark else LIGHT_BG
        s_bg = SIDEBAR_BG if is_dark else LIGHT_SIDEBAR
        fg = TEXT_COLOUR if is_dark else LIGHT_TEXT
        
        self.SetBackgroundColour(bg)
        self.sidebar.SetBackgroundColour(s_bg)
        self.chat_panel.SetBackgroundColour(s_bg)
        
        tree = self.dir_ctrl.GetTreeCtrl()
        tree.SetBackgroundColour(s_bg)
        tree.SetForegroundColour(fg)
        
        self.chat_log.SetBackgroundColour(bg)
        self.chat_log.SetForegroundColour(fg)
        self.chat_input.SetBackgroundColour(bg)
        self.chat_input.SetForegroundColour(fg)
        
        self._setup_editor_stc()
        self.Refresh()
        self._mgr.Update()

    def on_toggle_theme(self, event):
        new_mode = "light" if self.theme_mode == "dark" else "dark"
        self.apply_theme(new_mode)
        self.SetStatusText(f"Theme switched to {new_mode.capitalize()} mode")

    def on_zoom_in(self, event):
        self.zoom_level += 0.1
        if self.zoom_level > 3.0: self.zoom_level = 3.0
        self._update_zoom()

    def on_zoom_out(self, event):
        self.zoom_level -= 0.1
        if self.zoom_level < 0.5: self.zoom_level = 0.5
        self._update_zoom()

    def on_zoom_reset(self, event):
        self.zoom_level = 1.0
        self._update_zoom()

    def _update_zoom(self):
        zoom_points = int((self.zoom_level - 1.0) * 10)
        self.editor.SetZoom(zoom_points)
        
        selection = self.notebook.GetSelection()
        if selection != wx.NOT_FOUND:
            page_text = self.notebook.GetPageText(selection)
            if page_text == "Preview": self._update_preview()
            elif page_text == "Knowledge Graph": self._update_graph()
        
        new_font_size = int(self.base_font_size * self.zoom_level)
        new_font = wx.Font(new_font_size, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.dir_ctrl.GetTreeCtrl().SetFont(new_font)
        self.chat_log.SetFont(new_font)
        self.chat_input.SetFont(new_font)
        
        self.SetStatusText(f"Zoom Level: {int(self.zoom_level * 100)}%")
        self.Layout()
        self.Refresh()

    def _apply_file_changes(self, changes: List[FileChange]):
        for change in changes:
            full_path = os.path.join(self.agent.base_dir, change.file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w') as f:
                f.write(change.new_content)
        self.agent = WikiArchitectAgent()
        self.graph_gen = GraphGenerator(self.agent.base_dir)
        self.architect = AutonomousArchitect(self.agent)
        
        self.setup_ui()
        self.setup_menu()
        
        # Start background indexing
        threading.Thread(target=self._run_indexing_task, daemon=True).start()

    def setup_menu(self):
        menubar = wx.MenuBar()
        
        # File Menu
        file_menu = wx.Menu()
        exit_item = file_menu.Append(wx.ID_EXIT, "E&xit", "Terminate the application")
        self.Bind(wx.EVT_MENU, self.on_exit, exit_item)
        menubar.Append(file_menu, "&File")
        
        # Librarian Menu (Autonomous Architecture)
        lib_menu = wx.Menu()
        moc_item = lib_menu.Append(wx.ID_ANY, "Generate &MOC", "Update the Map of Content")
        audit_item = lib_menu.Append(wx.ID_ANY, "Run Vault &Audit", "Check for broken links and orphans")
        brief_item = lib_menu.Append(wx.ID_ANY, "Weekly &Briefing", "Synthesize recent changes into a report")
        
        self.Bind(wx.EVT_MENU, self.on_generate_moc, moc_item)
        self.Bind(wx.EVT_MENU, self.on_run_audit, audit_item)
        self.Bind(wx.EVT_MENU, self.on_weekly_briefing, brief_item)
        menubar.Append(lib_menu, "&Librarian")
        
        self.SetMenuBar(menubar)

    def on_generate_moc(self, event):
        self.status_bar.SetStatusText("Librarian: Generating Map of Content...")
        threading.Thread(target=self._run_architect_task, args=("moc",), daemon=True).start()

    def on_run_audit(self, event):
        self.status_bar.SetStatusText("Librarian: Auditing Vault Structure...")
        threading.Thread(target=self._run_architect_task, args=("audit",), daemon=True).start()

    def on_weekly_briefing(self, event):
        self.status_bar.SetStatusText("Librarian: Synthesizing Weekly Briefing...")
        threading.Thread(target=self._run_architect_task, args=("briefing",), daemon=True).start()

    def _run_architect_task(self, task_type):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            if task_type == "moc":
                loop.run_until_complete(self.architect.generate_moc())
                wx.CallAfter(self.status_bar.SetStatusText, "Librarian: MOC.md updated successfully.")
            elif task_type == "audit":
                loop.run_until_complete(self.architect.audit_vault())
                wx.CallAfter(self.status_bar.SetStatusText, "Librarian: Structural Audit complete (AUDIT.md).")
            elif task_type == "briefing":
                loop.run_until_complete(self.architect.generate_weekly_briefing())
                wx.CallAfter(self.status_bar.SetStatusText, "Librarian: Weekly Briefing generated successfully.")
            
            # Refresh directory control to show new files
            wx.CallAfter(self.dir_ctrl.Rehash)
        except Exception as e:
            wx.CallAfter(self.status_bar.SetStatusText, f"Librarian Error: {str(e)}")
        finally:
            loop.close()

    def _run_indexing_task(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            vault_path = self.agent.base_dir
            for root, _, files in os.walk(vault_path):
                # Filter out system hidden folders
                if ".wiki" in root or ".git" in root or "__pycache__" in root:
                    continue
                    
                for file in files:
                    if file.endswith(".md"):
                        rel_path = os.path.relpath(os.path.join(root, file), vault_path)
                        wx.CallAfter(self.status_bar.SetStatusText, f"Indexing: {rel_path}")
                        with open(os.path.join(root, file), 'r') as f:
                            content = f.read()
                            loop.run_until_complete(self.agent.semantic_engine.index_note(rel_path, content))
            
            wx.CallAfter(self.status_bar.SetStatusText, "Vault Semantic Index: Synchronized")
        except Exception as e:
            error_msg = str(e)
            if "Connection" in error_msg or "Remote" in error_msg:
                error_msg = "Ollama connection failed. Is it running?"
            wx.CallAfter(self.status_bar.SetStatusText, f"Indexing Error: {error_msg}")
            
            # Persistent Debug Log in the Vault
            try:
                log_path = os.path.join(self.agent.base_dir, ".wiki", "indexing.log")
                with open(log_path, "a") as f:
                    f.write(f"[{datetime.now()}] ERROR: {str(e)}\n")
                    import traceback
            except Exception as e:
                logging.error(f"Failed to log error to indexing.log: {str(e)}")
                pass
        finally:
            loop.close()
