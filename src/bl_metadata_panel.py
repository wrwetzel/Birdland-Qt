#!/usr/bin/python
# ------------------------------------------------------------------------------
#   WRW 15-Feb-2025
#   Metadata panel - this is the panel to the left of the PDF window in the Music Viewer tab.
# ------------------------------------------------------------------------------

from collections import namedtuple

from PySide6.QtCore import Qt

from PySide6.QtWidgets import QApplication
from PySide6.QtWidgets import QLabel, QVBoxLayout, QHBoxLayout, QWidget
from PySide6.QtWidgets import QSpacerItem, QSizePolicy
from PySide6.QtWidgets import QTextEdit

from MyGroupBox import MyGroupBox
from Store import Store

# ------------------------------------------------------------------------------
#   Slot names are generated from id_partial

Box = namedtuple('Box', [ 'id_partial', 'title', 'lines' ] )

Boxes = [
    Box( 'title', 'Title(s)', 4 ),                          # room for 4 lines in box, now stretch factor
    Box( 'canon', 'Canonical Name - Publisher', 2 ),
    Box( 'local', 'Local Name - Src', 2 ),
    Box( 'file',  'Media Filename', 4 ),
]

# ------------------------------------------------------------------------------

class BL_Metadata_Panel(QWidget):

    #   Only signals emitted by the Viewer Panel are the
    #       PDF controls. Currently they are in the PDF viewer
    #   There are a lot of slots for the display boxes.

    # sig_toc_cell_clicked = Signal( str, int, int )
    # sig_music_browser_clicked = Signal( QModelIndex )
    # sig_audio_browser_clicked = Signal( QModelIndex )

    def __init__( self ):
        super().__init__()
        s = Store()
        self.boxes = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins( 0, 0, 0, 0 )
        layout.setSpacing( 6 )

        # ----------------------------------------------------------------
        #   Originally viewer controls, now Pdf data,
        #   is different than the rest, code explicitly.

        group_box = MyGroupBox( "Media", False )
        # group_box = QGroupBox( "Media" )          # WRW 8-Apr-2025 - no need for MyGroupBox(). Yes there is, for dynamic styling
        group_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        gb_layout = QHBoxLayout()

        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        #   Bogus placeholder
        self.page = QLabel( '' )
        gb_layout.addWidget( self.page )

        self.sheet = QLabel( '' )
        gb_layout.addWidget( self.sheet )
        self.sheet.setAlignment(Qt.AlignRight)

        group_box.setLayout( gb_layout)
        layout.addWidget( group_box, 1 )

        # ----------------------------------------------------------------
        #   Do the rest in a loop

        for box in Boxes:
            gb = self.makeBox( box.id_partial, box.title, box.lines )
            layout.addWidget( gb )   # Don't need stretch when set Maximum explicitly

        spacer = QSpacerItem( 0, 0, QSizePolicy.Expanding, QSizePolicy.Expanding)     # Keep the text boxes from growing too big
        layout.addSpacerItem( spacer )

        s.sigman.register_slot( f"slot_update_meta_page", self.do_update_page )
        s.sigman.register_slot( f"slot_update_meta_sheet", self.do_update_sheet )

    # ----------------------------------------------------------------
    #   WRW 26-Feb-2025 - add document().setDocumentMargin(0) to reduce interior
    #       margin/buffer around text to eliminate scroll bars.
    #   WRW 8-Apr-2025 - After a LOT of thrashing about to prevent the text box from overflowing into the
    #       group-box border I finally realized I should set a stretch proportional to line count       
    #       when adding the group box to the layout. One issue was that I was testing on small screen.
    #       Got rid of fixed size text box based on line count and font metrics.
    #       Now too big on larger screens, really want to limit to some maximum.
    #       Back to original approach but setMaximumHeight(), not setFixedHeight(), now just what I want
    #       and no stretch applied above, Fixed vertical on group_box.

    def makeBox( self, id_partial, title, lines ):
        s = Store()

        # ----------------------------------------------------------------
        group_box = MyGroupBox( title, False )
        # group_box = QGroupBox( title )          # WRW 8-Apr-2025 - no need for MyGroupBox()
        group_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        gb_layout = QVBoxLayout()                                                          

        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

        text_edit = QTextEdit( )                # Don't use QPlainTextEdit() as want to use html.
        text_edit.setReadOnly(True)

        font_metrics = text_edit.fontMetrics()
        line_height = font_metrics.lineSpacing()  # Line spacing includes extra spacing
        total_height = line_height * lines + 2 * text_edit.frameWidth() + 8 # Add frame width, 8 for style margin.
        # text_edit.setMaximumHeight(total_height )
        text_edit.setMaximumHeight(total_height )

        text_edit.document().setDocumentMargin(0)   # See if this works better than style sheet. Yes, keep it.

        # text_edit.setFrameStyle(0)                # This did nothing
        # text_edit.setViewportMargins(0, 0, 0, 0)  # Likewise

        gb_layout.addWidget( text_edit )
        group_box.setLayout( gb_layout )

        self.boxes[ id_partial ] = text_edit       # Save the text box for updates below.

        # ----------------------------------------------------------------
        #   Here we generate slot names slot_update_meta_title, slot_update_meta_canon, etc., and
        #       register them with one slot, passing the partial name to the slot to obtain the
        #       text box identity for update.

        s.sigman.register_slot( f"slot_update_meta_{id_partial}", lambda x: self.do_update_text( id_partial, x ) )
        return group_box

    # ----------------------------------------------------------------

    def do_update_text( self, sig_partial, text ):

        # self.boxes[ sig_partial ].setText( text )
        text = text.replace( '\n', '<br>' )    # need separate lines for each title
        self.boxes[ sig_partial ].setHtml( f'<div style="text-align: right;">{text}</div>')

    def do_update_page( self, text ):
        self.page.setText( text )

    def do_update_sheet( self, text ):
        self.sheet.setText( text )

    # ----------------------------------------------------------------

# ------------------------------------------------------------------------------

if __name__ == "__main__":
    from bl_unit_test import UT
    from bl_style import StyleSheet

    s = UT()

    s.app = QApplication([])
    panel = BL_Metadata_Panel( )
    panel.setStyleSheet( StyleSheet )      # OK, unit test

    panel.show()
    s.app.exec()

# -------------------------------------------------------------------------------------
