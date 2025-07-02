#!/usr/bin/python
# -----------------------------------------------------------------------
#   bl_title_panel.py
# -----------------------------------------------------------------------

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QSizePolicy         
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QHBoxLayout, QSpacerItem

from Store import Store

class Title_Panel( QWidget ):
    def __init__( self ):
        super().__init__()
        s = Store()

        spacer = QSpacerItem( 100, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)
        layout = QHBoxLayout()
        layout.setContentsMargins( 0, 0, 0, 0 )
        layout.setSpacing( 0 )

        sax = QLabel(self)
        pixmap = QPixmap( s.Const.BL_Icon_PNG )
        pixmap = pixmap.scaled(pixmap.width() * .5, pixmap.height() * .5, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        sax.setPixmap( pixmap )
        sax.setAlignment(Qt.AlignCenter)
        layout.addWidget( sax )

        layout.addSpacing(10)

        main_title = QLabel( s.Const.BL_Long_Title)
        main_title.setObjectName("mainTitle")
        layout.addWidget( main_title )
        layout.addSpacerItem(spacer)

        subsub_title = QLabel( s.Const.BL_SubSubTitle )
        subsub_title.setObjectName("subSubTitle")
        layout.addWidget( subsub_title )
        spacer = QSpacerItem( 100, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)   # Can't reuse, must reinstantiate
        layout.addSpacerItem(spacer)

        sub_title = QLabel( s.Const.BL_SubTitle )
        sub_title.setObjectName("subTitle")
        layout.addWidget( sub_title )

        self.setLayout(layout)

# -------------------------------------------------------------------------------------

if __name__ == "__main__":
    from bl_unit_test import UT
    from bl_style import StyleSheet

    s = UT()

    s.app = QApplication([])
    s.window = Title_Panel()
    s.window.setStyleSheet( StyleSheet )              # OK - Unit test
    size = QApplication.primaryScreen().size()
    width = size.width()
    height = size.height()
    s.window.show()
    s.app.exec()

# -------------------------------------------------------------------------------------
