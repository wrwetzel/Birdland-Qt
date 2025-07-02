#!/usr/bin/python
# ------------------------------------------------------------------------------
#   WRW 26-Jan-2025
#   bl-actions.py - Respond from user actions - clicks, returns, etc.
#   WRW 1-Feb-2025 - Refactored to use Store() class for global storage

#   WRW 2-Feb-2025 - Put signal manager here to centralize processing of most signals,
#       what I'm calling 'managed signals'.

#   Signal Emitters:
#       Some of the UI elements catch lower level widget signals and emit their own signals.
#           E.g., MyTable.py emits:
#               self.sig_cell_clicked.emit( value, row, col )

#       Some UI elements connect emitting widgets directly to their own signals:
#           E.g., audio file browser in bl_left_panel.py:
#               self.audio_file_browser.clicked.connect( self.audio_browser_clicked_signal )

# ------------------------------------------------------------------------------

import sys
from pathlib import Path
import tempfile
import shutil

from PySide6.QtCore import Slot, QModelIndex
from PySide6.QtWidgets import QApplication, QPushButton, QLabel, QVBoxLayout, QWidget
from PySide6.QtWidgets import QMenu

# ---------------------------------------------------------
#   UI Objects

import bl_menu_actions as bma
from bl_constants import MT

# -----------------------------------------------------------------------------------

import fb_search
from Store import Store

# ==============================================================================
#   Trying to register_slot() here.
#   This is called from near end of module after all slot functions have
#   been defined. No good, Store not initialized at this point. Do another way.

def _initialize_on_import():
    pass

# ==============================================================================
#   Search - Get search parameters from text boxes, search each of the
#       primary DB tables, and populate the UI tables.

@Slot( str )
def search_box_return_pressed( title, composer, lyricist, artist, album, src, canonical, 
                          xdup_none, xdup_titles, xdup_canonicals, xdup_srcs, join_flag ):
    s = Store()

    statusText = []
    selectedTab = None

    # s.selectTab( MT.Index )

    # ------------------------------------------------------------------------------------
    #   Music Index

    columns = [ 'title', 'composer', 'canonical', 'page', 'sheet', 'src', 'local', 'file' ]

    data = []
    if join_flag:
        rows, pdf_count = fb_search.do_query_music_file_index_with_join( title, composer, lyricist, album, artist, src, canonical )
    else:
        rows, pdf_count = fb_search.do_query_music_file_index_with_join( title, composer, lyricist, None, None, src, canonical )

    if xdup_titles:
        rows = fb_search.select_unique_titles( rows )

    elif xdup_canonicals:
        rows = fb_search.select_unique_canonicals( rows )

    elif xdup_srcs:
        rows = fb_search.select_unique_srcs( rows )

    for row in rows:
        # irow = [ QStandardItem(row[col]) for col in columns ]
        irow = [ row[col] for col in columns ]
        data.append( irow )

    s.sigman.emit( "sig_music_table_data", data )    # WRW 14-Feb-2025 - completely decoupled signal/slot approach.
    statusText.append( f"<b>Music Index:</b> {pdf_count}" )
    if not selectedTab and pdf_count:
        selectedTab = MT.Index

    # ------------------------------------------------------------------------------------
    #   Audio files
    #       main_tab_bar.setCurrentIndex(4)

    columns = [ 'title', 'artist', 'album', 'file' ]

    rows, count = fb_search.do_query_audio_files_index( title, album, artist )
    data = []
    for row in rows:
        # irow = [ QStandardItem(row[col]) for col in columns ]
        irow = [ row[col] for col in columns ]
        data.append( irow )

    s.sigman.emit( "sig_audio_table_data", data )    # WRW 14-Feb-2025 - completely decoupled signal/slot approach.
    statusText.append( f"<b>Audio:</b> {count}" )
    if not selectedTab and count:
        selectedTab = MT.Audio

    # ------------------------------------------------------------------------------------
    #   Music Files

    columns = [ 'path', 'file' ]

    rows, count = fb_search.do_query_music_filename( title )
    data = []
    for row in rows:
        # irow = [ QStandardItem( row[col]) for col in columns ]
        irow = [ row[col] for col in columns ]
        data.append( irow )

    s.sigman.emit( "sig_music_files_table_data", data )    # WRW 14-Feb-2025 - completely decoupled signal/slot approach.
    statusText.append( f"<b>Music Files:</b> {count}" )
    if not selectedTab and count:
        selectedTab = MT.Files

    # ------------------------------------------------------------------------------------
    #   Midi Files

    columns = [ 'title', 'composer', 'path', 'file' ]

    rows, count = fb_search.do_query_midi_filename( title, composer )
    data = []
    for row in rows:
        # irow = [ QStandardItem( row[col]) for col in columns ]
        irow = [ str(row[col]) for col in columns ]
        data.append( irow )

    s.sigman.emit( "sig_midi_table_data", data )    # WRW 14-Feb-2025 - completely decoupled signal/slot approach.
    statusText.append( f"<b>Midi Files:</b> {count}" )
    if not selectedTab and count:
        selectedTab = MT.Midi

    # ------------------------------------------------------------------------------------
    #   ChordPro Files

    columns = [ 'title', 'artist', 'file' ]

    rows, count = fb_search.do_query_chordpro( title, artist )
    data = []
    for row in rows:
        # irow = [ QStandardItem( row[col]) for col in columns ]
        irow = [ row[col] for col in columns ]
        data.append( irow )

    s.sigman.emit( "sig_chordpro_table_data", data )    # WRW 14-Feb-2025 - completely decoupled signal/slot approach.
    statusText.append( f"<b>ChordPro Files:</b> {count}" )
    if not selectedTab and count:
        selectedTab = MT.Chord

    # ------------------------------------------------------------------------------------
    #   JJazzLab Files

    columns = [ 'title', 'file' ]

    rows, count = fb_search.do_query_jjazz_filename( title )
    data = []
    for row in rows:
        # irow = [ QStandardItem( row[col]) for col in columns ]
        irow = [ row[col] for col in columns ]
        data.append( irow )

    s.sigman.emit( "sig_jjazzlab_table_data", data )    # WRW 14-Feb-2025 - completely decoupled signal/slot approach.
    statusText.append( f"<b>JJazzLab Files:</b> {count}" )
    if not selectedTab and count:
        selectedTab = MT.JJazz

    # ------------------------------------------------------------------------------------
    #   YouTube Index
    #   WRW 23-May-2025 - duration removed

    # columns = [ 'title', 'ytitle', 'duration', 'yt_id' ]     # yt_id column is returned but not displayed
    columns = [ 'title', 'ytitle', 'yt_id' ]     # yt_id column is returned but not displayed

    rows, count = fb_search.do_query_youtube_index( title )
    data = []
    for row in rows:
        # irow = [ QStandardItem( row[col]) for col in columns ]
        irow = [ row[col] for col in columns ]
        data.append( irow )

    s.sigman.emit( "sig_youtube_table_data", data )    # WRW 14-Feb-2025 - completely decoupled signal/slot approach.
    statusText.append( f"<b>YouTube Index:</b> {count}" )
    if not selectedTab and count:
        selectedTab = MT.YouTube

    # ------------------------------------------------------------------------------------
    #   Report search results. Status bar is expected receiver.

    s.sigman.emit( "sig_search_results", ', '.join( statusText ) )
    if selectedTab:
        s.selectTab( selectedTab )


# ==============================================================================
#   WRW 14-Feb-2025 - signal emitter in bl_tables.py now fetches data, does not send row/col
#   'data' is dict indexed by modified header, lower case and first word of multi-word header.
#       header = ["Title", "Composer", "Canonical Book Name", "Page", "Sheet", "Src", "Local", "File"]
#   pdf_viewer is self contained, manages page changes internally, don't tell it to change page
#       externally other than for toc clicks.

@Slot( object )
def music_table_cell_clicked( data ):
    s = Store()

    s.selectTab( MT.Viewer )

    music_root = s.conf.val('music_file_root')
    path = Path( music_root, data.file )

    # s.pdf.showFi( file=path, title=data.title, alt_file=data.file, page=data.page, sheet=data.sheet,
    #               canonical=data.canonical, local=data.local, src=data.src )
    # args = {
    #     'file' : path, 'title' : data.title, 'alt_file' : data.file,
    #     'page' : data.page, 'sheet' : data.sheet, 'canonical' : data.canonical,
    #     'local' : data.local, 'src' : data.src
    # }

    s.sigman.emit( "sig_showFi", str(path), data )

# ------------------------------------------------------------------------------------

@Slot( object, object )
def music_table_cell_right_clicked( cursor_pos, data ):
    s = Store()

    # Create a context menu
    menu = QMenu()
    menu.setObjectName("MusicContextSearchMenu")
    action_search_title = menu.addAction("Search for Title")
    action_search_composer = menu.addAction("Search for Composer")

    # Show menu at the cursor position
    action = menu.exec(cursor_pos)

    # Handle menu actions
    if action == action_search_title:
        search_box_return_pressed( data.title, None, None, None, None, None, None,
                          None, None, None, None, None )

    if action == action_search_composer:
        search_box_return_pressed( None, data.composer, None, None, None, None, None,
                          None, None, None, None, None )

# ------------------------------------------------------------------------------------
#   Music Files Table - Music filename matched in search

@Slot( object )
def music_files_table_cell_clicked( data ):
    s = Store()

    s.selectTab( MT.Viewer )

    music_root = s.conf.val('music_file_root')
    path =  str(Path( music_root, data.path, data.file ))
    relpath =  str(Path( data.path, data.file ))
    # s.pdf.showFp( file=path, alt_file=relpath )
    #   WRW 1-Mar-2025 - Try using showFs() for music_files_table too. Should be the same now.

    # s.pdf.showFs( file=path, relpath=relpath )
    s.sigman.emit( "sig_showFs", path, relpath )

# ------------------------------------------------------------------------------------

@Slot( object )
def audio_table_cell_clicked( data ):
    s = Store()

    audio_root = s.conf.val('audio_file_root')
    path = Path( audio_root, data.file )

    if not path.is_file():
        s.conf.do_nastygram( 'audio_file_root', path )
    else:
        s.sigman.emit( "sig_play_audio", str(path) )
        # s.ap.play( path )

# ------------------------------------------------------------------------------------

@Slot( object, object )
def audio_table_cell_right_clicked( cursor_pos, data ):
    s = Store()

    # Create a context menu
    menu = QMenu()
    menu.setObjectName("AudioContextSearchMenu")
    action_search_title = menu.addAction("Search for Title")
    action_search_artist = menu.addAction("Search for Artist")
    action_search_album = menu.addAction("Search for Album")

    # Show menu at the cursor position
    action = menu.exec(cursor_pos)

    # Handle menu actions
    if action == action_search_title:
        search_box_return_pressed( data.title, None, None, None, None, None, None,
                          None, None, None, None, None )

    if action == action_search_artist:
        title = data.title
        search_box_return_pressed( None, None, None, data.artist, None, None, None,
                          None, None, None, None, None )

    if action == action_search_album:
        title = data.title
        search_box_return_pressed( None, None, None, None, data.album, None, None,
                          None, None, None, None, None )

# ------------------------------------------------------------------------------------

@Slot( object )
def midi_table_cell_clicked( data ):
    s = Store()

    midi_root = s.conf.val('midi_file_root')
    path = Path( midi_root, data.path, data.file )

    if not path.is_file():
        s.conf.do_nastygram( 'midi_file_root', path )
    else:
        # s.midi.play( path, data.file )
        s.sigman.emit( "sig_play_midi", str( path ), str( data.file ) )

# ------------------------------------------------------------------------------------
#   I briefly tried to add a title using a 'Template.mscx' file but ChatGPT was not helpful

@Slot( object, object )
def midi_table_cell_right_clicked( cursor_pos, data ):
    s = Store()

    # Create a context menu
    menu = QMenu()
    menu.setObjectName("engraveMenu")
    action_convert = menu.addAction("Engrave Score")
    action_search_title = menu.addAction("Search for Title")
    action_search_composer = menu.addAction("Search for Composer")

    # Show menu at the cursor position
    action = menu.exec(cursor_pos)

    # Handle menu actions
    if action == action_convert:
        # data = [self.model.item(row, col).text() for col in range(self.model.columnCount())]

        path = Path( s.conf.val( 'midi_file_root' ), data.path, data.file )
        ofile = tempfile.NamedTemporaryFile( suffix='.pdf', delete=False ).name

        musescore = s.conf.val( 'musescore_program' )
        if not musescore:
            musescore = 'mscore'       # NOTE Hard-coded OK on linux and windows, have to give path on MacOS via option.

        if shutil.which( musescore ):
            command = [ musescore, '-o', ofile, str(path) ]
            s.fb.run_external_command_binary( command, "sig_midi_ext_command_finished", aux_data=ofile  )
        else:
            # s.conf.do_popup( f"Midi to PDF conversion program, '{musescore}', not found." )
            s.msgWarn( f"Midi to PDF conversion program, '{musescore}', not found." )

    if action == action_search_title:
        search_box_return_pressed( data.title, None, None, None, None, None, None,
                          None, None, None, None, None )

    if action == action_search_composer:
        search_box_return_pressed( None, data.composer, None, None, None, None, None,
                          None, None, None, None, None )

# ------------------------------------------------------------------------------------
#   This is the end result of a right click in the midi table followed by a click on the
#       popup menu (unless I eliminat the menu).
#   Right-click -> bl_tables.py show_context_menu() ->
#       fb_utils.py run_external_command_binary() ->
#       fb_utils.py WorkerThread ->
#       emits signal specified in call in show_context_menu()

#   data here is [ ofile, stdout, stderr ]      where ofile comes from aux_data argument

@Slot( int, object )
def midi_ext_command_finished( rcode, data ):
    s = Store()
    path = data[0]
    if not rcode:
        s.selectTab( MT.Viewer )
        # s.pdf.showFt( file=path, title="Converted From Midi" )      # Title does not appear, overridded by blank, keep anyway.
        s.sigman.emit( "sig_showFt", path, None, "Converted From Midi" )      # Title does not appear, overridded by blank, keep anyway.

    # os.remove( path )   # OK to delete as soon as shown
    Path( path ).unlink(missing_ok=True)   # required for Windows

# ------------------------------------------------------------------------------------
#   Callback needed because tmpfile tfile generated by external process, can't show till generated.

@Slot( object )
def chordpro_table_cell_clicked( data ):

    s = Store()
    chordpro_root = s.conf.val('chordpro_file_root')
    path = Path( chordpro_root, data.file )

    def show_chordpro_file_callback( tfile ):
        s.selectTab( MT.Viewer )
        # s.pdf.showFt( file=str( tfile ), alt_file=data.file, title=data.title )
        s.sigman.emit( "sig_showFt", str( tfile ), data.file, data.title )

    if not path.is_file():
        s.conf.do_nastygram( 'chordpro_file_root', path )
    else:
        # s.chord.show( path, show_chordpro_file_callback )
        s.sigman.emit( "sig_show_chord", str(path), show_chordpro_file_callback )

# ------------------------------------------------------------------------------------

@Slot( object, object )
def chordpro_table_cell_right_clicked( cursor_pos, data ):
    s = Store()

    # Create a context menu
    menu = QMenu()
    menu.setObjectName("AudioContextSearchMenu")
    action_search_title = menu.addAction("Search for Title")
    action_search_artist = menu.addAction("Search for Artist")

    # Show menu at the cursor position
    action = menu.exec(cursor_pos)

    # Handle menu actions
    if action == action_search_title:
        search_box_return_pressed( data.title, None, None, None, None, None, None,
                          None, None, None, None, None )

    if action == action_search_artist:
        title = data.title
        search_box_return_pressed( None, None, None, data.artist, None, None, None,
                          None, None, None, None, None )

# ------------------------------------------------------------------------------------

@Slot( object )
def jjazzlab_table_cell_clicked( data ):

    s = Store()

    jjazz_root = s.conf.val('jjazz_file_root')
    path = Path( jjazz_root, data.file )

    if not path.is_file():
        s.conf.do_nastygram( 'jjazz_file_root', path )
    else:
        s.sigman.emit( "sig_show_jjazz", str(path) )
        # s.jjazz.show( path )

# ------------------------------------------------------------------------------------

@Slot( object )
def youtube_table_cell_clicked( data ):
    s = Store()
    # fb.open_youtube_file( ytitle )    # KEEP?
    s.sigman.emit( "sig_show_youtube", data.yt_id )
    # s.youtube.show( data.yt_id )

# ------------------------------------------------------------------------------------
#   Music Browser is file browser in left panel.
#   User clicked on music file name. 
#       load pdf,
#       update select src offsets for selected music file combo box.
#       update selected music file information
#       update metadata                       

@Slot( QModelIndex )
# def music_browser_clicked( path, src_offset ):          # path from browser is full path to file
def music_browser_clicked( path ):          # path from browser is full path to file
    s = Store()
    s.selectTab( MT.Viewer )

    music_root = s.conf.val('music_file_root')
    relpath = str(Path( path ).relative_to( music_root ).as_posix() )

    # s.pdf.showFs( file=path, relpath=relpath, src_offset=src_offset )
    # s.pdf.showFs( file=path, relpath=relpath )
    s.sigman.emit( "sig_showFs", path, relpath )

# ------------------------------------------------------------------------------------

@Slot( QModelIndex )
def audio_browser_clicked( path ):
    s = Store()

    path = Path( path )

    if not path.is_file():
        s.conf.do_nastygram( 'audio_file_root', path )
    else:
        s.sigman.emit( "sig_play_audio", str(path) )

# ------------------------------------------------------------------------------------

@Slot( QModelIndex )
def midi_browser_clicked( path ):
    s = Store()

    midi_root = s.conf.val('midi_file_root')
    path = Path( midi_root, path )

    if not path.is_file():
        s.conf.do_nastygram( 'midi_file_root', path )
    else:
        s.sigman.emit( "sig_play_midi", str(path), str( path ) )

# ------------------------------------------------------------------------------------
#   /// RESUME - Harmonize with chordpro above

@Slot( QModelIndex )
def chordpro_browser_clicked( path ):
    s = Store()
    chordpro_root = s.conf.val('chordpro_file_root')
    path = Path( chordpro_root, path )

    def show_chordpro_file_callback( tfile ):
        s.selectTab( MT.Viewer )
        s.sigman.emit( "sig_showFt", str( tfile ), path, 'Title not available' )

    if not path.is_file():
        s.conf.do_nastygram( 'chordpro_file_root', path )
    else:
        s.sigman.emit( "sig_show_chord", str(path), show_chordpro_file_callback )

# ------------------------------------------------------------------------------------
#   /// RESUME - Harmonize with jjazz above

@Slot( object )
def jjazz_browser_clicked( file ):

    s = Store()

    jjazz_root = s.conf.val('jjazz_file_root')
    path = Path( jjazz_root, file )

    if not path.is_file():
        s.conf.do_nastygram( 'jjazz_file_root', path )
    else:
        s.sigman.emit( "sig_show_jjazz", str(path) )
        # s.jjazz.show( path )

# ------------------------------------------------------------------------------------
#   Menu actions defined in bma - bl_menu_actions.py

@Slot()
def process_menu_action( t ):
    bma.process_menu_action( t )

#   This is called after all modules are loaded and all classes 
#       initialized such that all signals and slots have been registered.
#   Initialize all slots cotained in this module.
#   Slots must be registered in the namespace containing them.
#   I tried to do this in _initialize_on_import() but that was too early,
#   contents of Store not populated yet.

# ------------------------------------------------------------------------------------

def register_action_slots():
    s = Store()

    Slots = (
        ( "slot_search_box_return_pressed",             search_box_return_pressed ),
        ( "slot_music_table_cell_clicked",              music_table_cell_clicked ),
        ( "slot_music_table_cell_right_clicked",        music_table_cell_right_clicked ),
        ( "slot_music_files_table_cell_clicked",        music_files_table_cell_clicked ),
        ( "slot_audio_table_cell_clicked",              audio_table_cell_clicked ),
        ( "slot_audio_table_cell_right_clicked",        audio_table_cell_right_clicked ),
        ( "slot_midi_table_cell_clicked",               midi_table_cell_clicked ),
        ( "slot_midi_table_cell_right_clicked",         midi_table_cell_right_clicked ),
        ( "slot_midi_ext_command_finished",             midi_ext_command_finished ),
        ( "slot_chordpro_table_cell_clicked",           chordpro_table_cell_clicked ),
        ( "slot_chordpro_table_cell_right_clicked",     chordpro_table_cell_right_clicked ),
        ( "slot_jjazzlab_table_cell_clicked",           jjazzlab_table_cell_clicked ),
        ( "slot_youtube_table_cell_clicked",            youtube_table_cell_clicked ),
        ( "slot_music_browser_clicked",                 music_browser_clicked ),
        ( "slot_audio_browser_clicked",                 audio_browser_clicked ),
        ( "slot_midi_browser_clicked",                  midi_browser_clicked ),
        ( "slot_chordpro_browser_clicked",              chordpro_browser_clicked ),
        ( "slot_jjazz_browser_clicked",                 jjazz_browser_clicked ),
        ( "slot_menu_action",                           process_menu_action ),
    )

    for slot_name, slot in Slots:
        s.sigman.register_slot( slot_name, slot )

# ==============================================================================
#   WRW 12-Feb-2025 - This is called once on first import of module.
#       Initialize slots. Used when module is not using classes.
#       No good, gets called too early, before values in Store() established.

_initialize_on_import()

# ==============================================================================
#   Unit test for signal dispatcher

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Signal Dispatcher Unit Test")

        layout = QVBoxLayout(self)
        self.label = QLabel("Waiting for signals...")
        self.label.setObjectName("label")
        button1 = QPushButton("Button 1")
        button1.setObjectName("btn_one")

        button2 = QPushButton("Button 2")
        button2.setObjectName("btn_two")

        layout.addWidget(self.label)
        layout.addWidget(button1)
        layout.addWidget(button2)

# --------------------------------------------------------------

if __name__ == "__main__":

    TestConnections = [
        Connection( "btn_one", QPushButton, 'clicked', 'handle_button_one' ),
        Connection( "btn_two", QPushButton, 'clicked', 'handle_button_two' ),
        Connection( "btn_two", QPushButton, 'clicked', 'handle_button_two' ),
    ]

    @Slot()
    def handle_button_one():
        s = Store()
        label = s.window.findChild( QLabel, 'label' )   # OK - unit test
        label.setText(f"Handler 1")
    
    @Slot()
    def handle_button_two():
        s = Store()
        label = s.window.findChild( QLabel, 'label' )   # OK - unit test
        label.setText(f"Handler 2")

    s = Store()
    app = QApplication(sys.argv)
    s.window = MainWindow()
    s.window.show()
    Make_Connections( TestConnections )
    sys.exit(app.exec())

# --------------------------------------------------------------
