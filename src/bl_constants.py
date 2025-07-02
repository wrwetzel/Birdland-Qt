#!/usr/bin/env python
# --------------------------------------------------------------------------
#   WRW 9-Feb-2025
#   Constants to avoid hardwired values elsewhere in code.

#   WRW 24-Mar-2025 - Move constants into Const class so don't have to import
#       these items explicitly. Keep MT and LT separate, though.
#       Const is in Store() so no need to import other than in main program.

#   Understanding determination of Program_Directory and Data_Directory below:
#       __file__:     Birdland-Qt/src/fb_config.py
#       .parent()     Birdland-Qt/src/                  Program directory
#       .parent()     Birdland-Qt                       Data directory - development
#       sys._MEIPASS                                    Frozen

#   A Leading ':' in constant value means comes from QtResource
#   Build resources:
#       pyside6-rcc bl_resources.qrc -o bl_resources_rc.py

#   Install pyside6-rcc:
#       paru -S pyside6-tools-wrappers

# --------------------------------------------------------------------------

from PySide6.QtCore import QStandardPaths, QCoreApplication
from PySide6.QtWidgets import QStyleFactory

# --------------------------------------------------------------------------

import os
import sys
import socket
from pathlib import Path
import fb_version
from bl_style import getThemeNames

# --------------------------------------------------------------------------

class Const( ):

    # --------------------------------------------------------------------------------

    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        Frozen = True
        Package_Type = 'PyInstaller'       # WRW 26-Mar-2025 - Used only in get_about().
    #   Program_Directory = sys._MEIPASS
        Package_Data_Directory = sys._MEIPASS

        exec_path = os.path.dirname( sys.executable )
        bundle_path = sys._MEIPASS

        #   Not working, ignore for now. Don't really need the sub type in about.
        # if os.path.normpath( exec_path ) == os.path.normpath( bundle_path ):
        #     Package_Sub_Type = 'OneDir'
        # else:
        #     Package_Sub_Type = 'OneFile'

        Package_Sub_Type = 'NA'

    else:
        Frozen = False
        Package_Type = 'Development'
    #   Program_Directory = Path( __file__ ).parent.resolve()
        Package_Data_Directory = Path( __file__ ).parent.parent.resolve()
        Package_Sub_Type = 'NA'

    # ----------------------------------------------------------------------------
    #   Platform-specific code is used very little but more than zero.
    #   These flags control it.

    if sys.platform.startswith("win"):
        Platform = 'Windows'
    elif sys.platform.startswith("darwin"):
        Platform = 'MacOS'                          # This is an internal designation used only within birdland.
    elif sys.platform.startswith("linux"):
        Platform = 'Linux'
    else:
        Platform = 'Unknown'

    # ----------------------------------------------------------------------------

    BL_Program_Name =   "birdland_qt"
    BL_Author_Name =    "Bill Wetzel"
    BL_Short_Title =    "Birdland Qt Lite"
    BL_Long_Title =     "Birdland Musician's Assistant - Qt Lite Version"
    BL_SubTitle =       "Let\'s hear how it goes"
    BL_SubSubTitle =    "A Fake Book Librarian"
    BL_Desktop =       f"{BL_Program_Name}.desktop"
    Copyright =        f"Copyright \xa9 2025 {BL_Author_Name}"
    Hostname =           socket.gethostname()
    Version =          f"{fb_version.__version__} build {fb_version.__build__}"

    QCoreApplication.setApplicationName( BL_Program_Name )      # Must do this early as used in QStandardPaths below

    # --------------------------------------
    #   The following are currently functionally redundant with other constants
    #   defined in fb_config.py Migrate to these. Installation must agree with these.

    stdConfig =         QStandardPaths.standardLocations(QStandardPaths.AppConfigLocation)[0]
    stdData =           QStandardPaths.standardLocations(QStandardPaths.AppDataLocation)[0]
    stdLocalData =      QStandardPaths.standardLocations(QStandardPaths.AppLocalDataLocation)[0]
    stdCache =          QStandardPaths.standardLocations(QStandardPaths.CacheLocation)[0]
    stdApplication =    QStandardPaths.writableLocation(QStandardPaths.ApplicationsLocation)

    Datadir =   stdData         # Default value, may be overridden by command-line option
    Confdir =   stdConfig       # Default value, may be overridden by command-line option

    # --------------------------------------
    #   Files in bl_resources.qrc
    #   WRW 9-Apr-2025 - added many more under NIcon, ref directly for now.

    BL_Icon_ICO =               ":/Icons/Saxophone_64.ico"
    BL_Icon_PNG =               ":/Icons/Saxophone_64.png"
  # BL_Splash_Image =           ':/Images/splash-piano-hori-640.png'
    BL_Splash_Image =           ':/Images/splash-piano-hori-640-mixed-case.png'
    DocFile =                   ':/Documentation/birdland.pdf'
    QuickStartFile =            ':/Documentation/quickstart.pdf'
    ConfigurationFile =         ':/Documentation/configuration.pdf'
    Create_Quick_Ref =          ':/Documentation/birdland-create.pdf'
    confPrototype =             ':/birdland.conf.proto'
    License =                   ':/Documentation/License.txt'
  # palettesFile =              ':/palettes.csv'

    # --------------------------------------
    #   Started making full path but that is already done in fb_config.py.
    #   Just filenams here.
    #   Someday go back to full paths, big impact on fb_config.py
    #   Had a bug because I didn't update one reference at all places it was used.
    #   Full path here will avoid that. No, no, no. Big mistake to do that.

    Canonical_Dir =             'Canonical'
    Index_Source_Dir =          'Index-Sources'
    Icon_File_ICO =             'Saxophone_64.ico'
    Icon_File_PNG =             'Saxophone_64.png'
    Setlist_File =              'Setlist.json'
    Settings_Config_File =      'birdland_qt.settings.conf'
    Config_File =               'birdland_qt.conf'
    Proto_Local2Canon =         'Proto-Local2Canon.txt'
    Proto_Sheet_Offsets =       'Proto-Sheet-Offsets.txt'
    Proto_Canonical2File =      'Proto-Canonical2File.txt'
    Canonical2File =            'Canonical2File.txt'
    Local2Canon_File =          'Local2Canon.txt'
    Local_Book_Names_File =     'Local-Book-Names.txt'
    audioFileIndexFile =        'Audio-Index.json.gz'
    Example_Canonical2File =    'Example-Canonical2File.txt'
    Sheet_Offsets_File =        'Sheet-Offsets.txt'

    # --------------------------------------
    #   These are the directories copied from installation to AppData
    #   WRW 15-May-2025 - remove 'Music-Index', caused problem when empty
    #   build it on first run initialization.

    Bundled_Directories =       [ 'Book-Lists',    'Canonical',
                                  'Index-Sources', 'YouTube-Index' ]

    # --------------------------------------
    #   Database identity

    MySql_DB =          'Birdland'              # Database name
    SqLite_DB_File =    'Birdland.db'           # Filename containing sqlite3 database.

    # --------------------------------------

    audioFileTypes = [ ".mp3", ".fla", ".flac",
                       ".mpc", ".ape", ".ogg", ".wav", ".aif",
                       ".m4a",     # /// TEST
                       ".wma",     # /// TEST
                       ".aiff",    # /// TEST - Apple audio file format
                       ".mp4",     # /// TEST - container format
                       ".mid",     # WRW 23-May-2025
                       ".midi",    # WRW 23-May-2025
                     ]

    # --------------------------------------

    leftPanelWidth = 335            # Hand tuned to with of tabs + padding + margins
    metaDataPanelWidth = 250

    # --------------------------------------
    #   Appearances are a subset of several explored and still available in the code.
    #   These look and work well. Note that 'Birdland' was the former 'Default', similar
    #   to 'QDark' but adds some green color to 'Title' box and buttons.
    #   Set Appearances to empty list to suppress limits altogether.
    #   WRW 25-Apr-2025 - Migrate to modified style sheets using jinja templates, no
    #   more palettes.

    system_styles = QStyleFactory.keys()

    Appearances_BL = getThemeNames()
    Appearances_DS =  [ 'QDark', 'QLight'  ]
    Appearances = Appearances_BL + Appearances_DS

    # ---------------------------------------------------------------------
    #   $PATH not inherited by gui apps on MacOS

    MacExtraPaths = [
        "/opt/homebrew/bin",       # Homebrew (M1/ARM)
        "/opt/local/bin",          # MacPorts instead of Homebrew
        "/usr/local/bin",          # Homebrew (Intel)
        "/usr/bin",                # System
        "/bin",                    # System
        "/usr/sbin",               # System
        "/sbin",                   # System
        "/Library/Apple/usr/bin"   # System-provided extras
    ]

    # ---------------------------------------------------------------------
    #   Unicode character glyphs

    Uni_Keyboard    = '\U0001F3B9'
    Uni_Notes       = '\U0001F3B5'
    Uni_MultiNotes  = '\U0001F3B6'
    Uni_Beamed8th   = '\u266B'
    Uni_Speaker     = '\U0001F50a'
    Uni_Bullet      = '\u2022'
    Uni_Bullet      = '\u25cf'
    Uni_EmSpace     = '\u2003'

    Marker_Midi =  Uni_Bullet
    Marker_Audio = Uni_Bullet
    Marker_Space = Uni_EmSpace     

    Button_Audio = 'Audio'
    Button_Midi =  'Midi'
    Button_Full =  'Zoom'

    # ---------------------------------------------------------------------
    #   Names for 'midi_playback' option, used in fb_config.py and bl_media.py

    Midi_BI =       'Built-in Player'
    Midi_Ext =      'Ext MIDI Player'
    Midi_Tim =      'Ext Timidity'
    Midi_FS =       'Ext FluidSynth'
    Midi_FS_BI =    'Ext FluidSynth Conversion, Built-in Player'

    # =====================================================================

    def set( self, name, value ):
        setattr( self, name, value )

    # ---------------------------------------------------------------------

    def show( self ):
        for attr in dir( self ):
            if not attr.startswith( '__' ):
                print( f"{attr:>25} : {getattr( self, attr )}" )

# ==========================================================================
#   MT - Main tab bar tab identifiers

class MT():
    SetList = 0
    Browser = SetList + 1
    Viewer = Browser + 1
    Index = Viewer + 1
    Files = Index + 1
    Audio = Files + 1
    Midi = Audio + 1
    Chord = Midi + 1
    JJazz = Chord + 1
    YouTube = JJazz + 1
    Reports = YouTube + 1
    Edit = Reports + 1
    IMgmt = Edit + 1
    Results = IMgmt + 1

    def getName( id ):
        return f"MT-{id}"

# -----------------------------------------------------------------------------
#   LT - Left panel tab bar numbers, count over both rows of tabs, must be unique.

class LT():
    Browse_Music = 0
    Browse_Audio = 1
    Browse_Midi = 2
    Browse_Chord = 3
    Browse_JJazz = 4

    TOC = 5
    Audio_of_Title = 6
    Midi_of_Title = 7
    File_Info = 8

    def getName( self, id ):
        return f"LT-{id}"

# --------------------------------------------------------------------------

if False:
    class LT():
        Media_Browser = 0
        Toc = Media_Browser + 1
    
    class LT1():
        Music = 0
        Audio = Music + 1
        Midi = Audio + 1
        Chord = Mid + 1
    
    class LT2():
        Toc = 0
        Audio = Toc + 1
        Midi = Audio + 1
        Media = Mid + 1

# -------------------------------------------

def do_main():

    print( MT.SetList )
    print( MT.getName( MT.Viewer ))

    print( Const.BL_Icon_ICO )
    print( Const.audioFileTypes )

if __name__ == "__main__":
    do_main()

# --------------------------------------------------------------------------
#   File extensions found in music library.
#   Obvious non-audio-related removed from this list.

"""
  51327 .mp3
  13892 .flac
   1459 .m4a
    998 .m3u    playlist
    851 .ape
    824 .MP3
    712 .wma
    558 .ogg
    237 .mp4
    161 .mpc
     92 .sfv
     90 .wav
     84 .m3u8   playlist
     73 .FLAC
"""

# --------------------------------------------------------------------------
#   This was a futile attempt at automatically adjusting Const() values
#   on the fly on reference for frozen vs development source. Bad idea,
#   very bad idea. That function is performed in fb_Config.py val().

if False:
    class Const( ResourceMeta ):
        pass

    def resource_path(relative_path):
        """
        Return the absolute path to a bundled resource.
        Works both in development and when running as a PyInstaller executable.
        """
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)

    # --------------------------------------------------------------------------

    class ResourceMeta(type):
        def __new__(cls, name, bases, class_dict):
            transformed = {
                key: resource_path(value) if isinstance(value, str) else value
                for key, value in class_dict.items()
            }
            return super().__new__(cls, name, bases, transformed)

# --------------------------------------------------------------------------
