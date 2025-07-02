#!/usr/bin/python
# -----------------------------------------------------------------------------------
#   WRW 21-Mar-2025 - UI and supporting code for 'Edit Canonical->File' tab
# -----------------------------------------------------------------------------------

#   Link Canonical to File   Clear One Link   Save   Find: lineedit
#   label
#   table: Canonical Name   table: Canonical Name  File Name

#   WRW 29-May-2025 - I don't like the way this presently works, confusing, not intuitive.
#   Going to try another approach with three tables:
#   Canonical Names - My Music File Names - Canonical to File Map
#   WRW 30-May-2025 - Looks good now, easy to do, makes more sense.

# -----------------------------------------------------------------------------------

import shutil
from pathlib import Path

from PySide6.QtCore import Qt, QItemSelectionModel, QTimer, Slot
from PySide6.QtGui import QStandardItem
from PySide6.QtWidgets import QApplication, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QLineEdit, QWidget
from PySide6.QtWidgets import QSizePolicy, QAbstractItemView, QFrame, QTableView

from Store import Store
from bl_tables import CanonNameTable, CanonFileTable, CanonLinkTable
from SignalManager import SigMan

# -----------------------------------------------------------------------------------

class Canon2FileTab( QWidget ):

    def __init__(self ):
        super().__init__()
        self.dirty = False

        s = Store()
        self.find_current_row = None

        s.sigman.register_slot( "slot_canon_name_table_cell_clicked", self.slot_canon_name_table_cell_clicked )
        s.sigman.register_slot( "slot_canon_file_table_cell_clicked", self.slot_canon_file_table_cell_clicked )

        # ----------------------------------------------------------------------

        overall_layout = QVBoxLayout()

        # ----------------------------------------------------------------------
        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignLeft)

        b = QPushButton( "Load Tables" )
        b.clicked.connect(self.my_load_clicked)
        b.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        layout.addWidget( b )

        b = QPushButton( "Link Canonical to File" )
        b.clicked.connect(self.my_link_clicked)                               
        b.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        layout.addWidget( b )

        b = QPushButton( "Clear One Link" )
        b.clicked.connect(self.my_clear_clicked)
        b.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        layout.addWidget( b )

        b = QPushButton( "Save" )
        b.clicked.connect(self.my_save_clicked)
        b.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        layout.addWidget( b )

        l = QLabel( "Find Canon:" )
        l.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        layout.addWidget(l)

        e = QLineEdit()
        e.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)                     
        self.findCanonText = e
        layout.addWidget( e )
        e.returnPressed.connect( self.my_canon_return_pressed )
        e.textChanged.connect( self.my_canon_text_changed )

        l = QLabel("Find File:" )
        l.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        layout.addWidget(l)

        e = QLineEdit()
        e.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)                     
        self.findFileText = e
        layout.addWidget( e )
        e.returnPressed.connect( self.my_file_return_pressed )
        e.textChanged.connect( self.my_file_text_changed )

        overall_layout.addLayout( layout )

        # ----------------------------------------------------------------------

        layout = QHBoxLayout()
        l = QLabel( """Click 'Load Tables'.  Select a row in the 'Canonical Name' table. Select a row in the 'File Name' table. Click 'Link Canonical to File'.  Click 'Save' when done.""" )

        layout.addWidget( l )

        overall_layout.addLayout( layout )

        # ----------------------------------------------------------------------

        layout = QHBoxLayout()

        table_layout = QVBoxLayout()
        title = QLabel( "Canonical Name Table" )
        title.setObjectName( 'canon2file-title' )
        table_layout.addWidget( title, alignment=Qt.AlignCenter )

        self.canonNameTable = CanonNameTable()
        table_layout.addWidget( self.canonNameTable, stretch=1 )

        layout.addLayout( table_layout )

        vline = QFrame()
        vline.setFrameShape(QFrame.VLine)
        vline.setFrameShadow(QFrame.Plain)  # Optional: Sunken, Raised, or Plain - Only Plain worked
        vline.setFixedWidth( 1 )
        layout.addWidget( vline )

        table_layout = QVBoxLayout()
        title = QLabel( "File Name Table" )
        title.setObjectName( 'canon2file-title' )
        table_layout.addWidget( title, alignment=Qt.AlignCenter )

        self.canonFileTable = CanonFileTable()                  # WRW 29-May-2025 - Added
        table_layout.addWidget( self.canonFileTable, stretch=1 )

        layout.addLayout( table_layout )

        vline = QFrame()
        vline.setFrameShape(QFrame.VLine)
        vline.setFrameShadow(QFrame.Plain)  # Optional: Sunken, Raised, or Plain - Only Plain worked
        vline.setFixedWidth( 1 )
        layout.addWidget( vline )

        table_layout = QVBoxLayout()
        title = QLabel( "Canonical->File Map Table" )
        title.setObjectName( 'canon2file-title' )
        table_layout.addWidget( title, alignment=Qt.AlignCenter )

        self.canonLinkTable = CanonLinkTable()
        table_layout.addWidget( self.canonLinkTable, stretch=2 )

        layout.addLayout( table_layout )
        overall_layout.addLayout( layout )

        # ----------------------------------------------------------------------

        self.setLayout( overall_layout )

        # ----------------------------------------------------------------------
        #   Load the tables
        #   WRW 27-Mar-2025 - don't want to do this until user clicks on tab, otherwise
        #       get nastygram if c2f_editable_map file not yet named. Add 'Load' button
        #       to do it.

    # ===================================================================================

    def my_load_clicked( self ):
        self.load_canonNameTable()
        self.load_canonFileTable()
        self.load_canonLinkTable()

    # -----------------------------------------------------------------------------------

    def my_link_clicked( self ):
        s = Store()
        found = 0

        # ---------------------------------------------------------------
        #   Get the canonical name from the canonNameTable

        name_model = self.canonNameTable.model
        name_proxy_model = self.canonNameTable.proxy_model
        name_view = self.canonNameTable.view

        if name_model.rowCount():
            selected_indexes = name_view.selectionModel().selectedRows()
            if selected_indexes:
                proxy_index = selected_indexes[0]                           
                source_index = name_proxy_model.mapToSource(proxy_index)     # 2. Map to source model
                row = source_index.row()                                     # 3. Extract data from the source model
                selected_canonical_value = name_model.item(row, 0).text()
                found += 1

        # ---------------------------------------------------------------
        #   Get the file name from the canonFileTable

        file_model = self.canonFileTable.model
        file_proxy_model = self.canonFileTable.proxy_model
        file_view = self.canonFileTable.view

        if file_model.rowCount():
            selected_indexes = file_view.selectionModel().selectedRows()
            if selected_indexes:
                proxy_index = selected_indexes[0]                           
                source_index = file_proxy_model.mapToSource(proxy_index)    # 2. Map to source model
                row = source_index.row()                                    # 3. Extract data from the source model
                selected_file_value = file_model.item(row, 0).text()
                found += 1

        # ---------------------------------------------------------------
        #   Got items selected in the canon and file table, update the link table and link_table_data[]
        #   Fine  the selected_file_value in the 2nd column of the canonLineTable

        if found == 2:
            row = self.findText( self.canonLinkTable, selected_file_value, 1 )
            link_model = self.canonLinkTable.model
            link_proxy_model = self.canonLinkTable.proxy_model
            link_view =  self.canonLinkTable.view

            self.dirty = True

            # ---------------------------------------------------------------
            #   File exists in link table, update link table with new canonicl
            if row is not None:

                # self.link_table_data[ selected_link_row ][ 0 ] = selected_canonical_value
                # new_selected_link_row = selected_link_row + 1 if selected_link_row + 1 < len( self.link_table_data ) else len( self.link_table_data ) -1

                item = link_model.item(row, 0)
                item.setText( selected_canonical_value )
                modified_row = row

            # ---------------------------------------------------------------
            #   File does not exist in link table, add it and the canonical at the end of table
            else:
                # row_count = table_view.model().rowCount()
                new_items = [
                    QStandardItem( selected_canonical_value ),
                    QStandardItem( selected_file_value)
                ]
                link_model.appendRow(new_items)     # Append to the model (adds a row at the end)
                modified_row = link_model.rowCount() - 1

            # ---------------------------------------------------------------
            #   Scroll to and select modified row for user feedback.
            
            source_index = link_model.index(modified_row, 0)
            proxy_index = link_proxy_model.mapFromSource(source_index)
            link_view.scrollTo(proxy_index, QTableView.PositionAtCenter )

            selection_model = link_view.selectionModel()
            selection_model.clearSelection()
            selection_model.select(
                proxy_index,
                QItemSelectionModel.Select | QItemSelectionModel.Rows
            )

        else:
            t = """Please select a row in the <i>Canonical Name</i> table and a
            row in the <i>File Name</i> table"""
            s.msgWarn( t )

    # -----------------------------------------------------------------------------------
    def my_clear_clicked( self ):
        s = Store()
        model = self.canonLinkTable.model
        proxy_model = self.canonLinkTable.proxy_model
        view = self.canonLinkTable.view

        if model.rowCount():
            selected_indexes = view.selectionModel().selectedRows()
            if not selected_indexes:
                t = "Please select a row in the 'Canonical Name / File Name' table."
                s.msgWarn( t )
                return

            proxy_index = selected_indexes[0]
            source_index = proxy_model.mapToSource(proxy_index)
            row = source_index.row()

            model.removeRow(row)
            self.dirty = True

    # -----------------------------------------------------------------------------------

    def my_save_clicked( self ):
        s = Store()
        if not self.dirty:
            t = "You have not made any changes, nothing to save."
            s.msgInfo( t )
            return

        backup_file = Path( self.canon2file_path.parent, self.canon2file_path.name + '.bak' )

        if Path(self.canon2file_path).is_file():           # Possibly nothing to backup
            shutil.copyfile( str( self.canon2file_path ), str( backup_file ))

        with open( self.canon2file_path, "wt", encoding='utf-8'  ) as ofd:  # /// WRW 23-Mar-2025 ENCODING

            link_model = self.canonLinkTable.model

            for row in range(link_model.rowCount()):
                canonical = link_model.item(row, 0).text()
                file = link_model.item(row, 1).text()
                print( f'{canonical} | {file}', file=ofd )

            s.msgInfo( f"Saved to: {self.canon2file_path}<br>Saved backup to {backup_file}" )

    # -----------------------------------------------------------------------------------
    #   WRW 30-May-2025
    #   Search table for text, taken from selectText

    def findText( self, table, val, column ):
        if not val:
            return None

        model = table.model
        # proxy_model = table.proxy_model
        # view = table.view

        for row in range( 0, model.rowCount()):
            item = model.item( row, column )
            if item and val == item.text():
                return row

        return None

    # ------------------------------------------
    #   Search table for text, select it, save row +1 in find_current_row

    def selectText( self, table, val, start_row ):

        if not val:
            self.find_current_row = None
            return    

        model = table.model
        proxy_model = table.proxy_model
        view = table.view
        selection_model = view.selectionModel()

        selection_model.clearSelection()     # Clear any residual selection.

        column = 0
        for row in range( start_row, model.rowCount()):
            item = model.item(row, column )
            if item and val in item.text().lower():
                self.find_current_row = row + 1
                index = model.index(row, 0)
                proxy_index = proxy_model.mapFromSource(index)
                selection_model.clearSelection()     # Clear prior, single selection only applies to user interaction.
                selection_model.select( index, QItemSelectionModel.Select | QItemSelectionModel.Rows ) 
                view.scrollTo(proxy_index, QAbstractItemView.PositionAtCenter )
                break

    # ------------------------------------------
    #   Simplified version of above just to find complete match of canon name or file
    #       in link table. No consideration for resuming search.

    def selectTextLinkTable( self, val, canon_flag ):

        if not val:
            self.find_current_row = None
            return    

        link_model = self.canonLinkTable.model
        proxy_model = self.canonLinkTable.proxy_model
        view = self.canonLinkTable.view
        selection_model = view.selectionModel()
        selection_model.clearSelection()     # Clear any residual selection.

        if canon_flag:
            column = 0          # Search in canon column
        else:
            column = 1          # Search in link column

        for row in range( link_model.rowCount() ):
            item = link_model.item( row, column )
            if item and val == item.text():
                index = link_model.index(row, 0)
                proxy_index = proxy_model.mapFromSource(index)
                selection_model.clearSelection()     # Clear prior, single selection only applies to user interaction.
                selection_model.select( index, QItemSelectionModel.Select | QItemSelectionModel.Rows ) 
                view.scrollTo(proxy_index, QAbstractItemView.PositionAtCenter )
                break

    # ------------------------------------------
    #   Select row in canonNameTable via searching

    def my_canon_text_changed( self ):
        val = self.findCanonText.text()
        self.selectText( self.canonNameTable, val, 0 )

    # ------------------------------------------
    #   Continue search when return pressed

    def my_canon_return_pressed( self ):
        val = self.findCanonText.text()
        self.selectText( self.canonNameTable, val, self.find_current_row )

    # ------------------------------------------
    #   Select row in canonFileTable via searching

    def my_file_text_changed( self ):
        val = self.findFileText.text()
        self.selectText( self.canonFileTable, val, 0 )

    # ------------------------------------------
    #   Continue search when return pressed

    def my_file_return_pressed( self ):
        val = self.findFileText.text()
        self.selectText( self.canonFileTable, val, self.find_current_row )

    # ===================================================================================

    def load_canonNameTable( self ):
        s = Store()
        self.canonicals = s.fb.get_canonicals()
        self.canonNameTable.update(self.canonicals)

    # -----------------------------------------------------------------------------------

    def load_canonFileTable( self ):
        s = Store()

        root = Path( s.conf.val( 'music_file_root' ) )
        dirs = s.conf.val( 'c2f_editable_music_folders' )  
        allfiles = []
        for dir in dirs:
            path = Path( root, dir )
            files = [ [str(p.relative_to( root ).as_posix() )] for p in path.rglob("*") if p.suffix.lower() == ".pdf"]
            allfiles += files
        allfiles = sorted( allfiles )
        self.canonFileTable.update( allfiles )

    # -----------------------------------------------------------------------------------
    def load_canonLinkTable( self ):
        s = Store()

        self.canon2file_path = Path( s.conf.val( 'c2f_editable_map' ) )

        self.link_table_data = []

        if not self.canon2file_path.is_file():
            s.conf.do_nastygram( 'c2f_editable_map', self.canon2file_path )
            return

        with open( self.canon2file_path, 'rt', encoding='utf-8' ) as canon2file_fd:     # /// WRW 23-Mar-2025 ENCODING
            for line in canon2file_fd:
                line = line.strip()
                canon, file = line.split( '|' )
                canon = canon.strip()
                file = file.strip()
                self.link_table_data.append( [ canon, file ] )

        self.link_table_data = sorted( self.link_table_data, key=lambda x: x[1] )
        self.canonLinkTable.update(self.link_table_data)

    # -----------------------------------------------------------------------------------
    #   WRW 1-June-2025 - Want to select in link table when click in name or file table
    #   Is this the last feature?

    @Slot( object )
    def slot_canon_name_table_cell_clicked( self, data ):
        val = data.canonical     
        self.selectTextLinkTable( val, True )

    @Slot( object )
    def slot_canon_file_table_cell_clicked( self, data ):
        val = data.file     
        self.selectTextLinkTable( val, False )

# -----------------------------------------------------------------------------------

if __name__ == "__main__":
    from bl_unit_test import UT
    from bl_style import StyleSheet

    s = UT()

    s.app = QApplication([])
    window = Canon2FileTab()
    window.setStyleSheet( StyleSheet )      # OK, Unit test
    window.show()
    s.app.exec()

# -----------------------------------------------------------------------------------
