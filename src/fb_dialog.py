#!/usr/bin/python

from PySide6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QLabel,
    QPushButton, QHBoxLayout
)
import sys

class MyDialog(QDialog):
    def __init__(self, title, msg ):
        super().__init__()
        self.setWindowTitle( title )

        # Layouts
        layout = QVBoxLayout()
        button_layout = QHBoxLayout()

        self.msg = QLabel( msg )
        self.msg.setWordWrap( True )
        self.ok_button = QPushButton("OK")

        # Add widgets to layout
        layout.addWidget(self.msg)
        button_layout.addWidget(self.ok_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        # Connect button signals to slots
        self.ok_button.clicked.connect(self.accept)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    dialog = MyDialog( "Sample Title", "Sample text" )
    sys.exit(dialog.exec())
