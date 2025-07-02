#!/usr/bin/python
# -----------------------------------------------------------------------------------
#   WRW 21-Mar-2025 - Placeholder for Scales and Chords someday.
# -----------------------------------------------------------------------------------

import re

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QVBoxLayout, QHBoxLayout, QWidget
from PySide6.QtWidgets import QPlainTextEdit

from Store import Store

# -----------------------------------------------------------------------------------

class AnalysisTab( QWidget ):

    def __init__(self ):
        super().__init__()
        s = Store()

        overall_layout = QVBoxLayout()

        # ----------------------------------------------------------------------

        layout = QHBoxLayout()
        layout.setContentsMargins( 8, 8, 8, 8 )
        layout.setAlignment(Qt.AlignLeft)

        txt = """Analysis tab is a placeholder for a future addition of tools for analyzing musical scales
                and chords."""

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
