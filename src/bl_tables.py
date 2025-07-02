#!/usr/bin/python
# -------------------------------------------------------------------------------------
#   WRW 5-Feb-2025
#   Combined from individual table files. All are small, no need to separate.
#   WRW 12-Feb-2025 - add Signal() definitions here instead of kludgy way
#       of dealing with them in MyTable with setSignalName().
#   WRW 14-Feb-2025 - migrate to signals for sending data to tables.
# -------------------------------------------------------------------------------------

import sys

from PySide6.QtCore import Qt, Signal, Slot, QPoint
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow, 
    QVBoxLayout,
    QWidget,
    QTableView,
)

from Store import Store
from MyTable import MyTable

# -------------------------------------------------------------------------------------
#   Return a dict indexed by a slight perversion of the column header.

def getData( table, row, header ):
    data = {}
    for col, name in enumerate( header ):
        name = name.partition( ' ' )[0].lower()         # use only first word of multi-word header names
        data[ name ] = table.getItem( row, col )
    return data

#   As above but so can reference return with attribute notation.

class getDataNew():
    def __init__( self, table, row, header ):
        for col, name in enumerate( header ):
            name = name.partition( ' ' )[0].lower()         # use only first word of multi-word header names
            val = table.getItem( row, col )
            setattr( self, name, val)

    def __str__( self ):
        return( f"dict: {self.__dict__}" )          # __dict__ returns a dict of attribute values

# -------------------------------------------------------------------------------------
#   WRW 6-Mar-2025 - put more data in table than visible to carry data to point
#       where show pdf file.

class SetListTable( MyTable ):
    sig_setlist_table_cell_clicked = Signal( object )
    sig_setlist_table_row_clicked = Signal( int, object )

    def __init__(self):
        s = Store()
        self.lheader = [ "Title", "Canonical", "File", "Sheet", "Page", "Src", "Local", "Mode" ]
        ratios = [8, 8, 10, 2, 2 ]
        super().__init__( self.lheader, ratios )
        s.sigman.register_signal( "sig_setlist_table_cell_clicked", self.sig_setlist_table_cell_clicked )
        s.sigman.register_signal( "sig_setlist_table_row_clicked", self.sig_setlist_table_row_clicked )
        self.sig_cell_clicked.connect( self.my_on_cell_clicked )
        s.sigman.register_slot( "slot_setlist_table_data", self.setlist_table_data )

        self.selectionModel().selectionChanged.connect( self.my_on_row_selected )
        self.setSelectionMode(QTableView.SingleSelection)       # Allow only single row selection
        self.setSelectionBehavior(QTableView.SelectRows)        # Select entire rows

        for col in [ 5, 6, 7]:
            self.hideColumn(col)

    # -----------------------------------------------------------------------
    #   WRW 8-Mar-2025 - specifying argument type of nindex as 'object' is critical
    #       as None is passed as 0 of type was 'int'. Ouch, took a while to find.

    @Slot( object, object )
    def setlist_table_data( self, data, nindex ):
        # print( "/// setlist_table_data:", nindex )
        self.update( data, index=nindex )

    # -----------------------------------------------------------------------
    @Slot( str, int, int )
    def my_on_cell_clicked( self, value, row, col ):
        s = Store()
        data = getDataNew( self, row, self.lheader )
        # print( "/// my_on_cell_clicked()" )
        s.sigman.emit( "sig_setlist_table_cell_clicked", data )

    # -----------------------------------------------------------------------
    #   selected_indexes has the number of rows equal to table length, 
    #       use just the first one.
    #   Try emiting the entire row of data as above and row number

    @Slot( object, object )
    def my_on_row_selected( self, selected, deselected ):
        s = Store()
        ok = False

        # print("--------------------------------------------------" )
        # import traceback
        # traceback.print_stack()
        # print("--------------------------------------------------\n" )

        selected_indexes = selected.indexes()
        if selected_indexes:
            row = selected_indexes[0].row()             
            data = getDataNew( self, row, self.lheader )
            # print( "/// my_on_row_selected() select", row )
            s.sigman.emit( "sig_setlist_table_row_clicked", row, data )
            ok = True

        if deselected.indexes():
            row = deselected.indexes()[0].row()
            # print( "/// my_on_row_selected() deselect", row )
            ok = True

        if not ok:
            print( "WARNING: my_on_row_selected() selected and deselected are empty" )

# -------------------------------------------------------------------------------------
#   Connect MyTable internal signal to sigman to emit a managed signal.

class MusicTable( MyTable ):
    sig_music_table_cell_clicked = Signal( object )
    sig_music_table_cell_right_clicked = Signal( object, object )

    def __init__( self ):
        s = Store()
        self.lheader = ["Title", "Composer", "Canonical Book Name", "Page", "Sheet", "Src", "Local", "File"]
        ratios = [20, 10, 20, 4, 4, 3, 10, 20]
        numericCols = [3, 4]
        super().__init__( self.lheader, ratios, numericCols )
        s.sigman.register_signal( "sig_music_table_cell_clicked", self.sig_music_table_cell_clicked )
        s.sigman.register_signal( "sig_music_table_cell_right_clicked", self.sig_music_table_cell_right_clicked )
        self.sig_cell_clicked.connect( lambda value, row, col: self.my_on_cell_clicked( value, row, col ))
        s.sigman.register_slot( "slot_music_table_data", self.update )

        self.setSelectionMode(QTableView.SingleSelection)       # Allow only single row selection
        self.setSelectionBehavior(QTableView.SelectRows)        # Select entire rows

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.my_on_cell_right_click)

    def my_on_cell_clicked( self, value, row, col ):
        s = Store()
        data = getDataNew( self, row, self.lheader )
        s.sigman.emit( "sig_music_table_cell_clicked", data )

    # Handle right-click and show context menu
    def my_on_cell_right_click(self, pos: QPoint):
        s = Store()
        index = self.indexAt(pos)
        if index.isValid():
            row = index.row()
            data = getDataNew( self, row, self.lheader )
            cursor_pos = self.viewport().mapToGlobal(pos)       # QPoint
            s.sigman.emit( "sig_music_table_cell_right_clicked", cursor_pos, data )

# -------------------------------------------------------------------------------------

class MusicFilesTable( MyTable ):
    sig_music_files_table_cell_clicked = Signal( object )

    def __init__(self ):
        s = Store()
        self.lheader = [ "Path", "File" ]
        ratios = [1, 1]
        super().__init__( self.lheader, ratios )
        s.sigman.register_signal( "sig_music_files_table_cell_clicked", self.sig_music_files_table_cell_clicked )
        self.sig_cell_clicked.connect( lambda value, row, col: self.my_on_cell_clicked( value, row, col ))
        s.sigman.register_slot( "slot_music_files_table_data", self.update )

        self.setSelectionMode(QTableView.SingleSelection)       # Allow only single row selection
        self.setSelectionBehavior(QTableView.SelectRows)        # Select entire rows

    def my_on_cell_clicked( self, value, row, col ):
        s = Store()
        data = getDataNew( self, row, self.lheader )
        s.sigman.emit( "sig_music_files_table_cell_clicked", data )

# -------------------------------------------------------------------------------------

class AudioTable( MyTable ):
    sig_audio_table_cell_clicked = Signal(object)
    sig_audio_table_cell_right_clicked = Signal( object, object )

    def __init__(self ):
        s = Store()
        self.lheader = ["Title", "Artist", "Album", "File" ]                                      
        ratios = [1, 1, 1, 2]
        super().__init__( self.lheader, ratios )
        s.sigman.register_signal( "sig_audio_table_cell_clicked", self.sig_audio_table_cell_clicked )
        s.sigman.register_signal( "sig_audio_table_cell_right_clicked", self.sig_audio_table_cell_right_clicked )
        self.sig_cell_clicked.connect( lambda x, y, z: self.my_on_cell_clicked( x, y, z ))
        s.sigman.register_slot( "slot_audio_table_data", self.update )

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.my_on_cell_right_click)

        self.setSelectionMode(QTableView.SingleSelection)       # Allow only single row selection
        self.setSelectionBehavior(QTableView.SelectRows)        # Select entire rows

    def my_on_cell_clicked( self, value, row, col ):
        s = Store()
        data = getDataNew( self, row, self.lheader )
        s.sigman.emit( "sig_audio_table_cell_clicked", data )

    #   Right-click on row
    #   Keep on menu for now.

    # Handle right-click and show context menu
    def my_on_cell_right_click(self, pos: QPoint):
        s = Store()

        index = self.indexAt(pos)
        if index.isValid():
            row = index.row()
            data = getDataNew( self, row, self.lheader )
            # print( "///", row, data )

            cursor_pos = self.viewport().mapToGlobal(pos)       # QPoint
            s.sigman.emit( "sig_audio_table_cell_right_clicked", cursor_pos, data )

# -------------------------------------------------------------------------------------

class MidiTable( MyTable ):
    sig_midi_table_cell_clicked = Signal( object )
    sig_midi_table_cell_right_clicked = Signal( object, object )
    sig_midi_ext_command_finished = Signal( int, object )

    def __init__(self ):
        s = Store()
        self.lheader = [ "Title", "Composer", "Path", "File"]
        ratios = [10, 10, 10, 20]
        super().__init__( self.lheader, ratios )
        s.sigman.register_signal( "sig_midi_table_cell_clicked", self.sig_midi_table_cell_clicked )
        s.sigman.register_signal( "sig_midi_table_cell_right_clicked", self.sig_midi_table_cell_right_clicked )
        s.sigman.register_signal( "sig_midi_ext_command_finished", self.sig_midi_ext_command_finished )
        self.sig_cell_clicked.connect( lambda x, y, z: self.my_on_cell_clicked( x, y, z ))
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.my_on_cell_right_click)

        s.sigman.register_slot( "slot_midi_table_data", self.update )

        self.setSelectionMode(QTableView.SingleSelection)       # Allow only single row selection
        self.setSelectionBehavior(QTableView.SelectRows)        # Select entire rows

    # --------------------------------------------------------------

    def my_on_cell_clicked( self, value, row, col ):
        s = Store()
        data = getDataNew( self, row, self.lheader )
        s.sigman.emit( "sig_midi_table_cell_clicked", data )
        # print( "///", row, data )

    # --------------------------------------------------------------
    #   Right-click on row
    #   Do we really want to show a menu or just convert on the click
    #   Keep on menu for now.

    def my_on_cell_right_click(self, pos: QPoint):
        """Handle right-click and show context menu."""
        s = Store()

        index = self.indexAt(pos)
        if index.isValid():
            row = index.row()
            data = getDataNew( self, row, self.lheader )
            # print( "///", row, data )

            cursor_pos = self.viewport().mapToGlobal(pos)       # QPoint
            s.sigman.emit( "sig_midi_table_cell_right_clicked", cursor_pos, data )

# -------------------------------------------------------------------------------------

class ChordProTable( MyTable ):
    sig_chordpro_table_cell_clicked = Signal( object )
    sig_chordpro_table_cell_right_clicked = Signal( object, object )

    def __init__(self ):
        s = Store()
        self.lheader = [ "Title", "Artist", "File"]
        ratios = [1, 1, 2]
        super().__init__( self.lheader, ratios )
        s.sigman.register_signal( "sig_chordpro_table_cell_clicked", self.sig_chordpro_table_cell_clicked )
        s.sigman.register_signal( "sig_chordpro_table_cell_right_clicked", self.sig_chordpro_table_cell_right_clicked )
        self.sig_cell_clicked.connect( lambda x, y, z: self.my_on_cell_clicked( x, y, z ))
        s.sigman.register_slot( "slot_chordpro_table_data", self.update )

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.my_on_cell_right_click)

        self.setSelectionMode(QTableView.SingleSelection)       # Allow only single row selection
        self.setSelectionBehavior(QTableView.SelectRows)        # Select entire rows

    def my_on_cell_clicked( self, value, row, col ):
        s = Store()
        data = getDataNew( self, row, self.lheader )
        s.sigman.emit( "sig_chordpro_table_cell_clicked", data )

    def my_on_cell_right_click(self, pos: QPoint):
        s = Store()

        index = self.indexAt(pos)
        if index.isValid():
            row = index.row()
            data = getDataNew( self, row, self.lheader )
            cursor_pos = self.viewport().mapToGlobal(pos)       # QPoint
            s.sigman.emit( "sig_chordpro_table_cell_right_clicked", cursor_pos, data )

# -------------------------------------------------------------------------------------

class JJazzLabTable( MyTable ):
    sig_jjazzlab_table_cell_clicked = Signal( object )
    def __init__(self ):
        s = Store()
        self.lheader = [ "Title", "File"]
        ratios = [1, 1]
        super().__init__( self.lheader, ratios )
        s.sigman.register_signal( "sig_jjazzlab_table_cell_clicked", self.sig_jjazzlab_table_cell_clicked )
        self.sig_cell_clicked.connect( lambda x, y, z: self.my_on_cell_clicked( x, y, z ))
        s.sigman.register_slot( "slot_jjazzlab_table_data", self.update )

        self.setSelectionMode(QTableView.SingleSelection)       # Allow only single row selection
        self.setSelectionBehavior(QTableView.SelectRows)        # Select entire rows

    def my_on_cell_clicked( self, value, row, col ):
        s = Store()
        data = getDataNew( self, row, self.lheader )
        s.sigman.emit( "sig_jjazzlab_table_cell_clicked", data )

# -------------------------------------------------------------------------------------
#   WRW 23-May-2025 - Remove duration

class YouTubeTable( MyTable ):
    sig_youtube_table_cell_clicked = Signal( object )
    def __init__(self ):
        s = Store()
        # self.lheader = [ "Title", "YouTube Title", "Duration", "YT_ID" ]    # yt_id column is returned but not displayed
        self.lheader = [ "Title", "YouTube Title", "YT_ID" ]    # yt_id column is returned but not displayed
        # ratios = [7, 10, 2 ]
        ratios = [7, 10 ]
        super().__init__( self.lheader, ratios )
        s.sigman.register_signal( "sig_youtube_table_cell_clicked", self.sig_youtube_table_cell_clicked )
        self.sig_cell_clicked.connect( lambda x, y, z: self.my_on_cell_clicked( x, y, z ))
        s.sigman.register_slot( "slot_youtube_table_data", self.update )
        self.hideColumn(3)

        self.setSelectionMode(QTableView.SingleSelection)       # Allow only single row selection
        self.setSelectionBehavior(QTableView.SelectRows)        # Select entire rows

    def my_on_cell_clicked( self, value, row, col ):
        s = Store()
        data = getDataNew( self, row, self.lheader )
        s.sigman.emit( "sig_youtube_table_cell_clicked", data )

# -------------------------------------------------------------------------------------

class AudioOfTitle( MyTable ):
    sig_audio_of_title_table_cell_clicked = Signal(object)

    def __init__(self):
        s = Store()
        self.lheader = [ "Title", "Artist", "File" ]
        ratios = [1, 1, 0]
        super().__init__( self.lheader, ratios )
        s.sigman.register_signal( "sig_audio_of_title_table_cell_clicked", self.sig_audio_of_title_table_cell_clicked )
        self.sig_cell_clicked.connect( lambda x, y, z: self.my_on_cell_clicked( x, y, z ))
        s.sigman.register_slot( "slot_audio_of_table_table_data", self.update )
        self.hideColumn(2)

        self.setSelectionMode(QTableView.SingleSelection)       # Allow only single row selection
        self.setSelectionBehavior(QTableView.SelectRows)        # Select entire rows

    def my_on_cell_clicked( self, value, row, col ):
        s = Store()
        # file = self.getItem( row, 2 )
        data = getDataNew( self, row, self.lheader )
        s.sigman.emit( "sig_audio_of_title_table_cell_clicked", data )

# -------------------------------------------------------------------------------------

class MidiOfTitle( MyTable ):
    sig_midi_of_title_table_cell_clicked = Signal(object)

    def __init__(self):
        s = Store()
        self.lheader = [ "Path", "File" ]
        ratios = [1, 1]
        super().__init__( self.lheader, ratios )
        s.sigman.register_signal( "sig_midi_of_title_table_cell_clicked", self.sig_midi_of_title_table_cell_clicked )
        self.sig_cell_clicked.connect( lambda x, y, z: self.my_on_cell_clicked( x, y, z ))

        self.setSelectionMode(QTableView.SingleSelection)       # Allow only single row selection
        self.setSelectionBehavior(QTableView.SelectRows)        # Select entire rows

    def my_on_cell_clicked( self, value, row, col ):
        s = Store()
        # path = self.getItem( row, 0 )
        # file = self.getItem( row, 1 )
        data = getDataNew( self, row, self.lheader )
        s.sigman.emit( "sig_midi_of_title_table_cell_clicked", data )

# -------------------------------------------------------------------------------------

class TableOfContents( MyTable ):
    sig_toc_cell_clicked = Signal( str, str )

    def __init__(self):
        s = Store()
        header = [ "Title", "Sheet" ]
        ratios = [75, 25]
        numericCols = [1]
        super().__init__( header, ratios, numericCols )
        s.sigman.register_signal( "sig_toc_cell_clicked", self.sig_toc_cell_clicked )
        self.sig_cell_clicked.connect( lambda x, y, z: self.my_on_cell_clicked( x, y, z ))
        s.sigman.register_slot( "slot_update_meta_toc", self.update )

        self.setSelectionMode(QTableView.SingleSelection)       # Allow only single row selection
        self.setSelectionBehavior(QTableView.SelectRows)        # Select entire rows

    def my_on_cell_clicked( self, value, row, col ):
        s = Store()
        title = self.getItem( row, 0 )
        sheet = self.getItem( row, 1 )
        s.sigman.emit( "sig_toc_cell_clicked", title, sheet )

# -------------------------------------------------------------------------------------
#   /// RESUME switch to keywork args? For what? [] is numeric cols, none here.

class ReportsTable( MyTable ):
    def __init__(self ):
        s = Store()
        header = [ "Name", "Value" ]                                                
        ratios = [ 3, 1 ]
        super().__init__( header, ratios, [], True )        
        self.hideColumn(3)
        s.sigman.register_slot( "slot_update_reports_table", self.update )

# -------------------------------------------------------------------------------------

class CanonNameTable( MyTable ):
    sig_canon_name_table_cell_clicked = Signal( object )
    def __init__(self ):
        s = Store()
        self.lheader = [ "Canonical Name" ]
        ratios = [1]
        super().__init__( self.lheader, ratios )
        s.sigman.register_signal( "sig_canon_name_table_cell_clicked", self.sig_canon_name_table_cell_clicked )
        self.sig_cell_clicked.connect( lambda x, y, z: self.my_on_cell_clicked( x, y, z ))
        s.sigman.register_slot( "slot_canon_name_table_data", self.update )

        self.setSelectionMode(QTableView.SingleSelection)       # Allow only single row selection
        self.setSelectionBehavior(QTableView.SelectRows)        # Select entire rows

    def my_on_cell_clicked( self, value, row, col ):
        s = Store()
        data = getDataNew( self, row, self.lheader )
        s.sigman.emit( "sig_canon_name_table_cell_clicked", data )

# -------------------------------------------------------------------------------------

class CanonFileTable( MyTable ):
    sig_canon_file_table_cell_clicked = Signal( object )
    def __init__(self ):
        s = Store()
        self.lheader = [ "File Name" ]
        ratios = [1]
        super().__init__( self.lheader, ratios )
        s.sigman.register_signal( "sig_canon_file_table_cell_clicked", self.sig_canon_file_table_cell_clicked )
        self.sig_cell_clicked.connect( lambda x, y, z: self.my_on_cell_clicked( x, y, z ))
        s.sigman.register_slot( "slot_canon_file_table_data", self.update )

        self.setSelectionMode(QTableView.SingleSelection)       # Allow only single row selection
        self.setSelectionBehavior(QTableView.SelectRows)        # Select entire rows

    def my_on_cell_clicked( self, value, row, col ):
        s = Store()
        data = getDataNew( self, row, self.lheader )
        s.sigman.emit( "sig_canon_file_table_cell_clicked", data )

# -------------------------------------------------------------------------------------

class CanonLinkTable( MyTable ):
    sig_canon_name_file_table_cell_clicked = Signal( object )
    def __init__(self ):
        s = Store()
        self.lheader = [ "Linked Canonical Name", "Linked File Name" ]
        ratios = [1, 1]
        super().__init__( self.lheader, ratios )
        s.sigman.register_signal( "sig_canon_name_file_table_cell_clicked", self.sig_canon_name_file_table_cell_clicked )
        self.sig_cell_clicked.connect( lambda x, y, z: self.my_on_cell_clicked( x, y, z ))
        s.sigman.register_slot( "slot_canon_name_file_table_data", self.update )

        self.setSelectionMode(QTableView.SingleSelection)       # Allow only single row selection
        self.setSelectionBehavior(QTableView.SelectRows)        # Select entire rows

    def my_on_cell_clicked( self, value, row, col ):
        s = Store()
        data = getDataNew( self, row, self.lheader )
        # s.sigman.emit( "sig_canon_name_file_table_cell_clicked", data )

# -------------------------------------------------------------------------------------

def gen_data( table ):
    import random
    for row in range( 5 ):
        table.addRow( [ str( random.randint( 0, 1000 )) for _ in range( table.columnCount() ) ] )

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        central_layout = QVBoxLayout(self.central_widget)               # Make an overall layout

        for table_fcn in SetListTable, MusicTable, AudioTable, MusicFilesTable, MidiTable, ChordProTable, JJazzLabTable, YouTubeTable:
            table = table_fcn()
            gen_data( table )
            central_layout.addWidget( table )

# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from bl_unit_test import UT
    from bl_style import StyleSheet

    s = UT()

    s.app = QApplication(sys.argv)
    s.window = MainWindow()
    s.window.setStyleSheet( StyleSheet )      # OK, unit test
    s.window.setGeometry(100, 100, 800, 400)
    s.window.show()
    sys.exit(s.app.exec())

# -------------------------------------------------------------------------------------
