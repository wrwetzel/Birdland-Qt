#!/usr/bin/python
# -------------------------------------------------------------------------------------
#   WRW 28-Jan-2025
#   MyTable - Base class for all birdland tables.
#   With a little bit of work and help from Chat this turns out to be quite clean.
# -------------------------------------------------------------------------------------

import sys

from PySide6.QtCore import Qt, Signal, QSortFilterProxyModel, QItemSelectionModel
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QApplication,
    QTableView,
    QVBoxLayout,
    QHeaderView,
    QAbstractItemView,
)


# -------------------------------------------------------------------------------------
#   20-Feb-2025 - Proposed by CoPilot after a lot of screwing around with ChatGPT to
#       an eventual near solution but a lot of complexity. Actually, this was proposed
#       by chat early but I ignored it.

class NumericSortProxyModel( QSortFilterProxyModel ):

    def __init__( self, numericCols ):
        super().__init__()
        self.numericCols = numericCols

    # Override sorting to handle numeric values for specific columns
    def lessThan(self, left, right):
        col = left.column()
        if self.numericCols and col in self.numericCols:
            # Convert to float for numeric sorting
            left_value =  left.data(Qt.DisplayRole)
            right_value = right.data(Qt.DisplayRole)
            try:
                return float(left_value) < float(right_value)
            except ValueError:  # Fallback in case of non-numeric values
                return left_value < right_value
        return super().lessThan(left, right)

# -------------------------------------------------------------------------------------
#   Changed model to pmodel as had conflict with model when added numeric sort

class MyView( QTableView ):
    sig_cell_clicked = Signal( str, int, int )
    sig_header_clicked = Signal( int )

    def __init__(self, pmodel, column_ratios, disableSorting ):
        super().__init__()
        # s = Store()

        self.pmodel = pmodel
        self.setModel(self.pmodel)
        # self.setSortingEnabled(True)
        self.setSortingEnabled(False)
        # self.sortByColumn(0, Qt.AscendingOrder)  #  Sort first column initially, no no initial sort
        self.setAlternatingRowColors(True)
        self.setShowGrid(False)
        self.disableSorting = disableSorting

        # Configure header styles
        self.header = self.horizontalHeader()
        self.header.setSectionsClickable(True)
        self.header.setSectionResizeMode(QHeaderView.Interactive)
        self.header.setMinimumSectionSize(0)
        self.header.setHighlightSections(False)          # WRW 29-Apr-2025 - trying to remove slight color shift when active

        #   default section size does not reduce the row height enough, need to do it explicitly row by row.
        self.vheader = self.verticalHeader()
        self.vheader.setVisible(False)
        self.vheader.setSectionResizeMode(QHeaderView.Interactive)
        self.vheader.setDefaultSectionSize( 10 )    # Finally, this set the table item height, eventually simple.
        self.vheader.setMinimumSectionSize( 0 )     # This needed, too
        self.vheader.setHighlightSections(False)          # WRW 29-Apr-2025 - trying to remove slight color shift when active

        self.column_ratios = column_ratios
        self.set_column_widths()

        # Layout
        self.layout = QVBoxLayout()
        # self.layout.addWidget(self )
        self.setLayout(self.layout)

        # Connect signals for cell and header clicks to local signal handlers, which will emit
        #   the application signals.

        self.clicked.connect(self._on_cell_clicked)
        self.header.sectionClicked.connect(self._on_header_clicked)

    # -----------------------------------------------------------------------------
    # Definitely want both resizeEvent() and showEvent()

    def showEvent( self, event):        # showEvent for initial size.
        super().showEvent(event)
        self.set_column_widths()

    def resizeEvent(self, event):       # resizeEvent for subsequent resize.
        super().resizeEvent(event)
        self.set_column_widths()

    #   Set column widths based on relative proportions.
    def set_column_widths(self):
        total_width = self.viewport().width()
        total_ratios = sum(self.column_ratios)
        for col, ratio in enumerate(self.column_ratios):
            column_width = (ratio / total_ratios) * total_width
            self.header.resizeSection(col, column_width)

    def columnCount(self):
        return self.pmodel.columnCount()

    # -----------------------------------------------------------------------------
    #   These are internal signal handlers, outside the scope of SigMan though use
    #       it to emit signals to application.
    #   WRW 19-Mar-2025 - added underscore to name to prevent accidental override
    #       by same-names handler in program inheriting program.

    def _on_header_clicked(self, section):
        if not self.disableSorting:
            self.setSortingEnabled(True)
        self.sig_header_clicked.emit( section )

    def _on_cell_clicked(self, index):
        source_index = self.pmodel.mapToSource(index)
        value = self.pmodel.sourceModel().data(source_index, Qt.DisplayRole)
        row = source_index.row()
        col = source_index.column()

        if False:
            print( "click", value, row, col )
            c0 = self.getItem( row, 0 )
            c1 = self.getItem( row, 1 )
            print( "click", value, row, col, "from getItem():", c0, c1 )

        # value = self.pmodel.data(index, Qt.DisplayRole)
        # row = index.row()
        # col = index.column()
        self.sig_cell_clicked.emit( value, row, col )       # Emit native signal.

# -------------------------------------------------------------------------------------
#   WRW 19-Feb-2025 0 Add numericCols, an array of columns to treat as numeric for sorting

class MyTable( MyView ):

    def __init__(self, header, ratios, numericCols = None, disableSorting = False ):
        self.col_count = len(header)
        self.model = QStandardItemModel(0, self.col_count)
        self.model.setHorizontalHeaderLabels( header )

        if True:        # For numeric sorting of numericCols
            self.proxy_model = NumericSortProxyModel( numericCols )
            self.proxy_model.setSourceModel(self.model)
            super().__init__( self.proxy_model, ratios, disableSorting )

        else:           # For testing with original sort
            super().__init__( self.model, ratios, disableSorting )

        self.view = super()
        self.view.setEditTriggers(QAbstractItemView.NoEditTriggers)         # WRW 9-Apr-2025 - disable editing on Windows

        self.row_count = 0
        self.numericCols = numericCols

    # -----------------------------------------------------
    #   Had to set row height explicitly here to make it small.
    #   Make QStandardItme here, not in calling program.
    #   WRW 30-May-2025 - add tooltip, may want to make it conditional on flag as only
    #       wanted for canonical -> file tables. No, I like it on all as many columns are
    #       too short.

    def addRow( self, data ):
        # print( "/// addRow before append" )
        # irow = [ QStandardItem( d ) for d in data ]
        irow = []
        for d in data:
            item = QStandardItem(d)

            try:
                item.setToolTip(d)          # Fails if called with QStandardItem(), not applicable for that
            except:
                pass

            irow.append(item)

        self.model.appendRow( irow )
        self.setRowHeight(self.row_count, 20)
        self.row_count += 1
        # print( "/// addRow after append" )

    # -----------------------------------------------------
    # /// trying model here

    def getRow( self, row ):
        if row < self.row_count:
            return [ self.model.item(row, col).text() for col in range( self.model.columnCount() ) ]
        else:
            print( f"getRow() row {row} exceeds row count: {self.row_count}" )
            return None

    def getItem( self, row, col ):
        if row < self.row_count and col < self.col_count:
            return self.model.item(row, col).text()
        else:
            print( f"getItem() row {row} or col {col} exceeds row count: {self.row_count} or column count: {self.col_count}" )
            return None

    # -----------------------------------------------------
    #   WRW 14-Feb-2025 - when switch to update via signals.
    #   WRW 7-Mar-2025 - add row argument to optionally select row.
    #   WRW 8-Mar-2025 - Note: terrible bug here, index was coming in as 0 when passed as None
    #       because arg type was int. Ok when changed arg type to object.

    def update( self, data, index=None ):
        self.clear()
        for row in data:
            self.addRow( row )

        # print( "/// index", index )

        if index is not None:
            selection_model = self.selectionModel()
            index = self.model.index(index, 0)  # Get the index for the first column of the row
            self.blockSignals(True)     # select() generates a signal as if user clicked in row.
            selection_model.select(index, QItemSelectionModel.Select | QItemSelectionModel.Rows)
            self.blockSignals(False)

    # -----------------------------------------------------

    def clear( self ):
        self.row_count = 0
        self.model.setRowCount(0)
        # self.model.removeRows(0, self.model.rowCount())

# -------------------------------------------------------------------------------------
#   Always put this in a function to prevent globals leakage

def do_main():
    from bl_unit_test import UT
    from bl_style import StyleSheet
    s = UT()

    header = [ "Col-1", "Col-2", "Col-3" ]
    ratios = [ 1, 2, 4 ]

    s.app = QApplication(sys.argv)
    s.app.setStyleSheet( StyleSheet )   # OK, unit test

    table = MyTable( header, ratios )
    table.setGeometry(100, 100, 800, 500)
    table.show()

    for row in range( 10 ):     # Populate table
        table.addRow( [ str(3*row + 1), str(3*row + 2), str(3*row + 3) ] )

    def cell_click( value, row, column ):
        print( f"Cell Clicked: value: {value}, row: {row} column: {column}" )
        v1 = table.getItem( row, 0 )
        v2 = table.getItem( row, 1 )
        v3 = table.getItem( row, 2 )
        print( f"Row data: {v1}, {v2}, {v3}" )
        r = table.getRow( row )
        print( f"Row: {r}" )

    def header_click( section ):
        print( f"Header Clicked: {section}" )

    table.sig_cell_clicked.connect( cell_click )
    table.sig_header_clicked.connect( header_click )
    sys.exit(s.app.exec())

# -------------------------------------------------------------------------------------

if __name__ == "__main__":
    do_main()

# -------------------------------------------------------------------------------------
