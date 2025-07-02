#!/usr/bin/env python3
# ------------------------------------------------------------------------------
#   birdland_qt.py - formerly qbird, bl-main.py - Main program for Birdland-Qt
# ------------------------------------------------------------------------------
#   The imports here up to do_splash_screen() are the  minimum required for splash screen.
#   Exclude all others to get splash screen up as quickly as possible. It may be possible
#   to do it earlier from bundled package but I have not explored it. Fast enough as is.

import os
import sys

# -------------------------------------------------------
#   WRW 16-Apr-2025 - Suppress noisy chat from multimedia after upgrade to pyside6 6.9
#       This has to be above import Const, which calls QCoreApplication, just keep it at the top.

os.environ["QT_LOGGING_RULES"] = "qt.multimedia.*=false"

# -------------------------------------------------------

from PySide6.QtCore import Qt                              
from PySide6.QtGui import QFont, QPixmap, QPainter, QFontMetrics, QColor
from PySide6.QtWidgets import QApplication, QSplashScreen, QDialog, QLabel, QVBoxLayout

from Store import Store
from bl_constants import Const

# -------------------------------------------------------
#   Need this even though not directly referenced. DON'T Comment Out!
#   Must be imported at least once. Has side effects when imported,
#   calls qRegisterResourceData().

import bl_resources_rc      

# -----------------------------------------------------------

# import faulthandler       #   REMINDER - Keep if ever have anothe SIGSEV.
# faulthandler.enable()     #   Works great.

# ------------------------------------------------------------------------------------
#   Do splash screen - almost unnecessary time-wise but neat, nevertheless.
#   Position in code is significant, must be after minimum-required imports but
#       befor all others to be beneficial.
#   Some initialization for later use as well as for the splash screen.
#   The QApplication.setAttribute() call needed to suppress an error message after 
#       I moved the splash just under the minimum required imports for the splash.
#   Do in function instead of inline to prevent the creation of globals.
#   Save s.splash for 'finish()' call later.

#   WRW 17-Apr-2025 - I noticed splash screen stopped appearing, perhaps I didn't notice
#       for several days, since the pyside6 upgrade. Not sure. Took a long time with
#       a lot of help from chat to realize it will not work and to replace it with a dialog.

#   WRW 17-Apr-2025 - A new approach to splash screen. Do as Dialog, not splash. A lot of
#       work but with chat's help got something reliable. Before the oneshot added in the 
#       call to do_main_continue() the dialog was reliable.
#       Leave original (do_splash_splash()) in case I ever want to go back to it.

def do_splash_splash():
    s = Store()
    s.Const = Const()                   # Constants, short var name since used a bit.

    # os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"         # /// WRW 3-May-2025 - porting ot MacOS
    # os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
    # QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)

    # sys.argv[0] = s.Const.BL_Program_Name       # /// WRW 3-May-2025, RESUME, hacky, trying to get name in macos menu

    QApplication.setAttribute(Qt.AA_ShareOpenGLContexts)    

    s.app = QApplication(sys.argv)
    s.originalStyle = s.app.style().objectName()

    # s.app.setApplicationName( s.Const.BL_Program_Name )      # /// WRW 3-May-2025 - porting to MacOS

    pixmap = QPixmap( s.Const.BL_Splash_Image )
    if pixmap.isNull():
        pixmap = QPixmap(600, 400)
        pixmap.fill(Qt.darkRed)

    s.splash = QSplashScreen(pixmap)
    # s.splash.setWindowFlag(Qt.WindowStaysOnTopHint)
    # s.splash.setWindowFlags(Qt.SplashScreen | Qt.WindowStaysOnTopHint)
    # s.splash.setWindowFlags(Qt.SplashScreen )

    s.splash.raise_()           # /// TESTING per chat
    s.splash.show()             # This is taking the majority of the time to get the splash up.
    s.splash.setFont( QFont("Arial", 16) )
    s.splash.showMessage (
        f"{s.Const.BL_Short_Title}  {s.Const.Version}",
        alignment=Qt.AlignBottom | Qt.AlignLeft,
        color=Qt.white
    )
    s.app.processEvents()         # for splash screen

# ------------------------------------------------------------------------------------
#   Splash screen window setup:
#       Qt.Tool: floating window that stays above the main window but doesn't appear in taskbar or Alt+Tab
#       Qt.FramelessWindowHint: removes native window borders and title bar
#       Qt.WA_TranslucentBackground: allows transparent background (if the splash image has alpha)
#       Qt.ApplicationModal: blocks interaction with other windows until splash is dismissed (optional)

class SplashDialog( QDialog):
    def __init__(self, pixmap: QPixmap):
        super().__init__(None, Qt.Tool | Qt.FramelessWindowHint)
      # self.setWindowModality(Qt.ApplicationModal)
      # self.setWindowFlag(Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowTitle("Splash")

        self.label = QLabel()
        self.label.setPixmap(pixmap)
        self.label.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout()
        layout.addWidget( self.label )
        self.setLayout(layout)
        self.setFixedSize( pixmap.size() )

    def getLabel( self ):
        return self.label

# ------------------------------------------------------------------------------

class makeSplashPixmap( QPixmap ):

    def __init__( self, pixmap: QPixmap, title: str, version: str ) -> QPixmap:
        s = Store()                 
        super().__init__( pixmap )

        if pixmap.isNull():
            print( "ERROR-DEV: pixmap is null at makeSplashPixmap()" )
            sys.exit(1)

        self.pixmap = pixmap
        self.size = pixmap.size()             # Returns QSize
        self.width = pixmap.width()           # Returns int
        self.height = pixmap.height()
    
        painter = QPainter( self.pixmap )
        # painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QColor("white"))
    
        xpos = 40            # from left
        ypos = self.height - 60   # From top
    
        self.progress_x = 40
        self.progress_y = 40

        # title_font = QFont("Sans Serif", 18, QFont.Bold)
        title_font = QFont("Arial", 18, QFont.Bold)             # WRW 3-May-2025 - Port to MacOS
        title_metrics = QFontMetrics(title_font)
        title_height = title_metrics.height()
    
        # version_font = QFont("Sans Serif", 12, QFont.Bold)
        version_font = QFont("Arial", 12, QFont.Bold)           # WRW 3-May-2025 - Port to MacOS
        version_metrics = QFontMetrics(version_font)
        version_height = version_metrics.height()
    
        painter.setFont( title_font )
        painter.drawText( xpos, ypos, title)
        ypos += version_height
    
        painter.setFont( version_font )
        painter.drawText( xpos, ypos, version)
        painter.end()

    # -------------------------------------------------------

    def setLabel( self, label ):
        self.label = label

    # -------------------------------------------------------

    def progress( self, txt ):
        s = Store()
        painter = QPainter( self.pixmap )
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QColor("white"))

        # font = QFont("Sans Serif", 10 )
        font = QFont("Arial", 10 )
        height = QFontMetrics(font).height()
        painter.setFont( font )
        painter.drawText( self.progress_x, self.progress_y, txt)
        painter.end()
        self.label.setPixmap( self.pixmap )     # Update label after every draw.
        self.label.repaint()

        self.progress_y += height

# ------------------------------------------------------------------------------

def do_dialog_splash():
    s = Store()
    s.Const = Const()                   # Constants, short var name since used a bit.

    QApplication.setAttribute(Qt.AA_ShareOpenGLContexts)    
    s.app = QApplication(sys.argv)
    s.originalStyle = s.app.style().objectName()

    s.splash_pix = makeSplashPixmap( QPixmap(s.Const.BL_Splash_Image), s.Const.BL_Short_Title, s.Const.Version )

    if s.splash_pix.isNull():
        print("ERROR-DEV: Splash image not found or invalid:", s.Const.BL_Splash_Image)
        sys.exit(1)

    s.splash = SplashDialog( s.splash_pix.pixmap )
    splash_label = s.splash.getLabel()
    s.splash_pix.setLabel( splash_label )
    s.splash.show()
    s.app.processEvents()       # Force paint before continuing

# ------------------------------------------------------------------------------------
#   Show the splash screen before any further includes and initialization.

if True:
    do_dialog_splash( )
else:
    do_splash_splash()

# =======================================================================================
#   Remainder of imports after splash screen

import re
import click
import sqlite3
from pathlib import Path
from functools import partial
import warnings
import traceback

from PySide6.QtCore import qInstallMessageHandler, QtMsgType, QTimer
from PySide6.QtCore import QObject, QEvent, Signal, QSettings, Slot, QSize

from PySide6.QtGui import QIcon, QPalette, QColor
from PySide6.QtWidgets import QMessageBox, QSizePolicy, QToolTip, QWidget

from bl_main_window import Build_UI
import bl_actions
from bl_media import Audio, JJazzLab, ChordPro, Midi, YouTube, PDF
from SignalManager import SigMan
from fb_config import Config
from fb_utils import FB
from bl_constants import MT
from fb_setlist import SetList
from bl_connections import MakeConnections, RegisterNonClassSignals
from fb_make_desktop import make_desktop

# import logging
# logging.basicConfig(level=logging.DEBUG)

# ------------------------------------------------------------------------------
#   Useful routine to show all properties of an object.

#        meta = self.position_display.metaObject()
#        for i in range(meta.propertyCount()):
#            prop_name = meta.property(i).name()
#            prop_value = button.property(prop_name)
#            print(f"{prop_name}: {prop_value}")

# ------------------------------------------------------------------------------------
#   WRW 16-May-2025 - try/except around app.exec() doesn't work to catch errors in
#       event loop, i.e. after gui starts. Chat recommended following. Catches
#       unhandled exceptions. Set just before event loop starts.

def exception_hook(extype, value, tb):
    trace = '<br>'.join(traceback.format_exception(extype, value, tb))
    txt = f"ERROR: unhandled exception in event loop:<br>type: '{extype}'<br>value: '{value}'<br>{trace}"
    txt = txt.replace( '\n', '<br>' )
    myMessageBox().Critical( txt )
    QApplication.quit()
    # sys.exit(1)

# ------------------------------------------------------------------------------------
#   Custom message handler to reduce/eliminate chatter from some of the audio functions.
#   Installed in do_main().

def message_handler( mode, context, message ):

    if mode == QtMsgType.QtWarningMsg or mode == QtMsgType.QtInfoMsg:
        # Ignore the messages from QMediaPlayer/QAudioOutput
        return  # Simply return and ignore these messages

    else:
        #   Print other messages (errors, etc.)
        sys.stderr.write( f"Mode:{mode}, {message}\n" )

# ------------------------------------------------------------------------------------
#   WRW 24-Mar-2025 - I wanted to use html in messages, not supported by the simple
#   QMessageBox.Information() and related static functions. Add more complete implementation.
#   Cannot be used until do_splash(), which creates the QApplication. OK after that, even
#   before window.show().
#   WRW 2-Apr-2025 - Tried many Chat approaches to make the message box get bigger horizontally but no luck,
#   lines keep wrapping. Finally, Google said to override showEvent and resizeEvent and set a fixed width.
#   But it looks terrible for most messages.

class myMessageBase( QMessageBox ):

    def __init__(self, parent=None):
        s = Store()
        super().__init__(parent)

        self.setWindowTitle(s.Const.BL_Short_Title )
        self.setTextFormat(Qt.RichText)          # Enable HTML
        self.setStandardButtons( QMessageBox.Ok )
        self.setMinimumSize(QSize(800, 600))  # Set a reasonable minimum

        # self.setSizeGripEnabled(True)
        # self.setTextInteractionFlags(Qt.TextSelectableByMouse)
        # self.adjustSize()
        # self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum )
        # self.setMinimumSize(1, 1)       # This needed to override unknown minimum sizes.
        # self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)

        # Optionally: allow resizing by user
        # self.setSizePolicy(self.sizePolicy().horizontalPolicy(),
        #                    self.sizePolicy().verticalPolicy())

        # Manually force layout updates
        # self.layout().activate()

        # self._fixed_width = 800         # This worked

    # def sizeHint(self):
    #     return QSize(800, 600)  # Suggested default size

    # def showEvent(self, event: QEvent):
    #     super().showEvent(event)
    #     self.setFixedWidth(self._fixed_width)

    # def resizeEvent(self, event: QEvent):
    #     super().resizeEvent(event)
    #     self.setFixedWidth(self._fixed_width)

# ------------------------------------------------------------------------------------

class myMessageBox( myMessageBase ):

    # ----------------------------------
    #   I got tired of the text for messages cluttering up the code with content at the left margin.
    #   Strip spaces at beginning of the line. Not needed with html but keep for reference

    def fix( txt ):
        txt = re.sub( ' +', ' ', txt )
        txt = re.sub( '\n ', '\n', txt )          # Remove space at beginning of line
        return txt

    # ----------------------------------
    #   CONSIDER - any need for more buttons, see:
    #       https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QMessageBox.html#PySide6.QtWidgets.QMessageBox.StandardButton
    #       and setInformativeText(), setDetailedText()

    def __init__(self, parent=None):
        s = Store()
        super().__init__(parent)

    def Info( self, txt ):
        self.setText(txt)
        self.setIcon(QMessageBox.Information )
        return self.exec()

    def Warn( self, txt ):
        self.setText(txt)
        self.setIcon(QMessageBox.Warning)
        return self.exec()

    def Critical( self, txt ):
        self.setText(txt)
        self.setIcon(QMessageBox.Critical)
        return self.exec()

    def Question( self, txt ):
        self.setText(txt)
        self.setIcon(QMessageBox.Question)
        self.setStandardButtons( QMessageBox.Yes | QMessageBox.No )
        return self.exec()

# ------------------------------------------------------------------------------------
#   WRW 24-May-2025 - I was doing this once manually, needed another time, so
#       got basis for this this from chat.

class myMessageOnce( myMessageBox ):
    def __init__( self, parent=None  ):
        s = Store()
        super().__init__(parent)
        self.settings = QSettings( str( Path( s.Const.stdConfig, s.Const.Settings_Config_File )), QSettings.IniFormat )

    def Info(self, key: str, text: str):
        shown = self.settings.value(f"msgOnce/{key}", False, type=bool)
        if not shown:
            super().Info( text )
            self.settings.setValue(f"msgOnce/{key}", True)

    def Warn(self, key: str, text: str):
        shown = self.settings.value(f"msgOnce/{key}", False, type=bool)
        if not shown:
            super().Warn( text )
            self.settings.setValue(f"msgOnce/{key}", True)

    def Critical(self, key: str, text: str):
        shown = self.settings.value(f"msgOnce/{key}", False, type=bool)
        if not shown:
            super().Critical( text )
            self.settings.setValue(f"msgOnce/{key}", True)

    #   Resets the shown state. If key is None, resets all.

    def reset(self, key: str = None):
        if key:
            self.settings.remove(f"msgOnce/{key}")
        else:
            self.settings.beginGroup("msgOnce")
            self.settings.remove("")  # removes all keys in the group
            self.settings.endGroup()

# ------------------------------------------------------------------------------------
#   WRW - 29-Mar-2025
#   WRW 25-May-2025 - chat sayss that eventFilter can be called with spurious events,
#       Check the event is instance of QEvent before processing. Non-QEvents will not have
#       a .type(), causing a failure othrwise. I may have been causing it by bogus return
#       elsewhere.

class GlobalShortcutFilter( QObject ):
    sig_toggle_fullscreen = Signal()
    sig_do_fullscreen = Signal()
    sig_exit_fullscreen = Signal()

    def __init__(self, parent=None):
        s = Store()
        super().__init__(parent)
        self.main_window = parent  # or pass in whatever you need
        s.sigman.register_signal( "sig_toggle_fullscreen", self.sig_toggle_fullscreen )
        s.sigman.register_signal( "sig_do_fullscreen", self.sig_do_fullscreen )
        s.sigman.register_signal( "sig_exit_fullscreen", self.sig_exit_fullscreen )

    def eventFilter(self, obj, event):
        s = Store()
        if not isinstance(event, QEvent):
            # print( "/// not event at eventFilter" )                          
            return False

        if not hasattr( event, 'type' ):
            # print( "/// no type() at eventFilter" )                          
            return False

        if event.type() == QEvent.KeyPress:
            key = event.key()
            mods = event.modifiers()

            #   WRW 3-May-2025 - porting to MacOS. That intercepts F11 so need to use Ctrl-Cmd-F
            #   Not getting correct mods in my testing.
            #   WRW 20-May-2025 - remove shift-meta-f, keep Down and F11 only.
            #   No, not even F11 for consistency on all platforms. F11 is full-screen for           
            #   app on Linux and Windows.

            if key == Qt.Key_Escape:
                s.sigman.emit( "sig_fullscreen_button_clicked" )

            # if key == Qt.Key_Up:
            #     s.sigman.emit( "sig_do_fullscreen" )
            #     return True                                 # Stop further processing

            # if key == Qt.Key_Down:
            #     s.sigman.emit( "sig_exit_fullscreen" )
            #     return True                                 # Stop further processing

            # if key == Qt.Key_Up:
            #     s.selectTab( MT.Viewer )
            #     return True                                 # Stop further processing

            # if key == Qt.Key_Down:
            #     s.sigman.emit( "sig_toggle_fullscreen" )
            #     return True                                 # Stop further processing

            # if key == Qt.Key_F11 or key == Qt.Key_Down:
            #     s.sigman.emit( "sig_toggle_fullscreen" )
            #     return True                                 # Stop further processing

            # elif key == Qt.Key_V and (mods & Qt.ControlModifier):       # WRW 9-Apr-2025 Ctrl-V to show viewer tab
            #     s.selectTab( MT.Viewer )
            #     return True                                 # Stop further processing

        return False        # Pass event to other widgets

# ------------------------------------------------------------------------------------
#   WRW 4-Apr-2025 - Exploring widget inspection for aid in finding supporting code.

class Inspector( QObject ):

    def __init__(self, parent=None):
        super().__init__(parent)

    def eventFilter(self, obj, event):
      # if event.type() == QEvent.MouseButtonPress:
        if isinstance(obj, QWidget) and event.type() == QEvent.MouseButtonPress:
            if event.button() == Qt.LeftButton and event.modifiers() & Qt.ShiftModifier:
                self.inspect( obj, event )
                return True     # Stop further processing
        return False            # Pass event to other widgets

    # ---------------------------------------------

    def inspect( self, widget, event ):
        s = Store()

        sig_info = s.sigman.get_info( widget )        # /// RESUME - possibly much later, no direct way to do it.
        policy = widget.sizePolicy()
        horizontal_policy = policy.horizontalPolicy().name
        vertical_policy = policy.verticalPolicy().name
        text_color = widget.palette().color(QPalette.Text)
        bg_color = widget.palette().color(QPalette.Base)
        # style_sheet = widget.styleSheet()         # Nothing interesting.

        info = f"""
Widget: {widget.__class__.__name__}
Object Name: {widget.objectName() or '(unnamed)'}
Geometry: {widget.geometry().getRect()}
Horizontal Policy: {horizontal_policy}
Vertical Policy: {vertical_policy}
Color: {text_color}
Background: {bg_color}
{sig_info or 'No signal data'}
"""
# Style: {style_sheet}
        pos = event.globalPosition().toPoint()
        QToolTip.showText(pos, info.strip(), widget)

# ------------------------------------------------------------------------------------
#   Initialize several classes and other variables used through the app.
#   Initialize all singletons here and pass instance with Store().
#   Instantiate all players / viewers here so do so only once and get instance to
#       pass to others (No or Rarely) and to use in do_full_exit().
#   Initialization needed for all here.                                                          

def initialize_modules():
    s = Store()                     # Global storage for few shared variables.

    #   The utility modules are used throughout by reference only to these variables.

    s.sigman = SigMan()                                 # OK - appropriate
    s.conf = Config( s.Options.confdir,
                     s.Options.userdatadir )    # OK - appropriate

    s.conf.update_dict()                                # OK - Tell data_dict to look at s.driver to add MYSQL-specific options
    s.fb = FB()                                         # OK - appropriate
    s.setlist = SetList()                               # OK - s.setlist required for late initialization

    #   Call media objects to initialize signals and slots
    #   Works OK but should I save return object in permanent storage to keep from going out of scope?
    #   Yes, this works because of the s.sigman registration keeps the object from going out of scope but it is
    #   best to save the object explicitly to prevent possible future problems. Put underscore 
    #   in name to remind me not to reference the objects directly, just through signals.

    s._audio =      Audio()
    s._jjazz =      JJazzLab()
    s._chord =      ChordPro()
    s._youtube =    YouTube()
    s._midi =       Midi()
    s._pdf =        PDF()

# ------------------------------------------------------------------------------------
#   Connect to database.

def OMIT_initialize_db_connection():
    s = Store()

    path = Path( s.conf.user_data_directory, s.conf.sqlite_database )

    if path.is_file():
        try:
            conn = sqlite3.connect( path )
            c = conn.cursor()
            dc = conn.cursor()
            dc.row_factory = sqlite3.Row

        except Exception as e:
            (extype, value, traceback) = sys.exc_info()
            # print( f"ERROR on connect() or cursor(), type: {extype}, value: {value}", file=sys.stderr )
            s.msgCritical( f"Connect to sqlite3 database '{path}' failed\ntype: {extype}\nvalue: {value}" )

        else:
            s.dc = dc
            s.c = c         # /// not sure 'c' is ever used anymore.

    else:
        s.msgCritical( f"Sqlite3 database file: '{s.conf.sqlite_database}' not found in user data directory: {s.conf.user_data_directory}" )

# ------------------------------------------------------------------
#   Exit code value not used.
#   I think best not to catch aboutToQuit signal in modules. Do here since we opened it here.
#   Close media via signal in media modules? Then we won't need to save is Store()
#   the module references but may need to save to keep from going out of scope.

@Slot()
def do_full_exit():
    s = Store()
    # print( "/// do_full_exit" )

    if s.sigman.sig_registered( "sig_stopping" ):
        s.sigman.emit( "sig_stopping" )         # Stop/close media. Save tab order. Maybe more later.

    if s.conn:
        s.conn.close()

    if s.record:
        s.recorder.save()

    if hasattr( s, 'worker_thread' ) and s.worker_thread and s.worker_thread.isRunning():
        s.worker_thread.stop()

# ------------------------------------------------------------------------------------
#   Above called by Qt aboutToQuit signal, window not visible then. Do
#       this earlier from closeEvent

@Slot()
def preparing_to_exit():
    s = Store()
    if s.window.isVisible():
        settings = QSettings( str( Path( s.Const.stdConfig, s.Const.Settings_Config_File )), QSettings.IniFormat )
        settings.setValue("geometry", s.window.saveGeometry())
        settings.setValue("isMaximized", s.window.isMaximized())
        settings.setValue("isFullScreen", s.window.isFullScreen())
        settings.setValue("windowState", s.window.saveState())

# ------------------------------------------------------------------------------------

class Options():        # Just to hold command-line options
    pass

# ------------------------------------------------------------------------------------
#   WRW 30-Mar-2025 - Only a few now used in present work.
#   def do_main( verbose, very_verbose, confdir, database, progress, log, record, playback ):
#   WRW 17-Apr-2025 - Split do_main() into two pieces with oneshot triggering the second, do_main_continue_a().
#   This gives Qt an opportunity to paint the splash screen.

# @click.option( "-V", "--very_verbose", is_flag=True,    help="Show events" )
# @click.option( "-l", "--log",      is_flag=True,        help="Capture logging data" )

@click.command()
@click.option( "-c", "--confdir",                       help="Use alternate config directory" )
@click.option( "-u", "--userdatadir",                   help="Use alternate user-data directory" )
@click.option( "-d", "--database",                      help="Use database sqlite or mysql, default sqlite", default='sqlite' )
@click.option( "-p", "--progress", is_flag=True,        help="Show initialization progress to stderr" )
@click.option( "-v", "--verbose",  is_flag=True,        help="Show system info and media activity" )
@click.option( "-r", "--record",                        help="Record user interactions" )
@click.option( "-R", "--playback",                      help="Playback user interactions" )
@click.option( "-D", "--debug", is_flag=True,           help="Debug - enable selected messages" )

def do_main( confdir, userdatadir, database, progress, verbose, record, playback, debug ):
    s = Store()                                 # Global store, short var name since used a lot.
    QTimer.singleShot(100, lambda: do_main_continue_a( confdir, userdatadir, database, progress, verbose, record, playback, debug ))

    sys.excepthook = exception_hook         # WRW 16-May-2025 - catch exceptions in event loop.
    sys.exit( s.app.exec() )

# ----------------------------------------------------------
#   This is an attempt to pick up exceptions that occur while the splash screen
#   is still up and caused a hang.

def do_main_continue_a( confdir, userdatadir, database, progress, verbose, record, playback, debug ):
    s = Store()                                 # Global store, short var name since used a lot.

    try:
        do_main_continue_b( confdir, userdatadir, database, progress, verbose, record, playback, debug )

    except Exception:
        (extype, value, xtraceback) = sys.exc_info()

        # print( f"ERROR in do_main_continue_a() type: {extype}, value: {value}", file=sys.stderr )
        # traceback.print_exc()               # WRW 21-Apr-2025 - Want entire stack as if not caught.

        # -------------------------------------------
        #   WRW 16-May-2025 - Show a popup on this failure, otherwise stdout/stderr going
        #   down the tubes in bundled packaging.

        trace = '<br>'.join(traceback.format_exception(extype, value, xtraceback ))
        txt = f"ERROR unhandled exception during startup:<br>type: '{extype}'<br>value: '{value}'<br>{trace}"
        txt = txt.replace( '\n', '<br>' )
        myMessageBox().Critical( txt )

        # -------------------------------------------

        if True:
            s.splash.close()                # Out of an abundance of OCD caution. quit() below should do it.
        else:
            s.splash.finish( s.window )

        QApplication.quit()

# ----------------------------------------------------------
#   WRW 17-Apr-2025 - Continue with original content of do_main() after a short oneshot enclosure in and try/except.

def do_main_continue_b( confdir, userdatadir, database, progress, verbose, record, playback, debug ):
    s = Store()                                 # Global store, short var name since used a lot.
    s.splash_pix.progress( "Startup" )

    # --------------------------------------------------------------------
    #   Process command line options.
    #   Tried moving this above a separate function - do_process() - but that never returned
    #   because of some magic inside @click. Keep it as it was but introduce Options() to
    #   store the command line options.

    # s.Options.very_verbose = very_verbose
    # s.Options.log = log

    # -------------------------------------------------------
    #   Establish values for confdir and userdatadir from command line or s.Const.
    #       s.Const already instantiated in do_dialog_splash()
    #       s.Options.confdir et.al. passed to Config() in initialize_modules()
    #       removed from all check/init calls here.

    if not confdir:
        confdir = s.Const.Confdir                                                                  

    if not userdatadir:
        userdatadir = s.Const.Datadir

    s.Options = Options()
    s.Options.confdir = confdir
    s.Options.userdatadir = userdatadir     # WRW 19-May-2025 - added --userdatadir option, mostly for testing.
    s.Options.verbose = verbose
    s.Options.database = database
    s.Options.progress = progress
    s.Options.record = record
    s.Options.playback = playback
    s.Options.debug = debug

    # --------------------------------------------------------------------
    #   s.driver is used extensively, define it here and preserve it as is even though a little awkward.

    match database:
        case 'sqlite':
            s.driver = { 'mysql' : False, 'sqlite' : True, 'fullword' : False }         # always do this early, used elsewhere

        case 'mysql':
            s.driver = { 'mysql' : True, 'sqlite' : False, 'fullword' : False }         # always do this early, used elsewhere

        case _:
            print( f"ERROR: Unexpected --database option value {database}", file=sys.stderr )
            sys.exit(1)

    # --------------------------------------------------------------------
    #   Install the message handler to suppress unwanted messages
    #   Filter warning message
    #       The warning is caused by changes introduced in Python 3.12, 
    #       which now enforces that all built-in types must have a __module__ attribute.
    #       Malcolm is testing on MacOS with Python 3.12 most likely and got the warning.

    qInstallMessageHandler( message_handler )
    warnings.filterwarnings("ignore", message=".*swigvarlink.*", category=DeprecationWarning)   # WRW 20-Apr-2025

    # s.app.setQuitOnLastWindowClosed(True)     # CONSIDER - study need?

    # --------------------------------------------------------------------
    #   Store() implements global store pattern for a small number of values needed throughout.
    #   Note that s.app is already defined in do_splash()

    s.Const.set( 'Me', __file__ )
    s.python = sys.executable                   # Needed to run external commands when no shebang support
    s.app.aboutToQuit.connect( do_full_exit )   # Catch Qt quit

    # ----------------------------------
    #   Deal with a few command-line options
    #   Separate option to debug signals? No, working fine.
    #   verbose and very_verbose not well thought out and barely used beyond debugging.

    s.verbose = verbose
    # s.very_verbose = very_verbose
    # if s.very_verbose:                  # very_verbose implies verbose
    #     s.verbose = True

    # ----------------------------------
    #   Some early initialization

    s.icon = QIcon( s.Const.BL_Icon_PNG )   # Maybe just reference directly where s.icon is used?
    s.app.setWindowIcon( s.icon )

    #   For short name to replace s.conf.do_popup()

    s.msgInfo =     myMessageBox().Info           
    s.msgWarn =     myMessageBox().Warn
    s.msgCritical = myMessageBox().Critical
    s.msgQuestion = myMessageBox().Question

    s.msgInfoOnce =     myMessageOnce().Info            # s.msgInfoOnce( key, text )
    s.msgWarnOnce =     myMessageOnce().Warn
    s.msgCriticalOnce = myMessageOnce().Critical        # Meaningless to show a question only once.
    s.msgOnceReset =    myMessageOnce().reset           # s.msgInfoReset( key )

    # ----------------------------------
    #   Initialize a small number of modules and database connections
    #   WRW 1-Feb-2025 - moved get_config() and set_class_variables() into fb_config.py->Config()
    #   WRW 25-Mar-2025 - moved back here, 

    s.splash_pix.progress( "Initialize modules" )

    initialize_modules( )
    s.sigman.set_verbose( s.verbose )         # after initialize_modules so s.sigman is defined

    if s.Options.record:
        s.sigman.set_record( s.Options.record )

    s.sigman.register_slot( "slot_preparing_to_exit", preparing_to_exit )
    s.Const.set( 'theme', s.conf.get_appearances())  # Computed dynamically from ':palettes.csv' and more

    # ----------------------------------
    #   Set Default theme for coldstart messages before config file available.
    #   WRW 7-Apr-2025 - Keep in. The other themes don't make a lot of sense.
    #   WRW 21-May-2025 - This is needed so have icon color set when showing the
    #   config popup during first-start to get user/password for mysql DB.
    #   Use defaults that should be available.

    s.conf.setStyle( "Fusion" )                                     
    s.conf.setAppearance( "Dark-Blue" )

    # =======================================================================================
    #   WRW 25-Mar-2025 - BEGIN MIGRATION of initialization code below from prior birdland.py
    #   /// RESUME - move this code into separate functions? In bl_startup.py when implement that.
    # =======================================================================================

    s.splash_pix.progress( "Check configuration" )
    announce = 0

    # -----------------------------------------------------------------------
    #   WRW 20-May-2025 - I stumbled down a rabbit hole of a mess while trying to
    #   simply add the --userdatadir option. I'm rewriting the confdir check and
    #   initialization code to clean up the worts.

    if True:
        results, success = s.conf.check_config_directory()
        if not success:
            if s.Options.progress:
                print( f"Initializing config directory {s.Options.confdir}:", file=sys.stderr )
                print( '\n'.join( results ), file=sys.stderr )
            s.conf.initialize_config_directory()                                                                  
            announce += 1

    # -----------------------------------------------------------------------
    else:
        #   Some simple tests of configuration. First half can be done before get_config().
        results, success = s.conf.check_home_config( s.Options.confdir )
        if not success:
            if s.Options.progress:
                print( "Initializing home configuration:", file=sys.stderr )
                print( '\n'.join( results ), file=sys.stderr )
            s.conf.initialize_home_config( s.Options.confdir )      # Need confdir to test if should have .birdland in home dir.
            announce += 1

        results, success = s.conf.check_specified_config( s.Options.confdir )
        if not success:
            if s.Options.progress:
                print( "Initializing specified configuration:", file=sys.stderr )
                print( '\n'.join( results ), file=sys.stderr )

            s.conf.initialize_specified_config( s.Options.confdir )
            announce += 1

    # -----------------------------------------------------------------------
    #   WRW 1-Apr-2025 - Check and copy bundled data to AppData location

    results, success = s.conf.check_user_data_dir()
    if not success:
        if s.Options.progress:
            print( "Initializing user data directory:", file=sys.stderr )
            print( '\n'.join( results ), file=sys.stderr )
        s.conf.initialize_user_data_dir()
        announce += 1

    # -----------------------------------------------------------------------
    #   *** Bang! Get configuration.

    s.conf.get_config()

    # -----------------------------------------------------------------------
    #   WRW 3 Mar 2022 - Check for a config 'Host' section for hostname after get_config()
    #       but before anything using the config.

    results, success = s.conf.check_hostname_config()
    if not success:
        if s.Options.progress:
            print( "Initializing hostname configuration:", file=sys.stderr )
            print( '\n'.join( results ), file=sys.stderr )
        s.conf.initialize_hostname_config()
        announce += 1

    # -----------------------------------------------------------------------
    #   Update conf.v data and source <--> src mapping.
    #   Call at very specific place in start-up sequence because of first-launch strategy.
    #   Must be below initialize_hostname_config()

    s.conf.set_class_variables()

    # -----------------------------------------------------------------------
    #   WRW 20-May-2025 - Added for consistency with build_tables.py
    #   Another check for pathological cases. By now
    #   all should be set up but this may help in unusual testing cases.

    results, success = s.conf.check_confdir_content()
    if not success:
        txt = f"Config directory {s.Options.confdir} missing one or more expected files\n"
        txt += '\n'.join( results )
        txt += "Attempting to repair directory"
        s.msgWarn( txt )
        s.conf.initialize_config_directory_content()

    # -----------------------------------------------------------------------

    if announce:
        s.conf.report_progress()
        announce = 0

    # -----------------------------------------------------------------------
    #   WRW 15-May-2025 - Now make Music-Index dir if not there and build it
    #       with converted raw indexes. Previously was shipping Music-Index but
    #       no need as can be built from raw indexes.

    results, success = s.conf.check_music_index_dir()
    if not success:
        if s.Options.progress:
            print( "Initializing user data Music-Index directory:", file=sys.stderr )
            print( '\n'.join( results ), file=sys.stderr )
        s.conf.initialize_music_index_dir()
        announce += 1

    # -----------------------------------------------------------------------

    if announce:
        s.conf.report_progress( )

    # -----------------------------------------------------------------------
    #   Need a user and password for MySql. On initial startup will not have it.

    #   Some more simple tests of configuration.
    #   Second half must be done after get_config() as it may need DB credentials and other config data.
    #   May already have database in confdir under certain circumstances:
    #       Specified confdir at first execution, then none on later execution so using home confdir.

    MYSQL, SQLITE, FULLTEXT = s.driver.values()

    results, success = s.conf.check_database( s.Options.database )
    if not success:
        res = True
        if s.Options.progress:
            print( "Initializaing database configuration:", file=sys.stderr )
            print( '\n'.join( results ), file=sys.stderr )

        if MYSQL:       # If check_database() failed for mysql it is likely because of user credentials.
            res = s.conf.get_user_and_password( )

            if res:
                s.conf.initialize_database( s.Options.database )        # Try after get DB credentials above.

            else:
                txt = """Can't continue without user credentials for MySql database.<br>
                         Please provide valid credentials or launch without the <i>-d mysql</i> option.<br>
                         <br>Click OK to exit.
                     """

                s.msgCritical( txt )
                sys.exit(1)

        if SQLITE:
            s.conf.initialize_database( s.Options.database )

    # -----------------------------------------------------------------------
    #   Prepare connection to database.

    have_db = False

    # -----------------------------------------------
    MYSQL, SQLITE, FULLTEXT = s.driver.values()

    if MYSQL:
        try:
            import MySQLdb
            conn = MySQLdb.connect( "localhost", s.conf.val( 'database_user' ), s.conf.val( 'database_password' ), s.conf.mysql_database )
          # c = conn.cursor()
            dc = conn.cursor(MySQLdb.cursors.DictCursor)
            have_db = True
            s.dc = dc

        except Exception as e:
            (extype, value, traceback) = sys.exc_info()
            print( f"ERROR on connect() or cursor(), type: {extype}, value: {value}", file=sys.stderr )

    # -----------------------------------------------
    elif SQLITE:
        def trace_callback( s ):                                      # Helpful for debugging
            print( "Trace Callback:", s )

        if Path( s.conf.user_data_directory, s.conf.sqlite_database ).is_file():
            try:
                conn = sqlite3.connect( Path( s.conf.user_data_directory, s.conf.sqlite_database ))      # This will create file if not exists. Can't use it to test for existence.
              # conn.set_trace_callback( trace_callback )                           
                c = conn.cursor()
                dc = conn.cursor()
                dc.row_factory = sqlite3.Row
                s.dc = dc

            except Exception as e:
                (extype, value, traceback) = sys.exc_info()
                print( f"ERROR on connect() or cursor(), type: {extype}, value: {value}", file=sys.stderr )

            else:
                # conn.enable_load_extension(True)                      # Problem with fulltext caused by absence of this?
                # conn.load_extension("./fts3.so")                      # this doesn't exist.
                # c.execute( ".load /usr/lib/sqlite3/pcre.so" )         # This does not work, how load .so file. Perhaps this will be faster than my implementation.
                # sqlite3.enable_callback_tracebacks(True)              # This is very helpful for debugging
                # conn.create_function('regexp', 2, s.fb.regexp)        # This worked but not well. Perhaps with a little more work?
                # conn.create_function('my_match', 2, s.fb.my_match )   # This works great but is slower than LIKE.

                conn.create_function('my_match_c', 2, s.fb.my_match_c ) # This works great and is fast.
                have_db = True

                # s.dc.execute( "SELECT COUNT(*) FROM titles_distinct" ); print( [ row.keys() for row in s.dc.fetchall() ] )

    # -----------------------------------------------
    else:
        print( "ERROR-BUG: No database type specified", file=sys.stderr )
        sys.exit(1)

    # -----------------------------------------------
    #   Think about what to do here. I believe we should now always have a database by this point.

    if not have_db:
        print( "ERROR-BUG: Connect to database failed after initialization", file=sys.stderr )
        sys.exit(1)
        # conf.do_configure( first=True, confdir=confdir )
        # return

    # --------------------------------------------------------------------
    #   Platform-specific code.

    #   Make a .desktop file for launching birdland.
    #   This is file in ~/.local/share/applications used by the application launcher.

    if s.Const.Platform == 'Linux':
        make_desktop()       

    elif s.Const.Platform == 'MacOS':
        # default_font = QFont("Helvetica Neue", 13)        # /// RESUME - porting to MacOS, did nothing.
        # s.app.setFont(default_font)

        #   WRW 19-May-2025 - PATH issue, couldn't find fluidsynth when running from bundle. PATH is not inherited.
        current_paths = os.environ.get("PATH", "").split(os.pathsep)
        combined = s.Const.MacExtraPaths + [p for p in current_paths if p not in s.Const.MacExtraPaths ]
        os.environ["PATH"] = os.pathsep.join(combined)

    # =======================================================================================
    #   END MIGRATION from prior birdland.py
    # =======================================================================================
    #   Put a few values in Store()
    #   A few utility shortcuts for main tabbar tab management 
    #   via signals just for convenience.

    s.selectTab   =         partial( s.sigman.emit, "sig_select_tab" )
    s.setTabVisible =       partial( s.sigman.emit, "sig_set_tab_visibility" )
    s.toggleTabVisible =    partial( s.sigman.emit, "sig_toggle_tab_visibility" )

    s.Settings = s.conf.val     # MIGRATION - migrate to this form where called: s.Settings( 'music_file_root' )
                                # Good idea but not worth changing many, many lines of code. Perhaps as work in code.

    # ----------------------------------
    #   Deal with styles / appearances
    #   'Darwin' for MacOS
    #   Chat said to do this BEFORE building the UI, made big difference in startup time.
    #   Note that icons are updated AFTER building the UI and also in bl_menu_actions.py after
    #   changing the style or appearance.

    style = s.conf.val( 'style' )           # 'Darwin' for MacOS
    theme = s.conf.val( 'theme' )

    s.conf.setStyle( style )
    s.conf.setAppearance( theme )

    # ----------------------------------
    #   Build UI

    s.splash_pix.progress( "Build User Interface" )

    s.window = Build_UI()

    shortcut_filter = GlobalShortcutFilter( s.window )
    s.app.installEventFilter(shortcut_filter)

    # inspector = Inspector( s.window )             # /// RESUME if interesting, interfered with thumbnail browser
    # s.app.installEventFilter( inspector )

    # ----------------------------------
    #   Manage signals after all imports and after UI is
    #       built so all UI elements are already created and named,
    #       signals and slots are defined.
    #       Make connections after all sigs and slots registered.

    s._sigs = RegisterNonClassSignals()     # Register signals used outside of classes. Keep class in scope to be safe.
    bl_actions.register_action_slots()      # Register subset of slots not registered elsewhere
    MakeConnections()                       # Connect signals and slots

    # ----------------------------------
    #   Draw SVG icons on buttons after the UI is built and signals registered and connected.
    #   WRW 1-May-2025 - Moved down to point after signals registered and connected.

    s.conf.updateIcons( theme )

    # ----------------------------------
    #   Late initialization, after all modules instiatiated, ui built,
    #       signals and slots registered and connected.

    s.setlist.initialize()              # Populate setlist combo boxes. Must be after make_connections()
    s.sigman.emit( "sig_starting" )     # Restore tab order, maybe more later.

    s.setTabVisible( MT.Reports, False) # /// TRANSIENT, until restore order also restores visibility
    s.setTabVisible( MT.Results, False) # /// TRANSIENT, until restore order also restores visibility

    s.setTabVisible( MT.Edit, s.conf.val( 'show_canon2file_tab' ) )                                                       
    s.setTabVisible( MT.IMgmt, s.conf.val( 'show_index_mgmt_tabs' ))                                                       

    s.selectTab( MT.Viewer )            # Select tab for initial appearance.

    # ----------------------------------
    #   Restore prior position and state. If none use default geometry.

    settings = QSettings( str( Path( s.Const.stdConfig, s.Const.Settings_Config_File )), QSettings.IniFormat )
    s.window.setMinimumSize(1, 1)                   # This needed to override unknown minimum sizes.
    s.window.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)

    geometry = settings.value("geometry")

    if geometry is not None:
        s.window.restoreGeometry(geometry)
    else:
        size = QApplication.primaryScreen().size()
        width = size.width()
        height = size.height()
        width = min( 1800, width )              # /// Don't want it too big on my desktop
        height = width/1.61                     # Golden rectangle ratio
        s.window.resize( width*.8, height*.8 )

    state = settings.value("windowState")
    if state is not None:
        s.window.restoreState(state)

    if settings.value("isFullScreen") == "true":
        s.window.showFullScreen()

    elif settings.value("isMaximized") == "true":
        s.window.showMaximized()

    else:
        s.window.show()

    # --------------------------------------------------------------------
    #   Load documentation for initial content of pdf display

    s.sigman.emit( "sig_showFt", s.Const.QuickStartFile, None, "Birdland-Qt Quick-Start Guide" )

    # ----------------------------------
    #   Finally close the splash screen. Application already exec()'ed

    def finish_splash():
        if s.splash:
            if True:
                s.splash.close()
            else:
                s.splash.finish( s.window )

            s.splash = None  # only after it's safely closed

        # -----------------------------------------------------------

        if s.Options.playback:
            s.sigman.do_playback( s.Options.playback )

        # -----------------------------------------------------------
        #   WRW 20-May-2025 - Give focus to Title search box.
        #       Do late so nothing else steals focus. Finally, works.
        #       Trying inside onshot. Seems OK here.

        s.sigman.emit( "sig_title_focus" )

        # -----------------------------------------------------------

    QTimer.singleShot(50, finish_splash )

    # --------------------------------------------------------------------

    # t = s.app.exec()          # This now done much earlier.
    # sys.exit( t )

# -------------------------------------------------------------------------------------
#   main() is the entry point when packaged with PyInstaller (or invoked as python -m birdland NA currently).
#       birdland_qt.py -> __main__.py

def main():
    do_main()

if __name__ == '__main__':
    do_main()

# ---------------------------------------------------------------------------------------
