#!/usr/bin/env python3
# ----------------------------------------------------------------------------------------------
#   PDF_Browser.py - WRW 25-May-2025 - Thumbnail index of directory of PDF files,         
#       originally intended to be fakebooks but may generalize to any PDF.

#   WRW 3-June-2025 - added as_posix() in a couple of places to resolve prob
#       on Windows - no index count in browser

# ----------------------------------------------------------------------------------------------

import os
import sys
from pathlib import Path
import hashlib
import fitz                 # For PyMuPDF

from PySide6.QtCore import Qt, QSize, QEvent, QTimer, QObject, Slot, QTimer, QRect
from PySide6.QtGui import QPixmap, QImage, QCursor, QPainter, QFont, QColor, QFontMetrics, QPen
from PySide6.QtWidgets import QWidget, QApplication, QLabel, QGridLayout
from PySide6.QtWidgets import QSizePolicy, QScrollArea, QPushButton, QVBoxLayout

from Store import Store
from bl_constants import MT

# ----------------------------------------------------------------------------------------------

THUMBNAIL_WIDTH = 200   # Cached image width in pixels, should be larger than ever needed
GRID_COLUMNS = 8        # Number of columns in the grid - 6 is good comprimise, 8 was too small.

# ----------------------------------------------------------------------------------------------

class PDFThumbnailLabel( QLabel ):
    def __init__(self, pdf_path):
        super().__init__()
        self.pdf_path = pdf_path
        self.setToolTip(Path(pdf_path).name)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.on_click()
        else:
            super().mousePressEvent(event)

    def on_click(self):
        s = Store()
        path = Path( self.pdf_path ).as_posix()    # WRW 11-Apr-2025 - browser on Windows returning backslashes.
        s.sigman.emit( "sig_music_browser_clicked", path )

# ----------------------------------------------------------------------------------------------

class PDF_Browser(QWidget):
    def __init__(self, parent=None):
        s = Store()
        super().__init__(parent)

        s.sigman.register_slot( 'slot_make_thumbnails', self.slot_make_thumbnails )

        self.cache_dir = s.conf.val( 'thumbnail_dir' )
        os.makedirs( self.cache_dir, exist_ok=True )

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.container = QWidget()
        self.layout = QGridLayout(self.container)
        self.scroll_area.setWidget(self.container)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(self.scroll_area)
        self.setLayout(outer_layout)

        txt = """No cover browser thumbnails.
Please configure the 'Folders to show in Cover Browser' option and be sure that
the 'Root of music files' option is configured. Then: 
'Database->Build Cover Browser Thumbnails'
"""
        self.no_thumbnails_label = QLabel( txt )
        outer_layout.addWidget( self.no_thumbnails_label )

        self.get_pdf_files()

        self.labels = []
        self.cached_pixmaps = {}
        self.load_all_pixmaps( )              

        if self.cached_pixmaps:
            self.no_thumbnails_label.setVisible( False )

    # --------------------------------------------------------------------------------
    #   Get list of all pdf files in 'browser_folders' sorted by each folder, not all together.

    def get_pdf_files( self ):
        s = Store()
        self.pdf_files = []
        self.pdf_ppaths = {}

        pdf_root = s.conf.val( 'music_file_root' )

        for pdf_folder in s.conf.val( 'browser_folders' ):
            path = Path( pdf_root, pdf_folder )

            files = sorted( self.scan_pdfs( path ))
            self.pdf_files += files
            for fpath in files:
                ppath = Path( pdf_folder, fpath ).relative_to( pdf_root ).as_posix()
                self.pdf_ppaths[ fpath ] = ppath

    # --------------------------------------------------------------------------------

    def scan_pdfs(self, root_path):
        root_path = Path(root_path)
        return [str(p.as_posix()) for p in root_path.rglob('*') if p.is_file() and p.suffix.lower() == '.pdf']

    # --------------------------------------------------------------------------------

    def get_cache_path( self, pdf_path):
        pdf_hash = hashlib.md5(pdf_path.encode()).hexdigest()
        return os.path.join( self.cache_dir, f"{pdf_hash}.png")

    # --------------------------------------------------------------------------------
    #   User action from menu. Initially lots of timing problems here,
    #      now resolved with oneshots with chat help.

    @Slot()
    def slot_make_thumbnails( self ):
        s = Store()

        s.app.setOverrideCursor(QCursor(Qt.WaitCursor))
        self.get_pdf_files()                                # Start with fresh list of pdf files
        if self.pdf_ppaths:
            self.no_thumbnails_label.setVisible( False )

        QApplication.processEvents()
        QTimer.singleShot(0, self.start_thumbnail_generation)

    def start_thumbnail_generation(self):
        self.create_all_pixmaps()

    # --------------------------------------------------------------------------------

    def clear_grid_layout( self, grid_layout: QGridLayout ):
        while (item := grid_layout.itemAt(0)) is not None:
            widget = item.widget()
            grid_layout.removeWidget(widget)
            widget.setParent(None)

    # --------------------------------------------------------------------------------
    #   /// RESUME - combine common code here and populate_grid into a new function.

    def create_all_pixmaps( self ):
        s = Store()
        s.selectTab(MT.Browser)
        s.sigman.emit( "sig_search_results", "Building browser thumbnails" )
    
        self.clear_grid_layout(self.layout)
        self.labels.clear()
    
        self.row = 0
        self.col = 0

        self.column_width = self.container.width() / (GRID_COLUMNS + 1)
    
        self.pdf_iter = iter(self.pdf_files)
        self.add_next_thumbnail()
    
    # ----------------------------------------------------------

    def add_next_thumbnail( self ):
        s = Store()

        try:
            pdf_path = next(self.pdf_iter)
        except StopIteration:
            s.app.restoreOverrideCursor()
            s.sigman.emit( "sig_search_results", "Build browser thumbnails completed" )
            return  # Done
    
        pixmap = self.render_pdf_first_page( pdf_path )
        if pixmap:
            self.cached_pixmaps[pdf_path] = pixmap

            label = PDFThumbnailLabel(pdf_path)

            if pixmap.width() > self.column_width:
                scaled_pixmap = pixmap.scaledToWidth(self.column_width, Qt.SmoothTransformation)
            else:
                scaled_pixmap = pixmap

            label.setPixmap(scaled_pixmap)
            label.setFixedSize(scaled_pixmap.size())
            label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

            self.layout.addWidget(label, self.row, self.col)
            self.labels.append(label)

            self.col += 1
            if self.col >= GRID_COLUMNS:
                self.col = 0
                self.row += 1

            # Scroll to bottom
            scrollbar = self.scroll_area.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

        QTimer.singleShot(30, self.add_next_thumbnail)  # Delay before adding next

    # --------------------------------------------------------------------------------

    def render_pdf_first_page( self, pdf_path):
        s = Store()

        cache_path = self.get_cache_path(pdf_path)

        # if os.path.exists(cache_path):
        #     return QPixmap(cache_path)

        doc = fitz.open(pdf_path)

        try:
            page = doc.load_page(0)

        except Exception:
            (extype, value, xtraceback) = sys.exc_info()
            s.msgWarn( f"File {pdf_path} appears corrupted, type: '{extype}', value: '{value}', ignoring" )
            return None

        pix = page.get_pixmap(dpi=150)
        image = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGBA8888 if pix.alpha else QImage.Format_RGB888)
        scaled_image = image.scaledToWidth(THUMBNAIL_WIDTH, Qt.SmoothTransformation)
        pixmap = QPixmap.fromImage(scaled_image)

        ppath = self.pdf_ppaths[ pdf_path ]        
        cnt, src = s.fb.get_index_count_from_file( str( ppath ) )

        if cnt:
            # pixmap = self.add_text_to_pixmap( pixmap, f"{src}: {cnt}" )
            pixmap = self.add_text_to_pixmap( pixmap, f"Index: {cnt}" )

        pixmap.save(cache_path, "PNG")
        return pixmap

    # --------------------------------------------------------------------------------
    #   This is a lot of code for a minor feature but it is helpful to have
    #       to have index information about a book.

    def add_text_to_pixmap( self, pixmap: QPixmap, text: str ) -> QPixmap:
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        font = QFont("Arial", 16)       # Font and size
        painter.setFont( font )  

        metrics = QFontMetrics(font)
        text_rect = metrics.boundingRect( text )
        padding_x = 12      # pixels around the text
        padding_y = 4       # pixels around the text
        margin = 10         # box to edge of pixmap
        border_width = 2    # width of rectangle border

        rect_x = 10
        rect_y = 10
        box_width = text_rect.width() + 2 * padding_x
        box_height = text_rect.height() + 2 * padding_y
        # Position the box in bottom-right corner
        x = pixmap.width() - box_width - margin
        y = pixmap.height() - box_height - margin
        background_rect = QRect(x, y, box_width, box_height)

        # Draw background rectangle (e.g. white with black border)
        painter.setBrush(QColor(255, 255, 255, 230))  # Slight transparency in rectangle
        painter.setPen( QPen( QColor(0, 0, 255), border_width) )   # Border color
        painter.drawRect(background_rect)

        #   WRW 2-June-2025
        #   +10 because text_rect.width() was a little small causing clipping.
        #       This applies to the text rectangle, not the box.

        painter.setPen(QColor( '#c00000' ))   # Text color
        painter.drawText(
            QRect( x + padding_x, y + padding_y, text_rect.width()+10, text_rect.height()),
            Qt.AlignLeft | Qt.AlignTop,
            text
        )

        painter.end()
        return pixmap

    # --------------------------------------------------------------------------------
    #   Load existing thumbnail files for files in self.pdf_files into self.cached_pixmaps

    def load_all_pixmaps( self ):
        s = Store()
        # s.selectTab( MT.Browser )
        for pdf_path in self.pdf_files:
            cache_path = self.get_cache_path(pdf_path)
            if os.path.exists(cache_path):
                pixmap = QPixmap(cache_path)
                self.cached_pixmaps[pdf_path] = pixmap

    # --------------------------------------------------------------------------------
    #   Copy thumbnails from self.cached_pixmaps to grid.

    def populate_grid( self, container_width ):
        for i in reversed(range(self.layout.count())):
            widget = self.layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)

        self.labels.clear()
        column_width = container_width/(GRID_COLUMNS+1)       # +1 to prevent clipping of last one

        row = col = 0
        for pdf_path in self.pdf_files:
            if pdf_path not in self.cached_pixmaps:
                continue

            label = PDFThumbnailLabel(pdf_path)
            pixmap = self.cached_pixmaps[pdf_path]

            if pixmap.width() > column_width:
                scaled_pixmap = pixmap.scaledToWidth(column_width, Qt.SmoothTransformation)
            else:
                scaled_pixmap = pixmap

            label.setPixmap(scaled_pixmap)
            label.setFixedSize(scaled_pixmap.size())
            label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

            self.layout.addWidget(label, row, col)
            self.labels.append(label)
            col += 1
            if col >= GRID_COLUMNS:
                col = 0
                row += 1

    # -------------------------------------------------------------

    def resizeEvent( self, event ):
        super().resizeEvent(event)
        container_width = event.size().width()
        self.populate_grid( container_width )

# ----------------------------------------------------------------------------------------------
#   /// RESUME - not maintained

if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)

    s = Store()
    cache_dir = s.conf.val( 'thumbnail_dir' )
    os.makedirs(cache_dir, exist_ok=True)

    browser = PDF_Browser()
    browser.show()
    sys.exit(app.exec())

# ----------------------------------------------------------------------------------------------
