#!/usr/bin/python
# ---------------------------------------------------------------------------
#   WRW 10 Feb 2022 - fb_config.py - Pulled config stuff from fb_utils.py
#       and birdland.py

#   Try migrating away from direct refereces to config and hostname 
#        outside of this module. Done, looks good.

#   WRW 27 Feb 2022 - Convert from configparser to configobj so can include
#       comments and have nested host and source sections. Much cleaner now.

#   A reminder that that 'source' and 'src' refer to the source of the raw index data and
#       are found in the [[Source]] section of the config file.
#           e.g. Buffalo/Buf, Skrivarna/Skr, User/Usr, etc.

#   WRW 25-Mar-2025 - Thinking about removing intermediate config store in self.v and      
#       obtaining config value directly from self.config on demand in new Setting() class.
#       Unsure if it is a good idea. This works as is, no point disturbing it and likely
#       a bit fragile. Just wrap up access in a new name.

# ---------------------------------------------------------------------------

import json
import sys
import gzip
import shutil
import os
import csv
import io

from pathlib import Path
from io import StringIO

from PySide6.QtCore import Qt, QProcess, QFile, QTextStream, QDir, QModelIndex, QSize, Signal, QTimer
from PySide6.QtGui import QIcon, QCursor, QTextCursor, QMouseEvent, QPalette, QColor
from PySide6.QtWidgets import QWidget, QDialog, QTreeView
from PySide6.QtWidgets import QLabel, QComboBox, QTextEdit, QPushButton, QVBoxLayout, QHBoxLayout
from PySide6.QtWidgets import QScrollArea, QGridLayout, QLineEdit, QCheckBox, QPlainTextEdit
from PySide6.QtWidgets import QDialogButtonBox, QFileDialog, QSizePolicy, QListWidget, QFileSystemModel
from PySide6.QtWidgets import QSpacerItem, QStyleFactory

import qdarkstyle       # WRW 2-Mar-2025                                                               

from configobj import ConfigObj
from Store import Store
from bl_style import getStyle, getStyleGeometry

import bl_resources_rc      # Need this even though not directly referenced

# ---------------------------------------------------------------------------
#   WRW 25-Mar-2025 - New approach to access configuration settings.
#       Populated in set_class_variables(), below.

#       Replace:
#           s.conf.var( 'setting-name' ) 

#       With:
#           s.Setting.setting_name

#       I.e., no longer a function call with string name but reference to class object in dot notation.
#       Setting names must now be valid identifiers, i.e., no '-' in name. All names OK already.
#       Converted a few but many, many remain.

#       Singleton done in nod to my OCD.

# ------------------------------------------

class runExtCommandToPopup( QDialog ):
    def __init__(self, doneCallback, command, args=None ):
        super().__init__()
        s = Store()
        s.app.setOverrideCursor(QCursor(Qt.WaitCursor))

        self.setWindowTitle( s.Const.BL_Short_Title )
        self.resize(1000, 600)
        self.doneCallback = doneCallback
        self.command = [ command, *args ]

        self.text_edit = QPlainTextEdit(self)
        self.text_edit.setReadOnly(True)
        self.text_edit.setLineWrapMode(QPlainTextEdit.NoWrap)
        font = self.text_edit.font()
        font.setFamily("monospace")
        self.text_edit.setFont(font)

        layout = QVBoxLayout(self)
        layout.addWidget(self.text_edit)

        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(self.close)
        layout.addWidget(button_box)

        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.MergedChannels)  # Combine stdout + stderr

        self.process.readyReadStandardOutput.connect(self.on_stdout)
        self.process.readyReadStandardError.connect(self.on_stderr)
        self.process.finished.connect(self.on_finished)

        self.process.start(command, args or [])

    def append( self, txt ):
        # self.text_edit.appendPlainText( txt )

        cursor = self.text_edit.textCursor()
        cursor.movePosition( QTextCursor.End )
        self.text_edit.insertPlainText( txt )
        self.text_edit.moveCursor( QTextCursor.End )
        self.text_edit.setTextCursor(cursor)

    def on_stdout(self):
        output = self.process.readAllStandardOutput().data().decode()
        self.append(output)

    def on_stderr(self):
        error = self.process.readAllStandardError().data().decode()
        self.append( error )

    def on_finished(self, rcode, qstatus ):
        s = Store()
        s.app.restoreOverrideCursor()
        # self.text_edit.appendPlainText("\nProcess finished.")         # Chitchat handled by callback to calling function
        # self.text_edit.appendPlainText( f"Exit code: {rcode}")
        # self.text_edit.appendPlainText( f"Exit status: {qstatus}")
        self.exit_code = rcode
        self.status = qstatus
        self.doneCallback( self, rcode, qstatus )

    def close( self ):
        if self.process.state() != QProcess.NotRunning:
            self.process.terminate()  # Graceful
            if not self.process.waitForFinished(2000):  # Wait 2 sec max
                self.process.kill()  # Force if needed
        else:
            super().close()

# ---------------------------------------------------------------------------
#   WRW 2 Jan 2022
#   Build configuration window dynamically.
#   WRW 20 Feb 2022 - Add 'loc' flag to indicate base for value so higher-level functions don't have to
#       have that knowledge, for most options. Works great.
    
#   WRW 30-Mar-2025 - move into class so can use Store(), don't want to define s in global context.
#   WRW 31-Mar-2025 - After a lot of thrashing about I moved the initialization into an
#       instance and assigned the defined values to class variables. Use was getting
#       fragile, especially in the index-source-specific do_*.py routines. Fixed it.
#       Also make singleton.

class configDataDict( ):
    _instance = None

    def __new__( cls ):
        if cls._instance is None:
            cls._instance = super().__new__( cls )
        return cls._instance

    # ----------------------------------------------------------------------------------
    #       loc:
    locDef = """
           '-' - Return val without any change.
           'a' - Absolute, may include ~user expansion.
           'c' - Relative to config dir.
           'C' - Relative to config dir, prefix filename with hostname.
           'i' - Relative to data directory loaded at installation
           's' - Relative to Index_Sources dir under data directory, filename is in data dict, not config file
           'f' - Relative to Index_Sources dir under data directory.
           'L' - Label to show in config popup
    """
    #   type:
    #       'V' - value, textbox
    #       'B' - binary, checkbox
    #       'C' - multi-value, combobox, aux1, aux2, aux3, aux4, aux5 indicate values for box.

    #   rows: Number of rows in multiline element in config window.
    #         If given, val() returns an array, otherwise a scalar.

    #   name: Hard-wired name of file associated with 's' item.

    #   ptype: Picker type for single-line edit boxes
    #       'none' - no picker, just text
    #       'file' - file picker
    #       'dir' - directory picker

    # ----------------------------------------------------------------------------------

    def __init__( self ):
        if hasattr( self, '_initialized' ):     # Chat prefers this over a flag initialized in __new__().
            return                              # No point initializing a singleton twice.
        self._initialized = True

        s = Store()

        self.ci_canon_select = [     # This really belongs in the Create Index tab but no room for it on small screens.
            'All',              # Values must agree with selector in fb_create_index.py
            'With No Index',
            'Only With Index',
        ]

        self.midi_playback_select = [                                                                                       
             s.Const.Midi_BI,
             s.Const.Midi_Ext,
             s.Const.Midi_Tim,
             s.Const.Midi_FS,
             s.Const.Midi_FS_BI,
        ]

        self.settings_dict = {

            'label1' :                          { 'loc' : '-', 'type' : 'L', 'col' : 'L', 'show' : True, 'section' : 'Host',   'title' : 'Media Locations' },
            'music_file_root' :                 { 'loc' : 'a', 'type' : 'V', 'col' : 'L', 'show' : True, 'section' : 'Host',   'title' : 'Root of music files', 'ptype' : 'dir' },
            'music_file_folders' :              { 'loc' : '-', 'type' : 'V', 'col' : 'L', 'show' : True, 'section' : 'Host',   'title' : 'Folders containing music files', 'rows' : 5, 'link' : 'music_file_root' },
            'c2f_editable_music_folders' :      { 'loc' : '-', 'type' : 'V', 'col' : 'L', 'show' : True, 'section' : 'Host',   'title' : 'Folders containing music files\npermitting Canon->File editing', 'rows' : 2, 'link': 'music_file_root' },

            'browser_folders' :                 { 'loc' : '-', 'type' : 'V', 'col' : 'L', 'show' : True, 'section' : 'Host',   'title' : 'Folders to show in Cover Browser', 'rows' : 4, 'link': 'music_file_root' },

            'audio_file_root' :                 { 'loc' : 'a', 'type' : 'V', 'col' : 'L', 'show' : True, 'section' : 'Host',   'title' : 'Root of audio files', 'ptype' : 'dir'   },
            'audio_folders' :                   { 'loc' : '-', 'type' : 'V', 'col' : 'L', 'show' : True, 'section' : 'Host',   'title' : 'Folders containing audio files', 'rows' : 5, 'link': 'audio_file_root' },

            'midi_file_root' :                  { 'loc' : 'a', 'type' : 'V', 'col' : 'L', 'show' : True, 'section' : 'Host',   'title' : 'Root of MIDI files', 'ptype' : 'dir'  },
            'midi_folders' :                    { 'loc' : '-', 'type' : 'V', 'col' : 'L', 'show' : True, 'section' : 'Host',   'title' : 'Folders containing MIDI files', 'rows' : 3, 'link': 'midi_file_root'  },

            'chordpro_file_root' :              { 'loc' : 'a', 'type' : 'V', 'col' : 'L', 'show' : True, 'section' : 'Host',   'title' : 'Root of ChordPro files', 'ptype' : 'dir'  },
            'chordpro_folders' :                { 'loc' : '-', 'type' : 'V', 'col' : 'L', 'show' : True, 'section' : 'Host',   'title' : 'Folders containing ChordPro files', 'rows' : 3, 'link': 'chordpro_file_root'  },

            'jjazz_file_root' :                 { 'loc' : 'a', 'type' : 'V', 'col' : 'L', 'show' : True, 'section' : 'Host',   'title' : 'Root of JJazzLab files', 'ptype' : 'dir'  },
            'jjazz_folders' :                   { 'loc' : '-', 'type' : 'V', 'col' : 'L', 'show' : True, 'section' : 'Host',   'title' : 'Folders containing JJazzLab files', 'rows' : 3, 'link': 'jjazz_file_root'   },

            'soundfont_file' :                  { 'loc' : 'a', 'type' : 'V', 'col' : 'L', 'show' : True, 'section' : 'Host',   'title' : 'SoundFont file', 'ptype' : 'file'   },

            'label2' :                          { 'loc' : '-', 'type' : 'L', 'col' : 'R', 'show' : True, 'section' : 'Host',   'title' : 'Names of Files in the Configuration Folder' },

            'canonical2file' :                  { 'loc' : 'c', 'type' : 'V', 'col' : 'R', 'show' : True, 'section' : 'Host',   'title' : 'Canonical->File map file(s)', 'rows' : 3, 'link': '-' },
            'c2f_editable_map' :                { 'loc' : 'c', 'type' : 'V', 'col' : 'R', 'show' : True, 'section' : 'Host',   'title' : 'Editable Canonical->File map file', 'ptype' : 'file' },
            'setlistfile' :                     { 'loc' : 'c', 'type' : 'V', 'col' : 'R', 'show' : True, 'section' : 'System', 'title' : 'Setlist file', 'ptype' : 'file' },

            'label3' :                          { 'loc' : '-', 'type' : 'L', 'col' : 'R', 'show' : True, 'section' : 'Host',   'title' : 'Random Options' },

            'select_limit' :                    { 'loc' : '-', 'type' : 'V', 'col' : 'R', 'show' : True, 'section' : 'System', 'title' : 'Max number of search results', 'ptype' : 'none' },
            'show_index_mgmt_tabs':             { 'loc' : '-', 'type' : 'B', 'col' : 'R', 'show' : True, 'section' : 'System', 'title' : 'Show index management tab' },
            'show_canon2file_tab':              { 'loc' : '-', 'type' : 'B', 'col' : 'R', 'show' : True, 'section' : 'System', 'title' : 'Show Edit Canonoical->File tab' },
            'include_titles_missing_file':      { 'loc' : '-', 'type' : 'B', 'col' : 'R', 'show' : True, 'section' : 'System', 'title' : 'Include titles missing in music files' },
         # for index-mgmt    'ci_canon_select': { 'loc' : '-', 'type' : 'C', 'col' : 'R', 'show' : True, 'section' : 'System', 'title' : 'Create Index Canonicals (restart reqd)', 'aux2': self.ci_canon_select },

            'label4' :                          { 'loc' : '-', 'type' : 'L', 'col' : 'R', 'show' : True, 'section' : 'Host',   'title' : 'Appearance' },

            'style':                            { 'loc' : '-', 'type' : 'C', 'col' : 'R', 'show' : True, 'section' : 'System', 'title' : 'Style', 'aux1': 'styles' },
            'theme':                            { 'loc' : '-', 'type' : 'C', 'col' : 'R', 'show' : True, 'section' : 'System', 'title' : 'Theme', 'aux5': 'appearances' },

         #  'icon_theme':                       { 'loc' : '-', 'type' : 'C', 'col' : 'R', 'show' : True, 'section' : 'System', 'title' : 'Icon Theme', 'aux3': 'icon themes' },

            'label5' :                          { 'loc' : '-', 'type' : 'L', 'col' : 'R', 'show' : True, 'section' : 'Host',   'title' : 'External Applications' },

            'raw_index_editor' :                { 'loc' : '-', 'type' : 'V', 'col' : 'R', 'show' : True, 'section' : 'System', 'title' : 'Text Editor for Raw Index', 'ptype' : 'file'   },
            'raw_index_editor_line_num' :       { 'loc' : '-', 'type' : 'V', 'col' : 'R', 'show' : True, 'section' : 'System', 'title' : 'Text Editor line number option', 'ptype' : 'none'  },

         #  'use_external_music_viewer':        { 'loc' : '-', 'type' : 'B', 'col' : 'R', 'show' : True, 'section' : 'System', 'title' : 'Use external music viewer' },
         #  'external_music_viewer' :           { 'loc' : '-', 'type' : 'V', 'col' : 'R', 'show' : True, 'section' : 'System', 'title' : 'External Music Viewer', 'ptype' : 'file' },

            'use_external_audio_player':        { 'loc' : '-', 'type' : 'B', 'col' : 'R', 'show' : True, 'section' : 'System', 'title' : 'Use external Audio Player' },
            'external_audio_player' :           { 'loc' : '-', 'type' : 'V', 'col' : 'R', 'show' : True, 'section' : 'System', 'title' : 'Ext Audio Player', 'ptype' : 'file'  },
            'external_audio_player_options':    { 'loc' : '-', 'type' : 'V', 'col' : 'R', 'show' : True, 'section' : 'System', 'title' : 'Ext Audio Player Options', 'ptype' : 'none'  },

            'midi_playback':                    { 'loc' : '-', 'type' : 'C', 'col' : 'R', 'show' : True, 'section' : 'System', 'title' : 'MIDI Playback', 'aux4': self.midi_playback_select },
            'external_midi_player' :            { 'loc' : '-', 'type' : 'V', 'col' : 'R', 'show' : True, 'section' : 'System', 'title' : 'Ext MIDI Player', 'ptype' : 'file'  },
            'external_midi_player_options':     { 'loc' : '-', 'type' : 'V', 'col' : 'R', 'show' : True, 'section' : 'System', 'title' : 'Ext MIDI Player Options', 'ptype' : 'none'  },

            'external_youtube_viewer' :         { 'loc' : '-', 'type' : 'V', 'col' : 'R', 'show' : True, 'section' : 'System', 'title' : 'Ext YouTube Viewer', 'ptype' : 'file'  },
            'external_youtube_viewer_options' : { 'loc' : '-', 'type' : 'V', 'col' : 'R', 'show' : True, 'section' : 'System', 'title' : 'Ext YouTube Viewer Options', 'ptype' : 'none'  },
            'musescore_program' :               { 'loc' : '-', 'type' : 'V', 'col' : 'R', 'show' : True, 'section' : 'System', 'title' : 'MuseScore Executable', 'ptype' : 'file'  },
            'chordpro_program' :                { 'loc' : '-', 'type' : 'V', 'col' : 'R', 'show' : True, 'section' : 'System', 'title' : 'ChordPro Executable', 'ptype' : 'file'  },

            #   No user configurable options for these but need them to build conf.v variables.
            #   The value for these comes from the config file.

            'source_priority' :                 { 'loc' : '-', 'type' : 'V', 'col' : 'R', 'show' : False, 'section' : 'System', 'title' : 'Src Priority, top is highest', 'rows' : 5  },
            'documentation_dir' :               { 'loc' : 'i', 'type' : 'V', 'show' : False, 'section' : 'System' },
            'thumbnail_dir' :                   { 'loc' : 'i', 'type' : 'V', 'show' : False, 'section' : 'System' },
            'music_index_dir' :                 { 'loc' : 'i', 'type' : 'V', 'show' : False, 'section' : 'System' },
            'canonicals' :                      { 'loc' : 'i', 'type' : 'V', 'show' : False, 'section' : 'System' },
            'corrections' :                     { 'loc' : 'i', 'type' : 'V', 'show' : False, 'section' : 'System' },
          # 'example_canonical2file_source':    { 'loc' : 'i', 'type' : 'V', 'show' : False, 'section' : 'System' },
            'youtube_index' :                   { 'loc' : 'i', 'type' : 'V', 'show' : False, 'section' : 'System' },
            'audiofile_index' :                 { 'loc' : 'C', 'type' : 'V', 'show' : False, 'section' : 'System' },
          # 'music_file_extensions' :           { 'loc' : '-', 'type' : 'V', 'show' : False, 'section' : 'System' },
            'audio_file_extensions' :           { 'loc' : '-', 'type' : 'V', 'show' : False, 'section' : 'System' },
          # 'index_sources' :                   { 'loc' : '-', 'type' : 'V', 'show' : False, 'section' : 'System' },
          # 'themes' :                          { 'loc' : '-', 'type' : 'V', 'show' : False, 'section' : 'System' },
            'music_from_image' :                { 'loc' : '-', 'type' : 'V', 'show' : False, 'section' : 'System' },

            #   These appear under source-specific sections, e.g. [[Buffalo]]
            #   WRW 5 Mar 2022 - Removed local2canon, sheetoffset, localbooknames. Hard-wired names are fine for these.
            #   Not quite, need definition so can add source directory name. Hard wire filenames here.
            #   WRW 30-Mar-2025 -

            'sheetoffsets' :                    { 'loc' : 's', 'type' : 'V', 'show' : False, 'section' : 'Source', 'name' : s.Const.Sheet_Offsets_File },
            'local2canon' :                     { 'loc' : 's', 'type' : 'V', 'show' : False, 'section' : 'Source', 'name' : s.Const.Local2Canon_File },
            'localbooknames' :                  { 'loc' : 's', 'type' : 'V', 'show' : False, 'section' : 'Source', 'name' : s.Const.Local_Book_Names_File },
            'folder' :                          { 'loc' : 'f', 'type' : 'V', 'show' : False, 'section' : 'Source' },
            'command' :                         { 'loc' : '-', 'type' : 'V', 'show' : False, 'section' : 'Source' },
            'src' :                             { 'loc' : '-', 'type' : 'V', 'show' : False, 'section' : 'Source' },
        }

        #   These are added to config_data_dict only when using MySql.

        self.settings_mysql_dict = {
            'database_user' :               { 'loc' : '-', 'type' : 'V', 'col' : 'R', 'show' : True, 'section' : 'System', 'title' : 'Database User', 'ptype' : 'none' },
            'database_password' :           { 'loc' : '-', 'type' : 'V', 'col' : 'R', 'show' : True, 'section' : 'System', 'title' : 'Database Password', 'ptype' : 'none' },
        }

        #   This can't be done inline as may be called from the source-specific routines with no driver interest.

    def update_dict( self ):
        s = Store()
        MYSQL, SQLITE, FULLTEXT = s.driver.values()
        if MYSQL:
            self.settings_dict.update( self.settings_mysql_dict )

        # configDataDict.ci_canon_select = ci_canon_select
        # configDataDict.config_data_dict = config_data_dict
        # configDataDict.config_data_dict_mysql = config_data_dict_mysql

# --------------------------------------------------------------------------
#   This contains config variables for reference by others.
#   Reference as: conf.v.config_variable_name where config_variable_name is in table above.

#   WRW 11-May-2025 - I believe I finally removed all s.conf.v or self.v refernces after
#       finding a few in build_tables.py. Not quite, still use it set_class_variables().

class Var():
    pass

# --------------------------------------------------------------------------
#   Use this after the picker to go back to ~/ notation
#   This came from chat a while back. Both try/except blocks are to accommodate
#   older Python versions, not a concern to me, simplify below.

def OMIT_collapse_home( path: Path ) -> str:
    try:
        return f"~/{path.relative_to(Path.home())}" if path.is_relative_to(Path.home()) else str(path)
    except AttributeError:
        try:
            return f"~/{path.relative_to(Path.home())}" if str(path).startswith(str(Path.home())) else str(path)
        except ValueError:
            return str(path)

# --------------------------------------------------------------------------
#   Use this after the picker to go back to ~/ notation
#   resolve() is for use on macOS where there could be symlinks, according to chat.
#   WRW 1-June-2025 - simplified from above as support for old Python not needed.

def collapse_home( path: Path ) -> str:
    path = path.resolve()
    home = Path.home().resolve()

    if path.is_relative_to(home):
        return f"~/{path.relative_to(home)}"

    return str(path)

# --------------------------------------------------------------------------
#   WRW 1-June-2025 - for values already relative to confdir

def collapse_config( path: Path ) -> str:
    s = Store()

    path = path.resolve()
    confdir = Path( s.conf.confdir ).resolve()

    if path.is_relative_to( confdir ):
        return f"{path.relative_to( confdir )}"

    return str(path)

# --------------------------------------------------------------------------

class myQLineEdit( QLineEdit ):
    rightClicked = Signal( object )

    def __init__( self ):
        super().__init__()

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self.rightClicked.emit( self )
        else:
            super().mousePressEvent(event)

    # ----------------------------------------------

    def contextMenuEvent(self, event):
        event.ignore()                      # Suppress the default context menu

# --------------------------------------------------------------------------
#   WRW 3-May-2025 - The Orig below took a lot of time to get working. This
#       is a new implementation from chat to prevent a hang on MacOS.

#   WRW 5-May-2025 - add some of original back in but preserve dialog open(), 
#       not exec(), approach. Looks good now.

#   WRW 29-May-2025 - add loc to select confdir initial dir on loc == 'c'.

def myPicker( parent, line_edit, loc, pick_dirs=False ):
    s = Store()
    text = line_edit.text().strip()       # Added 5-May-2025  

    # ----------------------------------------------------------
    #   Added back in 5-May-2025
    #   Establish start_dir and start_file for each scenario.

    if not text:
        if loc == 'c':
            start_dir = s.conf.confdir
        else:
            start_dir = Path.home()          # Start with home if box is empty
        start_file = ''

    else:                               # Text is possibly an executable in PATH
        path = shutil.which( text )
        if path:
            start_file = Path( path )
            start_dir = start_file.parent

        else:
            expanded = Path(text).expanduser().resolve()            # resolve() - resolve symlinks
            if expanded is dir:
                start_dir = expanded
                start_file = ''

            else:
                if loc == 'c':
                    start_dir = s.conf.confdir
                else:
                    start_dir = expanded.parent
                start_file = expanded.name

    start_dir = str( start_dir )
    start_file = str( start_file )

    # ----------------------------------------------------------

    dialog = QFileDialog(parent)
    dialog.setFileMode(QFileDialog.Directory if pick_dirs else QFileDialog.ExistingFile)

    dialog.setOption(QFileDialog.DontUseNativeDialog, True)     # Added 5-May-2025      Needed for hidden files.
    dialog.setFilter(dialog.filter() | QDir.Hidden)             # Added 5-May-2025

    dialog.setWindowTitle("Select File or Folder")

    # ----------------------------------------------------------
    # Added back in 5-May-2025

    if pick_dirs:
        dialog.setFileMode(QFileDialog.Directory)
        dialog.setOption(QFileDialog.ShowDirsOnly, True)
    else:
        dialog.setFileMode(QFileDialog.ExistingFile)
        dialog.setNameFilter("All Files (*)")

    dialog.setDirectory( start_dir )
    dialog.selectFile( start_file )

    # ----------------------------------------------------------
    #   Change 'Open' to 'Select'

    button_box = dialog.findChild(QDialogButtonBox)
    if button_box:
        open_button = button_box.button(QDialogButtonBox.Open)
        if open_button:
            open_button.setText("Select")

    # ----------------------------------------------------------
    #   Callback to collapse full path to ~/path.
    #   WRW 1-June-2025 - add collapse_config() for options relative to config dir.

    def on_selected( path, loc ):
        if path:
            if loc == 'c':
                line_edit.setText( collapse_config( Path(path) ) )
            else:
                line_edit.setText( collapse_home( Path(path) ) )

    # ----------------------------------------------------------

    dialog.fileSelected.connect( lambda path, _loc=loc: on_selected( path, _loc ))
    dialog.open()       # This is the change that prevented the hang on macOS. use open(), not exec().

# --------------------------------------------------------------------------
#   Could not use one of the standard pickers, styling was way off with them.
#   WRW 3-Apr-2025 - convert to class

class ORIG_myPicker( ):
    def __init__( self, parent, line_edit, pick_dirs=False ):
        text = line_edit.text().strip()
    
        # ----------------------------------------------------------
        #   Establish start_dir and start_file for each scenario.

        if not text:
            start_dir = Path.home()          # Start with home if box is empty
            start_file = ''

        else:                               # Text is possibly an executable in PATH
            path = shutil.which( text )
            if path:
                start_file = Path( path )
                start_dir = start_file.parent

            else:
                expanded = Path(text).expanduser().resolve()            # resolve() - resolve symlinks
                if expanded is dir:
                    start_dir = expanded                     
                    start_file = ''

                else:
                    start_dir = expanded.parent
                    start_file = expanded.name

        start_dir = str( start_dir )
        start_file = str( start_file )

        # ----------------------------------------------------------
    
        # dialog = QFileDialog( line_edit )
        dialog = QFileDialog( parent )
        dialog.setOption(QFileDialog.DontUseNativeDialog, True)     # Needed to show hidden files
        dialog.setFilter(dialog.filter() | QDir.Hidden)
    
        if False:
            try:
                dialog.setOption(QFileDialog.ShowHidden, True)
            except AttributeError:
            # Fallback for older Qt versions
                dialog.setOption(QFileDialog.Option(0x04), True)
    
        if pick_dirs:
            dialog.setFileMode(QFileDialog.Directory)
            dialog.setOption(QFileDialog.ShowDirsOnly, True)
        else:
            dialog.setFileMode(QFileDialog.ExistingFile)
            dialog.setNameFilter("All Files (*)")
    
        dialog.setDirectory( start_dir )
        dialog.selectFile( start_file )

        button_box = dialog.findChild(QDialogButtonBox)
        if button_box:
            open_button = button_box.button(QDialogButtonBox.Open)
            if open_button:
                open_button.setText("Select")
    
        if dialog.exec():
            selected = Path(dialog.selectedFiles()[0]).resolve()
            collapsed = collapse_home(selected)
            line_edit.setText(collapsed)                # *** Update text box here

        #   Setting the directory back to a small one appears to improve performance on successive launches.
        dialog.setDirectory(os.path.expanduser("~")) # /// EXPERIMENTAL Trying to clear dialog cache to prevent slowdown
        dialog.deleteLater()                         # /// EXPERIMENTAL Trying to clear dialog cache to prevent slowdown
        del dialog                                   #      on each successive launch.

# --------------------------------------------------------------------------
#   As implemented by Chat.

def CHATmyPicker(parent, line_edit, pick_dirs=False):

    dialog = QFileDialog(parent)
    dialog.setFileMode(QFileDialog.Directory if pick_dirs else QFileDialog.ExistingFile)
    dialog.setOptions(QFileDialog.DontUseNativeDialog)
    dialog.setWindowTitle("Select File or Folder")

    # Determine the starting directory
    start_dir = str(Path.home())
    if text := line_edit.text().strip():
        expanded = Path(text).expanduser().resolve()
        if expanded.is_dir():
            start_dir = str(expanded)
        elif expanded.exists():
            start_dir = str(expanded.parent)
    dialog.setDirectory(start_dir)

    def on_selected(path):
        if path:
            line_edit.setText(collapse_home(Path(path)))

    dialog.fileSelected.connect(on_selected)
    dialog.open()

# --------------------------------------------------------------------------
#   WRW 3-Apr-2025 - From chat.

class myTextEdit( QTextEdit):
    rightClicked = Signal( object )

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.RightButton:
            self.rightClicked.emit( self )
            event.accept()
        else:
            super().mousePressEvent(event)

# ------------------------------------
#   Neither of myMultiFilePicker_A() or myMultiFilePicker_B() work well. I want
#   to show selected dirs and allow the user to select, deselect, and accept.
#   Qt does not support multiple selection on dirs. Best not to use a picker at
#   all for now until I can do it right, which is like B but with a bit more polish.

class myMultiFilePicker_A( ):
    def __init__(self, text_box_widget, base_dir, contents ):
        contents = contents or []

        dialog = QFileDialog( text_box_widget )
        dialog.setOption(QFileDialog.DontUseNativeDialog, True)  # Enables better styling + hidden files
        #   WRW 3-May-2025 - Testing on MacOS, no difference
        # dialog.setOption(QFileDialog.DontUseNativeDialog, False)
        dialog.setFileMode(QFileDialog.ExistingFiles)
        dialog.setNameFilter("All Files (*)")
        dialog.setDirectory(str(base_dir))
        dialog.setFilter(dialog.filter() | QDir.Hidden)
        dialog.setLabelText(QFileDialog.Accept, "Select")

        # Preselect files if possible
        if contents:
            for file in contents:
                dialog.selectFile( str(base_dir / file ))

        # Customize button label
        button_box = dialog.findChild(QDialogButtonBox)
        if button_box:
            select_button = button_box.button(QDialogButtonBox.Open)
            if select_button:
                select_button.setText("Select")

        if dialog.exec():
            selected = [Path(f).name for f in dialog.selectedFiles()]
            # Join as newline-separated list if multiline, or space/comma if you prefer
            text_box_widget.setText('\n'.join(selected))

# --------------------------------------------------------------------------

class myMultiFilePicker_B( QDialog ):
    def __init__(self, text_box_widget, base_dir=Path.home(), initial_dirs=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Multiple Directories")
        self.base_dir = base_dir
        self.selected_dirs = list(initial_dirs or [])

        layout = QVBoxLayout(self)

        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        layout.addWidget(self.text_edit)

        self.select_button = QPushButton("Add Directory")
        self.select_button.clicked.connect(self.select_directory)
        layout.addWidget(self.select_button)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self.update_text()

    def select_directory(self):
        selected = QFileDialog.getExistingDirectory(self, "Select Directory", str(self.base_dir))
        if selected:
            name = Path(selected).name
            if name not in self.selected_dirs:
                self.selected_dirs.append(name)
                self.update_text()

    def update_text(self):
        self.text_edit.setPlainText('\n'.join(self.selected_dirs))

    def get_selected_dirs(self):
        return self.selected_dirs

# --------------------------------------------------------------------------
#   WRW 29-May-2025 - This is the one currently used, all others had problems

class myMultiFilePicker_C( QDialog ):
    def __init__(self, field_name, base_dir=Path.home(), initial_dirs=None, parent=None):
        super().__init__(parent)

        self.setWindowTitle( f"Folder Selection")
        self.base_dir = Path(base_dir)
        self.setMinimumSize(700, 400)

        self.selected_dirs = list(initial_dirs or [])

        # -----------------------------------------------------------------
        # Main layout
        layout = QVBoxLayout(self)

        txt = QLabel( "Select a folder in the right panel, click 'Add' to add it to the folder list in the left panel." )
        layout.addWidget( txt )
        txt = QLabel( "Select a folder in the left panel, click 'Del' to remove it from the folder list" )
        layout.addWidget( txt )

        layout.addSpacerItem( QSpacerItem(0, 10, QSizePolicy.Minimum, QSizePolicy.Fixed ))

        # -----------------------------------------------------------------
        # Horizontal layout for list, buttons, and picker
        main_row = QHBoxLayout()

        left_column = QVBoxLayout()
        right_column = QVBoxLayout()

        # -----------------------------------------------------------------
        # Left: selected items list
        left_column.addWidget( QLabel( f"Item: {field_name}" ))

        self.dir_list = QListWidget()
        self.dir_list.addItems(self.selected_dirs)

        self.dir_list.setCurrentRow(-1)       # No selection            Attempt to remove the initial line under the first item, does not work. 
        self.dir_list.clearSelection()        # No visual selection     Attempt to remove the initial line under the first item, does not work. 
        self.dir_list.clearFocus()            # Removes focus ring      Attempt to remove the initial line under the first item, does not work. 

        left_column.addWidget( self.dir_list )
        main_row.addLayout(left_column)

        # -----------------------------------------------------------------
        # Middle: add/del buttons
        buttons_col = QVBoxLayout()
        buttons_col.addSpacerItem( QSpacerItem(0, 50, QSizePolicy.Minimum, QSizePolicy.Fixed ))
        self.add_button = QPushButton("Add")
        self.del_button = QPushButton("Del")

        buttons_col.addWidget(self.add_button)
        buttons_col.addWidget(self.del_button)
        buttons_col.addStretch()

        main_row.addLayout(buttons_col)

        # -----------------------------------------------------------------
        # Right: file system view
        right_column.addWidget( QLabel( f"Root Folder: {str(base_dir)}" ))

        self.model = QFileSystemModel()
        self.model.setRootPath(str(self.base_dir))
        self.model.setFilter(QDir.Dirs | QDir.Files | QDir.NoDotAndDotDot)      # WRW 29-May-2025 - add QDir.Files

        self.dir_view = QTreeView()
        self.dir_view.setModel(self.model)
        self.dir_view.setRootIndex(self.model.index(str(self.base_dir)))
        self.dir_view.setHeaderHidden(False)
        for col in range(1, self.model.columnCount()):      # Hide Size, Type, Modified
            self.dir_view.hideColumn(col)

        right_column.addWidget(self.dir_view)
        main_row.addLayout(right_column)

        layout.addLayout(main_row)

        # -----------------------------------------------------------------
        # Bottom: OK/Cancel buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        layout.addWidget(self.button_box)

        # Connections
        self.add_button.clicked.connect(self.add_selected_directory)
        self.del_button.clicked.connect(self.remove_selected_from_list)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

    def add_selected_directory(self):
        index: QModelIndex = self.dir_view.currentIndex()
        if index.isValid():
            path = self.model.filePath(index)
            name = Path(path).name
            if name not in [self.dir_list.item(i).text() for i in range(self.dir_list.count())]:
                self.dir_list.addItem(name)

    def remove_selected_from_list(self):
        for item in self.dir_list.selectedItems():
            self.dir_list.takeItem(self.dir_list.row(item))

    def get_selected_dirs(self):
        return [self.dir_list.item(i).text() for i in range(self.dir_list.count())]

# --------------------------------------------------------------------------

class ConfigPopup( QDialog ):
    def __init__(self, config, hostname ):

        super().__init__()
        self.setObjectName( 'configureDialog' )     # For styling
        s = Store()
        config_data_dict = configDataDict().settings_dict

        self.setWindowTitle("Configuration Options")
        self.setMinimumSize(1000, 600)  # Set appropriate window size
        self.inputs = {}  # Store input fields for access by get_values.
        
        main_layout = QVBoxLayout(self)     # Main layout

        #   CONSIDER Possibly add get_user_and_password() from prior. Already here
        #   WRW 21-May-2025 - remove first_flag and first_text logic from here.
        #   Previously I was showing a message at the top of the config window on first-launch
        #   with -d mysql, now show the message in a separate popup.

        # Scroll area to handle large forms
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        # Widget inside scroll area
        scroll_widget = QWidget()
        column_layout = QHBoxLayout()       # Two columns of two grids each, each grid has two columns

        form_left_layout =  QGridLayout()  # Grid layout for two-column arrangement
        form_right_layout = QGridLayout()  # Grid layout for two-column arrangement

        form_left_layout.setContentsMargins( 0, 0, 0, 0 )     # Spacing around items in layout
        form_right_layout.setContentsMargins( 0, 0, 0, 0 )

        # -------------------------------------------------------------------
        #   Traverse data dictionary. Make a label and input_widget for each item in dict.

        row_left = 0        # Row counter for each column of two columns in layout
        row_right = 0       # Maps item name, i.e. 'jjazz_file_root', to text edit widget for that item
        links = {}

        for item, dd in config_data_dict.items():       # Build configuration layout for dd items

            showIcon = False

            # -------------------------
            #   Ignore some items in data dict.

            if not dd[ 'show' ]:
                continue
    
            # -------------------------
            #   Get current value of option, some are host-specific
            #   Labels have no value and don't appear in settings file.

            if dd[ 'type' ] != 'L':
                if dd[ 'section' ] == 'Host':
                    val = config['Host'][ hostname ][ item ]
                else:
                    val = config[ dd['section'] ][ item ]
    
            # -------------------------
            #   Column left or right specified in data dict.

            if dd['col' ] == 'L':
                current_layout = form_left_layout
                row = row_left
                row_left += 1
            else:
                current_layout = form_right_layout
                row = row_right
                row_right += 1

            # --------------------------------------------------
            #   Get the item name and make a label from it.
            #   WRW 3-Apr-2025 - add category labels to columns

            field_name = dd.get( 'title', item )         # WRW 18 June 2022 - from pylint recommendation.

            if dd[ 'type' ] == 'L':
                label = QLabel( field_name )
                label.setObjectName( 'configureLabel' )      # For styling

                current_layout.addWidget(label, row, 1 )     # Now on left side of col 1
                label.setAlignment(Qt.AlignLeft)
                label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed) # Needed this to prevent top-left item from expanding
                continue                                     # nothing in col 1 for labels

            else:
                label = QLabel( field_name + ":")
                current_layout.addWidget( label, row, 0)  # Label        # *** Add Label
                label.setAlignment(Qt.AlignTop | Qt.AlignRight)

            # -------------------------

            if dd[ 'type' ] == 'V':
                # self.inputs[field_name] = input_widget  # Store reference

                # --------------------------------------------------------------------------
                #   QTextEdit for multiple line input indicated by 'rows' in data dictionary.

                if 'rows' in dd:                    
                    rows = dd[ 'rows' ]
                    input_widget = myTextEdit()
                    input_widget.setContextMenuPolicy(Qt.NoContextMenu)

                    if 'ptype' in dd and dd[ 'ptype' ] == 'none':
                        input_widget.setToolTip("Enter content directly")
                    else:
                        input_widget.setToolTip("Right-click to select list of files in above folder or enter '.' for all files in folder")

                    #   A linked widget is a QLineEdit box above this myTextEdit box in the data dictionary.
                    #   WRW 29-May-2025 - Link can now be '-' to imply use config directory.

                    link = dd[ 'link' ] if 'link' in dd else None
                    if link == '-':
                        linked_widget = '-'
                    else:
                        linked_widget = links[ link ] if link in links else None

                    #   Thanks chat for this cute construct for passing current multiple values with lambda
                    #   Otherwise, got the last value in the loop. 'Late binding closure' problem.
                    #   _box_widget is text box which received click.

                    if linked_widget:
                        input_widget.rightClicked.connect( lambda _box_widget, 
                               _linked_widget=linked_widget,
                               _field_name=field_name: 
                                self.files_right_click( _field_name, _box_widget, _linked_widget ))

                # --------------------------------------------------------------------------

                else:
                    rows = 1
                    iconSize = QSize( 16, 16 )

                    if 'ptype' in dd:
                        loc = dd[ 'loc' ]       # WRW 29-May-2025 - Add for use of initial dir in myPicker

                        match dd[ 'ptype' ]:
                            case 'none':
                                input_widget = QLineEdit()
                                input_widget.setToolTip("Enter content directly")

                            case 'dir':
                                input_widget = myQLineEdit()        # right-clickable for directory picker
                                input_widget.rightClicked.connect( lambda box_widget, p=self, loc=loc: myPicker( p, box_widget, loc, pick_dirs=True ))
                                input_widget.setToolTip("Right-click to choose a folder")
                                icon = s.fb.getColoredSvgIcon( ":NIcons/document-open-folder.svg", iconSize )
                                label = QLabel()
                                pixmap = icon.pixmap(iconSize)
                                label.setPixmap(pixmap)
                                showIcon = True

                            case 'file':
                                input_widget = myQLineEdit()        # right-clickable for directory picker
                                input_widget.rightClicked.connect( lambda box_widget, p=self, loc=loc: myPicker( p, box_widget, loc, pick_dirs=False ))
                                input_widget.setToolTip("Right-click to choose a file")
                                icon = s.fb.getColoredSvgIcon( ":NIcons/document-properties.svg", iconSize )
                                label = QLabel()
                                pixmap = icon.pixmap(iconSize)
                                label.setPixmap(pixmap)
                                showIcon = True

                            case _:
                                print( f"ERROR-DEV: Unexpectd ptype '{dd[ 'ptype' ]}' for '{item}'", file=sys.stderr )
                                sys.exit(1)
                    else:
                        print( f"ERROR-DEV: No ptype given where expected for '{item}'", file=sys.stderr )
                        sys.exit(1)

                input_widget.setText( val )
                self.inputs[item] = input_widget  # Store reference
                input_widget.setFixedHeight( input_widget.fontMetrics().height() * rows + 4 )

            # -------------------------
            #   Binary checkbox

            elif dd[ 'type' ] == 'B':
                input_widget = QCheckBox()
                self.inputs[item] = input_widget  # Store reference
                t = val == 'True'
                input_widget.setChecked( t )

            # -------------------------
            #   Combo box, values come from 'aux1', 'aux2', 'aux3', 'aux4', 'aux5'

            elif dd[ 'type' ] == 'C':
                input_widget = QComboBox()
                self.inputs[item] = input_widget  # Store reference

                # ------------------------------------------------------
                if 'aux1' in dd:
                    # content = [ x for x in config[ dd['section'] ][ dd['aux1'] ].split('\n' )]
                    content = s.Const.system_styles
                    input_widget.addItems( content )  # Add dropdown options

                    initial_text = s.conf.val( 'style' )
                    index = input_widget.findText(initial_text)  # Get the index of the text
                    if index != -1:                              # Ensure the text exists in the combo box
                        input_widget.setCurrentIndex(index)

                # ------------------------------------------------------
                elif 'aux2' in dd:
                    content = dd['aux2']
                    input_widget.addItems( content )  # Add dropdown options

                # ------------------------------------------------------
                #   WRW 16-Mar-2025 - Add theming for icons. Not part of themes or styles above.
                #   WRW 10-Apr-2025 - 'icon_theme' commented out, this not used.

                elif 'aux3' in dd:
                    icon_themes = []
                    for path in QIcon.themeSearchPaths():
                        if path == ':/icons':
                            continue
                        dirs = [entry for entry in Path(path).iterdir() if entry.is_dir()]
                        for dir in dirs:
                            if Path( path, dir, 'index.theme' ).is_file():
                                icon_themes.append( str(dir.name) )

                    input_widget.addItems( icon_themes )  # Add dropdown options

                    initial_text = s.conf.val( 'icon_theme' )
                    index = input_widget.findText(initial_text)  # Get the index of the text
                    if index != -1:                              # Ensure the text exists in the combo box
                        input_widget.setCurrentIndex(index)

                # ------------------------------------------------------
                #   WRW 31-Mar-2025 - Finally added options for midi playback
                elif 'aux4' in dd:
                    content = dd['aux4']
                    input_widget.addItems( content )  # Add dropdown options

                    initial_text = s.conf.val( 'midi_playback' )
                    index = input_widget.findText(initial_text)  # Get the index of the text
                    if index != -1:                              # Ensure the text exists in the combo box
                        input_widget.setCurrentIndex(index)

                #   WRW 13-Apr-2025 - I'd like the dialog box to reflect the changes in 'appearance' as the
                #   user selects from the dropdown but this is not enough and I don't want to persue it now.
                #   Probably generalized setAppearance() code to accept a window argument

                if False:
                    def updateConfigWindow( widget, window, index ):
                        appearance = widget.itemText(index)
                        s = Store()
                        palette = s.conf.palettes[ appearance ]
                        palette = s.conf.create_palette( palette )
                        window.setPalette( palette )

                # ------------------------------------------------------
                if 'aux5' in dd:
                    content = s.conf.get_appearances( )
                    input_widget.addItems( content )  # Add dropdown options

                    initial_text = s.conf.val( 'theme' )
                    index = input_widget.findText(initial_text)  # Get the index of the text
                    if index != -1:                              # Ensure the text exists in the combo box
                        input_widget.setCurrentIndex(index)

                  # input_widget.currentIndexChanged.connect( lambda x, _widget=input_widget: updateConfigWindow( _widget, self, x ) )

                # ------------------------------------------------------

            else:
                print( f"ERROR-DEV: Unexpected type: {dd[ 'type']} in ConfigPopup()" )

            # --------------------------------------------------------------------------
            #   Finally, add one of the above widgets to one of the columns
            #   WRW 9-Apr-2025 Add icon to right of some text boxes.

            if showIcon:
                ebox_layout = QHBoxLayout()
                ebox_layout.addWidget( input_widget, alignment=Qt.AlignTop )
                ebox_layout.addWidget( label, alignment=Qt.AlignTop )
                current_layout.addLayout( ebox_layout, row, 1 )

            else:
                current_layout.addWidget(input_widget, row, 1 )          # *** Add widget to hold value of item

            links[ item ] = input_widget

            # --------------------------------------------------------------------------

        column_layout.addLayout( form_left_layout )
        column_layout.addLayout( form_right_layout )

        # Set layout for the scrollable widget
        scroll_widget.setLayout(column_layout)
        scroll_area.setWidget(scroll_widget)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.accept)  # Close on click
        button_layout.addWidget(save_button)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)  # Close window on cancel, chat recommeded reject over close
        button_layout.addWidget(cancel_button)

        main_layout.addWidget(scroll_area)
        main_layout.addLayout(button_layout)

    # ------------------------------------------------------------------

    def files_right_click( self, field_name, text_box_widget, linked_widget ):
        s = Store()

        contents = text_box_widget.toPlainText().splitlines()
        if linked_widget == '-':
            dir = Path( s.conf.confdir )
        else:
            dir = Path( linked_widget.text()).expanduser()

        Use_A = False
        Use_B = False
        Use_C = True

        if Use_A:
            myMultiFilePicker_A( text_box_widget, Path(dir), contents )

        if Use_B:
            dialog = myMultiFilePicker_B( text_box_widget, Path(dir), contents )
            if dialog.exec():
                dirs = dialog.get_selected_dirs()
                # print( "/// selected:", dirs )

        #   WRW 26-May-2025 - a pain on MacOS but ok now with dialog as an instance var
        #   to keep dialog in scope and passing parent=self. Don't know if self.dialog
        #   is critical but keep it to be safe.
            
        if Use_C:
            self.dialog = myMultiFilePicker_C(                           
                field_name=field_name,
                initial_dirs=contents,
                base_dir=dir,
                parent=self         # Critical on MacOS. Ensures it's modal relative to the config window
            )

            def on_finished(result):
                if result == QDialog.Accepted:
                    final_list = self.dialog.get_selected_dirs()
                    text_box_widget.setPlainText('\n'.join(final_list))

            self.dialog.finished.connect(on_finished)
            self.dialog.open()  # Modal, non-blocking, works on macOS

    # ------------------------------------------------------------------
    #   Returns a dictionary with all field values.

    def get_values(self):
        values = {}

        for item, widget in self.inputs.items():

            if isinstance(widget, QLineEdit):
                values[item] = widget.text()

            elif isinstance(widget, QCheckBox):
                values[item] = widget.isChecked()

            elif isinstance(widget, QComboBox):
                values[item] = widget.currentText()

            elif isinstance(widget, QTextEdit):
                values[item] = widget.toPlainText()

        return values

# --------------------------------------------------------------------------
#   WRW 12 Mar 2022 - Dealing with data_directory, location where installation        
#       process places some files. Much cleaner, can remove set_install_cwd() from many locations.
#       Name of self.install_cwd is vestigial.

#   WRW 1-Feb-2025 - Convert to singleton.  Only change is little code at top.
#   Singleton is now of ocd interest only because this, and FB, are instiatiated only
#   once and subsequently referenced by s.conf, s.fb.

class Config():
    _instance = None

    def __new__( cls, confdir, userdatadir ):
        if cls._instance is None:
            cls._instance = super().__new__( cls )
        return cls._instance

    # ----------------------------------------------------------

    def __init__( self, confdir, userdatadir ):
        if hasattr( self, '_initialized' ):     # Chat prefers this over a flag initialized in __new__().
            return                              # No point initializing a singleton twice.
        self._initialized = True

        s = Store()

        # self.palettes = self.get_palettes()
        self.currentAppearance = None

        # ------------------------------------------------------------
        #   WRW 20-May-2025 - init self.confdir and self.userdatadir from calling args.

        self.confdir = confdir              # stdConfig or specified on command line with -c confdir
        self.userdatadir = userdatadir      # stdData or specified on command line with -u userdatadir
        self.user_data_directory= self.userdatadir      # too many references, keep duplicate of userdatadir
        self.v = Var()                      # Config options stored under v for use here.
        self.config = None                  # Configparser object, contents of config file
        self.progress = []                  # Journal of initialization steps for debugging. View with -p option.

        # ------------------------------------------------------------
        #   The local references are used so extensively here I don't 
        #       want to change to to s.Const, at least not yet. This is fine. Yup, keep as is.
        #       Destabilization is likely otherwise. At least they come from constants.

      # self.program_directory =        s.Const.Program_Directory
      # self.home_confdir =             s.Const.Home_Confdir
      # self.userdatadir =              s.Const.User_Data_Dir      # WRW 1-Apr-2025 - Separated into two from self.data_directory
        self.package_data_directory =   s.Const.Package_Data_Directory
        self.hostname =                 s.Const.Hostname
        self.config_file =              s.Const.Config_File         # Name of configuration file, in home or specified dir.
        self.index_source_dir =         s.Const.Index_Source_Dir    # Root of source-specific directories.
        self.canonical_dir =            s.Const.Canonical_Dir       # Some additional files
        self.mysql_database =           s.Const.MySql_DB
        self.sqlite_database =          s.Const.SqLite_DB_File

        #   These are names of default files in the configuration directory created at first launch.

        self.audiofile_index_file =     s.Const.audioFileIndexFile
        self.setlist_file =             s.Const.Setlist_File
        self.canonical2file =           s.Const.Canonical2File
        self.example_canonical2file =   s.Const.Example_Canonical2File

    # ----------------------------------------------------------------------------
    #   Called from early initialization, just after Config() instantiated.

    def update_dict( self ):
        config_data_dict = configDataDict()              
        config_data_dict.update_dict()

    # ----------------------------------------------------------------------------
    #   Accessor function for configuration options stored in self.config or self.v store.
    #   /// RESUME - someday understand why I did this and not get directly from self.config.
    #   /// RESUME - consider refactoring with chat code in Chat-fb_config_refactor.py.

    #   Return value of configuration option 'item', which may be in 'source' section of file.
    #   A reminder that that 'source' and 'src' refer to the source of the raw index data and
    #   are found in the [[Source]] section of the config file.

    #   WRW 20 Feb 2022 - Trying to insulate calling code further from configuration details.
    #       This will fetch the config value indicated by item and possibly expanded as indicated by 'loc' flag.
    #       For now convert all to posix. Later may want to deal only with Path.
    #       If 'rows' is defined return values as list, otherwise as a single value.
    #   WRW 21 Feb 2022 - add 'src' argument to get source-specific options.

    #   WRW 13-May-2025 - after converting a few remaining s.conf.v.music_file_folders (and other) references
    #       to s.conf.val( 'music_file_folders' ) I hit a snag on items with 'rows'. s.conf.v.* returns
    #       a string while s.conf.val() returns a list.

    def val( self, item, source=None ):
        config_data_dict = configDataDict().settings_dict
        if item not in config_data_dict:
            print( f"ERROR-DEV: Configuration item {item} not in data dictionary", file=sys.stderr )
            sys.exit(1)

        # ---------------------------------------------------------------
        #   Get val from source-specific section of config directly.
        #   Have to go back to configparser object to handle this. 
        #   Assume loc is '-' for this. That is the case for all items so far.
        #   WRW 25-Mar-2025 - Change to if/elif

        if source:
            # if not self.config.has_section( source ):
            if 'Source' not in self.config and source not in self.config[ 'Source' ]:
                print( f"ERROR-DEV: Source {source} section not found in config file {self.config_file}", file=sys.stderr )
                sys.exit( 1 )

            dd = config_data_dict[ item ]
            if dd[ 'section' ] != 'Source':
                print( f"ERROR-DEV: Configuration item {item} does not match 'Source' section in config file {self.config_file}", file=sys.stderr )
                sys.exit( 1 )

            # val = self.config['Source'][ source ][ item ]
            loc = dd[ 'loc' ]

            if loc == '-':
                val = self.config['Source'][ source ][ item ]           # *** Get val from self.config
                return val

            elif loc == 's':
                name = dd[ 'name' ]
                return Path( self.userdatadir, "Index-Sources", source, name )

            elif loc == 'f':
                val = self.config['Source'][ source ][ item ]
                return Path( self.userdatadir, "Index-Sources", val )

            else:
                print( f"ERROR-DEV: Unexpected value of loc '{loc}' in 'Source' section in config file {self.config_file}", file=sys.stderr )
                sys.exit( 1 )

        # ----------------------------------------------------------------
        #   WRW 5 Mar 2022 - Looks like issue here when have empty val. Introduced that 
        #       in the host-specific values in the config file initialized here.
        #       No, working just as expected. For 'c' returned just confdir without any file.
        #   WRW 16 May 2022 - add test for empty val so don't return [''] or PosixPath( '.' )
        #   WRW 25-Mar-2025 - Change to if/elif

        dd = config_data_dict[ item ]
        val = getattr( self.v, item )       # *** Get value from self.v store.
        loc = dd[ 'loc' ]

        rows = dd[ 'rows' ] if 'rows' in dd else None

        # -----------------------------
        if loc == '-':
            if val:
                return [ x for x in val.split( '\n' ) ] if rows else val
            else:
                return [] if rows else val

        # -----------------------------
        #   return [ str(Path( self.confdir, x ) ) for x in val.split( '\n' ) ] if rows else )
        #   WRW 31-May-2025 - val will include "~/.config/birdland_qt/" if used the
        #       picker to enter a value instead of just typing the filename.
        #       Check of anchored at '/'. If so don't add self.confdir.

        elif loc == 'c':
            if val:
                if rows:        # Return list
                    ret = []
                    for x in val.split( '\n' ):
                        x = Path(x).expanduser()
                        if x.is_absolute():
                            ret.append( str( x ))
                        else:
                            ret.append( str(Path( self.confdir, x )))
                    return ret

                else:           # Return str
                    val = Path(val).expanduser()
                    if val.is_absolute():
                        return str( val )
                    else:
                        return str(Path( self.confdir, val ))
            else:
                return [] if rows else ''

        # WRW 4 Mar 2022 - Add hostname to filename.
        #   I'd rather put it between stem and suffixes but a general solution too much work and this is fine.

        # -----------------------------
        elif loc == 'C':
            if val:
                if rows:
                    res = []
                    for x in val.split( '\n' ):
                        res.append( str( Path( self.confdir, f"{self.hostname}-{x}" )) )
                    return res
                else:
                    t = str(Path( self.confdir, f"{self.hostname}-{val}" ))
                    return t
            else:
                return [] if rows else ''

        # -----------------------------
        elif loc == 'i':

            # print( "fb_config:", item, val, self.userdatadir )

            if val:
                return [ str(Path( self.userdatadir, x )) for x in val.split( '\n' ) ] if rows else str(Path( self.userdatadir, val ))
            else:
                return [] if rows else ''

        # -----------------------------
        elif loc == 'a':
            if val:
                return [ str(Path( x ).expanduser()) for x in val.split( '\n' ) ] if rows else str(Path( val ).expanduser())
            else:
                return [] if rows else ''

        # -----------------------------
        elif loc in ('s', 'f'):        # In dd only for 'source' section WRW 25-Mar-2025 - comment out, no leave in for show_datadict()
            pass

        # -----------------------------
        else:
            print( f"ERROR-DEVP unexpected 'loc' value '{loc}' for {item} in data dictionary", file=sys.stderr )
            sys.exit(1)


    # ----------------------------------------------------------------------------
    #   WRW 5 March 2022 - needed this when removed 's' items from data dict.

    def get_source_path( self, source ):
        return Path( self.userdatadir, "Index-Sources", source )

    # ----------------------------------------------------------------------------
    #   WRW 5 March 2022 - Get an array of all source sections in config file.

    def get_sources( self ):
        return self.sources

    # ----------------------------------------------------------------------------
    #   This is specifically for a configuration option error only.

    def do_nastygram( self, option, path ):
        s = Store()
        config_data_dict = configDataDict().settings_dict

        if not option in config_data_dict:
            print( f"ERROR-DEV: option {option} not found in config_data_dict", file=sys.stderr )
            # t = f"ERROR-DEV: option {option} not found in config_data_dict"
            # s.msgCritical( t )
            sys.exit(1)

        title = config_data_dict[ option ][ 'title' ]
        # section = config_data_dict[ option ][ 'section' ]
        # &nbsp;&nbsp;in the '{section}' section of the configuration file<br><br>

        t = f"""It appears that you have not configured the option<br><br>
            &nbsp;&nbsp;'{title}'<br><br>
            or the location:<br><br>
            &nbsp;&nbsp;'{path}'<br><br>
            is not a full path to a file.<br>
            Please check your configuration in:<br><br>
            &nbsp;&nbsp;<i>File->Settings</i>.
        """
        # self.do_popup( t )
        s.msgWarn( t )
        return

    # ----------------------------------------------------------------------------
    #   WRW 30-Mar-2025 - show the config data pretty-printed. Thanks, chat.

    def print_nested_dict(self, d, indent=0):
        pad = "    " * indent
        for key, value in d.items():
            if isinstance(value, dict):
                print(f"{pad}{key}:")
                self.print_nested_dict(value, indent + 1)
            elif isinstance(value, str) and '\n' in value:
                print(f"{pad}{key}:")
                for line in value.splitlines():
                    print(f"{pad}    {line}")
            else:
                print(f"{pad}{key}: {value}")

    def show_settings( self ):
        self.print_nested_dict( self.config )

    # -------------------------------------------------------------------------------
    #   Show all values in data dictionary expanded to full path as appropriate.
    #   Not too pretty but adequate to diagnose path issues.

    def show_datadict( self ):
        config_data_dict = configDataDict().settings_dict

        hosts = self.config[ 'Host' ].sections
        print( "Hosts:", hosts )

        sources = self.config[ 'Source' ].sections
        print( "Sources:", sources )

        print( '' )
        print( "Definition of (loc) field" )
        print( configDataDict.locDef )

        for item, dd in sorted( config_data_dict.items()):
            loc = dd[ 'loc' ]
            if dd[ 'section' ] == 'Source':
                for source in sources:
                    try:
                        val = self.val( item, source )
                    except:
                        val = 'na'

                    if '\n' in str(val):
                        val = ', '.join( val.splitlines())

                    print( f"{item:>30} ({loc}) : {val}" )
            else:
                try:
                    val = self.val( item )
                except:
                    val = 'na'

                if '\n' in str(val):
                    val = ', '.join( val.splitlines())
                print( f"{item:>30} ({loc}) : {val}" )

    # --------------------------------------------------------------------------
    #   Look for config directory and file in one, not several, well-known locations unless specified
    #       by user. Creat it in default location if not found.
    #       Save config filename and config dir for possible later use by save_config()
    #   Configuration is saved in class variables in self.v object for reference elsewhere.
    #   Note that raw 'config' as returned by configparser is not used externally.

    #   WRW 22 Feb 2022 (Yes, 22222) - I don't think I should be trying to initialize here.
    #       Do that separately. Getting into a loop when build-table.py calls get_config() when
    #       we call build-table.py here to build the table. Pulled it out.

    #   WRW - Had to add as_posix() when running in virtual environment??? No, use str() for all paths
    #   WRW 20-May-2025 - Migrating to cleaner approach

    def get_config( self ):
        path = Path( self.confdir, self.config_file )                                                       
        self.config = ConfigObj( str(path) )                 # *** Bang! Read config file here.

    # ----------------------------------------------------------------
    #   Set class variables for later access. For migration away from hostname and direct references.
    #   Get source names from config file and a map to the src names, which must be an element of the source.
    #   Builds a secondary store of configuration option values in self.v for access by s.conf.val().
    #   And builds two source <--> src mapping dicts.

    def set_class_variables( self ):

        s = Store()
        config = self.config

        # ----------------------------------------------------------------------------------------------------
        #   Create a mapping between src and source.     
        #       src_to_source used in fb_utils.py
        #       source_to_source not used, it appears.

        #   WRW 2 Mar 2022 - Finally geting around to localizing the definition of the source/src to just
        #   the config file (and probably the source-specific routines do_*.py in Index-Sources). They
        #   must agree with the config file.

        self.sources = config[ 'Source' ].sections
        self.source_to_src = {}
        self.src_to_source = {}

        for source in self.sources:
            if 'src' not in config[ 'Source' ][ source ]:
                print( f"ERROR: At set_class_variables() config file {self.config_file} missing 'src' for {source} in 'Source' section" )
                sys.exit(1)

            ssource = str( source )

            src = str( config[ 'Source' ][ source ][ 'src' ] )
            self.source_to_src[ ssource ] = src
            self.src_to_source[ src ] = ssource

        # --------------------------------------------------
        #   Traverse data dictionary, obtain option value from 'config' dict,
        #   populate self.v for access by val() (and also Settings class - no longer).

        config_data_dict = configDataDict().settings_dict
        for item, dd in config_data_dict.items():                                                

            if dd[ 'type' ] == 'L':         # Labels are not in config file
                continue

            # -----------------------------------------
            try:
                if dd[ 'section' ] == 'Host':
                    val = config['Host'][ self.hostname ][ item ]       # *** Obtain val from config dict.

                elif dd[ 'section' ] == 'System':
                    val = config[ dd['section'] ][ item ]               # *** Obtain val from config dict.

            except KeyError as e:
                t = Path( self.confdir, self.config_file )

                s.msgCritical( f"Your configuration file '{t}' is missing {e} setting" )
                print( f"ERROR Your configuration file '{t}' is missing {e} setting", file=sys.stderr )
                sys.exit(1)

            # -------------------------------------------

            if dd[ 'type' ] == 'B':                                                       
                val = val == 'True'             # Was: val = True if val == 'True' else False

            setattr( self.v, item, val )        # Old style.        *** Save val in self.v for ref in val()

          # s.Setting.set( item, val )          # New style. WRW 25-Mar-2025 ////EXPLORATORY

    # ============================================================================
    #   Display configuration window so user can change settings.
    
    def do_configure( self ):
        s = Store()
    
        while True:
            popup = ConfigPopup( self.config, self.hostname )
            res = popup.exec()  # Show as a modal popup

            #   Note that can still call popup.get_values() until popup goes out of scope,
            #   i.e., when do_configure() returns.

            # ---------------------------------------------------------------
            if res:         # Click on Save
                values = popup.get_values()

                if self.validate_config( values ):
                    self.config = self.do_configure_save( self.config, values )
                    self.get_config()               # Reread the saved config
                    break

                else:       
                    saveOnError = False
                    t = "One or more settings are not valid:<br>"
                    t += '<br>'.join( self.validate_errors )
                    t += '<br>'
                    if saveOnError:
                        t += 'Saving with errors.'
                    s.msgWarn( t )

                    # WRW 4-Mar-2025 - At least temporarily during port to Windows save
                    # the configuration even if it has errors.

                    if saveOnError:
                        self.config = self.do_configure_save( self.config, values )
                        self.get_config()               # Reread the saved config
                        break

            # ---------------------------------------------------------------
            else:               # Click on Cancel or close in the decoration
                return False

        # --------------------------------------------
        return True         # break out of loop to here


    # --------------------------------------------------------------------------
    #   WRW 26 Feb 2022 - Add code to validate some configuration values before
    #       save config back in birdland.conf.

    def validate_config( self, values ):
        s = Store()
        MYSQL, SQLITE, FULLTEXT = s.driver.values()

        errors = []

        for folder in values[ 'music_file_folders' ].split( '\n' ):
            path = Path( Path( values[ 'music_file_root' ] ).expanduser(), folder )
            if not path.is_dir():
                errors.append( f"Music folder '{path}' not found." )

        for folder in values[ 'audio_folders' ].split( '\n' ):
            path = Path( Path( values[ 'audio_file_root' ] ).expanduser(), folder )
            if not path.is_dir():
                errors.append( f"Audio folder '{path}' not found." )

        for folder in values[ 'midi_folders' ].split( '\n' ):
            path = Path( Path( values[ 'midi_file_root' ]).expanduser(), folder )
            if not path.is_dir():
                errors.append( f"MIDI folder '{path}' not found." )

        for folder in values[ 'chordpro_folders' ].split( '\n' ):
            path = Path( Path( values[ 'chordpro_file_root' ]).expanduser(), folder )
            if not path.is_dir():
                errors.append( f"Chordpro folder '{path}' not found." )

        for folder in values[ 'jjazz_folders' ].split( '\n' ):
            path = Path( Path( values[ 'jjazz_file_root' ]).expanduser(), folder )
            if not path.is_dir():
                errors.append( f"JJazz folder '{path}' not found." )

        path = values[ 'soundfont_file' ]
        if path:
             path = Path( path )
             if not path.is_file():
                if not path.expanduser().is_file():
                    errors.append( f"Soundfont file '{path}' not found." )

        if MYSQL and values[ 'database_user' ] and values[ 'database_password' ]:
            import MySQLdb
            try:
                conn = MySQLdb.connect( "localhost", values[ 'database_user' ] , values[ 'database_password'], self.mysql_database )

          # except Exception as e:
            except Exception:
                (extype, exvalue, traceback) = sys.exc_info()
                errors.append( f"Error accessing {self.mysql_database} database:" )
                errors.append( f"\t{exvalue}" )         # This is not as pretty.
                # errors.append( f"\t{e.args[1]}" )     # This assumes execpetion-specific knowledge.

            else:
                conn.close()

        self.validate_errors = errors

      # return False if len( errors ) else True
        return not errors  
    
    # --------------------------------------------------------------------------

    def do_configure_save( self, config, values ):
    
        # -------------------------------------------------------------
        #   Copy parameters in configure window back into the config
        #       and save it
    
        config_data_dict = configDataDict().settings_dict
        for item, dd in config_data_dict.items():
            if not dd[ 'show' ]:
                continue

            if dd[ 'type' ] == 'L':         # Labels not saved in config file
                continue

            val = values[ item ]
            # print( f"item: {item}, val: {val}, dd: {dd}" )

            if dd[ 'type' ] == 'B':
                val = 'True' if val else 'False'

            if dd[ 'section' ] == 'Host':
                config['Host'][ self.hostname ][ item ] = val
            else:
                config[ dd['section'] ][ item ] = val

        self.save_config( config )
        return config
    
    # --------------------------------------------------------------------------
    #   Backup current config file and save config in config file.

    def save_config( self, config, config_file = None ):        # config_file only used when testing fb_utils in __main__.
        if not config_file:                                     # File not given or None
            config_file = Path( self.config_file )

        backup_file = Path( config_file.parent, config_file.name + '.bak' )
        backup_path = str( Path( self.confdir, backup_file ))
        config_path = str( Path( self.confdir, config_file ))

        if Path(config_path).is_file():           # Possibly nothing to backup
            shutil.copyfile( config_path, backup_path )

        config.filename = config_path
        config.write()

    # ====================================================================================
    #   First Launch - move to separate file.
    # ====================================================================================
    #   WRW 23 Feb 2022 - After a frustrating afternoon yesterday trying to figure out the best
    #       structure for initial launch I decided to break out checking from building.
    #       build_tables.py will check and not even try to run if configuration not set up.
    #       This assumes we will definitely need the home config directory. If using MySql that may
    #       not be the case but for now keep it. I'll likely eventually put other files in there, too.
    #   WRW 24 Feb 2022 - Another frustrating day, too tired. Split out home check and build.

    # --------------------------------------------------------------------------
    #   WRW 20-May-2025 - Rewriting first-launch checks and inits to clean up worts.
    #   It appear that some of the worts arose because I was always creating a home
    #   config directory, probably to have a place for the sqlite database. That is
    #   no longer an issue as the database is stored separately. Now a lot cleaner.

    def check_config_directory( self ):
        results = []
        success = True

        if not Path( self.confdir ).is_dir():
            results.append( f"Configuration directory '{self.confdir}' not found" )
            success = False

        return results, success

    # --------------------------------------------------------------------------
    #   WRW 20-May-2025 - Rewriting first-start checks and inits to clean up worts.
    #   Config directory does not exist. Make and populate it.

    def initialize_config_directory( self ):
        s = Store()
        path = Path( self.confdir )

        if path.is_file():
            s.msgCritical( f"""ERROR: A file with the same name as the configuration directory {self.confdir} already exists.<br>
                             Click OK to exit.""" )
            sys.exit(1)

        self.progress.append(   # Note: not conditional on verbose
            f"""<br><b>This appears to be the first time you launched Birdland.</b><br><br>
                Creating your configuration directory:<br><i>{path}</i><br>and initial content.""" )

        path.mkdir()
        self.initialize_config_directory_content( )

    # --------------------------------------------------------------------------
    #   Check for existence of [[Host]] [hostname] section in config file. This called after
    #   config loaded by get_config() so have conf.confdir defined.
    #   Check number of [hostname] sections to see if already initialized at least once.

    def check_hostname_config( self ):
        # s = Store()
        results = []
        success = True

        if not self.hostname in self.config['Host']:
            results.append( f"Hostname {self.hostname} not found in 'Host' section of configuration file" )
            success = False

        return results, success

    # --------------------------------------------------------------------------
    #   Check if sqlite database exists if SQLITE.
    #   Check if can connect to mysql database if MYSQL.

    def check_database( self, database='' ):
        s = Store()
        MYSQL, SQLITE, FULLTEXT = s.driver.values()

        results = []
        success = True

        if SQLITE and database == 'sqlite':
            if not Path( self.userdatadir, self.sqlite_database ).is_file():
                results.append( f"Database file {self.sqlite_database} not found in home user data directory '{self.userdatadir}'" )
                success = False

        if MYSQL and database == 'mysql':
            import MySQLdb
            try:
                conn = MySQLdb.connect( "localhost", self.val( 'database_user' ), self.val( 'database_password' ), self.mysql_database  )

          # except Exception as e:
            except Exception:
                (extype, value, traceback) = sys.exc_info()
                results.append( f"ERROR: Connect to MySql database {self.mysql_database} failed, type: {extype}, value: {value}" )
                success = False
            else:
                conn.close()

        return results, success

    # --------------------------------------------------------------------------
    #   WRW 1-Apr-2025 - Check to be sure all the expected directories in user data are there.
    #       Don't worry about the contents.

    def check_user_data_dir( self ):
        s = Store()

        results = []

        user_dir = self.userdatadir

        for dir in s.Const.Bundled_Directories:
            path = Path( user_dir, dir )
            if not path.is_dir():
                results.append( f"check_user_data_dir(): path {path} not found" )
                return results, False

        return results, True

    # --------------------------------------------------------------------------
    #   WRW 6 Mar 2022 - Make [[Host]] [hostname] section for current hostname from ProtoHostnameSection.
    #   Now doing it in all initialization cases.
    #   Motivated by circumstance when Birdland run and config initalized
    #       on one machine in a shared confdir and then run on another machine
    #       with with the same shared confdir. Need a different [hostname] section
    #       for each new machine.

    def initialize_hostname_config( self ):

        if len( self.config['Host'].keys() ) == 1:
            first_config = True
        else:
            first_config = False
            prior_hosts = ', '.join( self.config['Host'].keys()[1:] )

        proto_config =   self.config[ 'Host' ][ 'ProtoHostnameSection' ]
        proto_comments = self.config[ 'Host' ][ 'ProtoHostnameSection' ].comments

        self.config[ 'Host' ][ self.hostname ] = { tag : proto_config[ tag ] for tag in proto_config }
        self.config[ 'Host' ][ self.hostname ].comments = { tag : proto_comments[ tag ] for tag in proto_comments }

        # ----------------------------------------
        #   /// RESUME OK - Cosmetics, add couple of blank lines in config file.
        #   Trying to add a couple of blank lines above the hostname section but this makes save_config() crap out.
        #       self.config[ 'Host' ].comments = {
        #           self.hostname : [ '', '' ],
        #       }
        # ----------------------------------------

        self.save_config( self.config )

        t = ''

        if not first_config:
            t = f"""\nThis appears to be the first time you launched Birdland on
                    {self.hostname} using a shared configuration directory that had 
                    been previously initialized on {prior_hosts}.
                """

        #   Please enter configuration details for this host with:<br><i>File->Settings</i>.

        t += f"""Adding a host-specific section for your host <i>{self.hostname}</i> to your configuration file: <i>{self.config_file}</i>
            """
        self.progress.append( '' )
        self.progress.append( t )       # Note: not conditional on verbose

    # ----------------------------------------------------------------------------
    #   Load the prototype config file from resources.

    def load_text_file_from_qrc( self, qrc_path):
        s = Store()
        qfile = QFile(qrc_path)
        if not qfile.open(QFile.ReadOnly | QFile.Text):
            s.msgCritical( f"Failed to open item from resource: {qrc_path}")
            sys.exit(1)

        stream = QTextStream(qfile)
        contents = stream.readAll()
        qfile.close()

        return ConfigObj(StringIO(contents))

    # ----------------------------------------------------------------------------

    def copy_qrc_file(self, qrc_path, output_path):
        file = QFile(qrc_path)
        if not file.open(QFile.ReadOnly):
            print( f"ERROR-DEV Open {qrc_path} failed")
            sys.exit(1)
    
        with open(output_path, "wb") as out:
            out.write(file.readAll().data())  # readAll() returns QByteArray
    
        file.close()

    # ----------------------------------------------------------------------------
    #   WRW 7 Mar 2022 - In a pathological case some files were missing. Let's catch
    #       them and report with a sensible error message.
    #       Example canonical2file and icons are not checked.

    def check_confdir_content( self ):
        s = Store()
        results = []
        success = True

        path = Path( self.confdir, self.config_file )
        if not path.is_file():                                                                                   
            results.append( f"Config file {path} not found" )
            success = False

        path = Path( self.confdir, self.setlist_file ).expanduser()
        if not path.is_file():
            results.append( f"Setlist file {path} not found" )
            success = False
               
        path = Path( self.confdir, f"{self.hostname}-{self.audiofile_index_file}" ).expanduser()
        if not path.is_file():
            results.append( f"Audio file index {path} not found" )
            success = False

        for file in self.val( 'canonical2file' ):
            path = Path( self.confdir, file )
            if not path.is_file():
                results.append( f"Canonical2file {path} not found" )
                success = False

        return results, success

    # --------------------------------------------------------------------------
    #   Copy or initialize several files into configuration directory.
    #       birdland_qt.conf           - based on proto config file
    #       empty setlist
    #       empty audio index
    #       empty canonical2file
    #       example canonical2file  - copied from package directory
    #       icon files - copied from resources file, needed for .desktop file.

    def initialize_config_directory_content( self ):
        s = Store()
        confdir = self.confdir

        self.progress.append( '' )      # Not conditional on verbose

        # ----------------------------------------------------------
        #   *** Initialize config file with default settings in prototype file.
        #   WRW 3 Mar 2022 - Now build a new config file from the proto config file.
        #       Originally it was built with a simple copy:
        #           config_file_path.write_text(  Path( default_proto_file_name  ).read_text() )                                

        proto_file = self.load_text_file_from_qrc( s.Const.confPrototype )
        config_file_path = Path( confdir, self.config_file )
        if s.verbose:
            self.progress.append( f"Initializing Configuration directory: {config_file_path}" )

        if not config_file_path.is_file():      # A safety check. Don't creat one if already exists. Don't want to overwrite.
            proto_file.filename = config_file_path
            proto_file.write()
            if s.verbose:
                self.progress.append( f"Creating initial configuration file: {config_file_path}" )
        else:
            if s.verbose:
                self.progress.append( f"Preserving existing configuration file: {config_file_path}" )

        # ----------------------------------------------------------
        #   *** Initialize setlist

        setlist_path = Path( confdir, self.setlist_file ).expanduser()

        if not setlist_path.is_file():
            t = { 'current' : 'Default', 
                  'setlist' :  { 'Default' : [] },
                }

            setlist_path.write_text( json.dumps( t, indent=2 ) )
            if s.verbose:
                self.progress.append( f"Created empty setlist file: {setlist_path}" )
        else:
            if s.verbose:
                self.progress.append( f"Preserving existing setlist file: {setlist_path}" )
               
        # ----------------------------------------------------------
        #   *** Initialize audio index.

        audio_index_path = Path( confdir, f"{self.hostname}-{self.audiofile_index_file}" ).expanduser()

        if not audio_index_path.is_file():
            t = { 'audio_files' : [] }
            json_text = json.dumps( t, indent=2 )
            with gzip.open( audio_index_path, 'wt', encoding='utf-8'  ) as ofd:  # /// WRW 23-Mar-2025 ENCODING
                ofd.write( json_text )
            if s.verbose:
                self.progress.append( f"Created empty audio index file: {audio_index_path}" )
        else:
            if s.verbose:
                self.progress.append( f"Preserving existing audio index file: {audio_index_path}" )

        # ----------------------------------------------------------
        #   *** Initialize canonical2file for user to populate.

        canonical2file_path = Path( confdir, self.canonical2file )
        if not canonical2file_path.is_file():
            Path.touch( canonical2file_path )
            if s.verbose:
                self.progress.append( f"Created empty canonical2file file: {canonical2file_path}" )
        else:
            if s.verbose:
                self.progress.append( f"Preserving existing canonical2file file: {canonical2file_path}" )

        # ----------------------------------------------------------
        #   *** Copy example canonical2file for user.
        #   This is the only place where we copy data from the package data directory to the config directory
        #       Elsewhere we copy it to the user data directory.

        dest = Path( confdir, self.example_canonical2file )
        src =  Path( self.package_data_directory, self.canonical_dir, self.example_canonical2file )

        if not dest.is_file():
            dest.write_text( src.read_text() )
            if s.verbose:
                self.progress.append( f"Copied example canonical2file file from: {src} to your config directory: {dest}" )
        else:
            if s.verbose:
                self.progress.append( f"Preserving existing example canonical2file file: {dest}" )

        # ----------------------------------------------------------
        #   *** Copy icon file.

        src =  s.Const.BL_Icon_ICO
        dest = Path( confdir, s.Const.Icon_File_ICO )
        self.copy_qrc_file( src, dest )
        if s.verbose:
            self.progress.append( f"Copied application icon: {src} To: {dest}" )

        src =  s.Const.BL_Icon_PNG
        dest = Path( confdir, s.Const.Icon_File_PNG )
        self.copy_qrc_file( src, dest )
        if s.verbose:
            self.progress.append( f"Copied application icon: {src} To: {dest}" )

    # ----------------------------------------------------------------------------
    #   WRW 1-Apr-2025 - These two functions are callable from the Development menu
    #       for testing to avoid going through a complete coldstart sequence.

    #   Copy data that is bundled in bundle package
    #       or adjacent to program directory to the AppData folder.
    #       Want consistency in location for bundled and non-bundled installations.
    #   For now just overwrite if already exists. /// RESUME Later check times?
    #   shutil.copytree("source_dir", "destination_dir", dirs_exist_ok=True)
    #   A minor pain, doesn't copy tree directly but contents of tree. Resolve by adding dst_path.

    def initialize_user_data_dir( self ):
        s = Store()
        src = self.package_data_directory 
        dst = self.userdatadir

        # self.progress.append( '' )
        self.progress.append( f"""Creating your data directory:<br><i>{dst}</i><br>and initial content""" )      # Not conditional on verbose

        for dir in s.Const.Bundled_Directories:
            src_path = Path( src, dir )
            dst_path = Path( dst, dir )
            shutil.copytree( src_path, dst_path,
                             dirs_exist_ok=True,
                             ignore=shutil.ignore_patterns(",*", ".e*") )

            if s.verbose:
                self.progress.append( f"Copied: {src_path} To: directory: {dst}" )

    # ------------------------------------
    #   WRW 25-May-2025 - Add one more step for initialization so don't have to ship
    #       contents of Music-Index. Test for existence of Music-Index.
    #   /// RESUME - check for a few files in dir?

    def check_music_index_dir( self ):
        s = Store()
        results = []

        path = Path( s.conf.val( "music_index_dir" ) )

        if not path.is_dir():
            results.append( f"Music index directory {path} not found" )
            return results, False

        return results, True

    # ----------------------------------------------------------------------------
    #   WRW 15-May-2025 - A curious situation arose. This is running build_tables.py
    #   earlier than before, in particular before check_database(). build_tables.py
    #   is connecting to the database even though it is not needed for --convert_raw,
    #   thus creating an empty database when then causes check_database() to succeed
    #   and the database not to be built. Changed build_tables.py to not init DB
    #   for options where is is not needed.
    #   WRW 21-May-2025 - I had what appeared to be an error here,
    #       path = Path( self.userdatadir, s.conf.val( "music_index_dir" ) )
    #   i.e. including userdatadir twice as s.conf.val already added it for
    #   music_index_dir, which has an 'i' flag. Turns out that pathlib ignores
    #   first argument if second argument is absolute, i.e., starts with slash.


    def initialize_music_index_dir( self ):
        s = Store()
        path = Path( s.conf.val( "music_index_dir" ) )

        text = []
        text.append( f"""The music index directory <i>{path}</i> does not exist.
                            It will be created and populated with data from the raw indexes
                            delivered with with Birdland.
                            This will take several seconds to a minute or so.<br><br>
                            You can repeat this process at any time
                            by goint to <i>Index Management -> Process Raw Index Sources</i>.
                            You must do this followed by <i>Database->Rebuild All Tables</i> if you change the raw index data. <br>""" )

        text.append( """Click OK to continue.""" )
        s.msgInfo( '<br>'.join( text ) )

        # -----------------------------------------------
        def music_index_doneCallback( popup, rcode, qstatus ):
            self.rcode = rcode
            if rcode:
                popup.append( f"\nMusic-Index build failed\n  { ' '.join( popup.command )}\n\nReturned exit code: {rcode}\n" )
            else:          
                popup.append( "\nMusic-Index build completed successfully.\n" )
                popup.append( "Press Close to continue with startup.\n" )

        # -----------------------------------------------

        path = Path( s.conf.val( "music_index_dir" ) )

        if not path.is_dir():       # Already checked above, do it again in case dir exists but contents are bogus
            path.mkdir()

        if s.verbose:
            self.progress.append( f"Creating Music-Index directory: {path}" )
            self.progress.append( f"Converting raw indexes to Music-Index directory" )

        if s.Const.Frozen:
            command = [ 'build_tables', '--convert_raw', '-c', str( self.confdir ), '-u', str( self.userdatadir ) ]
        else:
            command = [ './build_tables.py', '--convert_raw', '-c', str( self.confdir ), '-u', str( self.userdatadir ) ]

        s.popup = runExtCommandToPopup( music_index_doneCallback, s.python, command )
        s.popup.exec()
        return self.rcode

    # ----------------------------------------------------------------------------
    #   Show accumulated progress as a Info popup.
    #   WRW 15-May-2025 - It looks like everything added conditional on s.verbose is pretty much useless.
    #   The rest is not, however. I believe I added this facility to accumulate several messages for
    #   one popup and not pester the user with several popups.

    def report_progress( self ):
        s = Store()
        if self.progress:       # WRW 21-May-2025 - don't pester user if nothing to show.
            self.progress.append( f"""<br>Click OK to continue.""" )

            txt = '<br>'.join( self.progress )        # Make string out of list of strings
            s.msgInfo( txt )

            self.progress = []          # Clear progress after report it.

    # ----------------------------------------------------------------------------
    #   This, too, pulled out of get_config(). Called only from birdland.py, never from build-tables.py

    def initialize_database( self, database ):
        s = Store()
        MYSQL, SQLITE, FULLTEXT = s.driver.values()

        text = []

        text.append( """When Birdland launches go to <i>File->Settings</i> to configure the location
                        of your music files (fake books), audio files, and midi files folders:<br>
                        <i>Root of music files</i>, <i>Folders containing music files</i>, etc.<br>
                     """ )


        text.append( """Then configure the subset of the music files folders from above
                        that you want to make
                        available for <i>Canonical->File</i> editing. This is probably the folder
                        containing your fake books:<br>
                        <i>Folders containing music files permitting Canonical->File editing</i>.<br>
                     """ )


        text.append( """Then select the <i>Edit Canonical->File</i> tab and tell Birdland the location
                        of each of your music files in the folders you configured above,
                        See the <i>Birdland-Qt Quick-Start Guide</i> for details.<br>
                     """ )

        text.append( """Then go to <i>Database->Rebuild All Tables</i> to add your files to the database.<br>""" )

        # -------------------------------------------------------------------

        if SQLITE and database == 'sqlite':
            dbpath = Path( self.userdatadir, self.sqlite_database )

            text.append( f"""The database file <i>{dbpath}</i> does not exist.
                            It will be created with the music index data previously built from the raw index
                            data delivered with Birdland and YouTube index data.
                            This will take several seconds to a minute or so.<br>""" )

        if MYSQL and database == 'mysql':
            db = self.mysql_database

            text.append( f"""The database {db}                       
                            will be built with the music index data previously built from the raw index
                            data delivered with Birdland and YouTube index data.
                            This will take several seconds to a minute or so.<br>""" )

        # -------------------------------------------------------------------

        text.append( """Click OK to continue.""" )

        s.msgInfo( '<br>'.join( text ) )
        # self.do_popup( '\n'.join( text ) )

        rcode = self.build_database( database )

        if rcode:
            sys.exit(1)

    # --------------------------------------------------------------------------
    #   WRW 19 Feb 2022 - Initialize the database with build_tables.py. Has database option for
    #   mysql vs. sqlite.

    #   doneCallback() called by finished code in runExtCommandToPopup().
    #       popup is the text window receiving command output.

    def doneCallback( self, popup, rcode, qstatus ):
        self.rcode = rcode
        if rcode:
            db_file = Path( self.userdatadir, self.sqlite_database )
            if os.path.exists( db_file ):
                os.remove(db_file)

            popup.append( f"\nDatabase build failed:\n    { ' '.join( popup.command )}\n\nReturned exit code: {rcode}\n" )
            popup.append( "Database deleted.\n\n" )
            popup.append( "Press Close to exit." )

        else:
            popup.append( "\nDatabase build completed successfully.\n" )
            popup.append( "Press Close to launch Birdland with default configuration file.\n" )
            popup.append( "Then go to File->Settings to configure location of music, audio, and midi files." )

    def build_database( self, database ):
        s = Store()

        if s.Const.Frozen:
            command = [ 'build_tables', '--all', '-c', str( self.confdir ), '-u', str( self.userdatadir ), '-d', database ]
        else:
            command = [ './build_tables.py', '--all', '-c', str( self.confdir ), '-u', str( self.userdatadir ), '-d', database ]

        s.popup = runExtCommandToPopup( self.doneCallback, s.python, command )
        s.popup.exec()

        return self.rcode

    # ----------------------------------------------------------------------------
    #   25 Feb 2022 - This applies only to MySql. Already filtered before calling.
    #   Get user and password from user if not already in config file.
    #   Set temporarily internal but not in config file?

    def get_user_and_password( self ):
        s = Store()

        text = []

        text.append( f"""
        You have launched Birdland with the <i>-d mysql</i> option to use MySql database
        instead of the default Sqlite database.<br><br>

        If you have not already done so
        please create the {self.mysql_database} database and a user, set a password for the user, and grant ALL
        privileges to the user.
        You have to do the external to Birdland before you can use a MySql database within Birdland.<br><br>

        After you click OK the configuration window will appear.
        Please enter <i>Database User</i> and <i>Database Password</i> fields with the
        credentials you gave when you created the {self.mysql_database} database.
        You can change them later in the <i>File->Settings</i> menu.
        You can also enter the locations of your media files and other parameters
        now or later through the <i>File->Settings</i> menu.<br>

        """ )

        text.append( """Click OK to continue.""" )
        s.msgInfo( '<br>'.join( text ) )

        # if( not self.v.database_user or self.v.database_user == '***' and
        #     not self.v.database_password or self.v.database_password == '***' ):
        #     res = self.do_configure( first=True, text=text, confdir=confdir )
        #     return res

        if( not self.val( 'database_user' ) or self.val( 'database_user' ) == '***' and
            not self.val( 'database_password' ) or self.val( 'database_password' ) == '***' ):

            res = self.do_configure( )        # *** Show config window.

            #   WRW 28-Mar-2025 - suspect this is needed.
            #   WRW 21-May-2025 - This is definitely needed here so have credentials for connection in birdland_qt.py

            self.set_class_variables( )     # Update conf.v data and source <--> src mapping. 

            return res

        return True

    # ----------------------------------------------------------------------------
    #   get_appearances() used to determine content of Appearances menu, see 'aux5'
    #   Note that 'Default-Dark' is in palettes.
    #   WRW 17-Apr-2025 - Restrict appearances to few that look good and don't interact without reboot.

    def get_appearances( self ):
        s = Store()
        return sorted( s.Const.Appearances )

    # ------------------------------------------------------

    def read_csv_from_qrc( self, resource_path, col_names):
        file = QFile(resource_path)
        if not file.open(QFile.ReadOnly | QFile.Text):
            raise IOError(f"Cannot open resource file: {resource_path}")
    
        # Read file content and decode as UTF-8
        text = bytes(file.readAll()).decode("utf-8")
    
        # Wrap it as a file-like object
        text_io = io.StringIO(text)
    
        # Use csv.DictReader normally
        reader = csv.DictReader(text_io, fieldnames=col_names)
      # header = next(reader)  # Skip or process header as needed. No header on the reduced palettes.csv file.
    
        return reader

    # ------------------------------------------------------

    def create_palette( self, theme_row ):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(theme_row["Window"]))
        palette.setColor(QPalette.WindowText, QColor(theme_row["WindowText"]))
        palette.setColor(QPalette.Base, QColor(theme_row["Base"]))
        palette.setColor(QPalette.AlternateBase, QColor(theme_row["AlternateBase"]))
        palette.setColor(QPalette.ToolTipBase, QColor(theme_row["ToolTipBase"]))
        palette.setColor(QPalette.ToolTipText, QColor(theme_row["ToolTipText"]))
        palette.setColor(QPalette.Text, QColor(theme_row["Text"]))
        palette.setColor(QPalette.Button, QColor(theme_row["Button"]))
        palette.setColor(QPalette.ButtonText, QColor(theme_row["ButtonText"]))
        palette.setColor(QPalette.BrightText, QColor(theme_row["BrightText"]))
        palette.setColor(QPalette.Highlight, QColor(theme_row["Highlight"]))
        palette.setColor(QPalette.HighlightedText, QColor(theme_row["HighlightedText"]))
        return palette

    # ----------------------------------------------------------------------------

    def setPalette( self, palette ):
        s = Store()
        theme_row = self.palettes[ palette ]
        palette = self.create_palette( theme_row )
        s.app.setPalette( palette )

        if False:
            for w in s.app.topLevelWidgets():               # Do full update when palette changes
                self.apply_palette_recursive(w, palette)
                w.update()

            for w in s.app.topLevelWidgets():               # /// RESUME TESTING
                self.apply_palette_recursive(w, palette)
                w.repaint()

    # ----------------------------------------------------------------------------

    def apply_palette_recursive(self, widget, palette):
        widget.setPalette(palette)
        for child in widget.findChildren(QWidget):
            child.setPalette(palette)

    # ----------------------------------------------------------------------------
    #   WRW 11-Apr-2025 - It turns out that I can use both styles and themes.
    #   WRW 11-Apr-2025 - Major restructure into three, orthogonal items: style, theme, palette
    #       Previously were ambiguously somewhat combined. I combined theme and palette into
    #       an item I call appearance.
    #   WRW 5-May-2025 - Changed 'appearance' back to 'theme" in configuration, more common term.
    #       Keep 'appearance' in code for now.

    def setStyle( self, style ):
        s = Store()
        s.app.setOverrideCursor(QCursor(Qt.WaitCursor))         # This can take a few seconds, show waiting
        s.app.setStyle( QStyleFactory.create( style ) )
        s.app.restoreOverrideCursor()

    # ---------------------------------------------------
    #   WRW 12-Apr-2025 - 'Appearance' as used here is a combination of both themes and palettes
    #   as they look the same to the user but are implemented differently.
    #   Stylesheet with setStyle(), palettes with setPalette() but the two are not independent.
    #   Stylesheets already contain color information so it is pointless to set a palette after a stylesheet.
    #   Set null palette (really system palette):  QApplication.style().standardPalette()

    #   WRW 17-Apr-2025 - this has become a big nuisance, trying to give more flexibility than needed,
    #   with styles and palettes and themes that interact. Back of to just a few that work well.
    #   Remove setPalette() from most of the appearances, appears to do nothing. It would be great
    #   to explore tweaking QDark or QLight to add some more color but looks like a huge time sink. Not now.
    #   Appearances in 'aux5' menu now limited to s.Const.Appearances. Keep others here for future exploration.

    #   WRW 25-Apr-2025 - Migrate to an approach based on jinja templates, no more palettes, keep QDark and QLight
    #   from qdarkstyle. NOTE: the word 'Dark' or 'Light' in the appearance name is used to select the
    #   icon color. Yes, a kludge, but I can live with it lieu of a appearance table with additional data.
    #   Note also that the appearances shown in the config combo box is defined in bl_constants.py and
    #   must agree with appearances below.

    #   WRW 1-May-2025 - Remove updateSvgIcons from here. updateIcons always called after setAppearance, redundant.

    def setAppearance( self, appearance ):
        s = Store()
        s.app.setOverrideCursor(QCursor(Qt.WaitCursor))         # This can take a few seconds, show waiting
        self.currentAppearance = appearance

        if appearance in s.Const.Appearances_BL:
            stylesheet = getStyle( appearance )
            s.app.setStyleSheet( stylesheet )
            # icon_color = getOneStyle( appearance, 'qwidget_text' )
            # s.fb.updateSvgIcons( QColor( icon_color ) )

        elif appearance in s.Const.Appearances_DS:
            match appearance:
                case 'QDark':
                    dark_stylesheet = qdarkstyle.load_stylesheet( qt_api='pyside6', palette=qdarkstyle.DarkPalette )
                    my_stylesheet = getStyleGeometry()       # Just dimensional styles
                    stylesheet = dark_stylesheet + my_stylesheet
                    s.app.setStyleSheet( stylesheet )
                    # icon_color = getOneStyle( 'Dark', 'qwidget_text' )
                    # s.fb.updateSvgIcons( QColor( icon_color ))

                case 'QLight':
                    dark_stylesheet = qdarkstyle.load_stylesheet( qt_api='pyside6', palette=qdarkstyle.LightPalette )
                    my_stylesheet = getStyleGeometry()       # Just dimensional styles
                    stylesheet = dark_stylesheet + my_stylesheet
                    s.app.setStyleSheet( stylesheet )
                    # icon_color = getOneStyle( 'Light', 'qwidget_text' )
                    # s.fb.updateSvgIcons( QColor( icon_color ))

                case _:
                    print( f"ERROR-DEV: Appearance '{appearance}' not recognized" )
                    stylesheet = getStyle( 'Dark' )
                    s.app.setStyleSheet( stylesheet )
                    # icon_color = getOneStyle( 'Dark', 'qwidget_text' )
                    # s.fb.updateSvgIcons( QColor( icon_color ))

        else:
            print( f"ERROR-DEV: Appearance '{appearance}' not found in lists" )
            stylesheet = getStyle( 'Dark' )
            s.app.setStyleSheet( stylesheet )

        # ------------------------------------------------

        s.app.restoreOverrideCursor()

    # ----------------------------------------------------------------------------
    def dump_palette( self, palette: QPalette, label="Palette"):
        print(f"\n{label}:")
    
        # Iterate using QPalette.ColorRole enums explicitly
        roles = [
            QPalette.Window,
            QPalette.WindowText,
            QPalette.Base,
            QPalette.AlternateBase,
            QPalette.ToolTipBase,
            QPalette.ToolTipText,
            QPalette.Text,
            QPalette.Button,
            QPalette.ButtonText,
            QPalette.BrightText,
            QPalette.Highlight,
            QPalette.HighlightedText,
            QPalette.Link,
            QPalette.LinkVisited,
            QPalette.PlaceholderText,
        ]
    
        for role in roles:
            role_name = role.name if hasattr(role, 'name') else str(role)
            color = palette.color(QPalette.Active, role)
            print(f"{role_name:<20} {color.name()}")
    
        print("\nInactive differences:")
        for role in roles:
            a = palette.color(QPalette.Active, role)
            i = palette.color(QPalette.Inactive, role)
            if a != i:
                role_name = role.name if hasattr(role, 'name') else str(role)
                print(f"{role_name:<20} Active: {a.name()}  Inactive: {i.name()}")
    
        print("\nDisabled differences:")
        for role in roles:
            a = palette.color(QPalette.Active, role)
            d = palette.color(QPalette.Disabled, role)
            if a != d:
                role_name = role.name if hasattr(role, 'name') else str(role)
                print(f"{role_name:<20} Active: {a.name()}  Disabled: {d.name()}")
    
    # ----------------------------------------------------------------------------
    #   Set the color of the SVG icons by 'qwidget_text' theme parameter.
    #   WRW 27-Apr-2025 - QGroupBox color now styled normally, not with custom property.
    #       No longer a little bit hacky at all. Now just update 'pdf' group icons directly
    #       Signal AudioPlayer to update 'audio' group icons. Likewise PDF_Viewer
    
    def updateIcons( self, appearance ):
        s = Store()

        #   Translate darkstyle QDark and QLight to 'Dark' and 'Light' appearance

        if appearance in s.Const.Appearances_DS:
            match appearance:
                case 'QDark':
                    appearance = 'Dark'

                case 'QLight':
                    appearance = 'Light'

                case _:
                    appearance = 'Dark'
    
        s.sigman.emit( "sig_appearance", appearance )       # Tell AudioPlayer to update player icons.

# ----------------------------------------------------------------------------

def do_main():
    from bl_unit_test import UT
    s = UT()

    config = s.conf.config

    # folders = [ x for x in config['System']['Music_File_Folders'].split( '\n' ) if x ]
    # for folder in folders:
    #     print( folder )

    # print( config['System'][ 'index_sources'] )
    # sources = [ x for x in config['System']['index_sources'].split( '\n' ) if x ]
    
    for source in s.conf.get_sources():
        print( source )
        print( "  ", config['Source'][source]['folder'] )
        print( "  ", config['Source'][source]['command'] )
        print()

    # for folder in folders:
    #     print( folder )

    # --------------------------------------------------------------
    #   The new reference style is used throughout birdland.py and other modules now.

    print( "-----------------------" )
    print( 'Example of s.conf.val( item )')
    for item in sorted( ['select_limit', 'music_file_root', 'audio_file_root',
                 'external_audio_player', 'music_file_folders', 'canonical2file', 'music_index_dir',
                 'c2f_editable_map', 'c2f_editable_music_folders', 'audiofile_index', 'documentation_dir',
                ]):

        print( f"{item:>30}: {s.conf.val( item )}" )

    print( "Source Priority:" )
    priorities = s.conf.val( 'source_priority' )
    print( ', '.join(priorities) )

    config_file = Path( '/tmp/junk-bluebird.conf' )
    s.conf.save_config( config, config_file )

    print( '' )
    print( 'Example of source-specific values:')
    for (item, src ) in [[ 'src', 'Sher'], ['folder', 'Skrivarna'], ['command', 'MikelNelson'], 
                         [ 'sheetoffsets', 'Buffalo'], ['local2canon', 'User' ], [ 'localbooknames', 'ExtractedIndex' ]]:
        print( f"{src:>20}: {item:15}: {s.conf.val( item, src )}" )

# --------------------------------------------------------------

if __name__ == '__main__':

    do_main()

# --------------------------------------------------------------
