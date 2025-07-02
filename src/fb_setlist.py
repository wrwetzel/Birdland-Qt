#!/usr/bin/python
# ---------------------------------------------------------------------------
#   fb_setlist.py

#   WRW 23 Jan 2022 - Setlist routines, pulled out of fb_utils.
#   Need to think about inheritance instead of passing pdf, fb, etc. into here

#   Save but not useful so far:
#       print( "/// qsize after update", self.window.thread_queue.qsize() )

#   WRW 4-Mar-2025 - Convert to pyside6 implementation with signals & slots.
#   WRW 19-Mar-2025 - Move setlist table content here from bl_main_window.py and later bl_main_tabbar.py.

# ---------------------------------------------------------------------------

from pathlib import Path
import json

from PySide6.QtCore import Signal, Qt, Slot

from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget
from PySide6.QtWidgets import QPushButton
from PySide6.QtWidgets import QCheckBox, QComboBox

from Store import Store
from bl_constants import MT             
from bl_tables import SetListTable
from MyGroupBox import MyGroupBox

# ---------------------------------------------------------------------------

class SetListTab( QWidget ):
    sig_setlist_add = Signal( str )
    sig_setlist_add_select = Signal( str )
    sig_setlist_manage_select = Signal( str )
    sig_setlist_move_up = Signal()
    sig_setlist_move_down = Signal()
    sig_setlist_delete = Signal()
    sig_setlist_save = Signal()
    sig_setlist_table_cell_clicked_full = Signal(object, int )
    sig_setlist_table_row_clicked_full = Signal( int, object, int )
    sig_setlist_edit_state_change = Signal( object )

    # ------------------------------------------------------------------------------------

    def register_signals( self ):
        Signals = (
            ( "sig_setlist_add", self.sig_setlist_add ),
            ( "sig_setlist_add_select", self.sig_setlist_add_select ),
            ( "sig_setlist_manage_select", self.sig_setlist_manage_select ),
            ( "sig_setlist_move_up", self.sig_setlist_move_up ),
            ( "sig_setlist_move_down", self.sig_setlist_move_down ),
            ( "sig_setlist_delete", self.sig_setlist_delete ),
            ( "sig_setlist_save", self.sig_setlist_save ),
            ( "sig_setlist_table_cell_clicked_full", self.sig_setlist_table_cell_clicked_full ),
            ( "sig_setlist_table_row_clicked_full", self.sig_setlist_table_row_clicked_full ),
            ( "sig_setlist_edit_state_change", self.sig_setlist_edit_state_change ),
        )

        s = Store()
        for sig_name, signal in Signals:
            s.sigman.register_signal( sig_name, signal )

    # ------------------------------------------------------------------------------------

    def register_slots( self ):
        Slots = (
            ("slot_setlist_update_manage_select",   self.slot_setlist_update_manage_select ),
            ("slot_setlist_select_manage_select",   self.slot_setlist_select_manage_select ),
            ("slot_setlist_table_cell_clicked",     self.slot_setlist_table_cell_clicked ),
            ("slot_setlist_table_row_clicked",      self.slot_setlist_table_row_clicked ),
            ("slot_setlist_edit_state_change",      self.slot_setlist_edit_state_change ),
        )

        s = Store()
        for slot_name, slot in Slots:
            s.sigman.register_slot( slot_name, slot )

    # ------------------------------------------------------------------------------------

    def __init__( self ):
        super().__init__()
        s = Store()

        self.register_signals()
        self.register_slots()

        # - - - - - - - - - - - - - - - - - - - - -

        sl_layout = QHBoxLayout()
        self.setLayout( sl_layout )                                                          
        sl_layout.setContentsMargins( 0, 0, 0, 0 )
        sl_layout.setSpacing( 0 )
        table = SetListTable()
        sl_layout.addWidget( table )

        # - - - - - - - - - - - - - - - - - - - - -

        gb_layout = QVBoxLayout( )
        gb_layout.setAlignment(Qt.AlignTop)

        t = QComboBox()
        t.setFixedHeight(28)
        # t.setCurrentIndex(-1)    # No selection initially
        # t.currentIndexChanged.connect( lambda x: s.sigman.emit( "sig_setlist_manage_select", x))
        t.currentIndexChanged.connect( self.on_setlist_manage_select )
        gb_layout.addWidget( t )
        self.setlist_manage_select = t

        self.editSetList = QCheckBox("Edit Set List")
        gb_layout.addWidget( self.editSetList )
        # self.editSetList.checkbox.toggled.connect( self.on_setlist_edit_toggle )
        # self.editSetList.checkStateChanged.connect( self.on_setlist_edit_state_change )
        self.editSetList.checkStateChanged.connect( lambda x: s.sigman.emit( "sig_setlist_edit_state_change", x ))

        b = QPushButton( "Move Up" )
        b.clicked.connect( lambda: s.sigman.emit( "sig_setlist_move_up" ))                               
        b.setEnabled(False)
        gb_layout.addWidget( b )
        self.setlist_move_up = b

        b = QPushButton( "Move Down" )
        b.clicked.connect( lambda: s.sigman.emit( "sig_setlist_move_down" ))
        b.setEnabled(False)
        gb_layout.addWidget( b )
        self.setlist_move_down = b

        b = QPushButton( "Delete" )
        b.clicked.connect( lambda: s.sigman.emit( "sig_setlist_delete" ))
        b.setEnabled(False)
        gb_layout.addWidget( b )
        self.setlist_delete = b

        b = QPushButton( "Save Set List" )
        b.clicked.connect( lambda: s.sigman.emit( "sig_setlist_save" ))
        b.setEnabled(False)
        gb_layout.addWidget( b )
        self.setlist_save = b

        group_box = MyGroupBox( "Manage Set List", False )
        group_box.setLayout( gb_layout )
        sl_layout.addWidget(group_box)

    # -------------------------------------------------------------------

    @Slot( object )
    def slot_setlist_edit_state_change(self, editFlag ):
        s = Store()
        if editFlag == Qt.Checked:
            self.setlist_move_up.setEnabled(True)
            self.setlist_move_down.setEnabled(True)
            self.setlist_delete.setEnabled(True)
            self.setlist_save.setEnabled(True)
        else:
            self.setlist_move_up.setEnabled(False)
            self.setlist_move_down.setEnabled(False)
            self.setlist_delete.setEnabled(False)
            self.setlist_save.setEnabled(False)

    # -------------------------------------------------------------------
    @Slot( object )
    def on_setlist_manage_select( self, index ):
        s = Store()
        id = self.setlist_manage_select.itemText(index)
        s.sigman.emit( "sig_setlist_manage_select", id )        # Emit with name, not index

    # -------------------------------------------------------------------

    @Slot(int)
    def OMIT_on_setlist_edit_state_change( self, editFlag ):
        s = Store()
        print( "/// edit changed", editFlag )
        # editFlag = self.editSetList.isChecked()
        # s.sigman.emit( "sig_setlist_manage_select", id )        # Emit with name, not index

    # -------------------------------------------------------------------

    @Slot( object )
    def slot_setlist_update_manage_select( self, data ):
        t = self.setlist_manage_select
        t.blockSignals(True)          # signal emitted by clear() / addItems() causing lots of confusion
        t.clear()
        t.addItems( data )
        t.blockSignals(False)

    # -------------------------------------------------------------------
    #   User made selection in Setlist Manage combo box.

    @Slot( object )
    def slot_setlist_select_manage_select( self, id ):
        t = self.setlist_manage_select
        t.blockSignals(True)                                                                            
        index = t.findText( id )
        if id != -1:
            t.setCurrentIndex(index)
        t.blockSignals(False)

    # -------------------------------------------------------------------
    #   data is from setlist table.

    @Slot( object, int )
    def slot_setlist_table_cell_clicked( self, data ):
        s = Store()
        editFlag = self.editSetList.isChecked()
        s.sigman.emit( "sig_setlist_table_cell_clicked_full", data, editFlag )

    # -------------------------------------------------------------------
    #   WRW 7-Mar-2025 - slightly new approach of including row number in
    #       emission at same time selecting the entire row for visuals.

    @Slot( int, object, int )
    def slot_setlist_table_row_clicked( self, row, data ):
        s = Store()
        editFlag = self.editSetList.isChecked()
        s.sigman.emit( "sig_setlist_table_row_clicked_full", row, data, editFlag )

    # ------------------------------------------------------------------------------

    def resizeEvent(self, event):
        """Recalculate column widths on window resize."""
        super().resizeEvent(event)

# ---------------------------------------------------------------------------

class SetList(QWidget):

    # --------------------------------------------------------------------

    sig_setlist_update_add_select = Signal( object )
    sig_setlist_select_add_select = Signal( str )
    sig_setlist_update_manage_select = Signal( object )
    sig_setlist_select_manage_select = Signal( object )
    sig_setlist_current_data = Signal( object )

    def __init__( self ):
        super().__init__()
        s = Store()
        self.setlist = None
        self.current_setlist_name = None        # /// 'Default'?
        self.current_setlist_table = None
        self.current_data = None                # Sent from click in music table in case needed to add to setlist
      # self.setlist_edit_row_data = None       # Data for selected row in setlist table.
        self.setlist_selected_row = None        # WRW 7-Apr-2025 - forgot to initialize, issue if up/down/delete before selecting row

        self.register_signals()
        self.register_slots()

    # ------------------------------------------------------------------------------------

    def register_signals( self ):
        Signals = (
            ( "sig_setlist_update_add_select",      self.sig_setlist_update_add_select ),
            ( "sig_setlist_select_add_select",      self.sig_setlist_select_add_select ),
            ( "sig_setlist_update_manage_select",   self.sig_setlist_update_manage_select ),
            ( "sig_setlist_select_manage_select",   self.sig_setlist_select_manage_select ),
            ( "sig_setlist_current_data",           self.sig_setlist_current_data ),
        )

        s = Store()
        for sig_name, signal in Signals:
            s.sigman.register_signal( sig_name, signal )

    # ------------------------------------------------------------------------------------

    def register_slots( self ):
        Slots = (
            ( "slot_setlist_add",                     self.setlist_add ),
            ( "slot_setlist_add_select",              self.setlist_add_select ),
            ( "slot_setlist_manage_select",           self.setlist_manage_select ),
            ( "slot_setlist_move_up",                 self.setlist_move_up ),
            ( "slot_setlist_move_down",               self.setlist_move_down ),
            ( "slot_setlist_delete",                  self.setlist_delete ),
            ( "slot_setlist_save",                    self.setlist_savex ),
            ( "slot_setlist_current_data",            self.setlist_current_data ),
            ( "slot_setlist_table_cell_clicked_full", self.setlist_table_cell_clicked_full ),
            ( "slot_setlist_table_row_clicked_full",  self.setlist_table_row_clicked_full ),
        )

        s = Store()
        for slot_name, slot in Slots:
            s.sigman.register_slot( slot_name, slot )

    # ------------------------------------------------------------------------------------
    #   Initialize combo boxes and setlist table after UI is built.

    def initialize( self ):
        s = Store()

        sl_name = self.load_setlist_file()
        sl_names = self.get_sl_names()

        s.sigman.emit( "sig_setlist_update_add_select", sl_names )
        s.sigman.emit( "sig_setlist_update_manage_select", sl_names )

        s.sigman.emit( "sig_setlist_select_add_select", sl_name )
        s.sigman.emit( "sig_setlist_select_manage_select", sl_name )

        self.show_sl_by_name( sl_name )

    # ------------------------------------------------------------------------------------
    #   Setlist Actions
    # ------------------------------------------------------------------------------------
    #   Add item to setlist
    
    def setlist_add( self, sl_name ):
        s = Store()
        # print( "/// setlist_add", sl_name )

        self.current_setlist_name = sl_name          # WRW 30 Mar 2022 - To correct funny.
        data = self.current_data

        # metadata = self.meta.get_info()
        # print( f"/// At add, titles: {metadata[ 'titles' ]}, canonical: {metadata[ 'canonical']}, page: {metadata['page']}" )

        if hasattr( data, 'file' ):
            file = data.file

            # ----------------------------------------------
            #   Avoid pathological case.

            if file in [ s.Const.DocFile, s.Const.QuickStartFile ]:
                s.msgWarn( "Stop fooling around.\nCan't add the documentation to a setlist." )
                return True

            # ----------------------------------------------
            #   Add to self.setlist internal data structure.
            #   May have multiple titles on one page, add them all.

            if hasattr( data, 'titles'):
                for title in data.titles:
                    self.setlist_save_to_table( sl_name, title, data.canonical, data.src, data.local, data.sheet, data.page, data.file, data.mode )
            else:
                self.setlist_save_to_table( sl_name, None. data.canonical, data.src, data.local, data.sheet, data.page, data.file, data.mode )

            # -------------------------------------------------------
            #   Update setlist table and select last item added.
            #   Get data from internal data structure for the setlist indicated by 'sl_name'.
            #   WRW 6-Mar-2025 - include all data in setlist table, not just visible data.

            sl_list = self.get_sl_by_name( sl_name )
            if sl_list:
                values = [ [ x[ 'title' ], x[ 'canonical' ], x[ 'file' ], x[ 'sheet' ],
                             x[ 'page' ],  x[ 'src' ],       x[ 'local'], x[ 'mode' ]
                         ] for x in sl_list ]

                # print( "/// before sig_setlist_table_data, None" )
                s.sigman.emit( "sig_setlist_table_data", values, None )
                # print( "/// after sig_setlist_table_data, None" )

            self.setlist_save( [ title for title in data.titles ] )

            # -------------------------------------------------------
            #   After addition make the added-to list current and selected in the Combo menus.
            #   Show the setlist table.

            s.sigman.emit( "sig_setlist_select_add_select", sl_name )
            s.sigman.emit( "sig_setlist_select_manage_select", sl_name )
            s.selectTab( MT.SetList )

    # ------------------------------------------------------------------------------------
    #   'cell_clicked_full' generated in main window, same as 'click' with addition of editFlag.

    def setlist_table_cell_clicked_full( self, data, editFlag ):
        s = Store()
        # print( "/// setlist_table_cell_clicekd_full" )

        if not editFlag:        # Don't display file when editing.
            if data:
                if data.file:   # Nothing to show if no file
                    path = Path( s.conf.val( 'music_file_root' ), data.file )           
                    if data.mode == 'Fi':

                        # s.pdf.showFi( file=full_path, title=data.title, alt_file=data.file,
                        #               page=data.page, sheet=data.sheet,
                        #               canonical=data.canonical, local=data.local, src=data.src )
                        # args = {
                        #     'file' : full_path, 'title' : data.title, 'alt_file' : data.file,
                        #     'page' : data.page, 'sheet' : data.sheet, 'canonical' : data.canonical,
                        #     'local' : data.local, 'src' : data.src
                        # }

                        s.sigman.emit( "sig_showFi", str(path), data )
                        s.selectTab( MT.Viewer )

                    elif data.mode == 'Fs':
                        # s.pdf.showFs( file=path, relpath=data.file )
                        s.sigman.emit( "sig_showFs", path, data.file )
                        s.selectTab( MT.Viewer )

                    elif data.mode == 'Ft':
                        print( "ERROR: Unexpected data.mode '{data.mode}' at setlist_table_cell_clicked_full" )

                    else:
                        print( f"PROGRAM ERROR: Unexpected data.mode '{data.mode}' at setlist_table_cell_clicked_full" )

                else:
                    print( f"ERROR: No music file for title: {data.title}, canonical {data.canonical} at setlist_table_cell_clicked_full()" )

            else:
                print( "PROGRAM ERROR: No data at setlist_table_cell_clicked_full()" )

    # ------------------------------------------------------------------------------------
    #   'row_clicked_full' generated in main window, same as 'click' with addition of editFlag.

    @Slot( int, object, int )
    def setlist_table_row_clicked_full( self, row, data, editFlag ):
        # print( "/// setlist_table_row_clicked_full" )
        s = Store()
        self.setlist_selected_row = row         # Save even if non-edit in case user then goes into edit mode.
        # if editFlag:
            # self.setlist_edit_row_data = data
            # print( "setlist_table_row_clicked_full:", row )

    # ------------------------------------------------------------------------------------
    #   Add-to-Setlist combo box changed,                                                  
    #   Yes, setting current index in add-select combo box.

    def setlist_add_select( self, id ):
        s = Store()
        # print( "/// add_select", id )
        s.sigman.emit( "sig_setlist_select_add_select", id )

        # /// ? self.current_setlist_name = id
    
    # ------------------------------------------------------------------------------------
    #   Manage-Setlist combo box changed,                                                  
    #   Yes, setting current index in manage-select combo box.

    def setlist_manage_select( self, sl_name ):
        s = Store()
        # print( "/// manage_select", sl_name )
        self.show_sl_by_name( sl_name )
        s.sigman.emit( "sig_setlist_select_manage_select", sl_name )
    
    # ------------------------------------------------------------------------------------
    #   Move the selected row in the setlist table up one position.

    def setlist_move_up(self):
        s = Store()
        sl = self.get_current_sl()
        if not sl:
            return     

        index = self.setlist_selected_row      

        if index is None:
            index = len(sl) - 1

        nindex = index - 1

        if nindex >= 0 and sl:
            item = sl.pop( index )
            sl.insert( nindex, item )

            data = [ [ x[ 'title' ], x[ 'canonical' ], x[ 'file' ], x[ 'sheet' ],
                       x[ 'page' ],  x[ 'src' ],       x[ 'local'], x[ 'mode' ]
                   ] for x in sl ]

            s.sigman.emit( "sig_setlist_table_data", data, nindex )
            self.setlist_selected_row = nindex

    # ----------------------------------------------------------------

    def setlist_move_down(self):
        s = Store()
        sl = self.get_current_sl()
        if not sl:
            return     

        index = self.setlist_selected_row      

        if index is None:
            index = len( self.setlist ) -1

        nindex = index + 1

        if nindex < len( sl ):
            item = sl.pop( index )
            sl.insert( nindex, item )

            data = [ [ x[ 'title' ], x[ 'canonical' ], x[ 'file' ], x[ 'sheet' ],
                       x[ 'page' ],  x[ 'src' ],       x[ 'local'], x[ 'mode' ]
                   ] for x in sl ]

            s.sigman.emit( "sig_setlist_table_data", data, nindex )
            self.setlist_selected_row = nindex

    # ----------------------------------------------------------------

    def setlist_delete(self):
        s = Store()
        sl = self.get_current_sl()
        if not sl:
            return     

        index = self.setlist_selected_row      
        if index is None:
            index = 0

        sl.pop( index )
        if index >= len( sl ):
            index = len(sl) - 1

        data = [ [ x[ 'title' ], x[ 'canonical' ], x[ 'file' ], x[ 'sheet' ],
                   x[ 'page' ],  x[ 'src' ],       x[ 'local'], x[ 'mode' ]
                 ] for x in sl ]

        if data:
            s.sigman.emit( "sig_setlist_table_data", data, index )
            self.setlist_selected_row = index
        else:
            s.sigman.emit( "sig_setlist_table_data", [], None )


    # ----------------------------------------------------------------

    def setlist_savex(self):
        self.setlist_save( [] )

    # ---------------------------------------------------------------------------

    #   User clicked in music table, save the data for possible addition to setlist
    #   data is an array of named attributes from getDataNew() in bl_tables.py

    @Slot( object )
    def setlist_current_data( self, data ):
        self.current_data = data

    # ------------------------------------------------------------------------------------
    #   Must maintain setlist data structure separate from setlist table.
    #   WRW 5-Mar-2025 That is a vestige of pysimplegui but keep it for now, 
    #       likely forever, works fine.

    def setlist_save_to_table( self, id, title, canonical, src, local, sheet, page, file, mode ):
        s = Store()

        if not self.setlist:
            self.setlist = {}

        if id not in self.setlist:
            self.setlist[ id ] = []

            #   WRW 25 Jan 2022 - Update setlist Combo box menus with new id.

            sl_names = self.get_sl_names()

            s.sigman.emit( "sig_setlist_update_add_select", sl_names )
            s.sigman.emit( "sig_setlist_update_manage_select", sl_names )

            s.sigman.emit( "sig_setlist_select_add_select", self.current_setlist_name )
            s.sigman.emit( "sig_setlist_select_manage_select", self.current_setlist_name )

        self.setlist[ id ].append( { 'title' : title, 
                                     'canonical' : canonical,
                                     'src' : src,
                                     'local' : local,
                                     'sheet' : sheet,
                                     'page' : page,
                                     'mode' : mode,
                                     'file' : file } )
    
    # ---------------------------------------------------

    def get_sl_by_name( self, sl_name ):
        if not self.setlist or sl_name not in self.setlist:
            return None
        else:
            return self.setlist[ sl_name ]

    # ---------------------------------------------------

    def get_current_sl( self ):
        return self.get_sl_by_name( self.current_setlist_name )

    # ---------------------------------------------------
    def load_setlist_file( self ):
        s = Store()
        setlist_path = Path( s.conf.val( 'setlistfile' ))
        if setlist_path.is_file():
            try:
                t = json.loads( setlist_path.read_text() )
                self.setlist = t[ 'setlist' ]
                self.current_setlist_name = t[ 'current' ]
                return t[ 'current' ]
            except:
                self.setlist = []
                self.current_setlist_name = 'Default'
                return 'Default'
        else:
            self.setlist = []
            self.current_setlist_name = 'Default'
            return 'Default'

    # ---------------------------------------------------
    #   WRW 30 Mar 2022 - Add titles to function for more sensible message.

    def setlist_save( self, titles ):
        s = Store()
        setlist_path = Path( s.conf.val( 'setlistfile' ))
        t = { 'current' : self.current_setlist_name, 'setlist' : self.setlist }
        setlist_path.write_text( json.dumps( t, indent=2 ) )

        # ----------------------------------------------
        #   Confirmation of save to usr.

        t = [ f"'{x}'" for x in titles ]
        txt = f"""
        Saved title(s): {', '.join( t )}\n
        To setlist: '{self.current_setlist_name}'\n
        In file: '{setlist_path}'
        """
        # s.conf.do_popup( txt )
        s.msgInfo( txt )

    # ---------------------------------------------------
    #   Show current setlist in setlist tab.

    def show_sl_by_name( self, sl_name ):
        # print( "setlist_show", sl_name )
        s = Store()
        self.current_setlist_name = sl_name
        sl = self.get_sl_by_name( sl_name )

        if sl:
            data = [ [ x[ 'title' ], x[ 'canonical' ], x[ 'file' ], x[ 'sheet' ],
                       x[ 'page' ],  x[ 'src' ],       x[ 'local'], x[ 'mode' ]
                   ] for x in sl ]

            self.current_setlist_table = data
            s.sigman.emit( "sig_setlist_table_data", data, None )

        else:
            s.sigman.emit( "sig_setlist_table_data", [], None )

    # ---------------------------------------------------
    def get_sl_names( self ):
        return [ x for x in self.setlist ]

    # ---------------------------------------------------
    def OMIT_setlist_get_item( self, index ):
        return self.setlist[ self.current_setlist_name ][ index ]

    # ---------------------------------------------------
    def OMIT_get_current_sl_len( self ):
        return len( self.setlist[ self.current_setlist_name] )

    # ----------------------------------------------------------------------------
