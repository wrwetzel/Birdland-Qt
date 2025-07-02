#!/usr/bin/python
# -----------------------------------------------------------------------------------
#   WRW 21-Mar-2025 - UI and supporting code for 'Edit Canonical->File' tab
# -----------------------------------------------------------------------------------

#   Link Canonical to File   Clear One Link   Save   Find: lineedit
#   label
#   table: Canonical Name   table: Canonical Name  File Name

# -----------------------------------------------------------------------------------

import re

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QVBoxLayout, QHBoxLayout, QWidget
from PySide6.QtWidgets import QPlainTextEdit

from Store import Store

# -----------------------------------------------------------------------------------

class IndexManagementTab( QWidget ):

    def __init__(self ):
        super().__init__()
        s = Store()

        overall_layout = QVBoxLayout()

        # ----------------------------------------------------------------------

        layout = QHBoxLayout()
        layout.setContentsMargins( 8, 8, 8, 8 )
        layout.setAlignment(Qt.AlignLeft)

        txt = """The Index Management feature supports development of new indexes and editing of existing
                    indexes. The feature is included in the PySimpleGui/FreeSimpleGui version of Birdland 
                    and will be available in the full version of Birdland-Qt when ported sometime in the future."""

        txt = re.sub( ' +', ' ', txt )
        # txt = re.sub( '\n ', '\n', txt )
        txt = re.sub( '\n', '', txt )

        e = QPlainTextEdit()
        e.setReadOnly(True)
        layout.addWidget( e )
        e.insertPlainText( txt )

        layout.addWidget( e )

        # ----------------------------------------------------------------------

        overall_layout.addLayout( layout )
        self.setLayout( overall_layout )

        # ----------------------------------------------------------------------

# -----------------------------------------------------------------------------------
if __name__ == "__main__":
    from bl_style import StyleSheet
    s = Store()
    app = QApplication([])
    window = IndexManagementTab()
    window.setStyleSheet( StyleSheet )      # OK, unit test
    window.show()
    app.exec()

# -----------------------------------------------------------------------------------
