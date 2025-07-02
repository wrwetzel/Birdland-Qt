#!/usr/bin/python
# ------------------------------------------------------------------------------
#   bl_main_tabbar.py
#   WRW 19-Mar-2025 - Refactored from bl_main_window.py
# ------------------------------------------------------------------------------

from collections import namedtuple
from pathlib import Path

from PySide6.QtCore import Slot, QSize, QSettings, Qt
from PySide6.QtGui import QFontMetrics
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget, QApplication
from PySide6.QtWidgets import QTabWidget, QTabBar
from PySide6.QtWidgets import QSizePolicy
from PySide6.QtWidgets import QPlainTextEdit           

from PDF_Viewer import Viewer_Tab                                    
from PDF_Browser import PDF_Browser
from fb_setlist import SetListTab

from bl_tables import MusicTable
from bl_tables import MusicFilesTable
from bl_tables import AudioTable
from bl_tables import MidiTable
from bl_tables import ChordProTable
from bl_tables import JJazzLabTable
from bl_tables import YouTubeTable
from bl_tables import ReportsTable

from bl_canon2file_tab import Canon2FileTab
from bl_index_management_tab import IndexManagementTab

from Store import Store
from bl_constants import MT

# ------------------------------------------------------------------------------

#   NOTE: When adding/deleting/changing titles of tabs be sure to delete tab order item in settings.

tabList = [         # Determines order of tabs in tab bar, /// RESUME, probably a little more needed for this to work.
    MT.SetList,
    MT.Browser,
    MT.Viewer,
    MT.Index,
    MT.Files,
    MT.Audio,
    MT.Midi,
    MT.Chord,
    MT.JJazz,
    MT.YouTube,
    MT.Reports,
    MT.Edit,
    MT.IMgmt,
    MT.Results,
]

tabLabels = {                         
    MT.SetList :    "Set List",
    MT.Browser:     "Cover Browser",
    MT.Viewer :     "Music Viewer",
    MT.Index :      "Music Index",
    MT.Files :      "Music Files",
    MT.Audio :      "Audio",
    MT.Midi :       "MIDI",
    MT.Chord :      "ChordPro",
    MT.JJazz :      "JJazzLab",
    MT.YouTube :    "YouTube",
    MT.Reports :    "Reports",
    MT.Edit :       "Edit Canonical->File",
    MT.IMgmt :      "Index Management",
    MT.Results :    "Command Output",
}

# ------------------------------------------------------------------------------
#   WRW 21-Mar-2025 - Another attempt at getting tabs to expand horizontally

class MyTabBar(QTabBar):
    def __init__(self, parent=None):
        super().__init__(parent)

    def tabSizeHint(self, index ):
        text = self.tabText(index)
        font = self.font()  # or use self.tabButton(index, QTabBar.LeftSide).font() if customized
        metrics = QFontMetrics(font)

        text_width = metrics.horizontalAdvance(text)
        padding = 20  # Add some buffer for padding/margins

        # count = self.count() if self.count() > 0 else 1
        # total_width = self.width()
        # tab_width = total_width // count
        tab_height = super().tabSizeHint(index).height()

        # print( "width", total_width, "count", count )
        # print( "width", tab_width, "height", tab_height )
        return QSize(text_width + padding, tab_height)

# ------------------------------------------------------------------------------

class BL_Main_TabBar( QWidget ):

    def __init__( self ):
        super().__init__()
        s = Store()

        # ===================================================================
        #   Tabs on main TabBar

        self.layout = QHBoxLayout()
        self.setLayout( self.layout )       # Oops! I missed this, nothing showed. Thanks Chat.
        self.layout.setContentsMargins( 0, 0, 6, 0 )
        self.layout.setSpacing( 0 )

        self.mainTabBar = QTabWidget()

        # ----------------------------------

        self.mainTabBar.tabBar().setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred )

        #   WRW 3-May-2025 - Porting to MacOS - changed setExpanding() to False
        #       Trying to get tabs left aligned. Nothing working.

        # self.mainTabBar.tabBar().setMovable(True)
        self.mainTabBar.tabBar().setExpanding(False)     # This does not appear to work for all tabs, just the first?
        self.mainTabBar.setLayoutDirection(Qt.LeftToRight) #   WRW 3-May-2025 - Porting to MacOS - tryint to align left.

        self.layout.addWidget( self.mainTabBar )        # Add the tabbar to the local layout.

        s.sigman.register_slot( f"slot_addto_results",  self.slot_addto_results )
        s.sigman.register_slot( f"slot_clear_results",  self.slot_clear_results )

        s.sigman.register_slot( f"slot_select_tab",             self.slot_select_tab )
        s.sigman.register_slot( f"slot_set_tab_visibility",     self.slot_set_tab_visibility )
        s.sigman.register_slot( f"slot_toggle_tab_visibility",  self.slot_toggle_tab_visibility )

    #   WRW 3-June-2025 - no longer support reordering.
    #   s.sigman.register_slot( "slot_restore_tab_order",       self.restoreTabOrder ),
    #   s.sigman.register_slot( "slot_save_tab_order",          self.saveTabOrder ),

        # - - - - - - - - - - - - - - - - - - - - - - - -
        # Add tabs to tab widget

        self.tabWidgets = {}    # maps tabId to tab widget for getting tabWidget without use of objectName

        for tabId in tabList:              
            tabWidget = QWidget()
          # tabWidget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred )    # /// Testing, NG
            self.tabWidgets[ tabId ] = tabWidget
            self.mainTabBar.addTab(tabWidget, tabLabels[ tabId ] )

        # - - - - - - - - - - - - - - - - - - - - - - - -
        #   Adjust visibility of a few tabs

        self.mainTabBar.tabBar().setTabVisible(MT.IMgmt,   False)         # A couple of tabs are default not visible.
        self.mainTabBar.tabBar().setTabVisible(MT.Reports, False)
        self.mainTabBar.tabBar().setTabVisible(MT.Results, False)

        # ===================================================================
        #   *** SetList Tab ***

        tab = self.getTabWidgetFromId( MT.SetList )
        tab.setSizePolicy( QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        setlist_tab = SetListTab()
        setlist_tab.setObjectName( 'setlist-tab' )      # OK - for styling
        layout = QVBoxLayout()
        layout.addWidget( setlist_tab )
        tab.setLayout( layout)

        # ===================================================================
        #   *** PDF Browser Tab *** -
        #   WRW 25-May-2025

        tab = self.getTabWidgetFromId( MT.Browser )
        tab.setSizePolicy( QSizePolicy.Expanding, QSizePolicy.Expanding)

        browser_tab = PDF_Browser()
        layout = QVBoxLayout()
        layout.addWidget( browser_tab )
        tab.setLayout( layout )

        # ===================================================================
        #   *** PDF Viewer Tab *** -
        #   Includes metadata panel, viewer buttons and slider, viewer page.

        tab = self.getTabWidgetFromId( MT.Viewer )
        tab.setSizePolicy( QSizePolicy.Expanding, QSizePolicy.Expanding)

        viewer_tab = Viewer_Tab()
        layout = QVBoxLayout()
        layout.addWidget( viewer_tab )
        tab.setLayout( layout )

        # ===================================================================
        #   *** Loop for Multiple Tabs ***
        #   MusicTable, AudioTable, MusicFilesTable, MidiTable,
        #   ChordProTable, JJazzLabTable, YouTubeTable

        #   WRW 4-Feb-2025 - Convert to table driven table generation
        #   WRW 14-Feb-2025 - Convert further to updates with signals, remove object names.

        Table = namedtuple('Table', ['tabID', 'tableObject' ] )

        Tables = [     
        #   Table( MT.SetList,  SetListTable,       ),
            Table( MT.Index,    MusicTable,         ),
            Table( MT.Files,    MusicFilesTable,    ),
            Table( MT.Audio,    AudioTable,         ),
            Table( MT.Midi,     MidiTable,          ),
            Table( MT.Chord,    ChordProTable,      ),
            Table( MT.JJazz,    JJazzLabTable,      ),
            Table( MT.YouTube,  YouTubeTable,       ),
            Table( MT.Reports,  ReportsTable,       ),
        ]

        for table in Tables:
            tab = self.getTabWidgetFromId( table.tabID )
            tab.setSizePolicy( QSizePolicy.Expanding, QSizePolicy.Expanding)

            if not tab:
                print( f"[ERROR] tab name {table.tabID} not found" )
                continue

            tab.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            layout = QVBoxLayout()
            layout.setContentsMargins( 0, 0, 0, 0 )
            layout.setSpacing( 0 )
            tableObject = table.tableObject()                   # *** Instantiate table here
            layout.addWidget( tableObject )
            tab.setLayout( layout )

        # ===================================================================
        #   *** Canonical to File Tab ***

        tab = self.getTabWidgetFromId( MT.Edit )
        tab.setSizePolicy( QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout()
        self.canon2File = Canon2FileTab()
        self.canon2File.setObjectName( 'canon2file-tab' )   # OK
        layout.addWidget( self.canon2File )
        tab.setLayout(layout)

        # ===================================================================
        #   *** Index Management Tab *** Placeholder for now.

        tab = self.getTabWidgetFromId( MT.IMgmt )
        tab.setSizePolicy( QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout()
        self.indexManagement = IndexManagementTab()
        layout.addWidget( self.indexManagement )
        tab.setLayout(layout)

        # ===================================================================
        #   *** Results Tab ***

        tab = self.getTabWidgetFromId( MT.Results )
        tab.setSizePolicy( QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout()
        layout.setContentsMargins( 8, 8, 8, 8 )
        self.resultsText = QPlainTextEdit()
        self.resultsText.setReadOnly(True)
        self.resultsText.setObjectName( 'resultsText' )     # OK - for styling
        layout.addWidget( self.resultsText )
        tab.setLayout(layout)

    # ------------------------------------------------------------------------------
    #   WRW 2-June-2025 - special case for Viewer, which could be in popup window,
    #       so-called 'fullscreen' mode. I don't like special-case, exception processing,
    #       but in this situation it appears appropriate if we generalize the semantics
    #       of selectTab to show the content whether in a tab or popup.     

    def slot_select_tab( self, tabId ):
        s = Store()
        tab = self.getTabWidgetFromId( tabId )
        self.mainTabBar.setCurrentWidget(tab)
        if tabId == MT.Viewer:                  
            s.sigman.emit( "sig_fullscreen_button_clicked" )    # WRW 2-June-2025

    def slot_set_tab_visibility( self, tabId, visibility ):
        tab = self.getTabWidgetFromId( tabId )
        index = self.mainTabBar.indexOf( tab )
        self.mainTabBar.tabBar().setTabVisible(index, visibility)

    def slot_toggle_tab_visibility( self, tabId ):
        tab = self.getTabWidgetFromId( tabId )
        index = self.mainTabBar.indexOf( tab )
        vis = self.mainTabBar.tabBar().isTabVisible( index )
        self.mainTabBar.tabBar().setTabVisible( index, not vis )
        self.mainTabBar.adjustSize()    # Needed to prevent scroll buttons <> appearing on tab until resize

    # ------------------------------------------------------------------------------

    def getTabWidgetFromId( self, tabId ):
        if tabId in self.tabWidgets:
            return self.tabWidgets[ tabId ]
        print( f"ERROR: tabId '{tabId}' not found in tabWidgets" )

    # ------------------------------------------------------------------------------

    def resizeEvent(self, event):
        """Recalculate column widths on window resize."""
        super().resizeEvent(event)
        # self.mainTabBar.tabBar().setExpanding(True)

    # -------------------------------------------------------------------

    @Slot( str )
    def slot_addto_results( self, line ):
        self.resultsText.insertPlainText( line )

    @Slot()
    def slot_clear_results(self):
        self.resultsText.clear()

    # -------------------------------------------------------------------
    #   WRW 3-June-2025 - I had commented out setMovable(True) ages ago,
    #   not sure why, a minor feature at best. Causing a headache every time
    #   I changed the tabbar including today when I changed Midi->Midi.
    #   Remove all consideration of it.

    @Slot()
    def OMIT_saveTabOrder(self):
        s = Store()
        settings = QSettings( str( Path( s.Const.stdConfig, s.Const.Settings_Config_File )), QSettings.IniFormat )
        tab_order = [self.mainTabBar.tabText(i) for i in range(self.mainTabBar.count())]
        settings.setValue("tabOrder", tab_order)

    # -------------------------------------------------------------------

    @Slot()
    def OMIT_restoreTabOrder(self):
        s = Store()
        settings = QSettings( str( Path( s.Const.stdConfig, s.Const.Settings_Config_File )), QSettings.IniFormat )
        saved_order = settings.value("tabOrder", [])
    
        if not saved_order:
            return  # No saved order
    
        # Map tab texts to widgets
        tab_map = {
            self.mainTabBar.tabText(i): self.mainTabBar.widget(i)
            for i in range(self.mainTabBar.count())
        }
    
        # Remove all tabs
        while self.mainTabBar.count():
            self.mainTabBar.removeTab(0)
    
        # Re-add in saved order
        for name in saved_order:
            if name in tab_map:
                self.mainTabBar.addTab(tab_map[name], name)

# ===================================================================

if __name__ == "__main__":
    from bl_unit_test import UT
    from bl_style import StyleSheet

    s = UT()

    s.app = QApplication([])
    s.window = BL_Main_TabBar()
    s.window.setStyleSheet( StyleSheet )              # OK - Unit test
    s.window.show()
    s.app.exec()

# -------------------------------------------------------------------------------------
