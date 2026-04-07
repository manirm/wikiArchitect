import wx
import wx.stc
import difflib
from typing import List
# Note: In a real app, we would import FileChange from src.core.agent
# but for now we define it or assume its structure.

DARK_BG = wx.Colour(30, 30, 30)
TEXT_COLOUR = wx.Colour(204, 204, 204)
ADD_COLOUR = wx.Colour(34, 139, 34)  # Green
DEL_COLOUR = wx.Colour(178, 34, 34)   # Red

class DiffViewerDialog(wx.Dialog):
    """
    A dialog for the 'Architect' to review and approve LLM-proposed file changes.
    """

    def __init__(self, parent, proposals: List[any], title="Review Proposed Changes"):
        super(DiffViewerDialog, self).__init__(parent, title=title, size=(1000, 700))
        
        self.proposals = proposals
        self.accepted_indices = []
        
        self.SetBackgroundColour(DARK_BG)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # --- List of changes ---
        self.check_list = wx.CheckListBox(self, choices=[p.file_path for p in proposals])
        self.check_list.SetBackgroundColour(DARK_BG)
        self.check_list.SetForegroundColour(TEXT_COLOUR)
        # Check all by default
        for i in range(len(proposals)):
            self.check_list.Check(i)
            
        # --- Diff Display ---
        self.diff_display = wx.stc.StyledTextCtrl(self, style=wx.BORDER_NONE)
        self._setup_diff_stc()
        
        # --- Layout ---
        splitter = wx.BoxSizer(wx.HORIZONTAL)
        splitter.Add(self.check_list, 1, wx.EXPAND | wx.ALL, 10)
        splitter.Add(self.diff_display, 3, wx.EXPAND | wx.ALL, 10)
        
        # Buttons
        btn_sizer = wx.StdDialogButtonSizer()
        self.apply_btn = wx.Button(self, wx.ID_OK, label="Apply Selected")
        self.cancel_btn = wx.Button(self, wx.ID_CANCEL, label="Discard All")
        btn_sizer.AddButton(self.apply_btn)
        btn_sizer.AddButton(self.cancel_btn)
        btn_sizer.Realize()
        
        main_sizer.Add(wx.StaticText(self, label="Review the following changes (select to preview):"), 0, wx.ALL, 10)
        main_sizer.Add(splitter, 1, wx.EXPAND)
        main_sizer.Add(btn_sizer, 0, wx.ALIGN_RIGHT | wx.ALL, 10)
        
        self.SetSizer(main_sizer)
        
        # Bind events
        self.check_list.Bind(wx.EVT_CHECKLISTBOX, self.on_list_select)
        self.check_list.Bind(wx.EVT_LISTBOX, self.on_list_select)
        
        # Initial preview
        if proposals:
            self.show_diff(0)

    def _setup_diff_stc(self):
        self.diff_display.SetReadOnly(True)
        self.diff_display.StyleSetBackground(wx.stc.STC_STYLE_DEFAULT, DARK_BG)
        self.diff_display.StyleSetForeground(wx.stc.STC_STYLE_DEFAULT, TEXT_COLOUR)
        self.diff_display.StyleClearAll()
        
        # Diff styles
        self.diff_display.StyleSetForeground(1, ADD_COLOUR) # Added
        self.diff_display.StyleSetForeground(2, DEL_COLOUR) # Deleted
        self.diff_display.StyleSetForeground(3, wx.Colour(100, 100, 255)) # Info/Hunk

    def on_list_select(self, event):
        idx = self.check_list.GetSelection()
        if idx != wx.NOT_FOUND:
            self.show_diff(idx)

    def show_diff(self, idx):
        proposal = self.proposals[idx]
        orig = proposal.original_content or ""
        new = proposal.new_content
        
        # Generate unified diff
        diff_lines = difflib.unified_diff(
            orig.splitlines(keepends=True),
            new.splitlines(keepends=True),
            fromfile=f"a/{proposal.file_path}",
            tofile=f"b/{proposal.file_path}"
        )
        
        self.diff_display.SetReadOnly(False)
        self.diff_display.ClearAll()
        
        for line in diff_lines:
            start = self.diff_display.GetLength()
            self.diff_display.AppendText(line)
            end = self.diff_display.GetLength()
            
            # Apply styling
            if line.startswith('+') and not line.startswith('+++'):
                self.diff_display.StartStyling(start)
                self.diff_display.SetStyling(end - start, 1)
            elif line.startswith('-') and not line.startswith('---'):
                self.diff_display.StartStyling(start)
                self.diff_display.SetStyling(end - start, 2)
            elif line.startswith('@@'):
                self.diff_display.StartStyling(start)
                self.diff_display.SetStyling(end - start, 3)
                
        self.diff_display.SetReadOnly(True)

    def get_selected_proposals(self) -> List[any]:
        return [self.proposals[i] for i in range(len(self.proposals)) if self.check_list.IsChecked(i)]
