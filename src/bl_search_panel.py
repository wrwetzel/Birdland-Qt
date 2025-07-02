#!/usr/bin/python
# ----------------------------------------------------------------------------
#   WRW 13-Jan-2025 - Music search panel widget
#   WRW 13-Feb-2025 - Migrate away from ObjectNames to object storage in instance.

# ----------------------------------------------------------------------------

from PySide6.QtCore import Signal, Qt, Slot
from PySide6.QtWidgets import QApplication, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QLineEdit, QWidget
from PySide6.QtWidgets import QSizePolicy, QCheckBox, QRadioButton, QComboBox, QButtonGroup
from PySide6.QtWidgets import QSpacerItem
from MyGroupBox import MyGroupBox
from Store import Store

# ----------------------------------------------------------------------------

class BL_Search_Panel(QWidget):
    button_clicked_signal = Signal(str)
    return_pressed_signal = Signal(str, str, str, str, str, str, str, int, int, int, int, int )     # Ouch!
    stop_media_signal = Signal()
    src_offset_changed = Signal( int )
    add_title_to_setlist = Signal()

    def __init__(self ):
        super().__init__()
        s = Store()

        s.sigman.register_slot( f"slot_update_src_offset", self.slot_update_src_offset )
        s.sigman.register_slot( f"slot_set_src_offset_visible", self.set_src_offset_visible )
        s.sigman.register_slot( f"slot_setlist_update_add_select", self.slot_setlist_update_add_select )
        s.sigman.register_slot( f"slot_setlist_select_add_select", self.slot_setlist_select_add_select )
        s.sigman.register_slot( f"slot_title_focus", self.slot_title_focus )

        # -----------------------------------------------------------------------

        row1_layout = QHBoxLayout()
        row2_layout = QHBoxLayout()

        # ================================================================================
        #   Row 1
        # ================================================================================

        gb_layout = QHBoxLayout( )
        gb_layout.setAlignment(Qt.AlignLeft)

        t = QLabel("Title:", self)
        t.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        gb_layout.addWidget(t)

        self.title= QLineEdit()
        self.title.setObjectName("titleLineEdit")
        self.title.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)      # /// EXPLORING
        self.title.setFixedWidth( 150 )
        self.title.setFocus()               # WRW 20-May-2025 - had this on label, not QLineEdit, stil NG.

        gb_layout.addWidget( self.title  )
        self.title.returnPressed.connect(self.on_return_pressed)

        if False:                                   # Styled in bl_style.py
            self.title.setStyleSheet( """           /* OK if False: out */
                QLineEdit {
                    background-color: #008000;
                    color: #ffffff;
                }
            """ )

        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

        group_box = MyGroupBox( "Search Indexes, Media Filenames", False )
        group_box.setLayout( gb_layout )
        row1_layout.addWidget(group_box)

        # -----------------------------------------------------------------------

        gb_layout = QHBoxLayout()
        gb_layout.setAlignment(Qt.AlignLeft)

        t = QLabel("Composer:", self)
        t.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        gb_layout.addWidget(t)

        self.composer = QLineEdit()
        self.composer.setObjectName("composer")
        self.composer.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)      # /// EXPLORING
        gb_layout.addWidget( self.composer  )
        self.composer.returnPressed.connect(self.on_return_pressed)

        t = QLabel("Lyricist:", self)
        t.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        gb_layout.addWidget(t)

        self.lyricist = QLineEdit()
        self.lyricist .setObjectName("lyricist")
        self.lyricist.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)      # /// EXPLORING
        gb_layout.addWidget( self.lyricist  )
        self.lyricist.returnPressed.connect(self.on_return_pressed)

        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

        group_box = MyGroupBox( "Search Music Index", False )
        group_box.setLayout( gb_layout )
        row1_layout.addWidget(group_box)

        # -----------------------------------------------------------------------

        gb_layout = QHBoxLayout()
        gb_layout.setAlignment(Qt.AlignLeft)

        t = QLabel("Artist:", self)
        t.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        gb_layout.addWidget(t)

        self.artist = QLineEdit()
        self.artist .setObjectName("artist")
        self.artist.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)      # /// EXPLORING
        gb_layout.addWidget( self.artist  )
        self.artist .returnPressed.connect(self.on_return_pressed)

        t = QLabel("Album:", self)
        t.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        gb_layout.addWidget(t)

        self.album = QLineEdit()
        self.album .setObjectName("album")
        self.album.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)      # /// EXPLORING
        gb_layout.addWidget( self.album  )
        self.album.returnPressed.connect(self.on_return_pressed)

        self.alsoSearchCheckBox = QCheckBox("Also Search Audio Title in Music")
        self.alsoSearchCheckBox.setChecked(True)
        gb_layout.addWidget( self.alsoSearchCheckBox  )

        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

        group_box = MyGroupBox( "Search Audio Index for Artist/Album, ChordPro Index for Artist", False )
        group_box.setLayout( gb_layout )
        row1_layout.addWidget(group_box)

        # -----------------------------------------------------------------------
        #   Src for offsets ComboBox

        gb_layout = QHBoxLayout()
        gb_layout.setAlignment(Qt.AlignLeft)

        # layout.addSpacerItem(QSpacerItem(0, 10))
        # row1_layout.addWidget( QLabel( "Select src for offsets for selected music file:" ))
        # gb_layout.addWidget( QLabel( "Src:" ))

        self.src_offset = QComboBox()
        self.src_offset.setFixedHeight(28)
        self.src_offset.setObjectName("srcOffset")
        self.src_offset.setCurrentIndex(-1)  
        self.src_offset.currentIndexChanged.connect( lambda x: s.sigman.emit( "sig_src_offset_changed", x))
        gb_layout.addWidget( self.src_offset )

        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

        self.src_group_box = MyGroupBox( "Src", False )
        self.src_group_box.setLayout( gb_layout )
        self.src_group_box.setVisible( False )          # Only put it on as needed
        row1_layout.addWidget(self.src_group_box)

        # -----------------------------------------------------------------------

        spacer = QSpacerItem( 0, 0, QSizePolicy.Expanding, QSizePolicy.Fixed)
        row1_layout.addSpacerItem( spacer )

        # ================================================================================
        #   Row 2
        # ================================================================================

        gb_layout = QHBoxLayout( )
        gb_layout.setAlignment(Qt.AlignLeft)

        b = QPushButton( "Search" )
        # row2_layout.addWidget( b )
        gb_layout.addWidget( b )
        b.clicked.connect(self.on_return_pressed)     # Search is same as return

        b = QPushButton( "Clear" )
        # row2_layout.addWidget( b )
        gb_layout.addWidget( b )
        b.clicked.connect(self.on_clear_clicked)                               

        b = QPushButton( "Stop Media" )
        b.clicked.connect( lambda: s.sigman.emit( "sig_stop_media" ))
        stop_media_button = b
        # row2_layout.addWidget( b )
        gb_layout.addWidget( b )

        # b = QPushButton( "Close PDF" )
        # row2_layout.addWidget( b )

        b = QPushButton( "Exit" )
        # row2_layout.addWidget( b )
        b.clicked.connect(lambda: ( s.app.quit() ))
        gb_layout.addWidget( b )

        group_box = MyGroupBox( "Controls", False )
        group_box.setLayout( gb_layout )
        row2_layout.addWidget(group_box)

        # -----------------------------------------------------------------------
        xdup_group = QButtonGroup( self )
        xdup_group.idClicked.connect(self.on_return_pressed )

        gb_layout = QHBoxLayout( )
        gb_layout.setAlignment(Qt.AlignLeft)

        self.xdup_none = b = QRadioButton( "None" )
        b.setChecked(True)
        xdup_group.addButton(b)
        gb_layout.addWidget(b)

        self.xdup_titles = b = QRadioButton( "Titles" )
        xdup_group.addButton(b)
        gb_layout.addWidget(b)

        self.xdup_canonicals = b = QRadioButton( "Canonicals" )
        xdup_group.addButton(b)
        gb_layout.addWidget(b)

        self.xdup_srcs = b = QRadioButton( "Srcs" )
        xdup_group.addButton(b)
        gb_layout.addWidget(b)

        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

        group_box = MyGroupBox( "Exclude Duplicates", False )
        group_box.setLayout( gb_layout )
        row2_layout.addWidget(group_box)

        # -----------------------------------------------------------------------

        gb_layout = QHBoxLayout( )
        gb_layout.setAlignment(Qt.AlignLeft)

        l = QLabel( "Src:" )
        l.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        gb_layout.addWidget(l)

        self.src = e = QLineEdit()
        gb_layout.addWidget(e)
        e.returnPressed.connect(self.on_return_pressed)
        e.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)      # /// EXPLORING

        l = QLabel( "Canonical:" )
        l.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        gb_layout.addWidget(l)

        self.canonical = e = QLineEdit()
        e.returnPressed.connect(self.on_return_pressed)
        gb_layout.addWidget(e)
        e.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)      # /// EXPLORING

        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

        group_box = MyGroupBox( "Filter Music Index By", False )
        group_box.setLayout( gb_layout )
        row2_layout.addWidget(group_box)

        # -----------------------------------------------------------------------

        gb_layout = QHBoxLayout( )
        gb_layout.setAlignment(Qt.AlignLeft)

        l = QPushButton( "Add" )
        l.clicked.connect( self.on_setlist_add )
        gb_layout.addWidget(l)

        c = QComboBox()
        c.setFixedHeight(28)
        c.setEditable(True)      # Accept user input for new setlist name
        c.currentIndexChanged.connect( self.on_setlist_add_select )
        gb_layout.addWidget(c)
        self.setlist_add_select = c

        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

        group_box = MyGroupBox( "Add Title to Setlist", False )
        group_box.setLayout( gb_layout )
        row2_layout.addWidget(group_box)

        # -----------------------------------------------------------------------

        spacer = QSpacerItem( 0, 0, QSizePolicy.Expanding, QSizePolicy.Fixed)
        row2_layout.addSpacerItem( spacer )

        # ================================================================================
        combined_layout = QVBoxLayout(self)
        combined_layout.addLayout( row1_layout )
        combined_layout.addLayout( row2_layout )

        # -------------------------------------------------------------------------------
        #   WRW 4-Apr-2025 - Moved to bottom so widgets are defined, test inspection with
        #   Title box and Stop Media button.

        s.sigman.register_signal( "sig_search_box_return_pressed", self.return_pressed_signal, self.title )
        s.sigman.register_signal( "sig_stop_media", self.stop_media_signal, stop_media_button )
        # s.sigman.register_signal( "sig_src_offset_changed", self.src_offset_changed, self.src_offset )
        s.sigman.register_signal( "sig_src_offset_changed", self.src_offset_changed )
        s.sigman.register_signal( "sig_add_title_to_setlist", self.add_title_to_setlist, self.setlist_add_select )

    # ----------------------------------------------------------------------

    def getTitle( self ):
        return self.title.text()

    def getComposer( self ):
        return self.composer.text()

    def getLyricist( self ):
        return self.lyricist.text()

    def getArtist( self ):
        return self.artist.text()

    def getAlbum( self ):
        return self.album.text()

    def getAlsoSearch( self ):
        return self.alsoSearchCheckBox.isChecked()

    # ----------------------------------------------------------------------

    @Slot( int )
    def set_src_offset_visible( self, vis ):
        self.src_group_box.setVisible( vis )

    # ----------------------------------------------------------------------
    #   Local signal catcher, emit signal

    @Slot()
    def on_button_click(self):
        text = self.getTitle()
        self.button_clicked_signal.emit( text )

    # --------------------------------------------------
    @Slot()
    def on_return_pressed(self):
        s = Store()
        join_flag = self.alsoSearchCheckBox.isChecked()

        s.sigman.emit( "sig_search_box_return_pressed",
                          self.title.text(), self.composer.text(), self.lyricist.text(),
                          self.artist.text(), self.album.text(), 
                          self.src.text(), self.canonical.text(),
                          self.xdup_none.isChecked(),
                          self.xdup_titles.isChecked(),
                          self.xdup_canonicals.isChecked(),
                          self.xdup_srcs.isChecked(),
                          join_flag )

    # --------------------------------------------------
    @Slot()
    def on_clear_clicked( self ):
        self.title.clear()
        self.composer.clear()
        self.lyricist.clear()
        self.artist.clear()
        self.album.clear()  
        self.src.clear()
        self.canonical.clear()

    # --------------------------------------------------
    @Slot(object)
    def slot_update_src_offset( self, data ):
        self.src_offset.blockSignals(True)          # signal emitted by clear() / addItems() causing lots of confusion
        self.src_offset.clear()
        self.src_offset.addItems( data )
        self.src_offset.blockSignals(False)

    # --------------------------------------------------
    #   User made a selection in Setlist Add combo box

    @Slot( object )
    def on_setlist_add_select( self, index ):
        s = Store()
        id = self.setlist_add_select.itemText(index)
        s.sigman.emit( "sig_setlist_add_select", id )        # Emit with name, not index

    # --------------------------------------------------
    #   Set new list of data in the Add-Select QComboBox

    @Slot(object)
    def slot_setlist_update_add_select( self, data ):
        t = self.setlist_add_select    
        t.blockSignals(True)          # signal emitted by clear() / addItems() causing lots of confusion
        t.clear()
        t.addItems( data )
        t.blockSignals(False)

    # --------------------------------------------------
    #   User clicked Add button

    @Slot()
    def on_setlist_add( self ):
        s = Store()
        t = self.setlist_add_select    
        id = t.currentText()
        s.sigman.emit( 'sig_setlist_add', id )

    # --------------------------------------------------
    #   Set the current selection in the Add-Select QComboBox given the selected text.

    @Slot(object)
    def slot_setlist_select_add_select( self, id ):
        t = self.setlist_add_select    
        t.blockSignals(True)                                                                            
        index = t.findText( id )
        if id != -1:
            t.setCurrentIndex(index)
        t.blockSignals(False)

    #   WRW 20-May-2025 - Try to set very late in startup sequence on signal from birdland_qt.py

    @Slot()
    def slot_title_focus( self ):
        self.title.setFocus()                                                                             

# ----------------------------------------------------------------------------

if __name__ == "__main__":
    from bl_unit_test import UT
    from bl_style import StyleSheet

    s = UT()

    def return_pressed( text ):
        print( f"Return pressed! {text}")

    s.app = QApplication([])
    panel = BL_Search_Panel()
    panel.setStyleSheet( StyleSheet )      # OK, unit test

    panel.return_pressed_signal.connect( return_pressed )

    panel.show()
    s.app.exec()

# -------------------------------------------------------------------------------------
