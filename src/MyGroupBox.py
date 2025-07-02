#!/usr/bin/python
# ---------------------------------------------------------------------------
#   MyGroupBox - WRW 11-Jan-2025
#       Reduced to bare essentials just to add title, checkable and style to box.
#       Finally, got title in border. Trick was the 'left' style element
#       on QGroupBox::title.
# ---------------------------------------------------------------------------

import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGroupBox, QVBoxLayout, QLabel, QWidget
from PySide6.QtWidgets import QApplication, QMainWindow

from Store import Store

# ---------------------------------------------------------------------------

class MyGroupBox( QGroupBox ):
    def __init__( self, title, checkable ):
        super().__init__( title )
        s = Store()

        self.setCheckable( checkable )
        margin_top = "10px" if checkable else "8px"
        s.fb.registerGroupBox( self )

# ---------------------------------------------------------------------------

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        central_layout = QVBoxLayout(self.central_widget)               # Make an overall layout

        group_box = MyGroupBox( "Example of MyGroupBox", False )        # Make a group box
        if False:
            self.setStyleSheet("""          # OK, unit test
                QMainWindow {
                    background-color: #000040;
                    color: #ffffff;
                }
                MyGroupBox {
                    background-color: #800000;
                    color: #ffffff;
                }
                QLabel {
                    color: #ffffff;
                }

            """)

        gb_layout = QVBoxLayout()               # Make an internal layout for the group box content
        gb_layout.setAlignment(Qt.AlignTop)
        group_box.setLayout( gb_layout)         # Assign the internal layout to the group box

        gb_layout.addWidget( QLabel( "This is a label in MyGroupBox" ) )        # add widgets to the internal layout
        gb_layout.addWidget( QLabel( "This is a label in MyGroupBox" ) )

        central_layout.addWidget( group_box )   # add the group box to the central layout

        group_box = MyGroupBox( "Another Example of MyGroupBox", False )        # Make a group box
        central_layout.addWidget( group_box )   # add the group box to the central layout

# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from bl_unit_test import UT
    from bl_style import StyleSheet
    s = UT()

    s.app = QApplication(sys.argv)
    s.app.setStyleSheet( StyleSheet )   # OK, unit test
    s.window = MainWindow()
    s.window.setGeometry(100, 100, 400, 200)
    s.window.show()
    sys.exit(s.app.exec())

# -------------------------------------------------------------------------------------
