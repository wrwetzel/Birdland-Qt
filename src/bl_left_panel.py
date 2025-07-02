#!/usr/bin/python
# ----------------------------------------------------------------------------
#   WRW 13-Jan-2025 - Music search panel widget

#   This encompasses several internal UI elements

#    def on_item_clicked(self, index):
#        # Check if the clicked index is a directory or file
#        if self.model.isDir(index):
#            print("Clicked on a directory")
#        else:
#            print("Clicked on a file")

# ----------------------------------------------------------------------------

from collections import defaultdict
from pathlib import Path

from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
from PySide6.QtWidgets import QTextBrowser
from PySide6.QtWidgets import QTabWidget, QComboBox, QFileSystemModel, QTreeView

# from MyGroupBox import MyGroupBox

from Store import Store
from fb_config import Config

from bl_constants import MT       # Only used in the file, no need to have in constants.
from bl_constants import LT                                                             
from SignalManager import SigMan
from bl_tables import AudioOfTitle, MidiOfTitle, TableOfContents

# ----------------------------------------------------------------------------

TabList = [
    { 'section' : 1,
      'id' : LT.Browse_Music,
      'title' : "Music",
      'pos' : 0,
    },
    { 'section' : 1,
      'id' : LT.Browse_Audio,
      'title' : "Audio",
      'pos' : 1,
    },

    { 'section' : 1,
      'id' : LT.Browse_Midi,
      'title' : "MIDI",
      'pos' : 2,
    },

    { 'section' : 1,
      'id' : LT.Browse_Chord,
      'title' : "ChordPro",
      'pos' : 3,
    },

    { 'section' : 1,
      'id' : LT.Browse_JJazz,
      'title' : "JJazzLab",
      'pos' : 4,
    },

    { 'section' : 2,
      'id' : LT.TOC,
      'title' : "Table of\nContents",
      'pos' : 0,
    },

    { 'section' : 2,
      'id' : LT.Audio_of_Title,
      'title' : "Audio of\nTitle",
      'pos' : 1,
    },

    { 'section' : 2,
      'id' : LT.Midi_of_Title,
      'title' : "Midi of\nTitle",
      'pos' : 2,
    },

    { 'section' : 2,
      'id' : LT.File_Info,
      'title' : "Media\nInfo",
      'pos' : 3,
    },
]

# ----------------------------------------------------------------------------

def OMIT_nested_dict(n, type):
    if n == 1:
        return defaultdict(type)
    else:
        return defaultdict(lambda: nested_dict(n-1, type))

# ----------------------------------------------------------------------------

class BL_Left_Panel(QWidget):
    # -------------------------------------------------
    #   Signals emited by BL_Left_Panel class

    sig_music_browser_clicked =     Signal( str )
    sig_audio_browser_clicked =     Signal( str )
    sig_midi_browser_clicked =      Signal( str )
    sig_chordpro_browser_clicked =  Signal( str )
    sig_jjazz_browser_clicked =     Signal( str )

    # -------------------------------------------------

    def __init__(self, parent=None ):
        super().__init__( parent )
        s = Store()

        # -----------------------------------------------------------------------

        s.sigman.register_signal( "sig_music_browser_clicked", self.sig_music_browser_clicked )
        s.sigman.register_signal( "sig_audio_browser_clicked", self.sig_audio_browser_clicked )
        s.sigman.register_signal( "sig_midi_browser_clicked", self.sig_midi_browser_clicked )
        s.sigman.register_signal( "sig_chordpro_browser_clicked", self.sig_chordpro_browser_clicked )
        s.sigman.register_signal( "sig_jjazz_browser_clicked", self.sig_jjazz_browser_clicked )

        s.sigman.register_slot( "slot_show_file_info", self.show_file_info )
        s.sigman.register_slot( "slot_update_browsers_root", self.slot_update_browsers_root )  # WRW 31-May-2025

        # -----------------------------------------------------------------------
        #   WRW 5-Apr-2025 - Tried QToolBox to support more tabs than room on one line.
        #   Did not like QToolBox, change to tab, i.e. tab of tabs.
        #   Some indication online that one tab row could wrap but I could find nothing
        #   in Pyside6 docs so go to two rows of tabs.

        self.sectionTabBar = QTabWidget()                   # 1st row tabbar
        self.sectionTabBar.setObjectName( 'topTabBar' )

        super_layout = QVBoxLayout(self)        # Extra layout needed for proper sizing when added extra row of tabs.
        super_layout.addWidget( self.sectionTabBar )
        super_layout.setContentsMargins(0, 0, 0, 0)

        # -----------------------------------------------------------------------
        #   All this thrashing about to get a little space between the two rows of tabs.

        layout = QVBoxLayout()
        layout.setContentsMargins( 0, 0, 0, 0 )

        layout.addSpacing(4)                #   Add space here
        s1_tabWidget = QWidget()            #   To hold 2nd row tabbar under left first row tab (section 1)
        layout.addWidget( s1_tabWidget )
        self.wrapper_t0 = QWidget()                 # Need widget, not layout, for addTab()
        self.wrapper_t0.setLayout(layout)
        self.sectionTabBar.addTab( self.wrapper_t0, 'Media Browsers' )

        layout = QVBoxLayout()
        layout.setContentsMargins( 0, 0, 0, 0 )

        layout.addSpacing(8)                #   Add space here
        s2_tabWidget = QWidget()            #   To hold 2nd row tabbar under right first row tab (section 2)
        layout.addWidget( s2_tabWidget )
        self.wrapper_t1 = QWidget()                 # Need widget, not layout, for addTab()
        self.wrapper_t1.setLayout(layout)
        self.sectionTabBar.addTab( self.wrapper_t1, 'TOC / Media Data' )

        # -----------------------------------------------------------------------
        #   Tabs
        # -----------------------------------------------------------------------
        #   Maps tabId to tab widget for getting tabWidget without use of objectName

        self.tabWidgets = {}
        self.tabTexts = {}

        # -------------------------------------------------
        #   Build tabs

        s1_layout = QVBoxLayout()
        self.s1_leftTabBar = QTabWidget()                   # 2nd row tab bar under left 1st row tab
        self.s1_leftTabBar.setObjectName( 'leftTabBar' )

        s2_layout = QVBoxLayout()
        self.s2_leftTabBar = QTabWidget()                   # 2nd row tab bar under right 1st row tab
        self.s2_leftTabBar.setObjectName( 'rightTabBar' )   

        for item in TabList:
            tabWidget = QWidget()

            self.tabWidgets[ item[ 'id' ]] = tabWidget

            if item[ 'section' ] == 1:
                self.s1_leftTabBar.addTab(tabWidget, item[ 'title'] )
                self.tabTexts[ item[ 'id' ] ] = ( self.s1_leftTabBar, item[ 'pos' ] )

            elif item[ 'section' ] == 2:
                self.s2_leftTabBar.addTab(tabWidget, item[ 'title'] )
                self.tabTexts[ item[ 'id' ] ] = ( self.s2_leftTabBar, item[ 'pos' ] )

        s1_layout.addWidget(self.s1_leftTabBar)
        s1_layout.setContentsMargins( 0, 0, 0, 0 )
        s1_layout.setSpacing( 0 )
        s1_tabWidget.setLayout( s1_layout )

        s2_layout.addWidget(self.s2_leftTabBar)
        s2_layout.setContentsMargins( 0, 0, 0, 0 )
        s2_layout.setSpacing( 0 )
        s2_tabWidget.setLayout( s2_layout )

        # =======================================================================

        if False:
            # --------------------------------------------------
            #   Src for offsets ComboBox

            # layout.addSpacerItem(QSpacerItem(0, 10))
            layout.addWidget( QLabel( "Select src for offsets for selected music file:" ))

            self.src_offset = QComboBox()
            self.src_offset.setObjectName("srcOffset")
            self.src_offset.setCurrentIndex(-1)  # No selection initially
            # self.src_offset.currentIndexChanged.connect(self.update_label)
            layout.addWidget( self.src_offset )

        # =======================================================================
        #   Tab - Music File Browser

        tab = self.getTabWidgetFromId( LT.Browse_Music )

        layout = QVBoxLayout()
        self.music_file_model = QFileSystemModel()
        self.music_file_browser = QTreeView()               # Set up the tree view
        self.music_file_browser.setObjectName( "musicBrowser")
        self.music_file_browser.setModel(self.music_file_model)

        for column in range(1, self.music_file_model.columnCount()):        # Hide all but first column
            self.music_file_browser.setColumnHidden(column, True)

        self.music_file_browser.clicked.connect( self.on_music_browser_clicked )
        
        layout.addWidget( self.music_file_browser )     # Add the tree view to the tab layout
        tab.setLayout(layout)               # and add the tab layout to the tab.

        # =======================================================================
        #   Tab - Audio File Browser

        tab = self.getTabWidgetFromId( LT.Browse_Audio  )

        layout = QVBoxLayout()
        self.audio_file_model = QFileSystemModel()
        self.audio_file_browser = QTreeView()           # Set up the tree view
        self.audio_file_browser.setObjectName("audioBrowser")
        self.audio_file_browser.setModel(self.audio_file_model)

        for column in range(1, self.audio_file_model.columnCount()):
            self.audio_file_browser.setColumnHidden(column, True)

        self.audio_file_browser.clicked.connect( self.on_audio_browser_clicked )
        
        layout.addWidget( self.audio_file_browser )     # Add the tree view to the tab layout
        tab.setLayout(layout)                           # and add the tab layout to the tab.

        # =======================================================================
        #   Tab - Midi File Browser

        tab = self.getTabWidgetFromId( LT.Browse_Midi )

        layout = QVBoxLayout()
        self.midi_file_model = QFileSystemModel()
        self.midi_file_browser = QTreeView()           # Set up the tree view
        self.midi_file_browser.setObjectName("midiBrowser")
        self.midi_file_browser.setModel(self.midi_file_model )

        for column in range(1, self.midi_file_model.columnCount()):
            self.midi_file_browser.setColumnHidden(column, True)

        self.midi_file_browser.clicked.connect( self.on_midi_browser_clicked )
        
        layout.addWidget( self.midi_file_browser )     # Add the tree view to the tab layout
        tab.setLayout(layout)                           # and add the tab layout to the tab.

        # =======================================================================
        #   Tab - Chordpro File Browser

        tab = self.getTabWidgetFromId( LT.Browse_Chord )

        layout = QVBoxLayout()
        self.chordpro_file_model = QFileSystemModel()
        self.chordpro_file_browser = QTreeView()           # Set up the tree view
        self.chordpro_file_browser.setObjectName("chordproBrowser")
        self.chordpro_file_browser.setModel(self.chordpro_file_model )

        for column in range(1, self.chordpro_file_model.columnCount()):
            self.chordpro_file_browser.setColumnHidden(column, True)

        self.chordpro_file_browser.clicked.connect( self.on_chordpro_browser_clicked )
        
        layout.addWidget( self.chordpro_file_browser )     # Add the tree view to the tab layout
        tab.setLayout(layout)                           # and add the tab layout to the tab.

        # =======================================================================
        #   Tab - JJazzLab File Browser

        tab = self.getTabWidgetFromId( LT.Browse_JJazz )

        layout = QVBoxLayout()
        self.jjazz_file_model = QFileSystemModel()
        self.jjazz_file_browser = QTreeView()           # Set up the tree view
        self.jjazz_file_browser.setObjectName("jjazzBrowser")
        self.jjazz_file_browser.setModel(self.jjazz_file_model )

        for column in range(1, self.jjazz_file_model.columnCount()):
            self.jjazz_file_browser.setColumnHidden(column, True)

        self.jjazz_file_browser.clicked.connect( self.on_jjazz_browser_clicked )
        
        layout.addWidget( self.jjazz_file_browser )     # Add the tree view to the tab layout
        tab.setLayout(layout)                           # and add the tab layout to the tab.

        # =======================================================================
        #   Tab - Table of Contents

        tab = self.getTabWidgetFromId( LT.TOC )

        layout = QVBoxLayout()
        # header = [ "Title", "Sheet" ]
        # ratios = [75, 25]
        # self.toc = MyTable( header, ratios )
        self.toc = TableOfContents()
        self.toc.setObjectName("musicToc")
        layout.addWidget( self.toc )     # Add the tree view to the tab layout
        tab.setLayout(layout)               # and add the tab layout to the tab.

        # =======================================================================
        #   Tab - Audio of Title

        tab = self.getTabWidgetFromId( LT.Audio_of_Title )

        layout = QVBoxLayout()
        layout.setContentsMargins( 0, 0, 0, 0 )
        layout.setSpacing( 0 )
        self.audio_of_title_table = AudioOfTitle()                # *** Instantiate table here
        layout.addWidget( self.audio_of_title_table )

        tab.setLayout(layout)               # and add the tab layout to the tab.

        # =======================================================================
        #   Tab - Midi of Title

        tab = self.getTabWidgetFromId( LT.Midi_of_Title )

        layout = QVBoxLayout()
        layout.setContentsMargins( 0, 0, 0, 0 )
        layout.setSpacing( 0 )
        self.midi_of_title_table = MidiOfTitle()                # *** Instantiate table here
        layout.addWidget( self.midi_of_title_table )

        tab.setLayout(layout)               # and add the tab layout to the tab.

        # =======================================================================
        #   Media file information panel.

        tab = self.getTabWidgetFromId( LT.File_Info )
        layout = QVBoxLayout()
        layout.setContentsMargins( 0, 0, 0, 0 )
        layout.setSpacing( 0 )

        self.media_info = QTextBrowser( )      # /// WRW 28-Feb-2025 - Chat suggested Browser vs Edit
        self.media_info.setObjectName("musicFileInfo" )
        self.media_info.setReadOnly(True)
        layout.addWidget( self.media_info )

        tab.setLayout(layout)               # and add the tab layout to the tab.

        # =======================================================================
        #   Register slots                    

        s.sigman.register_slot( f"slot_update_meta_current_audio", self.slot_update_meta_current_audio )
        s.sigman.register_slot( f"slot_update_meta_current_midi", self.slot_update_meta_current_midi )
      # s.sigman.register_slot( f"slot_update_music_file_info", self.slot_update_music_file_info )
        s.sigman.register_slot( f"slot_update_audio_of_tab", self.slot_update_audio_of_tab )
        s.sigman.register_slot( f"slot_update_midi_of_tab", self.slot_update_midi_of_tab )

        # s.sigman.register_slot( f"slot_update_meta_toc", self.toc.update )
        # s.sigman.register_slot( f"slot_update_meta_current_midi", self.midi_of_title_table.update )

        s.sigman.register_slot( f"slot_select_left_tab", self.slot_select_left_tab )

    # ----------------------------------------------------------------------

    if False:
        TabList = [
            { 'section' : 1,
              'id' : LT.Browse_Music,
              'title' : "Music",
              'pos' : 0,
            },
        ]

    # ----------------------------------------------------------------------
    #   WRW 28-May-2025 - Select 'Audio of Title' or 'Midi of Title' tab under
    #   the 'TOC / Media Data' first row tab.

    @Slot( int )
    def slot_select_left_tab( self, tabId ):
        self.sectionTabBar.setCurrentWidget( self.wrapper_t1 )  #   Select 'TOC / Media Data' tab in first row
        tab = self.getTabWidgetFromId( tabId )                  #   Tab within second row.
        self.s2_leftTabBar.setCurrentWidget( tab )              #   Select second-row tab in section 2

    # ----------------------------------------------------------------------

    @Slot( str )
    def show_file_info( self, t ):
        s = Store()
        if t:
            self.media_info.setHtml( t )
        else:
            self.media_info.setHtml( '' )

    # ---------------------------------------------------

    @Slot()
    def on_music_browser_clicked( self, index ):                # connected to native signal
        s = Store()
        model = index.model()
        if model.isDir( index ):            # Ignore directories.
            return
        path = model.filePath(index)
        path = Path( path ).as_posix()    # WRW 11-Apr-2025 - browser on Windows returning backslashes.
        s.sigman.emit( "sig_music_browser_clicked", path )

    # -------------------------------------------------
    @Slot()
    def on_audio_browser_clicked( self, index ):                # connected to native signal
        s = Store()
        model = index.model()
        if model.isDir( index ):            # Ignore directories.
            return
        path = model.filePath(index)
        path = Path( path ).as_posix()   # WRW 11-Apr-2025 - browser on Windows returning backslashes.
        s.sigman.emit( "sig_audio_browser_clicked", path )

    # -------------------------------------------------
    @Slot()
    def on_midi_browser_clicked( self, index ):                # connected to native signal
        s = Store()
        model = index.model()
        if model.isDir( index ):            # Ignore directories.
            return

        path = Path( model.filePath(index) )
        ext = path.suffix.lower()
        ppath = Path( path ).as_posix()    # WRW 11-Apr-2025 - browser on Windows returning backslashes.
        if ext in [ '.txt', '.text' ]:                      # Some midi folders have text sidecard files worth viewing
            content = path.read_text(encoding="utf-8")      # /// RESUME This really belongs in bl_media.py but OK here.
            s.setTabVisible( MT.Results, True )
            s.selectTab( MT.Results )
            s.sigman.emit( "sig_clear_results" )
            s.sigman.emit( "sig_addto_results", content )

        else:
            s.sigman.emit( "sig_midi_browser_clicked", ppath )

    # -------------------------------------------------
    @Slot()
    def on_chordpro_browser_clicked( self, index ):                # connected to native signal
        s = Store()
        model = index.model()
        if model.isDir( index ):            # Ignore directories.
            return
        path = model.filePath(index)
        path = Path( path ).as_posix()    # WRW 11-Apr-2025 - browser on Windows returning backslashes.
        s.sigman.emit( "sig_chordpro_browser_clicked", path )

    # -------------------------------------------------
    @Slot()
    def on_jjazz_browser_clicked( self, index ):                # connected to native signal
        s = Store()
        model = index.model()
        if model.isDir( index ):            # Ignore directories.
            return
        path = model.filePath(index)
        path = Path( path ).as_posix()    # WRW 11-Apr-2025 - browser on Windows returning backslashes.
        s.sigman.emit( "sig_jjazz_browser_clicked", path )

    # -------------------------------------------------
    @Slot()
    def slot_update_meta_current_audio( self, table ):
        self.audio_of_title_table.update( table )

    # -------------------------------------------------
    @Slot()
    def slot_update_meta_current_midi( self, table ):
        self.midi_of_title_table.update( table )

    # -------------------------------------------------
    #   Paramaterize unicode chars? Add chordpro and jjazz. No, don't have chordpro or jjazz tabs.
    #       audio_avail = '\U0001F50a'  if self.current_audio else ''
    #       midi_avail  = '\U0001f39d ' if self.current_midi else  ''
    #       chordpro_avail =  'Cp '  if self.current_chordpro else  ''
    #       jjazz_avail =     'Jj '  if self.current_jjazz else  ''

    # -------------------------------------------------
    @Slot()
    def slot_update_audio_of_tab( self, table ):
        s = Store()
        bar, pos = self.tabTexts[ LT.Audio_of_Title ]
        if table:
            text = bar.tabText( pos )                                      
            text = text.replace( f' {s.Const.Marker_Space}', '' )    # Remove possible old space
            text = text.replace( f' {s.Const.Marker_Audio}', '' )                # Remove possible old char
            text += f' {s.Const.Marker_Audio}'                                   # and add new one
            bar.setTabText( pos, text )

        else:
            text = bar.tabText( pos )                                      
            text = text.replace( f' {s.Const.Marker_Audio}', f' {s.Const.Marker_Space}' )
            bar.setTabText( pos, text )

    # -------------------------------------------------
    @Slot()
    def slot_update_midi_of_tab( self, table ):
        s = Store()
        bar, pos = self.tabTexts[ LT.Midi_of_Title ]
        if table:
            text = bar.tabText( pos )                                      
            text = text.replace( f' {s.Const.Marker_Space}', '' )                # Remove possible old space
            text = text.replace( f' {s.Const.Marker_Midi}', '' )
            text += f' {s.Const.Marker_Midi}'
            bar.setTabText( pos, text )
        else:
            text = bar.tabText( pos )                                      
            text = text.replace( f' {s.Const.Marker_Midi}', f' {s.Const.Marker_Space}' )
            bar.setTabText( pos, text )

    # ----------------------------------------------------------------------
    #   WRW 31-May-2025 - Testing to see if can change browser root when
    #       it changes in configuration. Appears OK but identified a possible
    #       bug in way folders under root are processed. Maybe not,
    #       browser should show all folders, not just those listed.

    @Slot()
    def slot_update_browsers_root( self ):
        s = Store()

        self.set_music_root( s.conf.val('music_file_root') )
        self.set_audio_root( s.conf.val('audio_file_root') )
        self.set_midi_root( s.conf.val('midi_file_root') )
        self.set_chordpro_root( s.conf.val('chordpro_file_root') )
        self.set_jjazz_root( s.conf.val('jjazz_file_root') )

    # ----------------------------------------------------------------------

    def getTabWidgetFromId( self, tabId ):
        if tabId in self.tabWidgets:
            return self.tabWidgets[ tabId ]
        print( f"ERROR: tabId '{tabId}' not found in tabWidgets" )

    # ----------------------------------------------------------------------
    #   This is where the file browsers are populated

    def set_music_root( self, root ):
        self.music_file_model.setRootPath(root)  # Set to the root path of the file system
        self.music_file_browser.setRootIndex(self.music_file_model.index(root))  # Default to the root directory

    def set_audio_root( self, root ):
        self.audio_file_model.setRootPath(root)  # Set to the root path of the file system
        self.audio_file_browser.setRootIndex(self.audio_file_model.index(root))  # Default to the root directory

    def set_midi_root( self, root ):
        self.midi_file_model.setRootPath(root)  # Set to the root path of the file system
        self.midi_file_browser.setRootIndex(self.midi_file_model.index(root))  # Default to the root directory

    def set_chordpro_root( self, root ):
        self.chordpro_file_model.setRootPath(root)  # Set to the root path of the file system
        self.chordpro_file_browser.setRootIndex(self.chordpro_file_model.index(root))  # Default to the root directory

    def set_jjazz_root( self, root ):
        self.jjazz_file_model.setRootPath(root)  # Set to the root path of the file system
        self.jjazz_file_browser.setRootIndex(self.jjazz_file_model.index(root))  # Default to the root directory

    def add_toc_row(self, txt1, txt2 ):
        """Add a row with data to the table."""
        self.toc.addRow( [txt1, txt2] )

    # ----------------------------------------------------------------------

    def resizeEvent(self, event):
        """Recalculate column widths on window resize."""
        super().resizeEvent(event)
        # self.set_toc_column_widths()

    def OMIT_set_toc_column_widths(self):
        """Set column widths based on relative proportions."""
        total_width = self.toc.viewport().width()
        total_ratios = sum(self.toc_column_ratios)
        for col, ratio in enumerate(self.toc_column_ratios):
            column_width = (ratio / total_ratios) * total_width
            self.toc.setColumnWidth(col,column_width )

    #   Can't get correct viewport() size until tab changed.
    #   Might be OK now that overriding showEvent()

    def OMITon_tab_changed( self, tab ):
        if tab == 2:                    # /// Paramaterize
            # self.resizeEvent( None )
            # self.set_toc_column_widths()
            pass

# ----------------------------------------------------------------------------
#   Unit test.

if __name__ == "__main__":
    from bl_unit_test import UT
    from bl_style import StyleSheet

    s = UT()

    def toc_click( item, row, col ):
        print( f"toc_click(): {item}, {row}, {col}" )

    s.app = QApplication([])
    panel = BL_Left_Panel()
    panel.setFixedWidth(400)
    panel.setStyleSheet( StyleSheet )   # OK, unit test

    music_root = s.conf.val('music_file_root')
    panel.set_music_root( music_root )

    audio_root = s.conf.val('audio_file_root')
    panel.set_audio_root( audio_root )

    # panel.toc_cell_clicked_signal.connect( toc_click )
    panel.add_toc_row( "Title one", "3" )
    panel.add_toc_row( "Title two", "17" )

    panel.resize( 600, 600 )
    panel.show()
    s.app.exec()

# -------------------------------------------------------------------------------------
