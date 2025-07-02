#!/usr/bin/python
# ---------------------------------------------------------------------------------------
#   WRW 24-Jan-2025
#   PDFViewer - taken from Birdland fb_pdf.py and ChatGPT.
#   With help from ChatGPT
#   FUTURE - add logic to spawn remote viewer? Local viewer on seperate monitor?
#       Likely no as fullscreen works fine.

# ---------------------------------------------------------------------------------------

import sys
import fitz                 # From PyMuPDF package
from pathlib import Path

from PySide6.QtCore import Qt, Signal, QTimer, Slot, QSettings, QSize
from PySide6.QtGui import QImage, QPixmap, QKeyEvent, QKeySequence, QWheelEvent, QShortcut, QColor
from PySide6.QtWidgets import QApplication, QLabel, QHBoxLayout, QVBoxLayout, QWidget
from PySide6.QtWidgets import QPushButton, QScrollArea, QScrollBar, QMainWindow, QSizePolicy

from bl_metadata_panel import BL_Metadata_Panel
from Store import Store
from bl_style import getOneStyle                  

# ---------------------------------------------------------------------------------------
#   Need the pdf viewer even for some docs even if using external viewer for music.
#   Convert to managed signals? No, native signals are fine WITHIN a module.
#   Not sure, I think better to use managed signals as this is external to the pdf viewer module
#       though connected functions are just within that module.
#   WRW 19-Mar-2025 - Removed need for s.pdf_viewer variable, used with load_pdf() and getPageCount().
#       Now done with signals.

class Viewer_Tab( QWidget ):

    def __init__( self, parent=None ):
        super().__init__(parent)
        s = Store()

        # - - - - - - - - - - - - - - - - - - - - - - - -
        #   Instiatiate the widgets

        pdf_viewer = PDFViewer( parent=self )        # Instantiate the PDF viewer
        self.pdf_viewer = pdf_viewer
        self.pdf_viewer_layout = QVBoxLayout()
        self.pdf_viewer_layout.addWidget( pdf_viewer )
    
        pdf_controls = PDFControls(self, vertical=False)
        pdf_controls.setObjectName( "pdfViewerControls" )       # OK - for styles
    
        # /// 21-Apr-2025 pdf_slider = PDFSlider( self, vertical=True )

        metadata = BL_Metadata_Panel()
        metadata.setObjectName( "metadataPanel" )
        metadata.setFixedWidth( s.Const.metaDataPanelWidth  )

        # - - - - - - - - - - - - - - - - - - - - - - - -
        #   Layout the controls and metadata

        meta_ctrl_layout = QVBoxLayout()                                      
        meta_ctrl_layout.setContentsMargins( 0, 0, 6, 0 )
        meta_ctrl_layout.setSpacing( 8 )

        meta_ctrl_layout.addWidget( pdf_controls, alignment=Qt.AlignLeft )
        meta_ctrl_layout.addWidget( metadata, alignment=Qt.AlignLeft )

        # - - - - - - - - - - - - - - - - - - - - - - - -
        #   Layout for above, slider, and viewer pane
        #   WRW 21-Apr-2025 - moved slider into viewer so it moves when enlarge with F11

        viewer_layout = QHBoxLayout()
        viewer_layout.setContentsMargins( 0, 0, 0, 0 )
        viewer_layout.setSpacing( 0 )

        viewer_layout.addLayout( meta_ctrl_layout )
        viewer_layout.addLayout( self.pdf_viewer_layout )

        # - - - - - - - - - - - - - - - - - - - - - - - -

        self.setLayout( viewer_layout )
        self.viewer_layout = viewer_layout

        # --------------------------------------------------------------------
        # Connect signals and slots between viewer, controls, slider

        pdf_viewer.page_changed_signal.connect( pdf_controls.page_changed )     # *** connection from pdf to controls

        # /// WRW 21-Apr pdf_viewer.page_changed_signal.connect( pdf_slider.page_changed )     # *** connection from pdf to controls

        pdf_viewer.sig_pdf_changed.connect( pdf_controls.pdf_changed )
        # /// WRW 21-Apr pdf_viewer.sig_pdf_changed.connect( pdf_slider.pdf_changed )

        # /// WRW 21-Apr pdf_slider.page_slider_changed.connect(pdf_viewer.page_slider_changed)

        pdf_controls.first_page_clicked.connect(pdf_viewer.first_page)
        pdf_controls.next_page_clicked.connect(pdf_viewer.next_page)
        pdf_controls.previous_page_clicked.connect(pdf_viewer.previous_page)
        pdf_controls.last_page_clicked.connect(pdf_viewer.last_page)
        pdf_controls.fit_h_clicked.connect(pdf_viewer.fit_h)
        pdf_controls.fit_v_clicked.connect(pdf_viewer.fit_v)
        pdf_controls.zoom_in_clicked.connect(pdf_viewer.zoom_in)
        pdf_controls.zoom_out_clicked.connect(pdf_viewer.zoom_out)
        pdf_controls.fullscreen_clicked.connect(self.do_fullscreen)

        # --------------------------------------------------------------------
        #   WRW 29-Mar-2025

        s.sigman.register_slot( "slot_toggle_fullscreen", self.slot_toggle_fullscreen )
        s.sigman.register_slot( "slot_do_fullscreen", self.slot_do_fullscreen )
        s.sigman.register_slot( "slot_exit_fullscreen", self.slot_exit_fullscreen )
        s.sigman.register_slot( "slot_fullscreen_button_clicked",   self.slot_fullscreen_button_clicked )

        self.fullscreen_mode = False

    # --------------------------------------------------------------------
    #   WRW 28-May-2025 - Last feature?

    @Slot()
    def slot_fullscreen_button_clicked( self ):
        if self.fullscreen_mode:                    # Make conditional so can use sig_fullscreen_button_clicked more broadly
            self.fullscreen_window.raise_()
            self.fullscreen_window.activateWindow()
            self.fullscreen_window.setFocus()
            self.pdf_viewer.setFocus()              # Try give focus to widget withing window

    # ------------------------------------------------------------
    #   WRW 29-Mar-2025 - One of the last features I'm considering before the 'lite' release
    #   Set the pdf viewer to fullscreen, return via escape or another F11
    #   WRW 27-May-2025 - trying separate keys for full and non-full for usability. I seem
    #   to want to do this when using it.
    #   WRW 2-June-2025 - Emit signal on toggle to control Zoom button in status bar.

    @Slot()
    def slot_toggle_fullscreen( self ):
        s = Store()
        if not self.fullscreen_mode:
           # self.fullscreen_mode = True
            self.do_fullscreen()
            s.sigman.emit( "sig_announce_do_fullscreen" )

        else:
            self.fullscreen_mode = False
            self.fullscreen_window.exit_fullscreen()
            s.sigman.emit( "sig_announce_exit_fullscreen" )

    @Slot()
    def slot_do_fullscreen( self ):
        if not self.fullscreen_mode:
            self.fullscreen_mode = True
            self.do_fullscreen()

    @Slot()
    def slot_exit_fullscreen( self ):
        if self.fullscreen_mode:
            self.fullscreen_mode = False
            self.fullscreen_window.exit_fullscreen()

    # --------------------------------------------------------
    #   User clicked the fullscreen icon or called from toggle above on keypress

    def do_fullscreen( self ):
        self.fullscreen_mode = True
        self.fit, self.zoom = self.pdf_viewer.get_state()
        # print(self.fit, self.zoom)
        # self.setParent(None)  # this is a problem, hid entire contents of tab
        self.pdf_viewer_layout.removeWidget( self.pdf_viewer )    # Remove from layout, a bit obsessive

        self.fullscreen_window = makeFullScreenPdfWindow( self.pdf_viewer, self.restore_callback)
        self.fullscreen_window.setFocusPolicy(Qt.StrongFocus)       # WRW 2-June-2025 - Trying for more natural response to Zoom button

      # self.fullscreen_window.showFullScreen()
      # self.fullscreen_window.showMaximized()
        self.fullscreen_window.show()       # Helpful for testing
        # self.fullscreen_window.full_horizontal_signal.connect( self.pdf_viewer.fit_h )
        # self.fullscreen_window.full_vertical_signal.connect( self.pdf_viewer.fit_v )

    def restore_callback( self, pdf_viewer ):
        self.fullscreen_mode = False
        # self.pdf_viewer_layout.insertWidget(0, pdf_viewer )
        self.pdf_viewer_layout.addWidget( pdf_viewer )
        # pdf_viewer.setParent(self)          # Re-parent the viewer back to the viewer tab, OK without it
        # widget.show()                     # Unnecessary
        # self.tabs.setCurrentWidget(self)  # Unnecessary
        self.pdf_viewer.set_state( self.fit, self.zoom )

    # --------------------------------------------------------------

# ---------------------------------------------------------------------------------------
#   WRW 16-Mar-2025 - Pull out from PDFControls() so can place the slider independent
#   of control buttons.
#   Slider is internal to PDF_Viewer.py and works in 0-based page numbers.

class PDFSlider( QWidget ):
    page_slider_changed = Signal( int )             # emitted when user changes slider

    def __init__(self, parent=None, vertical=False):
        super().__init__(parent)

        layout = QHBoxLayout()
        layout.setContentsMargins( 0, 0, 0, 0 )
        layout.setSpacing( 0 )

        self.page_slider = QScrollBar()
        self.page_slider.setValue(1)                                                      
        self.page_slider.sliderMoved.connect( self.page_slider_changed )        # Only user action, avoids double refresh() calls
        self.page_slider.setObjectName("pageSlider")
        self.page_slider.setMinimum( 0 )                                                                                    
        self.page_slider.setMaximum( 100 )                                                                                  

        if vertical:
            self.page_slider.setOrientation(Qt.Orientation.Vertical)

        else:
            self.page_slider.setOrientation(Qt.Orientation.Horizontal)

        layout.addWidget( self.page_slider )
        self.setLayout( layout )

    def page_changed( self, page ):
        # print( f"/// page_changed, set slider position to {page} {self.page_slider.minimum()} {self.page_slider.maximum()} ")
        self.page_slider.setValue( page )           # /// PAGE

    def pdf_changed( self, page_count ):
        # print( "/// pdf_changed, page_count: ", page_count )
        self.page_slider.setMaximum( page_count -1 )       # /// PAGE

# ---------------------------------------------------------------------------------------
#   Native signals are used here mostly, OK as within a module.

class PDFControls( QWidget ):
    
    first_page_clicked =    Signal()           # Signals for button clicks
    next_page_clicked =     Signal()
    previous_page_clicked = Signal()
    last_page_clicked =     Signal()
    fit_h_clicked =         Signal()
    fit_v_clicked =         Signal()
    zoom_in_clicked =       Signal()
    zoom_out_clicked =      Signal()
    fullscreen_clicked =    Signal()

    def __init__(self, parent=None, vertical=False ):
        super().__init__(parent)
        s = Store()
        
        self.page_count = 0
        if vertical:
            self.button_layout = QVBoxLayout()                 # Vertical Layout for the buttons
            self.button_layout.setAlignment(Qt.AlignTop)

        else:
            self.button_layout = QHBoxLayout()                 # Horizonta Layout for the buttons
            self.button_layout.setAlignment(Qt.AlignLeft)

        self.button_layout.setContentsMargins( 0, 4, 0, 4 )     # last 4 to give a little more room for some buttons styles.
        self.button_layout.setSpacing( 9 )                      # before fullscreen button added.
        self.button_layout.setSpacing( 5 )

        self.setLayout( self.button_layout )

        iconSize = QSize( 32, 32 )

        self.first_button = QPushButton()   # Create the buttons
        s.fb.registerSvgIcon( self.first_button, ":NIcons/go-first-view-page.svg", iconSize, 'pdf' )

        self.prev_button = QPushButton( )
        s.fb.registerSvgIcon( self.prev_button, ":NIcons/zoom-previous.svg", iconSize, 'pdf' )

        self.next_button = QPushButton( )
        s.fb.registerSvgIcon( self.next_button, ":NIcons/zoom-next.svg", iconSize, 'pdf' )

        self.last_button = QPushButton()
        s.fb.registerSvgIcon( self.last_button, ":NIcons/go-last-view.svg", iconSize, 'pdf' )

        self.fit_h_button = QPushButton()
        s.fb.registerSvgIcon( self.fit_h_button, ":NIcons/zoom-fit-width.svg", iconSize, 'pdf' )

        self.fit_v_button = QPushButton()
        s.fb.registerSvgIcon( self.fit_v_button, ":NIcons/zoom-fit-height.svg", iconSize, 'pdf' )

        self.zoom_out_button = QPushButton()
        s.fb.registerSvgIcon( self.zoom_out_button, ":NIcons/view-zoom-out-symbolic.svg", iconSize, 'pdf' )

        self.zoom_in_button = QPushButton()
        s.fb.registerSvgIcon( self.zoom_in_button, ":NIcons/view-zoom-in-symbolic.svg", iconSize, 'pdf' )

        self.fullscreen_button = QPushButton()
        s.fb.registerSvgIcon( self.fullscreen_button, ":NIcons/view-fullscreen.svg", iconSize, 'pdf' )

        self.button_layout.addWidget(self.first_button)        # Add buttons to the button_layout
        self.button_layout.addWidget(self.prev_button)
        self.button_layout.addWidget(self.next_button)
        self.button_layout.addWidget(self.last_button)
        self.button_layout.addWidget(self.fit_h_button)
        self.button_layout.addWidget(self.fit_v_button)
        self.button_layout.addWidget(self.zoom_out_button)
        self.button_layout.addWidget(self.zoom_in_button)
        self.button_layout.addWidget(self.fullscreen_button)

        self.first_button.clicked.connect(self.first_page_clicked)      # Connect button signals to class signals
        self.next_button.clicked.connect(self.next_page_clicked)
        self.prev_button.clicked.connect(self.previous_page_clicked)
        self.last_button.clicked.connect(self.last_page_clicked)
        self.fit_h_button.clicked.connect(self.fit_h_clicked)
        self.fit_v_button.clicked.connect(self.fit_v_clicked)
        self.zoom_out_button.clicked.connect(self.zoom_out_clicked)
        self.zoom_in_button.clicked.connect(self.zoom_in_clicked)
        self.fullscreen_button.clicked.connect(self.fullscreen_clicked)

        s.sigman.register_slot( "slot_pdf_appearance", self.pdf_appearance )

    # ------------------------------------------------------------------------------------
    #   WRW 7-Mar-2025 - add block of signal to prevent signal from programmatic set of slider
    #   position.  NO! No signal emitted by ScrollBar on programmatic change. OK, agrees with observations.

    def pdf_changed( self, page_count ):
        # print( "/// pdf_changed, page_count: ", page_count )
        self.page_count = page_count

    def page_changed( self, page ):
        # print( f"/// page_changed, set slider position to {page} {self.page_slider.minimum()} {self.page_slider.maximum()} ")
        pass

    # ------------------------------------------------------------------------------------

    @Slot( object )
    def pdf_appearance( self, appearance ):
        self.appearance = appearance
        s = Store()
        icon_color = getOneStyle( appearance, 'qwidget_text' )
        s.fb.updateSvgIcons( QColor( icon_color ), group='pdf' )

# ---------------------------------------------------------------------------------------
#   WRW 29-Mar-2025

class makeFullScreenPdfWindow( QMainWindow ):
    full_horizontal_signal = Signal()
    full_vertical_signal = Signal()

    def __init__(self, pdf_viewer, restore_callback):
        super().__init__()                              # Create new QMainWindow
        s = Store()
        self.setWindowFlags(Qt.Window)
      # self.setWindowFlag(Qt.WindowStaysOnTopHint, True)   # WRW 28-May-2025
        self.setWindowTitle("PDF Viewer Window")
        self.setCentralWidget(pdf_viewer)               # Put pdf_viewer in central widget

        # -------------------------------------------------
        #   Set up a few keys for control
        #       ESC to exit fullscreen
        #       H & V to set full horizontal or vertical
        #   WRW 27-May-2025 - don't know why I did this, moving function to keyPressEvent(),
        #       H & V were not getting picked up in main window. Yes, only connected them
        #       in fullscreen.

        if False:
            esc_shortcut = QShortcut(QKeySequence(Qt.Key_Escape), self)
            esc_shortcut.activated.connect(self.exit_fullscreen)

            full_h_shortcut = QShortcut(QKeySequence(Qt.Key_H), self)
            full_h_shortcut.activated.connect( self.full_horizontal_signal )

            full_v_shortcut = QShortcut(QKeySequence(Qt.Key_V), self)
            full_v_shortcut.activated.connect( self.full_vertical_signal )

        # -------------------------------------------------

        settings = QSettings( str( Path( s.Const.stdConfig, s.Const.Settings_Config_File )), QSettings.IniFormat )

        self.setMinimumSize(1, 1)       # This needed to override unknown minimum sizes.
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)

        geometry = settings.value("PDF-geometry")

        if geometry is not None:
            self.restoreGeometry(geometry)
        else:
            width = 480                     # Without this the default size was VERY small.
            height = 640
            self.resize( width, height )

        state = settings.value("PDF-windowState")
        if state is not None:
            self.restoreState(state)

        if settings.value("PDF-isFullScreen") == "true":
            self.showFullScreen()

        elif settings.value("PDF-isMaximized") == "true":
            self.showMaximized()

        # -------------------------------------------------

        self._pdf_viewer = pdf_viewer
        # self._original_parent = parent
        self._restore_callback = restore_callback

        QTimer.singleShot(0, lambda: pdf_viewer.refresh( True ))    # /// TESTING


    def showFullScreen(self):
        super().showFullScreen()

    def exit_fullscreen(self):
        # Reparent PDF widget back to original layout
        # self._pdf_viewer.setParent(None)            # Set parent of the original pdf_viewer to None, not doing anything
        self.close()                                # Close the created window
        # self._original_parent.restore_pdf_viewer( self._pdf_viewer )
        self._restore_callback(self._pdf_viewer)    # And call the callback

    def closeEvent(self, event):
        s = Store()
        self._restore_callback(self._pdf_viewer)    # And call the callback
        if self.isVisible():
            settings = QSettings( str( Path( s.Const.stdConfig, s.Const.Settings_Config_File )), QSettings.IniFormat )
            settings.setValue("PDF-geometry", self.saveGeometry())
            settings.setValue("PDF-isMaximized", self.isMaximized())
            settings.setValue("PDF-isFullScreen", self.isFullScreen())
            settings.setValue("PDF-windowState", self.saveState())

        s.window.raise_()
        s.window.activateWindow()       # This is the main window
        s.window.setFocus()

        super().closeEvent(event)

# ---------------------------------------------------------------------------------------

class PDFViewer( QWidget ):
    sig_pdf_changed =      Signal( int )            # New pdf file, managed signal
    page_changed_signal =  Signal( int )            # New page, native signal
    sig_pdf_page_changed = Signal( int )            # Redundant with above but for managed signals

    def __init__(self, parent=None):
        super().__init__(parent)
        s = Store()

        self.setFocusPolicy(Qt.StrongFocus)
        self.zoom = 1
        self.fit = 'Both'               # WRW 18 Apr 2022 - Added this to get fit in any aspect ratio.
        self.external_viewer = False
        self.prep_gui_initialized = True
        self.gui_initialized = False    # To suppress unnecessary refresh() calls. They don't hurt but are sloppy.

        self.mouse_start_pos = None,
        self.mouse_state = 'up'
        self.current_pixmap_y = None                                                                                         
        self.current_file = None

        self.layout = QHBoxLayout(self)

        pdf_slider = PDFSlider( self, vertical=True )                           # WRW 21-Apr-2025 Move slider into PDFViewer()
        self.layout.addWidget( pdf_slider, alignment=Qt.AlignLeft )             # WRW 21-Apr-2025
        pdf_slider.page_slider_changed.connect( self.page_slider_changed )      # WRW 21-Apr-2025

        pdf_slider.page_slider_changed.connect( self.page_slider_changed )      # WRW 21-Apr-2025
        self.sig_pdf_changed.connect( pdf_slider.pdf_changed )                  # WRW 21-Apr-2025
        self.page_changed_signal.connect( pdf_slider.page_changed )     # *** connection from pdf to controls WRW 21-Apr-2025

        s.sigman.register_slot( "slot_load_pdf",                    self.load_pdf )
        s.sigman.register_slot( "slot_change_pdf_page",             self.change_pdf_page )
        
        # --------------------------------------------------------
        #   Navigation and zoom controls.

        if False:
            self.controls = PDFControls(self)
            self.layout.addWidget(self.controls)

            # Connect control signals to respective slot methods
            self.controls.first_page_clicked.connect(self.first_page)
            self.controls.next_page_clicked.connect(self.next_page)
            self.controls.previous_page_clicked.connect(self.previous_page)
            self.controls.last_page_clicked.connect(self.last_page)
            self.controls.fit_h_clicked.connect(self.fit_h)
            self.controls.fit_v_clicked.connect(self.fit_v)
            self.controls.zoom_in_clicked.connect(self.zoom_in)
            self.controls.zoom_out_clicked.connect(self.zoom_out)

        # --------------------------------------------------------
        #   Label is widget to contain pdf image

        self.label = QLabel("No PDF file loaded", self)     # QLabel to display the pdf image

        #   WRW 27-May-2025 per chat suggestion
        # self.label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)  # WRW 27-May-2025
        # self.label.setScaledContents(False)
        # self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.setFocusPolicy(Qt.StrongFocus)           # /// WRW 19-Feb-2025 - working on focus issues, set on widget
        self.label.setScaledContents(False)
        self.label.setAlignment(Qt.AlignTop)
        # self.label.setStyleSheet("background-color: gray;")   # Add a background for clarity

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.label)

        # self.scroll_area.setWidgetResizable(True)
        # self.scroll_area.setVerticalScrollBarPolicy( Qt.ScrollBarAlwaysOn )       # unnatural to be always on.
        # self.scroll_area.setHorizontalScrollBarPolicy( Qt.ScrollBarAlwaysOn )

        self.layout.addWidget(self.scroll_area)

        s.sigman.register_signal( "sig_pdf_page_changed", self.sig_pdf_page_changed )
        s.sigman.register_signal( "sig_pdf_changed",      self.sig_pdf_changed )                     

    # --------------------------------------------------------
    #   Set focus when mouse clicked in pdf window. Needed after
    #   loose focus to other widgets.

    # Ensure widget gains focus when clicked
    def mousePressEvent(self, event):
        self.setFocus()

    # Set focus automatically when the mouse enters the window
    def enterEvent(self, event):
        self.setFocus()

    # ------------------------------------------------------------
    #   WRW 3-Mar-2025 - added support for stream for use with file from pyside resource facility.

    @Slot( object, str, int )
    def load_pdf( self, stream=None, file=None, page=None ):
        s = Store()
        self.current_file = file

        page -= 1       # User-facing page numbers are 1-based, pdf files are 0-based.   /// PAGE

        if stream:
            try:
                self.pdf_document = fitz.open(stream=stream, filetype="pdf")         # Load the PDF document
            except:
                s.msgWarn( f"PDF file '{file}' not found (A)" )
                return

        else:
            if not Path( file ).is_file():
                s.msgWarn( f"PDF file '{file}' not found (B)" )
                return

            try:
                if Path( file ).suffix.lower() == '.pdf':       # WRW 7-Apr-2025 - Don't let fitz.open() barf.
                    self.pdf_document = fitz.open(file)         # Load the PDF document
                else:
                    s.msgInfo( f"File: {file} is not a .pdf file. Please select a .pdf file" )
                    return

            except Exception as ex:
                (extype, value, traceback) = sys.exc_info()
                s.msgWarn( f"Open PDF file '{file}' failed\ntype: {extype}\nvalue: {value}\nProbably not a PDF file." )
                return

        self.current_file = file
        self.page_count = self.pdf_document.page_count
        self.current_page = page

        #   Emit native sig_pdf_changed on new pdf file, connected to controls pdf_changed.
        self.sig_pdf_changed.emit( self.page_count )
        s.sigman.emit( "sig_pdf_changed", self.page_count )

        #   WRW 7-Mar-2025 Call refresh() AFTER update page_count, this threw a curve ball when BEFORE.
        self.refresh( False )   # No managed page_changed signal on initial load, called explicitly in calling routine

    # ---------------------------------------------------------------------------------
    #   Fetch a pixmap for page_number and show it in label.                    

    def OMIT_show_page( self, page_number ):
        if 0 <= page_number < self.page_count:
            qpixmap = self.get_image( page_number )         # ******
            self.label.setPixmap( qpixmap )
        else:
            self.label.setText("Page out of range.")

    # ---------------------------------------------------------------------------------

    def getPageCount( self ):
        return self.page_count

    # ---------------------------------------------------------------------------------

    def first_page(self):
        self.current_page = 0
        self.refresh( True )

    def next_page(self):
        if self.current_page + 1 < self.page_count:
            self.current_page += 1
            self.refresh( True )
            QTimer.singleShot(0, self.scroll_to_top)

    def previous_page(self, scroll_to_bottom_flag=True):
        if self.current_page - 1 >= 0:
            self.current_page -= 1
            self.refresh( True )
            if scroll_to_bottom_flag:
                QTimer.singleShot(0, self.scroll_to_bottom)

    def last_page(self):
        self.current_page = self.page_count-1
        self.refresh( True )

    def fit_h( self ):
        self.fit = 'Width'
        self.refresh( True )

    def fit_v( self ):
        self.fit = 'Height'
        self.refresh( True )

    def fit_b( self ):
        self.fit = 'Both'
        self.refresh( True )

    def zoom_in( self ):
        self.zoom *= 1.2
        self.fit = 'User'
        self.refresh( True )

    def zoom_out( self ):
        self.zoom *= 1/1.2
        self.fit = 'User'
        self.refresh( True )

    def get_state( self ):              # 29-Mar-2025
        return self.fit, self.zoom

    #   WRW 31-Mar-2025 - A simple solution for a nagging problem
    #   After return from FullScreen it takes Qt some time for the UI to stabilize. The QTimer.singleShot()
    #   delays refresh until such is done. Without it the viewport size in get_zoom_from_fit() was the full screen
    #   one and the displayed image was much too big. A little help from chat but this was my own solution.

    def set_state( self, fit, zoom ):   # 29-Mar-2025
        self.fit = fit
        self.zoom = zoom
        QTimer.singleShot(0, lambda: self.refresh( True ))

    # --------------------------------------------------------------
    #   This only happens on user interaction, not programmatic.
    #   /// WRW 7-Mar-2025 - changed False to True, was False because I thought would
    #   setting slider position in refresh() would trigger another signal perhaps?

    @Slot( int )
    def page_slider_changed( self, page ):
        self.current_page = page
        self.refresh( True )        

    # --------------------------------------------------------------

    @Slot()
    def change_pdf_page( self, page ):
        self.current_page = page         # User-facing page numbers are 1-based.     /// PAGE
        self.refresh( True )

    # --------------------------------------------------------------
    #   Return pixmap of given zoom and page

    def get_image( self, page_number):

        if page_number < self.page_count:
            fitz.TOOLS.mupdf_display_errors(False)  # Suppress error messages in books with alpha-numbered front matter.
          # self.dlist = self.pdf_document[ page_number ].get_displaylist()
            fitz.TOOLS.mupdf_display_errors(True)
            zoom = self.get_zoom_from_fit()
            matrix = fitz.Matrix( zoom, zoom )
            page = self.pdf_document[page_number]   # ***** Previously used get_displaylist()
            scaled_pix = page.get_pixmap( matrix = matrix )
            qimage = QImage(scaled_pix.samples, scaled_pix.width, scaled_pix.height, scaled_pix.stride, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qimage)
            return pixmap

        else:
            return None
    
    # --------------------------------------------------------------
    #   Don't want to send a signal when the page is changed by moving the slider.
    #   Looks like no problem, just set's slider programmatically to current position already set manually.

    #   This was getting called twice because I was using the valueChanged signal, which
    #       is trigered on both user action AND when the slider position was changed programmatically.
    #       Switched to sliderMoved to trigger ONLY on user action.
    #   Emits native page_changed_signal and managed "sig_pdf_page_changed" signals
    #   page_changed_signal is used by controls to save page number and set slider position

    def refresh( self, send_signal ):
        # print( "/// at refresh" )
        #    print( ' --------------------------------- ' )
        #    print( "/// at refresh " )
        #    traceback.print_stack()
        #    print( ' --------------------------------- ' )
        #    print( '' )
        #    print( "/// at refresh " )

        s = Store()
        if not self.current_file or self.external_viewer:
            return

        self.mouse_start_pos = None
        self.mouse_state = 'up'

        if 0 <= self.current_page < self.page_count:            # /// PAGE
            qpixmap = self.get_image( self.current_page )       # *** Get PDF image here of given size/zoom
            if qpixmap:
                self.label.setPixmap( qpixmap )                 # *** Display PDF file here.

                #   /// WRW 7-Mar-2025 - Move following emit outside the 'if send_signal' block.
                #       to set slider position when pdf loaded

                # print( "/// calling emit page_changed_signal" )
                self.page_changed_signal.emit( self.current_page )   # Native - set slider position in controls.

                if send_signal:
                    # /// WRW 7-Mar-2025 - Move following emit inside the 'if send_signal' block.
                    #   To correct duplicate call to bl_media.py proc_sheet()

                    s.sigman.emit( "sig_pdf_page_changed", self.current_page+1 )  # Managed   /// PAGE Add 1 to return to user numbering

            else:
                self.label.setText( f"ERROR: get_image() failed, page: {self.current_page}")

        else:
            self.label.setText( f"Page '{self.current_page}' out of range '1' - '{self.page_count}'.")

    # --------------------------------------------------------------
    #   WRW 19-Apr-2025 - Try updating just pdf page, nothing else, call from resize. Try to reduce
    #       number of signals emitted on resize. Maybe packed too much into refresh()

    def refresh_size( self ):
        if not self.current_file or self.external_viewer:
            return

        if 0 <= self.current_page < self.page_count:            # /// PAGE
            qpixmap = self.get_image( self.current_page )       # *** Get PDF image here of given size/zoom
            if qpixmap:
                self.label.setPixmap( qpixmap )                 # *** Display PDF file here.

    # --------------------------------------------------------------
    #   Get zoom factor from current graph size, not saved graph size, and page size.
    #   'graph' terminology came from pysimplegui.

    def get_zoom_from_fit( self ):
        if self.pdf_document:
            # if self.current_page >= self.page_count:
            #     t = f"ERROR: Selected page {self.current_page +1} exceeds document page count {self.page_count +1}"
            #     self.conf.do_popup( t )
            #     self.current_page = self.page_count -1    # Fail gracefully with announcement

            # Get the visible area of the QLabel within the QScrollArea
            #   Visible area changes when scroll bars are added.
            #   Turn them on, get the dimensions with them on, then set back to as needed.
            #   This will sometimes leave a little blank space, better than have the bars on unnecessarily.

            self.scroll_area.setVerticalScrollBarPolicy( Qt.ScrollBarAlwaysOn )       # unnatural to be always on.
            self.scroll_area.setHorizontalScrollBarPolicy( Qt.ScrollBarAlwaysOn )

            visible_rect = self.scroll_area.viewport().rect()  # Visible area of the scroll viewport

            self.scroll_area.setVerticalScrollBarPolicy( Qt.ScrollBarAsNeeded )       # unnatural to be always on.
            self.scroll_area.setHorizontalScrollBarPolicy( Qt.ScrollBarAsNeeded)

            graph_width = visible_rect.width()                   
            graph_height = visible_rect.height()                   

            # print(f"Visible Area: {visible_rect.width()}x{visible_rect.height()}")

            fitz.TOOLS.mupdf_display_errors(False)  # Suppress error messages in books with alpha-numbered front matter.
           #  r = self.pdf_document[self.current_page].get_displaylist().rect
            r = self.pdf_document[self.current_page].rect       # LATER - understand why don't need displaylist from earlier work.
            fitz.TOOLS.mupdf_display_errors(True)
            self.page_height = (r.br - r.tr).y
            self.page_width =  (r.tr - r.tl).x

            if self.fit == 'Full':
                self.zoom = 1

            elif self.fit == 'Height':
                if self.current_page < self.page_count:
                    self.zoom = graph_height / self.page_height

            elif self.fit == 'Width':
                if self.current_page < self.page_count:
                    self.zoom = graph_width / self.page_width

            elif self.fit == 'Both':
                if self.current_page < self.page_count:
                    zoom_width = graph_width / self.page_width
                    zoom_height = graph_height / self.page_height
                    self.zoom = min( zoom_width, zoom_height )

            elif self.fit == 'User':        # After user adjusted zoom setting with +/-.
                return self.zoom

            else:
                self.zoom = 1

        return self.zoom
    
    # ---------------------------------------------------------------------------------------
    #   Handle key events ONLY in this widget.
    #   WRW 9-May-2025 - remove Qt.Key_Up, Qt.Key_Down, use for full-screen PDF display
    #       in GlobalShortcutFilter
    #   WRW 27-May-2025 - a little final tweaking. Add sensible scroll position on scrollwheel motion.
    #       Add fractional scrolling with keys. Remove Home and End, not really useful.
    #       event.accept() ONLY for keys we process here.
    #   WRW 9-June-2025 - More tweaking based on expected behavior and symmetry

    def keyPressEvent(self, event: QKeyEvent):
        s = Store()

        key_code = event.key()
        mods = event.modifiers()

        if False:
            key_name = self.get_key_name( key_code )
            print( f"/// code: {key_code}, {key_code:x} name: {key_name}, mods: {mods}" )

        # -----------------------------------------------------
        #   These are less useful but I don't want to eliminate entirely
        #   so put on <shift>.

        if False and mods == Qt.ShiftModifier:
            match key_code:
                case Qt.Key_Home:
                    self.first_page()
                    event.accept()  # Accept the event so it doesn't propagate further

                case Qt.Key_End:
                    self.last_page()
                    event.accept()  # Accept the event so it doesn't propagate further

                case _:
                    super().keyPressEvent(event)    # Pass all else along

        # -----------------------------------------------------
        #   WRW 31-May-2025 - disjunction working fine on Linux failed on MacOS.
        #       separate all keys cases. Also add Qt.KeypadModifier for macOS.
        #   WRW 2-June-2025 - Trying to get most useful keys on arrows.

        elif mods == Qt.NoModifier or mods == Qt.KeypadModifier:
            match key_code:
                case Qt.Key_Right:
                    self.scroll_by_fraction(0.25)
                    event.accept()  # Accept the event so it doesn't propagate further

                case Qt.Key_Space:
                    self.scroll_by_fraction(0.25)
                    event.accept()  # Accept the event so it doesn't propagate further

                case Qt.Key_Left:
                    self.scroll_by_fraction(-0.25)
                    event.accept()  # Accept the event so it doesn't propagate further

                case Qt.Key_Backspace:
                    self.scroll_by_fraction(-0.25)
                    event.accept()  # Accept the event so it doesn't propagate further

                case Qt.Key_Down:
                    s.sigman.emit( "sig_toggle_fullscreen" )
                    event.accept()  # Accept the event so it doesn't propagate further

                case Qt.Key_Up:
                    if self.fit != 'Width':
                        self.fit_h()
                    else:
                        self.fit_v()
                    event.accept()  # Accept the event so it doesn't propagate further

                # -------------------------------

                case Qt.Key_Home:
                    self.first_page()
                    event.accept()  # Accept the event so it doesn't propagate further

                case Qt.Key_PageUp:
                    self.previous_page(scroll_to_bottom_flag=False)
                    event.accept()  # Accept the event so it doesn't propagate further

                case Qt.Key_PageDown:
                    self.next_page()
                    event.accept()  # Accept the event so it doesn't propagate further

                case Qt.Key_End:
                    self.last_page()
                    event.accept()  # Accept the event so it doesn't propagate further

                # -------------------------------

                case Qt.Key_V:
                    self.fit_v()
                    event.accept()  # Accept the event so it doesn't propagate further

                case Qt.Key_H:
                    self.fit_h()
                    event.accept()  # Accept the event so it doesn't propagate further

                case Qt.Key_B:      # Mostly for testing
                    self.fit_b()
                    event.accept()  # Accept the event so it doesn't propagate further

                case _:
                    super().keyPressEvent(event)    # Pass all else along

    # ---------------------------------------------------------------------------------------

    def scroll_by_fraction(self, fraction: float):
        bar = self.scroll_area.verticalScrollBar()
        step = int(bar.pageStep() * abs(fraction))
        current = bar.value()

        if fraction > 0:                            # Scrolling down
            if current == bar.maximum():
                self.next_page()
            else:
                bar.setValue(bar.value() + step)
        else:                                       # Scrolling up
            if current == bar.minimum():
                self.previous_page()
            else:
                bar.setValue(bar.value() - step)

    def scroll_to_bottom( self ):
        bar = self.scroll_area.verticalScrollBar()
        bar.setValue(bar.maximum())

    def scroll_to_top( self ):
        bar = self.scroll_area.verticalScrollBar()
        bar.setValue(0)

    def wheelEvent(self, event: QWheelEvent):
        delta = event.angleDelta().y()  # Vertical scroll movement

        if delta > 0:
            self.previous_page()
            if self.current_page > 0:                               # WRW 9-June-2025
                QTimer.singleShot(0, self.scroll_to_bottom )

        elif delta < 0:
            self.next_page()
            if self.current_page < self.page_count -1:                 # WRW 9-June-2025
                QTimer.singleShot(0, self.scroll_to_top)

    # ---------------------------------------------------------------------------------------

    def get_key_name(self, key_code):
        return QKeySequence(key_code).toString()

    # ---------------------------------------------------------------------------------------

    def resizeEvent( self, event ):
        super().resizeEvent(event)
        # print( "/// Resize" )
        if self.gui_initialized:
            # self.refresh( True )      # WRW 19-Apr-2025 - testing reduced refresh
            self.refresh_size( )

    def showEvent(self, event):
        super().showEvent(event)
        # print("/// showEvent")
        if self.prep_gui_initialized:
            QTimer.singleShot(100, self.mark_gui_initialized)
            self.prep_gui_initialized = False                       # Can have multiple showEvent() calls

    # Set flag after all layout adjustments are completed

    def mark_gui_initialized(self):
        # print("/// GUI has fully initialized!")
        self.gui_initialized = True  # Now allow resizeEvent() to call refresh()

# ---------------------------------------------------------------------------------------

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        s = Store()

        container = QWidget()           # Main container widget
        layout = QVBoxLayout(container)
        hlayout = QHBoxLayout()

        self.pdf_viewer = PDFViewer()       # Instantiate the PDF viewer
        pdf_slider = PDFSlider( vertical=True )

        # Optionally add the controls
        show_controls = True  # Toggle this to include/exclude the controls

        if show_controls:
            controls = PDFControls()
            self.pdf_viewer.page_changed_signal.connect( controls.page_changed )    # *** connect to controls
            self.pdf_viewer.sig_pdf_changed.connect( controls.pdf_changed )

            layout.addWidget(controls)

            # Connect controls to viewer slots
            controls.first_page_clicked.connect(self.pdf_viewer.first_page)
            controls.next_page_clicked.connect(self.pdf_viewer.next_page)
            controls.previous_page_clicked.connect(self.pdf_viewer.previous_page)
            controls.last_page_clicked.connect(self.pdf_viewer.last_page)
            controls.fit_h_clicked.connect(self.pdf_viewer.fit_h)
            controls.fit_v_clicked.connect(self.pdf_viewer.fit_v)
            controls.zoom_in_clicked.connect(self.pdf_viewer.zoom_in)
            controls.zoom_out_clicked.connect(self.pdf_viewer.zoom_out)
            pdf_slider.page_slider_changed.connect(self.pdf_viewer.page_slider_changed)

        hlayout.addWidget(pdf_slider)
        hlayout.addWidget(self.pdf_viewer)
        layout.addLayout( hlayout )

        self.load_button = QPushButton( "Load" )
        layout.addWidget( self.load_button )
        self.load_button.clicked.connect( self.load_pdf )
        self.setCentralWidget(container)

    # ------------------------------------------------------

    def load_pdf( self ):
        path = '/home/wrw/Library/DL-Music_Books/Fake Books/Real Book Vol 2.pdf'
        self.pdf_viewer.load_pdf( file=path, page=1 )

# ---------------------------------------------------------------------------------------

if __name__ == "__main__":
    from bl_unit_test import UT
    from bl_style import StyleSheet
    s = UT()

    s.app = QApplication(sys.argv)
    s.app.setStyleSheet( StyleSheet )   # OK, unit test
    window = MainWindow()
    window.setWindowTitle("PDF Viewer with PyMuPDF")
    window.show()
    window.resize( 800, 500 )
    window.resizeEvent( None )
    sys.exit(s.app.exec())

# ---------------------------------------------------------------------------------------
