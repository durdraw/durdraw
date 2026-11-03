# Manage tabs

import pdb

from durdraw.durdraw_ui_widgets import Menu

class TabsUI:
    def __init__(self):
        pass


class TabsManager:
    def __init__(self, appState):
        self.tabs = []
        self.appState = appState
        #self.current_tab_index = None   # int of currently selected tab
        self.current_tab = None

    #@property
    #def current_tab(self):
    #    return self.tabs[self.current_tab_index]

    def add_tab_to_list(self, tab):
        self.tabs.append(tab)

    def delete_tab_from_list(self, tab):
        if tab in self.tabs:
            self.tabs.remove(tab)

    def make_new_tab(self): 
        # If no tabs are open, make a new tab 
        # and save current state to it.
        if not self.tabs:
            first_tab = Tab(self.appState)
            first_tab.save_ui_state_to_tab()
            self.add_tab_to_list(first_tab)
        # Then make a new empty tab, 
        new_tab = Tab(self.appState)
        # make a new blank canvas, add it to the tab,
        self.appState.ui.clearCanvas(prompting=False)
        new_tab.save_ui_state_to_tab()
        self.add_tab_to_list(new_tab)
        # and switch to it.
        #self.tabs.append(tab)
        #self.current_tab_index = len(self.tabs) - 1
        self.current_tab = new_tab


    def close_current_tab(self):
        pass

    def close_tab(self, tab):
        self.delete_tab_from_list(tab)

    def render_tab(self, line, col):
        # Maybe put this in an tabs ncurses handler object?
        # Or: Use a menu object, put it on the right edge/toolbar.
        # Maybe a TabsUI class makes sense instead for this stuff. Then
        # it can make a menu, or horizontal menu, etc.
        pass

    def next_tab(self):
        if not self.tabs:
            return
        # save state
        self.current_tab.save_ui_state_to_tab()
        # next tab
        current_tab_index = self.tabs.index(self.current_tab)
        current_tab_index += 1
        if current_tab_index >= len(self.tabs):
            current_tab_index = 0
        #pdb.set_trace()
        self.current_tab = self.tabs[current_tab_index]
        self.current_tab.load_tab_state_to_ui()
        self.appState.ui.stdscr.clear()
        self.appState.ui.hardRefresh()

class Tab:
    def __init__(self, appState):
        # These are things that should be saved when switching from the tab,
        # and loaded when switching to the tab.
        self.mov = None
        self.opts = None
        self.playbackRange = None
        self.modified = None
        self.fileName = None
        self.undoState = None
        self.sauce = None
        self.colorMode = None

        # Run-time tab stuff
        self.name = None
        self.appState = appState    # Contains the UI object which we'll be interacting with

    def save_ui_state_to_tab(self):
        # Takes state from UI/appstate, saves it into tab object
        self.mov = self.appState.ui.mov
        self.opts = self.appState.ui.opts
        self.playbackRange = self.appState.playbackRange
        self.modified = self.appState.modified
        self.fileName = self.appState.curOpenFileName
        self.undoState = self.appState.ui.undo
        self.sauce = self.appState.sauce
        self.colorMode = self.appState.colorMode

    def load_tab_state_to_ui(self):
        # takes state from tab object, loads it into UI/appstate
        self.appState.ui.mov = self.mov
        self.appState.ui.opts = self.opts
        self.appState.playbackRange = self.playbackRange
        self.appState.modified = self.modified
        self.appState.curOpenFileName = self.fileName
        self.appState.ui.undo = self.undoState
        self.appState.sauce = self.sauce
        if self.appState.colorMode != self.colorMode:
            self.appState.ui.switchToColorMode(self.colorMode, tab_switching = True)


