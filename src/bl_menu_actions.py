#!/usr/bin/python
# ------------------------------------------------------------------------------------
#   WRW 6-Feb-2025
#   Functions here implement the actions for the menu bar and possibly icons if I ever add them.
#   Some of the underlying code is in fb_utils.py
# ------------------------------------------------------------------------------------

import sys
import os
from pathlib import Path
import platform
import sqlite3
import fitz
import configobj                 
import datetime
import ctypes

from PySide6 import QtCore
from PySide6.QtCore import QStandardPaths, QObject, Signal, Qt
from PySide6.QtCore import QFile, QTextStream
from PySide6.QtGui import QIcon, QPixmap, QGuiApplication
from PySide6.QtWidgets import QDialog, QLabel, QTextEdit, QPushButton, QVBoxLayout, QHBoxLayout
from PySide6.QtWidgets import QMessageBox
from PySide6.QtMultimedia import QAudioOutput, QMediaDevices, QMediaFormat
from PySide6.QtWidgets import QApplication, QStyleFactory

# from PDF_Viewer import PDFViewer, PDFControls

import fb_menu_stats
from Store import Store
from bl_constants import MT  #, audioFileTypes, DocFile

# ------------------------------------------------------------------------------------

class About_Window(QDialog):
    def __init__(self, info_text ):
        super().__init__()
        # from bl_style import getStyleSheet        # No longer needed after apply style to app, not central_window
        # self.setStyleSheet( getStyleSheet() )       # OK commented out

        s = Store()

        self.setWindowTitle( f"About {s.Const.BL_Short_Title}")
        self.setWindowIcon(s.icon)

        layout = QVBoxLayout()
        titleLayout = QHBoxLayout()

        sax = QLabel(self)
        sax.setPixmap(s.icon.pixmap(64, 64))  # Adjust the size as needed
        sax.setFixedSize(64, 64)     # Set the label size
        titleLayout.addWidget( sax )

        title= QLabel( s.Const.BL_Long_Title )
        title.setObjectName( "aboutTitle" )
        titleLayout.addWidget( title )
        layout.addLayout( titleLayout )

        label1 = QLabel( f"Version: {s.Const.Version}")
        label1.setObjectName( "aboutVersion" )
        layout.addWidget(label1)

        label2 = QLabel( s.Const.Copyright )
        label2.setObjectName( "aboutCopyright" )
        layout.addWidget(label2)

        label3 = QLabel( "This software and index data is licensed under the MIT License with Non-Commercial Clause.")
        label3.setObjectName( "aboutLicense" )
        layout.addWidget(label3)

        # Multi-line text box
        self.text = QTextEdit()
        self.text.setObjectName( "aboutText" )
        self.text.setText( info_text )
        layout.addWidget(self.text)

        button_layout = QHBoxLayout()
        button_layout.addStretch()                                   
        ok_button = QPushButton("Close")
        ok_button.clicked.connect(self.accept)  # Closes the dialog
        button_layout.addWidget(ok_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        # Set a fixed size for the about popup
        self.resize(1000, 600)

# ------------------------------------------------------------------------------------

class OutputRedirector:
    def __init__(self):
        pass

    def write(self, text):
        s = Store()
        s.sigman.emit( "sig_addto_results", text )

        # self.text_widget.moveCursor(QTextCursor.End)
        # self.text_widget.insertPlainText(text)
        # self.text_widget.ensureCursorVisible()

    def flush(self):
        pass  # Needed to conform to file-like interface

# ------------------------------------------------------------------------------------

def process_menu_action( menu_action ):
    s = Store()
    save_stdout = None

    # ----------------------------------------------------------------------------
    #   WRW 24-Mar-2025 - Redirect print into the results tab for selected menu items.

    if menu_action in [
        'menu-show-children', 'menu-show-widgets', 'menu-show-objects', 'menu-show-styles',
        'menu-show-global-store', 'menu-show-managed-signals', 'menu-show-screens', 'menu-show-constants',
        'menu-show-settings', 'menu-show-native-signals', 'menu-show-class-hierarchy',
        'menu-show-datadict', 'menu-initialize-data-dir', 'menu-initialize-config-dir',
        'menu-show-globals', 'menu-show-palette',
        ]:

        s.setTabVisible( MT.Results, True )
        s.selectTab( MT.Results )
        s.sigman.emit( "sig_clear_results" )

        save_stdout = sys.stdout
        sys.stdout = OutputRedirector()

    # ----------------------------------------------------------------------------

    match menu_action:
        case 'menu-about':
            do_about()

        case 'menu-about-qt':
            QMessageBox.aboutQt(None )

        case 'menu-contact':
            do_contact()

        case 'menu-license':
            do_license()

        case 'menu-website':
            do_website()

        case 'menu-locations':
            do_locations()

        # case 'menu-file-info':
        #     s.sigman.emit( 'sig_show_file_info', 'foo' )

        case 'menu-tutorial':
            s.selectTab( MT.Viewer )
            s.sigman.emit( "sig_showFt", s.Const.DocFile, None, s.Const.BL_Long_Title )

        case 'menu-quickstart-guide':
            s.selectTab( MT.Viewer )
            s.sigman.emit( "sig_showFt", s.Const.QuickStartFile, None, 'Birdland-Qt Quick-Start Guide')

        case 'menu-configuration-guide':
            s.selectTab( MT.Viewer )
            s.sigman.emit( "sig_showFt", s.Const.ConfigurationFile, None, 'Birdland-Qt Configuration Guide')

        case 'menu-configure':
            mediaRoots = [ 'music_file_root', 'audio_file_root', 'midi_file_root', 'chordpro_file_root', 'jjazz_file_root' ]
            oldRoots = [ s.conf.val( x ) for x in mediaRoots ]

            old_style = s.conf.val( 'style' )
            old_theme= s.conf.val( 'theme' )

            s.conf.do_configure()               # *** Bang *** - Show configuration window
            s.conf.set_class_variables( )       # Update conf.v data and source <--> src mapping.

            new_style = s.conf.val( 'style' )
            new_theme = s.conf.val( 'theme' )

            if old_style != new_style:
                s.conf.setStyle( new_style )
                # s.conf.updateIcons()

            if old_theme != new_theme:
                s.conf.setAppearance( new_theme )
                s.conf.updateIcons( new_theme )

            # ---------------------------------------------------
            #   WRW 31-May-2025 - I want the browsers in the left panel to
            #   update if the media roots configuration changes.
            #   Updating all independent of any changes appears to be ok,
            #   no noticeable lag. Perhaps test for changes to be more OCD.
            #   Yes, but update all if any root changes.

            newRoots = [ s.conf.val( x ) for x in mediaRoots ]
            if oldRoots != newRoots:
                s.sigman.emit( "sig_update_browsers_root" )

            # ---------------------------------------------------

        case 'make-thumbnails':
            s.sigman.emit( 'sig_make_thumbnails' )

        # ------------------------------------------------------------------
        #   WRW 30 Mar 2022 - A little different.

        case cmd if cmd.startswith("menu-stats"):
            t = menu_action.removeprefix( 'menu-stats-' )
            fb_menu_stats.do_menu_stats( t )

        # ------------------------------------------------------------------
        #   WRW 29 May 2022 - After a lot of time invested in support for the self-contained packages I
        #       decided not to use them for now and probably for ever. They are huge and no real benefit
        #       other than simplicity. Back off from that now. Now execute the build_tables.py command
        #       that is definitely here rather than bl-build-tables linked to above that may not be
        #       in .local/bin if the install command is not run and are executed from the cloned or
        #       unzipped directory, a possibility for some users. The birdland,
        #       bl-build-tables, and bl-diff-index links are for convenience so don't have to expose
        #       the *py file names and include 'bl-' in name to reduce likelihood of conflict.
        #   WRW 22-Mar-2025 - Added s.python to command after testing on Windows, with no shebang support.
        #   WRW 30-Mar-2025 - Converted all as_posix() to str(). We definitely don't want posix names on Windows.

        case 'menu-rebuild-all':
            s.fb.run_external_command( [ s.python, './build_tables.py', '--all', '-c', str( s.conf.confdir ), '-u', str( s.conf.user_data_directory ), '-d', s.fb.get_driver() ] )

        case 'menu-rebuild-source-priority':
            s.fb.run_external_command( [ s.python, './build_tables.py', '--src_priority', '-c', str( s.conf.confdir ), '-u', str( s.conf.user_data_directory ), '-d', s.fb.get_driver() ] )

        case 'menu-rebuild-audio':
            txt = """Scanning your audio library may take a long time depending on size of your library.\n
                    Do you really want to do this?
                  """
            t = s.msgQuestion( txt )

            if t == QMessageBox.Yes:
                s.fb.run_external_command( [ s.python, './build_tables.py', '--scan_audio', '--audio_files', '-c', str( s.conf.confdir ), '-u', str( s.conf.user_data_directory ), '-d', s.fb.get_driver() ] )

        case 'menu-rebuild-page-offset':
            s.fb.run_external_command( [ s.python, './build_tables.py', '--offset', '-c', str( s.conf.confdir), '-u', str( s.conf.user_data_directory ), '-d', s.fb.get_driver() ] )

        case 'menu-rebuild-canon2file':
            s.fb.run_external_command( [ s.python, './build_tables.py', '--canon2file', '-c', str( s.conf.confdir ), '-u', str( s.conf.user_data_directory ), '-d', s.fb.get_driver() ] )

        case'menu-convert-raw-sources':
            s.fb.run_external_command( [ s.python, './build_tables.py', '--convert_raw', '-c', str( s.conf.confdir ), '-u', str( s.conf.user_data_directory ), '-d', s.fb.get_driver() ] )

        # case 'menu-test-db-times':
        #     do_menu_test_db_times()

        # --------------------------------------------------

        case 'menu-summary':
            s.fb.run_external_command( [ s.python, './diff_index.py', '--summary', '--all', '-c', str(s.conf.confdir ), '-d', s.fb.get_driver() ] )

        case 'menu-page-summary':
            s.fb.run_external_command( [ s.python, './diff_index.py', '--page_summary', '--all', '-c', str(s.conf.confdir ), '-d', s.fb.get_driver() ] )

        case 'menu-verbose':
            s.fb.run_external_command( [ s.python, './diff_index.py', '--verbose', '--all', '-c', str( s.conf.confdir), '-d', s.fb.get_driver() ] )

        # --------------------------------------------------
        # case 'menu-show-recent-log':
        #     do_show_recent_log()

        # --------------------------------------------------
        # case 'menu-show-recent-event-histo':
        #     do_show_recent_event_histo()

        # --------------------------------------------------
        case 'menu-exit':
            s.app.quit()

        # --------------------------------------------------
        case 'menu-index-mgmt-tabs':
            s.toggleTabVisible( MT.IMgmt )

        case 'menu-canon2file-tab':
            s.toggleTabVisible( MT.Edit )

        case 'menu-command-output-tab':
            s.toggleTabVisible( MT.Results )

        # --------------------------------------------------
        #   Some diagnostic information, formerly 'if False:'ed in qbird.

        case 'menu-show-children':
            show_children_recursive( s.window )

        case 'menu-show-widgets':
            list_all_widgets()

        # Very helpful, shows info needed for findChild( type, name ). Less applicable now.
        case 'menu-show-objects':
            show_named_objects( s.window )

        case 'menu-show-styles':
            print( "Available styles:", QStyleFactory.keys())
            print( "Current style:", s.app.style().objectName() )

        case 'menu-show-global-store':
            print( "Items in global Store()" )
            print( '\n'.join(s.showItems()) )

        case 'menu-show-globals':
            print( "Globals in bl_menu_actions:" )
            print( '' )
            for key, val in sorted( globals().items()):
                print( f"{key:>25} : {val}" )

        case 'menu-show-managed-signals':
            s.sigman.show()

        case 'menu-show-native-signals':                                                  
            show_class_signals()

        case 'menu-show-class-hierarchy':
            show_class_hierarchy()

        case 'OMIT-menu-show-native-signals':            # EXPLORATORY, not interesting so far.
            signals = get_all_signals(s.window)
            for level, obj, name, signal in signals:
                # print(f"{'  '*level}{type(obj).__name__}.{name} -> {signal}")
                print(f"{'    '*level}{type(obj).__name__}.{name}")

        case 'menu-show-screens':
            for screen in s.app.screens():
                print( screen.name(), screen.size().toTuple() )

        case 'menu-show-constants':
            s.Const.show()

        case 'menu-show-settings':
            s.conf.show_settings()

        case 'menu-show-datadict':
            s.conf.show_datadict()

        case 'menu-show-message-box':
            s.msgInfo( "This is an information box" )
            s.msgInfo( "This is an information box with a very long line. And more data on the very long line." )
            s.msgWarn( "This is an warning box" )
            s.msgCritical( "This is an critical box" )
            s.msgQuestion( "This is an question box" )

        case 'menu-show-message-box-once':
            s.msgInfoOnce( 'test1', "This is an information box" )
            s.msgInfoOnce( 'test1', "This is an information box with a very long line. And more data on the very long line." )
            s.msgWarnOnce( 'test2', "This is an warning box" )
            s.msgCriticalOnce( 'test3', "This is an critical box" )

        case 'menu-show-message-box-once-reset':
            s.msgOnceReset( 'test2' )
            s.msgOnceReset( 'test3' )

        case 'menu-show-div-zero':
            1/0

        case 'menu-initialize-data-dir':
            s.conf.dev_initialize_data_dir()
            s.conf.report_progress()

        case 'menu-initialize-config-dir':
            s.conf.dev_initialize_config_dir()
            s.conf.report_progress()

        case 'menu-show-palette':
            s.conf.dump_palette( s.app.palette() )

        case 'menu-show-splash':
            pixmap = QPixmap( s.Const.BL_Splash_Image )
            if pixmap.isNull():
                pixmap = QPixmap(600, 400)
                pixmap.fill(Qt.darkRed)

            dialog = QDialog()

            dialog.setWindowModality(Qt.ApplicationModal)
            dialog.setAttribute(Qt.WA_DeleteOnClose)

            label = QLabel()
            label.setPixmap(pixmap)
            label.setAlignment(Qt.AlignCenter)

            layout = QVBoxLayout()
            layout.addWidget(label)
            dialog.setLayout(layout)

            dialog.resize(pixmap.size())
            dialog.exec()


        # --------------------------------------------------------------------
        case _:
            print( f"ERROR: Unexpected menu action '{menu_action} in bl_menu_actions.py" )

    # --------------------------------------------------------------------

    if save_stdout:
        sys.stdout = save_stdout

# ------------------------------------------------------------------------------------
#   Diagnostics - from ChatGPT
#   WRW 25-Mar-2025               

def show_class_hierarchy():
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    for cls in all_qobject_subclasses():
        if is_user_defined_class(cls, project_root):
            print(f"Class Hierarchy for: {cls.__name__}")
            print_mro_tree(cls, project_root)

def is_user_defined_class(cls, project_root):
    try:
        module = sys.modules.get(cls.__module__)
        if not module or not hasattr(module, "__file__"):
            return False
        return os.path.abspath(module.__file__).startswith(os.path.abspath(project_root))
    except Exception:
        return False

def all_qobject_subclasses():
    def recurse(cls):
        subclasses = set(cls.__subclasses__())
        for sub in list(subclasses):
            subclasses.update(recurse(sub))
        return subclasses
    return recurse(QObject)

def print_mro_tree(cls, project_root, indent=""):
    for base in cls.__mro__:
        is_user = is_user_defined_class(base, project_root)
        mark = "*" if is_user else " "
        print(f"{indent}{mark} {base.__name__}")
        indent += "  "
        if base is object:
            break
    print()

# ------------------------------------------------------------------------------------
#   Diagnostics - from ChatGPT
#   WRW 25-Mar-2025 - Show signals associated with each class, both user defined and inherited

import inspect

def show_class_signals():
    project_root = os.path.dirname(os.path.abspath(__file__))

    for cls in all_qobject_subclasses():
        if not is_user_defined_class(cls, project_root):
            continue
    
        all_signals = list_all_signals(cls)
    
        if all_signals:
            print(f"\nClass: {cls.__name__}")
            for name, signal in all_signals.items():
                defined_in = get_defining_class(name, cls)
                is_user_signal = (
                    defined_in is not None and is_user_defined_class(defined_in, project_root)
                )
                mark = "*" if is_user_signal else " "
                print(f"  {mark} {name}")

def get_defining_class(signal_name, cls):
    """Find the class in the MRO that actually defined this signal."""
    for base in cls.__mro__:
        if signal_name in base.__dict__:
            return base
    return None

def all_qobject_subclasses():
    def recurse(cls):
        subclasses = set(cls.__subclasses__())
        for sub in list(subclasses):
            subclasses.update(recurse(sub))
        return subclasses
    return recurse(QObject)

def is_user_defined_class(cls, project_root):
    try:
        module = sys.modules.get(cls.__module__)
        if not module or not hasattr(module, "__file__"):
            return False
        return os.path.abspath(module.__file__).startswith(os.path.abspath(project_root))
    except Exception:
        return False

def list_all_signals(cls):
    return {
        name: attr
        for name, attr in inspect.getmembers(cls)
        if isinstance(attr, Signal)
    }

def list_declared_signals(cls):
    return {
        name
        for name, attr in cls.__dict__.items()
        if isinstance(attr, Signal)
    }

# ------------------------------------------------------------------------------------
#   Diagnostics - from ChatGPT
#   WRW 25-Mar-2025 - Show all BOUND signals in the system

def get_all_signals(root: QObject):
    results = []
    for obj, level in find_all_qobjects( root ):
        for name, signal in list_bound_signals(obj).items():
            results.append((level, obj, name, signal))
    return results

# --------------------------------------

def find_all_qobjects(root: QObject) -> list[QObject]:
    found = []
    def recurse(obj, level=0):
        found.append( [obj, level] )
        for child in obj.children():
            recurse(child, level+1)
    recurse(root)
    return found

# --------------------------------------

def list_bound_signals(obj):
    results = {}

    for name in dir(obj):
        try:
            attr = getattr(obj, name)
            if type(attr).__name__ == "SignalInstance":
                results[name] = attr

        except Exception:
            continue

    return results

# ------------------------------------------------------------------------------------
#   Diagnostics
#   Less interesting after removing setObjectName() / findChild() for 
#   UI elements and moving to signals. Still interesting for styling.

def show_children_recursive( obj, level=0):
    indent = "   " * level                           # Indent for readability
    # print(f"{indent}{obj.objectName() or obj.__class__.__name__}   ({type(obj).__name__})" )

    name = f"Name: {obj.objectName()}, " if obj.objectName() else "no name"
    name.replace( '\n', ' ' )
    _class = type(obj).__name__

    wid = "Widget, " if obj.isWidgetType() else ''
    win = "Window, " if obj.isWindowType() else ''

    print( f"{indent}{name} Class: {_class}, {wid} {win}" )

    for child in obj.children():
        show_children_recursive( child, level + 1)

# ------------------------------------------------------------------------------------
#   Diagnostics

def show_named_objects( obj, level=0):
    indent = "   " * level                           # Indent for readability

    if obj.objectName():
        name = obj.objectName().replace( '\n', ' ' )    # some newlines in names
        if not name.startswith( 'qt_' ):
            _class = type(obj).__name__
            wid = "Widget, " if obj.isWidgetType() else ''
            # win = "Window, " if obj.isWindowType() else ''
            print( f"{indent}{_class}: {name}" )

    for child in obj.children():
        show_named_objects( child, level + 1)

# ------------------------------------------------------------------------------------
#   Diagnostics
#   WRW 2-Mar-2025 - I want a list of all widgets used so I can include them in
#       MySimpleQt.py

def list_all_widgets():
    widgets = QApplication.allWidgets()
    print("All Widgets in Application:")
    widgets = [ widget.metaObject().className() for widget in widgets ]
    uniq = sorted( set( widgets ))
    for widget in uniq:
        print( widget )

# ------------------------------------------------------------------------------------

def get_glibc_version():
    try:
        # Load the C standard library
        libc = ctypes.CDLL("libc.so.6")
        # Get the gnu_get_libc_version function
        gnu_get_libc_version = libc.gnu_get_libc_version
        gnu_get_libc_version.restype = ctypes.c_char_p
        # Call the function and decode the result
        version = gnu_get_libc_version().decode("utf-8")
        return version
    except Exception as e:
        return f"Error retrieving glibc version: {e}"

# ==========================================================================
#   Want more than can do in simple popup.
#   Show: Help->About Birdland
#   WRW 21 Mar 2022 - Pulled out into separate function to use with verbose, too.
#   WRW 30 May 2022 - Remove use of importlib. Only applicable when this installed by PyPi

#    Directories:
#        Settings Directory: {s.conf.confdir}
#        Program Directory: {s.conf.program_directory}
#        Data Directory: {s.conf.data_directory}

def get_about_data():
    s = Store()

    MYSQL, SQLITE, FULLTEXT = s.driver.values()

    # ----------------------------------
    if SQLITE:
        database1 = f"SqLite3" 
        database2 = f"File: '{Path( s.conf.user_data_directory, s.conf.sqlite_database)}'"

        if s.Const.Fullword_Available:
            fullword_notes = "Using fullword module"
        else:
            fullword_notes = "Using LIKE"

        mysqldb_module_version = "Not applicable"


    if MYSQL:
        database1 = f"MySql"
        database2 = f"'{s.conf.mysql_database}'"
        fullword_notes = 'Supported by MySql'

        import MySQLdb              # WRW 3 June 2022 - Imported in do_main() but not in namespace here.
        mysqldb_module_version = '.'.join([str(x) for x in MySQLdb.version_info ])

    # ----------------------------------
    #   WRW 28-Mar-2025 - when migrating to bundled distribution

    # Determine path to current script or executable

    if getattr(sys, 'frozen', False):
        app_path = sys.executable
    else:
        app_path = os.path.realpath( s.Const.Me )

    try:
        # mtime = os.path.getmtime(app_path)
        # timestamp = time.strftime('%a, %d-%b-%Y, %H:%M:%S', time.localtime(mtime))
        timestamp = datetime.datetime.fromtimestamp( Path( app_path ).stat().st_mtime ).strftime( '%a, %d-%b-%Y, %H:%M:%S')

    except Exception:
        timestamp = f"Not available for {app_path}"

    # ----------------------------------
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        run_environment = "PyInstaller bundle"

    # elif "__compiled__" in globals():
    #     run_environment = "Nuitka bundle"

    else:
        run_environment = "Python process"

    # ----------------------------------
    if False:
        try:
            # timestamp = datetime.datetime.fromtimestamp( Path(sys.executable).stat().st_mtime ).strftime( '%a, %d-%b-%Y, %H:%M:%S')
            # timestamp = datetime.datetime.fromtimestamp( Path(os.path.realpath(__file__)).stat().st_mtime ).strftime( '%a, %d-%b-%Y, %H:%M:%S')
            timestamp = datetime.datetime.fromtimestamp( Path(os.path.realpath(s.Const.Me)).stat().st_mtime ).strftime( '%a, %d-%b-%Y, %H:%M:%S')
        except Exception as e:
            # timestamp = f"not available for {sys.executable}"
            timestamp = f"not available for {os.path.realpath(s.Const.Me)}"

    # ----------------------------------
    # default: {device.isDefault()}
    # max sample rate: {device.maximumSampleRate()}
    # min sample rate: {device.minimumSampleRate()}
    # supported formats: {device.supportedSampleFormats()}
    # preferred format: {device.preferredFormat()}

    txt = []

    txt.append( "        Available audio devices:" )
    devices = QMediaDevices.audioOutputs()
    for device in devices:
        txt.append(f"             id: {str(device.id(), 'utf-8')}" )
        txt.append(f"             description: {device.description()}" )
        txt.append(f"             default: {device.isDefault()}"  )
        txt.append(f"             max sample rate: {device.maximumSampleRate()}" )
        txt.append(f"             min sample rate: {device.minimumSampleRate()}" )
        txt.append(f"             supported formats: {device.supportedSampleFormats()}" )
        txt.append(f"             preferred format: {device.preferredFormat()}" )
        txt.append( "" )

    # Display the supported file formats
    # Get supported file formats for decoding. Returns list of QMediaFormat.FileFormat
    media_format = QMediaFormat()           # Create an instance of QMediaFormat

    txt.append("        Supported File Formats for Decoding:")
    supported_formats = media_format.supportedFileFormats(QMediaFormat.ConversionMode.Decode)
    for fmt in supported_formats:
        txt.append(f"             {QMediaFormat.fileFormatName(fmt)} - {QMediaFormat.fileFormatDescription( fmt )}")
    txt.append( "" )

    txt.append( "        Supported Codecs for Decoding:")
    supported_codecs = media_format.supportedAudioCodecs(QMediaFormat.ConversionMode.Decode)
    for fmt in supported_codecs:
        txt.append( f"            {QMediaFormat.audioCodecName(fmt)} - {QMediaFormat.audioCodecDescription( fmt )}" )
    txt.append( "" )

    audio_system = '\n'.join( txt )

    # ----------------------------------

    audio_output = QAudioOutput()
    device = audio_output.device()

    # ----------------------------------

    screen = QGuiApplication.primaryScreen()
    logical_dpi = screen.logicalDotsPerInch()  # You can also use physicalDotsPerInch()
    physical_dpi = screen.physicalDotsPerInch()  # You can also use physicalDotsPerInch()

    # ----------------------------------
    # Python Paths: {', '.join( [ x for x in sys.path ]) }
    # ----------------------------------
    OMIT = """
    System:
        Sysname: {uname.sysname}
        Nodename: {uname.nodename}
        Release: {uname.release}
        Version: {uname.version}
        Machine: {uname.machine}
    """
    info_text = f"""
    System:
        Architecture: {platform.architecture()}
        Machine: {platform.machine()}
        Node: {platform.node()}
        sys.platform: {sys.platform}
        Platform: {platform.platform()}
        Processor: {platform.processor()}
        Sysname: {platform.system()}
        Release: {platform.release()}
        Version: {platform.version()}
        Original GUI Style: {s.originalStyle}
        glibc version: {get_glibc_version()}

    Display:
        Logical: {logical_dpi:.2f} DPI
        Physical: {physical_dpi:.2f} DPI
        P/L Ratio: {100*physical_dpi/logical_dpi:.2f}%

    Python:
        Python Version:  {platform.python_version()}
        Pyside6 Version: {QtCore.__version__}
        Runtime Qt Version: {QtCore.qVersion()}
        Sqlite Version: {sqlite3.sqlite_version}
        Sqlite Python Module Version: {sqlite3.version}
        MuPDF Library Version: {fitz.version[1]}
        PyMuPDF Module Version: {fitz.version[0]}
        ConfigObj Module Version: {configobj.__version__}
        MySQLdb Module Version: {mysqldb_module_version}

    Birdland:
        Version: {s.Const.Version}
        Run Environment: {run_environment}
        Package Type: {s.Const.Package_Type}
        Package Sub Type: {s.Const.Package_Sub_Type}
        Settings Directory: {s.conf.confdir}
        User Data Directory: {s.conf.user_data_directory}
        Package Data Directory: {s.conf.package_data_directory}
        Executable: {s.Const.Me} 
        Executable Timestamp: {timestamp}
        Database: {database1}
        Database Storage: {database2}
        Fullword: {fullword_notes}
        Style: {s.conf.val( 'style' )}
        Theme: {s.conf.val( 'theme' )}

    Qt Standard Locations:
        Config: {QStandardPaths.standardLocations(QStandardPaths.AppConfigLocation)[0]}
        Data: {QStandardPaths.standardLocations(QStandardPaths.AppDataLocation)[0]}
        LocalData: {QStandardPaths.standardLocations(QStandardPaths.AppLocalDataLocation)[0]}
        Applications: {QStandardPaths.standardLocations(QStandardPaths.ApplicationsLocation)[0]}
        Cache: {QStandardPaths.standardLocations(QStandardPaths.CacheLocation)[0]}

    PATH:
        {'\n        '.join( os.environ.get("PATH", "").split(os.pathsep) )}

    LD_LIBRARY_PATH:
        {'\n        '.join( os.environ.get("LD_LIBRARY_PATH", "").split(os.pathsep) )}

    Execution:
        Python executable: {sys.executable}
        Argv: {' '.join( sys.argv )}
        __file__: {s.Const.Me}
        Realpath( __file__ ): {os.path.realpath(s.Const.Me)}

    PySide6:
        Icon Theme Search Paths: {'\n          '.join( QIcon.themeSearchPaths() )}

    Audio System:
        Supported file types: {' '.join(s.Const.audioFileTypes )}

        Audio output device:  
            Id: {str(device.id(), 'utf-8')}
            Description: {device.description()}

{audio_system}

    """
    return info_text

# --------------------------------------------------------------------------
#   WRW 12 May 2022 - Now that I have a contact form on the website let's direct
#       users there.

def do_contact():
    s = Store()
    txt = """To contact us please go to:<br><br>

    <a href=https://birdland.wrwetzel.com/contact.html>https://birdland.wrwetzel.com/contact.html</a><br><br>

If writing about a problem please paste the content of the<br><br>

    <i>Help->About Birdland</i><br><br>

window into the contact form.
"""
    # s.conf.do_popup_raw( txt )
    s.msgInfo( txt )

# --------------------------------------------------------------------------

def do_license():
    s = Store()

    file = QFile( s.Const.License )
    if file.open(QFile.ReadOnly | QFile.Text):
        stream = QTextStream(file)
        txt = stream.readAll()
        file.close()
    else:
        txt = f"ERROR-DEV: Can't find license file: '{s.Const.License}'"

    s.msgInfo( txt )

# --------------------------------------------------------------------------

def do_website():
    s = Store()
    txt = """Birdland Website:<br><br>

    <a href=https://birdland.wrwetzel.com>https://birdland.wrwetzel.com</a>
"""
    # s.conf.do_popup_raw( txt )
    s.msgInfo( txt )

# --------------------------------------------------------------------------

def do_locations():
    s = Store()
    txt = f"""<b>Configuration:</b> {s.conf.confdir}<br><br>
              <b>Data Directory:</b> {s.conf.user_data_directory}
           """
    s.msgInfo( txt )

# --------------------------------------------------------------------------

def do_about():
    info_text = get_about_data()
    popup = About_Window( info_text )
    popup.exec()  # Show the popup as a modal dialog

# --------------------------------------------------------------------------

