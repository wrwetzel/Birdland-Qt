#!/usr/bin/python
# ------------------------------------------------------------------------------
#   Build MainWindow - 1-Feb-2025 moved from bl-main.py
#   WRW 2-Feb-2025 - split into small functions.

# ------------------------------------------------------------------------------

import sys

from PySide6.QtCore import Slot             
from PySide6.QtGui import QAction, QIcon, QFont

from PySide6.QtWidgets import QApplication, QLabel, QVBoxLayout, QHBoxLayout, QMainWindow, QWidget
from PySide6.QtWidgets import QStatusBar, QToolBar, QStyle, QTabWidget, QSizePolicy, QToolButton

# from PySide6.QtWebEngineWidgets import QWebEngineView
# from PySide6.QtWebEngineCore import QWebEngineSettings

# from PySide6.QtPdf import QPdfDocument            # Couldn't get this to work, use mupdf instead.
# from PySide6.QtPdfWidgets import QPdfView

from bl_title_panel import Title_Panel
from bl_search_panel import BL_Search_Panel
from bl_left_panel import BL_Left_Panel
from AudioPlayer_Vlc import AudioPlayer

from MyGroupBox import MyGroupBox
from Store import Store
from fb_config import Config
from bl_main_menu import Main_Menu
from SignalManager import SigMan
from bl_main_tabbar import BL_Main_TabBar      # WRW 19-Mar-2025 - pulled out into separate file

from bl_analysis import AnalysisTab    # WRW 22-Mar-2025 - for future Scales and Chords
from bl_constants import LT 

# ------------------------------------------------------------------------------
#   Note that methods and objects defined here may be accessed via s.window because
#       s.window = Build_UI in bl_main.py. With change in architecture very few
#       if any are, however.

class Build_UI( QMainWindow ):

    def __init__(self):
        super().__init__()
        s = Store()

        # -------------------------------------------------------------------
        s.sigman.register_slot( "slot_update_status", self.update_status )   # WRW 27-May-2025
        s.sigman.register_slot( "slot_update_audio_of_statusbar", self.slot_update_audio_of_statusbar )   # WRW 27-May-2025
        s.sigman.register_slot( "slot_update_midi_of_statusbar", self.slot_update_midi_of_statusbar )   # WRW 27-May-2025

        s.sigman.register_slot( "slot_announce_do_fullscreen", self.slot_announce_do_fullscreen )        # 28-May-2025
        s.sigman.register_slot( "slot_announce_exit_fullscreen", self.slot_announce_exit_fullscreen  )      # 28-May-2025

        # -------------------------------------------------------------------

        self.setWindowTitle( s.Const.BL_Long_Title )

        # -------------------------------------------------------------------
        #   WRW 22-Mar-2025 - Prepare for future addition of scales and chords
        #   in the 'Analysis' tab by adding sidetabs to the interface.

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        central_layout = QVBoxLayout(self.central_widget)
        central_layout.setContentsMargins( 0, 0, 0, 0 )
        central_layout.setSpacing( 0 )

        self.mainTabBar = QTabWidget()
        self.mainTabBar .setTabPosition(QTabWidget.West)
        central_layout.addWidget( self.mainTabBar )        # Add the tabbar to the local layout.

        self.library = Build_Library()
        self.mainTabBar.addTab( self.library, "Library" )

        self.analysis= Build_Analysis()
        self.mainTabBar.addTab( self.analysis, "Analysis"  )

        self.mainTabBar.setCurrentWidget( self.library )

        # -------------------------------------------------------------------
        #   Main menu

        mm = Main_Menu()
        mm.setParent(self)                  # Main_Menu is a bit peculiar
        mm.setObjectName( "mainMenu" )
        mm.build_menu( self )

        # -------------------------------------------------------------------
        #   Status bar - Include QLabel here and update label, not bar, in update_status()
        #   WRW 27-May-2025 - add markers for music and midi available.
        #   And with the addition of setfixedHeight() I assert I'm done!

        self.statusBar = QStatusBar()

        match s.Const.Platform:
            case 'Linux':
                font = QFont("Noto Color Emoji" )

            case 'Windows':
                font = QFont("Segoe UI Emoji" )

            case 'MacOS':
                font = QFont("Apple Color Emoji")

            case 'Unknown':
                print( "ERROR-DEV: Unexpected value for s.Const.Platform", file=sys.stderr )
                font = QFont("Noto Color Emoji" )


        self.setStatusBar(self.statusBar)
        self.statusBarLabel = QLabel('')                    # QLabel() to get html processing
        self.statusBar.addWidget( self.statusBarLabel )
        self.statusBar.setFixedHeight(24)                   # WRW 27-May-2024 music & midi chars just a bit taller than other text

        if False:
            self.statusBar_music = QLabel( ' ' )
            self.statusBar_music.setMinimumWidth( 12 )
            self.statusBar_music.setFont(font)
            self.statusBar.addPermanentWidget( self.statusBar_music )

        else:
            self.audio_button = QToolButton( )
            self.audio_button.setText( s.Const.Button_Audio )
            self.audio_button.setFont(font)
            self.audio_button.clicked.connect( self.on_audio_button_clicked )
            self.statusBar.addPermanentWidget( self.audio_button  )

        if False:
            self.statusBar_midi = QLabel( ' ' )
            self.statusBar_midi.setMinimumWidth( 12 )
            self.statusBar_midi.setFont(font)
            self.statusBar.addPermanentWidget( self.statusBar_midi )

        else:
            self.midi_button = QToolButton(  )
            self.midi_button.setText( s.Const.Button_Midi )
            self.midi_button.setFont(font)
            self.midi_button.clicked.connect(self.on_midi_button_clicked)
            self.statusBar.addPermanentWidget( self.midi_button  )

        self.fullscreen_button = QToolButton(  )
        self.fullscreen_button.setText( s.Const.Button_Full )
        self.fullscreen_button.setFont(font)
        self.fullscreen_button.clicked.connect(self.on_fullscreen_button_clicked )
        self.statusBar.addPermanentWidget( self.fullscreen_button  )
        self.fullscreen_button.setVisible( False )

        # -------------------------------------------------------------------
        #   Toolbar - not using presently, takes up too much vertical space.
        #   Keep as example if I change my mind.

        if False:
            style = QApplication.style()

            toolbar = QToolBar("Main Toolbar", self )
            self.addToolBar(toolbar)

            new_action = QAction(QIcon(), "New", self )
            toolbar.addAction(new_action)

            open_action = QAction(style.standardIcon(QStyle.SP_DialogOpenButton), "Open", self)
            toolbar.addAction(open_action)

            toolbar.addSeparator()
            close_action = QAction(style.standardIcon(QStyle.SP_DialogCloseButton), "Close", self )
            toolbar.addAction(close_action)
            close_action.triggered.connect( lambda: sys.exit(0))

    # ------------------------------------------------------------------------------

    def resizeEvent( self, event ):
        super().resizeEvent(event)

    # ------------------------------------------------------------------------------
    #   WRW 27-May-2025

    @Slot( int )
    def on_audio_button_clicked( b ):
        s = Store()
        s.sigman.emit( 'sig_select_left_tab', LT.Audio_of_Title )

    @Slot( int )
    def on_midi_button_clicked( b ):
        s = Store()
        s.sigman.emit( 'sig_select_left_tab', LT.Midi_of_Title )

    # ----------------------------------------------------------------
    #   WRW 28-May-2025 - A reminder to user that in fullscreen mode.
    #   The zoom window may be hiding beneath the main window.

    @Slot( int )
    def on_fullscreen_button_clicked( self ):
        s = Store()
        s.sigman.emit( "sig_fullscreen_button_clicked" )

    @Slot()
    def slot_announce_do_fullscreen( self ):
        self.fullscreen_button.setVisible( True )

    @Slot()
    def slot_announce_exit_fullscreen( self ):
        self.fullscreen_button.setVisible( False )


    # ------------------------------------------------------------------------------

    #   WRW 30-Mar-2025 - want to catch user clicking close in window decoration.

    def closeEvent(self, event):
        s = Store()
        s.sigman.emit( "sig_preparing_to_exit" )
        super().closeEvent(event)

    # ------------------------------------------------------------------------------
    #   WRW 18-Feb-2025 - Resolved a bug whereby the status bar kept growing. Now
    #       add a QLabel to the bar when initially build it and just update
    #       the label here, not delete the old one and add a new one.
    #       Need a QLabel so can include bold via html in status.
    #   WRW 26-Feb-2025 - at least one midi file is a medley with a very long file name.
    #       Truncate here to 80 chars.
    #   WRW 27-May-2025 - move this from bl_actions.py into the Build_UI class.
    
    @Slot( str )
    def update_status( self, text ):
        max_status = 200
        if len(text) > max_status:
            text = text[0:max_status] + " ..."
    
        self.statusBarLabel.setText( text )

    # --------------------------------------------------------------
    if False:
        @Slot( str )
        def slot_update_audio_of_statusbar( self, table ):
            s = Store()
            if table:
                text = s.Const.Marker_Audio
            else:
                text = s.Const.Marker_Space
            self.statusBar_music.setText( text )

        @Slot( str )
        def slot_update_midi_of_statusbar( self, table ):
            s = Store()
            if table:
                text = s.Const.Marker_Midi
            else:
                text = s.Const.Marker_Space
            self.statusBar_midi.setText( text )

    # --------------------------------------------------------------
    else:
        @Slot( str )
        def slot_update_audio_of_statusbar( self, table ):
            s = Store()
            if table:
                self.audio_button.setVisible( True )
                # self.audio_button.show()
                # self.audio_button.setDisabled( False )
            else:
                self.audio_button.setVisible( False )
                # self.audio_button.hide()
                # self.audio_button.setDisabled( True )

        @Slot( str )
        def slot_update_midi_of_statusbar( self, table ):
            s = Store()
            if table:
                self.midi_button.setVisible( True )
                # self.midi_button.show()
                # self.midi_button.setDisabled( False )

            else:
                self.midi_button.setVisible( False )
                # self.midi_button.hide()
                # self.midi_button.setDisabled( True )


# ------------------------------------------------------------------------------
#   WRW 22-Mar-2025 - Was Build_UI(), move that above and made this subordinate.

class Build_Library( QWidget ):

    def __init__(self):
        super().__init__()
        s = Store()

        # -------------------------------------------------------------------

        # self.central_widget = QWidget()
        # self.setCentralWidget(self.central_widget)
        # central_layout = QVBoxLayout(self.central_widget)

        central_layout = QVBoxLayout()
        central_layout.setContentsMargins( 4, 4, 4, 4 )
        central_layout.setSpacing( 4 )
        self.setLayout( central_layout )

        # central_layout.setContentsMargins( 0, 0, 8, 0 )
        # central_layout.setSpacing( 0 )

        # -------------------------------------------------------------------

        title_panel = Title_Panel()
        central_layout.addWidget( title_panel )

        # -------------------------------------------------------------------
        #   Search panel - consists of two rows of search-related items built elsewhere

        sp = BL_Search_Panel()
        sp.setObjectName( 'search-panel' )
        central_layout.addWidget(sp)

        # -------------------------------------------------------------------
        #   Lower Panel consisting of leftPanelTabBar and mainTabBar

        lower_panel_layout = QHBoxLayout()

        # -------------------------------------------------------------------
        #   Full Left Panel - consists of Audio Player and Left Panel

        full_left_panel_layout = QVBoxLayout()
        full_left_panel_layout.setContentsMargins( 4, 0, 4, 0 )    # left top right bottom /// TESTING
        full_left_panel_layout.setSpacing( 8 )                     # /// TESTING

        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        #   Audio Player

        audio_player = AudioPlayer()

        audio_player_layout = QVBoxLayout()
        audio_player_layout.setContentsMargins( 0, 0, 0, 0 )    # left top right bottom /// TESTING
        audio_player_layout.setSpacing( 0 )                     # /// TESTING

        audio_player_layout.addWidget( audio_player )

        group_box = MyGroupBox( "Audio Player", False )
        group_box.setFixedWidth(s.Const.leftPanelWidth)                                      
        group_box.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        group_box.setLayout( audio_player_layout )
        full_left_panel_layout.addWidget(group_box)

        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        #   Left Panel - consists of Left Panel object built in separate module
        #       including music and audio browsers, TOC, and audio / midi
        #       matching music file in viewer.

        left_panel = BL_Left_Panel( self )
        left_panel.setFixedWidth(s.Const.leftPanelWidth)       # *** note fixed width set here
        left_panel.setObjectName( 'leftPanel' )

        left_panel.set_music_root( s.conf.val('music_file_root') )
        left_panel.set_audio_root( s.conf.val('audio_file_root') )
        left_panel.set_midi_root( s.conf.val('midi_file_root') )
        left_panel.set_chordpro_root( s.conf.val('chordpro_file_root') )
        left_panel.set_jjazz_root( s.conf.val('jjazz_file_root') )

        full_left_panel_layout.addWidget( left_panel )

        # ===================================================================
        #   Lower Panel consists of Full Left Panel and Main Tabs

        self.mainTabBar = BL_Main_TabBar()
        lower_panel_layout.addLayout( full_left_panel_layout )
        lower_panel_layout.addWidget( self.mainTabBar )
        central_layout.addLayout( lower_panel_layout )    #   Finally, add Lower Panel to layout.

    # -------------------------------------------------------------------

    #   This is just for development to show object names when hovering over a ui element.
    #   This approach could be used to centralize all too tips in a dict indexed by name.
    #   This is valid use of getChildren(), keep it. No, setObjectName() now only used
    #   when needed for styling.
    
    def set_tooltips(self, widget ):
         """Find all child widgets and set their tooltip to their object name."""
         for widget in widget.findChildren(QWidget):        # OK - Diagnostics
             if widget.objectName():  # Only set tooltip if objectName is not empty
                 widget.setToolTip(widget.objectName())

    # -------------------------------------------------------------------

    def resizeEvent( self, event ):
        super().resizeEvent(event)

# ------------------------------------------------------------------------------
#   WRW 22-Mar-2025 - Add placeholder for Scales and Chords

class Build_Analysis( QWidget ):

    def __init__(self):
        super().__init__()
        s = Store()

        # -------------------------------------------------------------------

        central_layout = QVBoxLayout()
        central_layout.setContentsMargins( 4, 4, 4, 4 )
        central_layout.setSpacing( 4 )
        analysis = AnalysisTab()
        central_layout.addWidget( analysis )
        self.setLayout( central_layout )

    # -------------------------------------------------------------------

    def resizeEvent( self, event ):
        super().resizeEvent(event)

# ------------------------------------------------------------------------------
#   This will fail on exit. OK, no point setting up signals for unit test.

if __name__ == "__main__":
    from bl_unit_test import UT
    from bl_style import StyleSheet

    s = UT()

    s.app = QApplication([])

    s.window = Build_UI()
    s.window.setStyleSheet( StyleSheet )            # OK Unit test
    size = QApplication.primaryScreen().size()
    width = size.width()
    height = size.height()
    s.window.resize( width*.9, height*.9)
    s.window.show()
    sys.exit( s.app.exec() )

# -------------------------------------------------------------------------------------
