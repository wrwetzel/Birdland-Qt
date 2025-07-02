#!/usr/bin/python
# ------------------------------------------------------------------------------------
#   WRW 27-Feb-2025 - Media interface library.
#   Originally in fb_utils.py, more recently in bl_actions.py
#   Major refactoring - move some code out of bl_actions.py and all out of fb_metadata.py
#       and removed fb_metadata.py completely.

#   /// RESUME - clean up a little, remove redundant code, look to move duplicated code
#       into functions.

#   /// RESUME - 7-Mar-2025 - Commented out initial call to page_change_*() in each of
#       the showFt, showFi, and showFs functions to suppress duplicate executions of
#       page_change_*(). At first look it appears OK but analyze why I had the initial
#       calls in the first place. Restored initial call but moved emit of "sig_pdf_page_changed"
#       inside the 'if send_signal' block. For reasons I don't remember I wanted
#       an explicit initial call.

#   WRW 20-Mar-2025 - Change showFt, showFs, showFi to use fixed arguments instead of
#       variable and named for dealing with invocation with signals.

# ------------------------------------------------------------------------------------

import os
import subprocess
import shutil
import io
from pathlib import Path
import tempfile
from collections import namedtuple
import mido

from PySide6.QtCore import Qt, QObject, Signal, Slot, QFileInfo, QFile
from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextBrowser, QPushButton

from Store import Store
from bl_constants import MT
import fb_search
import bl_resources_rc

# ------------------------------------------------------------------------------------
#   WRW 26-Feb-2025 After a lot of thrashing about yesterday in a bit of a fog
#       I'm implementing page_changed here, in the same file where the pdf page
#       was initially loaded.
    
#   WRW 26-Feb-2025 - lets encapsulate higher level of PDF display here in
#       with  actions.

#   WRW 27-Feb-2025 - Trying new approach in to eliminate fb_metadata.py.
#       Have separate show() and page_changed() entry points for each mode 
#       defined in 2022 fb_metadata instead of discriminating based on a mode argument.

#           'Fi' - Music File with index data. From Music Index Table.
#           'Ft' - Tutorial / Chordpro file, no index data.
#           'Fs' - Music File, 'src' may be explicitly given in browse combo box. From Music Browser.

#           'Fp' - Obsolete - Music File, possibility of inferring index data. From Music Files Table.          

#   Note that refrese() in PDF_Viewer.py is called before load_pdf() returns and
#   and the page_count is available. Initialize page_count to prevent errors.

# ------------------------------------------------------------------------------------

class PDF( QObject ):
    sig_set_src_offset_visible = Signal( int )

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    # ----------------------------------------------------------

    def __init__( self ):
        if not hasattr( self, '_initialized' ):
            super().__init__()
            self._initialized = True    # Prevent multiple calls to super().__init__(), multiple QObject issue.
            self.page_changed = None
            s = Store()
            self.fileInfo = FileInfo()

            s.sigman.register_signal( "sig_set_src_offset_visible",   self.sig_set_src_offset_visible )

            s.sigman.register_slot( "slot_pdf_page_changed",    self.pdf_page_changed )
            s.sigman.register_slot( "slot_src_offset_changed",  self.src_offset_changed )
            s.sigman.register_slot( "slot_toc_cell_clicked",    self.toc_cell_clicked )
            s.sigman.register_slot( "slot_pdf_changed",         self.slot_pdf_changed )
            s.sigman.register_slot( "slot_showFt",              self.showFt )
            s.sigman.register_slot( "slot_showFs",              self.showFs )
            s.sigman.register_slot( "slot_showFi",              self.showFi )

    # ==============================================================================
    #   'Ft' - Tutorial / Chordpro file, not a music file, no index data.

    @Slot( str, str, str )
    def showFt( self, file=None, alt_file = None, title=None ):
        s = Store()
        self.clear_meta()
        self.page_count = None                           
        self.page_changed = self.page_changed_Ft
        self.file = file
        self.alt_file = alt_file

        # ---------------------------------------------------------
        #   WRW 20-Mar-2025 - moved logic from do_main(), removed stream from showFt() args

        if file.startswith( ':' ):
            qfile = QFile( file )
            qfile.open(QFile.ReadOnly)
            data = qfile.readAll().data()
            qfile.close()
            stream = io.BytesIO( data )
        else:
            stream = None

        # ---------------------------------------------------------

        if alt_file:
            self.update_meta_file( alt_file )       # including filename
        else:
            self.update_meta_file( file )           # including filename

        if title:
            s.sigman.emit( "sig_update_meta_title", title )
        else:
            s.sigman.emit( "sig_update_meta_title", "No title given" )

        if alt_file:
            self.fileInfo.save_filenames( file, alt_file )     # Save file name for page number update
        else:
            self.fileInfo.save_filenames( file, file )

        # ---------------------------------------------------------

        # s.pdf_viewer.load_pdf( stream=stream, file=file, page=0 )                # *** Load generated PDF - Start with first page in pdf file.
        s.sigman.emit( "sig_load_pdf", stream, file, 1 )                # /// PAGE

        # self.page_count = s.pdf_viewer.getPageCount()   # Get page count after load. Now sent with signal
        self.page_changed_Ft( page = 1 )                # Initial display of metadata       # /// PAGE

    # ----------------------------------------------------------

    def page_changed_Ft( self, page=None ):
        s = Store()
        s.sigman.emit( "sig_update_meta_page", f"Page: {page} of {self.page_count}" )        # /// PAGE
        self.proc_sheet( sheet=None, src=None, local=None, canonical=None, file=self.file, page=1, mode='Ft' )

    # ==============================================================================
    #   'Fs' - Music File, From Music Browser and Music File Table.
    #       'src' may be explicitly given in browse combo box.

    #   WRW 1-Mar-2025 - clean up src_offset mess. It is meaningless on first display of file.
    #   src_offset only meaningful when page changes and want to compute the sheet number.
    #   WRW 2-Mar-2025 - Now use showFs for both music browser and music file table.

    def showFs( self, file=None, relpath=None ):
        s = Store()
        self.clear_meta()
        self.page_count = None                           
        self.page_changed = self.page_changed_Fs
        file = str( file )
        self.srcs = []
        self.src = None
        self.local = None
        self.canonical = None
        self.page = 0
        self.relpath = relpath          # WRW 5-Mar-2025 - added for proc_setlist()

        self.update_meta_file( relpath )
        self.fileInfo.save_filenames( file, relpath )

        # -------------------------------------------------------------
        #   Update meta items that are file, not page, specific here.
        #       page-specific in page_changed_Fs().

        self.canonical = s.fb.get_canonical_from_file( relpath )

        if self.canonical:                                                
            s.sigman.emit( "sig_update_meta_canon", self.canonical )
            self.srcs = s.fb.get_srcs_by_canonical( self.canonical )
            if self.srcs:
                s.sigman.emit( 'sig_update_src_offset', self.srcs )
                s.sigman.emit( "sig_set_src_offset_visible", True )
                # s.fileInfo.update_srcs( self.srcs )
                self.src = self.srcs[0]       # Start with first src, user may change it later

                self.local = s.fb.get_local_from_src_canonical( self.src, self.canonical )
                if self.local:
                    s.sigman.emit( "sig_update_meta_local", f"{self.local} - {self.src}" )
                    toc = s.fb.get_table_of_contents( self.src, self.local )
                    s.sigman.emit( "sig_update_meta_toc", toc )

            else:
                s.sigman.emit( 'sig_update_src_offset', [] )

        else:
            s.sigman.emit( 'sig_update_src_offset', [] )

        # -------------------------------------------------------------
        #   WRW 1-Mar-2025 - try moving load_pdf() to end so trigger of page_changed_Fs() comes after 
        #   all initialization and don't call page_changed_Fs() explicitely here.
        #   WRW 2-Mar-2025 - No. Suppress signal from load_pdf() and call page_changed explicitly

        s.sigman.emit( "sig_load_pdf", None, file, 1 )

        # self.page_count = s.pdf_viewer.getPageCount()   # Get page count 'after load. Now sent with signal
        self.page_changed_Fs( page=1 )                  # Initial display of metadata after page_count obtained.

    # ----------------------------------------------------------
    #   The asterisk '*' signifies estimate, i.e., src by priority
    #   Called to update both the page and src_offset

    def page_changed_Fs( self, page=None, src_offset=None ):
        s = Store()

        if page is not None:    # Save page for update for src_offset change
            self.page = page
            s.sigman.emit( "sig_update_meta_page", f"Page: {self.page} of {self.page_count}" )   # /// PAGE

        if src_offset is not None:
            self.src = src_offset
            self.local = s.fb.get_local_from_src_canonical( self.src, self.canonical )

        #   recompute andd redisplay sheet on both page and src change

        if self.src and self.local:
            t = f"* {self.local} - {self.src}"
            s.sigman.emit( "sig_update_meta_local", t )
            sheet = s.fb.get_sheet_from_page( self.page, self.src, self.local )    # /// PAGE
            self.proc_sheet( sheet=sheet, src=self.src, local=self.local, canonical=self.canonical, file=self.relpath, page=self.page, mode='Fs' )
        else:
            self.proc_sheet( sheet=None, src=None, local=None, canonical=None, file=self.relpath, page=self.page, mode='Fs' )

    # ==============================================================================
    #   'Fi' - Music File with index data. From Music Index Table.
    #   WRW 20-Mar-2025 - When converting to signal invocation I didn't want to pass such a large number of args by position
    #       and couldn't pass them by name through signals. Use dict instead
    #   Reminder: data is a named tuple, from bl_tables.py:
    #        data = getDataNew( self, row, self.lheader )
    #   i.e. from the respective tables, named by the table column header.

    # def showFi( self, file=None, title=None, alt_file=None, page=None, sheet=None, canonical=None, local=None, src=None ):

    def showFi( self, file, data ):
        title = data.title              # Variables are residual from named args before switched to signals.
        alt_file = data.file
        page = data.page                # /// PAGE
        sheet = data.sheet   

        canonical = data.canonical   
        local = data.local   
        src = data.src   

        s = Store()
        self.page_changed = self.page_changed_Fi
        self.clear_meta()
        self.src = src
        self.local = local
        self.canonical = canonical      # for setlist
        self.relpath = alt_file         # for setlist

        if alt_file:
            self.update_meta_file( alt_file )                               
        else:
            self.update_meta_file( file )                               

        toc= s.fb.get_table_of_contents( src, local )
        s.sigman.emit( "sig_update_meta_toc", toc )
        s.sigman.emit( "sig_update_meta_canon", canonical )
        s.sigman.emit( "sig_update_meta_local", f"{local} - {src}" )

        self.fileInfo.save_filenames( file, alt_file )

        s.sigman.emit( "sig_load_pdf", None, str(file), int( page ) )      # /// PAGE

        self.page_changed_Fi( page )

    # ----------------------------------------------------------

    def page_changed_Fi( self, page=None ):
        s = Store()

        # if page is not None:    # Save page for update for src_offset change
        #     self.page = page

        self.page = page        # for setlist

        s.sigman.emit( "sig_update_meta_page", f"Page: {self.page} of {self.page_count}" )   # /// PAGE

        if self.src and self.local:
            t = f"{self.local} - {self.src}"
            s.sigman.emit( "sig_update_meta_local", t )

            sheet = s.fb.get_sheet_from_page( self.page, self.src, self.local )      # /// PAGE
            self.proc_sheet( sheet=sheet, src=self.src, local=self.local, canonical=self.canonical, file=self.relpath, page=self.page, mode='Fi' )

        else:
            self.proc_sheet( sheet=None, src=None, local=None, canonical=None, file=self.relpath, page=self.page, mode='Fi' )

    # ==============================================================================
    #   WRW 19-Mar-2025 - We now learn about new pdf page_count via signals to eliminate
    #       the need for s.pdf_viewer.getPageCount().

    @Slot(int)
    def slot_pdf_changed( self, page_count ):
        self.page_count = page_count

    # ----------------------------------------------------------

    @Slot()
    def pdf_page_changed( self, page ):
        s = Store()

        if self.page_changed:
            self.page_changed( page=page )       # Call mode-specific page-changed routine.
        else:
            print( "PROGRAM ERROR: self.page_changed() not defined at pdf_page_changed()" )

    # ----------------------------------------------------------

    @Slot( str )
    def src_offset_changed( self, index ):
        s = Store()
        if self.srcs:
            self.src_offset = self.srcs[ index ]

            if self.page_changed:
                self.page_changed( src_offset=self.src_offset )       # Call mode-specific page-changed routine to update sheet
            else:
                print( "PROGRAM ERROR: self.page_changed() not defined at src_offset_changed()" )

    # ----------------------------------------------------------
    #   WRW 2-Mar-2025 - Moved from bl_actions.py
    #                                                               
    
    @Slot( str, str )
    def toc_cell_clicked( self, title, sheet ):
        s = Store()
        if sheet:
            if self.src and self.local:
                page = s.fb.get_page_from_sheet( sheet, self.src, self.local )
                if page is not None:
                    s.sigman.emit( "sig_change_pdf_page", int( page )-1 )   # -1 to get back to 0-based numbers
                    s.selectTab( MT.Viewer )

    # ----------------------------------------------------------

    def update_meta_file( self, file ):
        s = Store()
        if '/' in file:
            files = file.split('/')
            file1 = '/'.join( files[ 0:-1] ) + '/'
            file2 = files[-1]

        else:
            file1 = file
            file2 = ''

        s.sigman.emit( "sig_update_meta_file", f'{file1}\n{file2}' )

    # ----------------------------------------------------------

    def clear_meta( self ):
        s = Store()
        s.sigman.emit( "sig_update_meta_title", [] )
        s.sigman.emit( "sig_update_meta_file", '' )
        s.sigman.emit( "sig_update_meta_page", '' )
        s.sigman.emit( "sig_update_meta_sheet", '' )
        s.sigman.emit( "sig_update_meta_toc", [] )
        s.sigman.emit( "sig_update_meta_canon", '' )
        s.sigman.emit( "sig_update_meta_local", '' )
        s.sigman.emit( "sig_update_src_offset", [] )
        s.sigman.emit( "sig_set_src_offset_visible", False )

    # ----------------------------------------------------------
    #   WRW 5-Mar-2025 - add code to inform setlist code of
    #   a new item for possible addition to setlist. Terrible
    #   waste 99% of time, better way for setlist to get it
    #   on demand? Not no, will not impact performance.
    #   Was being called twice. Resolved by suppressing initial managed signal in refresh().

    # import traceback    # DIAGNOSTICS - just diagnostics

    def proc_sheet( self, sheet, src, local, canonical, file, page, mode ):
        s = Store()

        if sheet is not None:
            # print( "------------------------------------------")
            # traceback.print_stack()

            s.sigman.emit( "sig_update_meta_sheet", f"Sheet/Title: {sheet}" )
            titles_array = s.fb.get_titles_from_sheet( sheet, src, local )
            titles_text = '\n'.join( titles_array )
            s.sigman.emit( "sig_update_meta_title", titles_text )
            self.update_current_audio( titles_array )
            self.update_current_midi( titles_array )

        else:
            # print( "------------------------------------------")
            # traceback.print_stack()

            s.sigman.emit( "sig_update_meta_sheet", '' )
            s.sigman.emit( "sig_update_meta_title", '' )
            self.update_current_audio( [] )
            self.update_current_midi( [] )
            titles_array = [ "None" ]

        #   WRW 5-Mar-2025 - Notify setlist for potential user 'Add-to-Setlist' action.

        self.proc_setlist( titles=titles_array, canonical=canonical, src=src, local=local, sheet=sheet, file=file, page=page, mode=mode )

    # ----------------------------------------------------------
    #   WRW 5-Mar-2025 - far more here than we are using but keep for compatibility with 
    #       setlist json file from earlier work. 6-Mar-2025 - now using it all

    def proc_setlist( self, titles, canonical, src, local, sheet, page, file, mode ):
        s = Store()

        Data = namedtuple('Data', ['titles', 'canonical', 'src', 'local', 'sheet', 'page', 'file', 'mode' ] )
        data = Data( titles, canonical, src, local, sheet, page, file, mode )
        s.sigman.emit( "sig_setlist_current_data", data )

    # ----------------------------------------------------------
    #   WRW 29 Jan 2022 - New idea - show audio files matching current titles

    def update_current_audio( self, titles_a ):
        s = Store()
        table = []
        for current_title in titles_a:
            for title, artist, file in fb_search.get_audio_from_titles( current_title ):
                table.append( (title, artist, file ) )

        s.sigman.emit( "sig_update_meta_current_audio", table )

    # -------------------------------

    def update_current_midi( self, titles_a ):
        s = Store()
        table = []
        for current_title in titles_a:
            for rpath, file in fb_search.get_midi_from_titles( current_title ):
                table.append( (rpath, file ) )

        s.sigman.emit( "sig_update_meta_current_midi", table )

# ------------------------------------------------------------------------------------

class Audio( QObject ):
    sig_play_audio_starting = Signal()
    sig_play_audio_started = Signal( str )
    sig_play_audio_local = Signal( object )

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    # ----------------------------------------------------------

    def __init__( self ):
        if not hasattr( self, '_initialized' ):
            super().__init__()
            self._initialized = True    # Prevent multiple calls to super().__init__(), multiple QObject issue.
            self.audio_popen = None
            self.fileInfo = FileInfo()

            s = Store()
            s.sigman.register_signal( "sig_play_audio_starting", self.sig_play_audio_starting )
            s.sigman.register_signal( "sig_play_audio_started", self.sig_play_audio_started )
            s.sigman.register_signal( "sig_play_audio_local", self.sig_play_audio_local )
            s.sigman.register_slot( "slot_stop_audio", self.close )
            s.sigman.register_slot( "slot_play_audio", self.play )
            s.sigman.register_slot( "slot_close_audio", self.close )

    # ----------------------------------------------------------

    @Slot( str )
    def play( self, path ):
        s = Store()

        if not Path( path ).is_file():                  # Likely excessive but let's be safe.
            t = f"Can't find audio file '{path}'."
            s.msgWarn( t )
            return

        self.fileInfo.save_filenames( path, path )

        # -----------------------------------------------------------------------

        if not s.conf.val( 'use_external_audio_player' ):
            s.sigman.emit( "sig_play_audio_local", path )
            s.sigman.emit( "sig_play_audio_started", str(path) )

        # -----------------------------------------------------------------------
        else:
            s.sigman.emit( "sig_play_audio_starting" )

            player = s.conf.val( 'external_audio_player' )  # WRW 1-Feb-2025
            options = s.conf.val( 'external_audio_player_options' ) # WRW 9-Apr-2025
            options = list( options.split() )      # Convert optional args to array elements

            if not player:
                t = "No Audio Player given in config file"
                s.msgWarn( t )
                return

            if shutil.which( player ):
                play_cmd = [ player, *options, path ]
                self.audio_popen = subprocess.Popen( play_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL )
                s.sigman.emit( "sig_play_audio_started", f"Audio: {str( path )}" )

            else:
                t = f"Audio Player given in config file '{player}' not found."
                s.msgWarn( t )

    # --------------------------------------------------------------------------

    @Slot()
    def close( self ):
        if self.audio_popen:
            self.audio_popen.kill()
            self.audio_popen = None

# ----------------------------------------------------------------------------

class Midi( QObject ):
    sig_play_midi_starting = Signal()
    sig_play_midi_started = Signal( str )
    sig_midi_to_audio_ext_command_finished = Signal( int, object )

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    # ----------------------------------------------------------
    #   WRW 10-Mar-2025 installed python-pyfluidsynth
    #   Looks promising but could not get working after some effort. Suspend work for now.
    #   /// RESUME Need way to convert midi to audio in a memory buffer, not a file.
    #   WRW 23-May-2025 - I suspect that python-vlc can play midi, a much easier solution.

    def __init__( self ):

        if not hasattr( self, '_initialized' ):
            super().__init__()
            s = Store()

            self.fileInfo = FileInfo()
            self._initialized = True    # Prevent multiple calls to super().__init__(), multiple QObject issue.
            self.midi_popen = None
            self.path = None

            s.sigman.register_signal( "sig_play_midi_starting", self.sig_play_midi_starting )
            s.sigman.register_signal( "sig_play_midi_started", self.sig_play_midi_started )
            s.sigman.register_signal( "sig_midi_to_audio_ext_command_finished", self.sig_midi_to_audio_ext_command_finished )
            s.sigman.register_slot( "slot_stop_midi", self.close )
            s.sigman.register_slot( "slot_midi_to_audio_ext_command_finished", self.midi_to_audio_ext_command_finished )
            s.sigman.register_slot( "slot_play_audio_local_started", self.play_audio_local_started )
            s.sigman.register_slot( "slot_play_midi", self.play )
            s.sigman.register_slot( "slot_close_midi", self.close )

    @Slot( str, str )
    def play( self, path, file ):
        s = Store()

        self.fileInfo.save_filenames( path, file )
        playback = s.Settings( 'midi_playback' )

        # ---------------------------------------------------------
        #   WRW 7-Apr-2025 - Show midi sidecar data in tab 

        sidecar = Path( path )
        sidecar = sidecar.with_name(sidecar.name + ".txt")
        if sidecar.is_file():
            content = sidecar.read_text(encoding="utf-8")      # /// RESUME This really belongs in bl_media.py but OK here.
            s.setTabVisible( MT.Results, True )
            s.selectTab( MT.Results )
            s.sigman.emit( "sig_clear_results" )
            s.sigman.emit( "sig_addto_results", content )

        # ---------------------------------------------------------
        #   WRW 23-May-2025 - Exploring using python-vlc library used for built-in audio
        #       for midi also. If works it will be a big simplification.

        if playback == s.Const.Midi_BI:
            s.sigman.emit( "sig_play_midi_starting" )

            if not Path( path ).is_file():                  # Likely excessive but let's be safe.
                t = f"Can't find midi file '{path}'."
                s.msgWarn( t )
                return                                                            

            soundfont = s.Settings( 'soundfont_file' )
            if not soundfont:
                txt = """A soundfont is required on some platforms for midi playback with the build-in player.
                         You may have to install a soundfont and indicate its location in <i>Soundfont</i> setting.
                         Proceeding without a soundfont. 
                         This message will not be repeated unless <i>Soundfont</i> setting changed.
                      """
                s.msgWarnOnce( 'vlc-sf-reqd', txt )         # 'vlc-sf-reqd' is key that used to reset msgOnce in play_audio_local()

            #   Use 'soundfont_file' if one specified
            # if Path( soundfont ).is_file():                  # Likely excessive but let's be safe.
            #     os.environ["VLC_SOUND_FONT"] = soundfont

            s.sigman.emit( "sig_play_audio_local", path )
            s.sigman.emit( "sig_play_audio_started", str(path) )

        # ---------------------------------------------------------
        elif playback == s.Const.Midi_Tim:
            s.sigman.emit( "sig_play_midi_starting" )

            if not Path( path ).is_file():                  # Likely excessive but let's be safe.
                t = f"Can't find midi file '{path}'."
                s.msgWarn( t )
                return                                                            

            synth = 'timidity'

            if shutil.which( synth ):
                command = [ synth, str( path ) ]
                self.midi_popen = subprocess.Popen( command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL )
                s.sigman.emit( "sig_play_midi_started", f"Midi: {str( path )}" )

            else:
                s.msgWarn( f"Timidity player, {synth}, not found." )

        # ---------------------------------------------------------
        #   Play using fluidsynth external command to convert to audio and
        #   play audio locally using built-in audio player.
        #   /// RESUME - move analogous MIDI -> score conversion code from bl_tables.py to here

        elif playback == s.Const.Midi_FS_BI:
            s.sigman.emit( "sig_play_midi_starting" )

            if not Path( path ).is_file():                  # Likely excessive but let's be safe.
                t = f"Can't find midi file '{path}'."
                # s.conf.do_popup( t )
                s.msgWarn( t )
                return

            soundfont = s.Settings( 'soundfont_file' )
            if not Path( soundfont ).is_file():                  # Likely excessive but let's be safe.
                t = f"Can't find soundfont file '{soundfont}'."
                s.msgWarn( t )
                return

            synth = 'fluidsynth'
            ofile = tempfile.NamedTemporaryFile( suffix='.flac', delete=False, delete_on_close=False ).name

            if shutil.which( synth ):
                command = [ synth, '-ni', soundfont, str( path ), '-F', ofile ]
                s.fb.run_external_command_binary( command, "sig_midi_to_audio_ext_command_finished", aux_data=ofile  )
            else:
                # s.conf.do_popup( f"Midi to Audio conversion program, {synth}, not found." )
                s.msgWarn( f"Midi to Audio conversion program, {synth}, not found."  )

        # ---------------------------------------------------------
        elif playback == s.Const.Midi_FS:
            s.sigman.emit( "sig_play_midi_starting" )

            if not Path( path ).is_file():                  # Likely excessive but let's be safe.
                t = f"Can't find midi file '{path}'."
                s.msgWarn( t )
                return                                                            

            soundfont = s.Settings( 'soundfont_file' )
            if not Path( soundfont ).is_file():                  # Likely excessive but let's be safe.
                t = f"Can't find soundfont file '{soundfont}'."
                s.msgWarn( t )
                return

            synth = 'fluidsynth'

            if shutil.which( synth ):
                command = [ synth, '-ni', soundfont, str( path ) ]
                self.midi_popen = subprocess.Popen( command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL )
                s.sigman.emit( "sig_play_midi_started", f"Midi: {str( path )}" )

            else:
                # s.conf.do_popup( f"FluidSynth player, {synth}, not found." )
                s.msgWarn( f"FluidSynth player, {synth}, not found." )

        # ---------------------------------------------------------
        elif playback == s.Const.Midi_Ext:
            s.sigman.emit( "sig_play_midi_starting" )

            if not Path( path ).is_file():                  # Likely excessive but let's be safe.
                t = f"Can't find midi file '{path}'."
                s.msgWarn( t )
                return

            player = s.conf.val( 'external_midi_player' )
            options = s.conf.val( 'external_midi_player_options' ) # WRW 9-Apr-2025
            options = list( options.split() )      # Convert optional args to array elements

            if not player:
                t = f"No Midi Player given in config file."
                s.msgWarn( t )
                return

            if shutil.which( player ):
                play_cmd = [ player, *options, path ]
                self.midi_popen = subprocess.Popen( play_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL )
                s.sigman.emit( "sig_play_midi_started", f"Midi: {str( path )}" )

            else:
                t = f"Midi Player given in config file '{player}' not found."
                s.msgWarn( t )
                return

        # ---------------------------------------------------------
        #   Play midi using fluidsynth python library, never got working.
        #   /// RESUME - abandoned for now, perhaps later

        elif False and self.NA_UseFluid_Api:
            import fluidsynth
            s.sigman.emit( "sig_play_midi_starting" )
            fs = fluidsynth.Synth()
            # fs.start()

            Selected_Sound_Font = s.Settings( 'soundfont_file' )

            sfid = fs.sfload( Selected_Sound_Font )  # Load a soundfont
            fs.program_select(0, sfid, 0, 0)        # Select program instrument

            # Convert MIDI to raw audio
            # fs.midi_file_play( path )

            audio_buffer = fs.get_samples( 100000 )
            # audio_buffer = audio_buffer.tobytes()
            audio_buffer =  fs.raw_audio_string(audio_buffer)

            # Capture the audio buffer
            # audio_buffer = io.BytesIO()
            # fs.delete()
            s.sigman.emit( "sig_play_audio_local_buffer", audio_buffer )
            s.sigman.emit( "sig_play_midi_started", f"Midi: {str( path )}" )

        else:
            s.msgCritical( f"ERROR-DEV: Midi playback mode '{playback}' not recognized" )
            return

    # -------------------------------------------------------------
    #   /// RESUME build queue of audio files to delete on close or next play started
    #   'data' is [ ofile, stdout, stderr ]      where ofile comes from aux_data argument
    
    @Slot( int, object )
    def midi_to_audio_ext_command_finished( self, rcode, data ):
        s = Store()
        self.path = data[0]                     # from aux_data
        # print( "/// stdout", data[1] )        # very chatty, no reason to show it.
        # print( "/// stderr", data[2] )
        s.sigman.emit( "sig_play_audio_local", self.path )
        s.sigman.emit( "sig_play_audio_started", str(self.path) )
    
    # -------------------------------------------------------------

    @Slot()
    def play_audio_local_started(self):
        if self.path:
            os.remove( self.path )   # Can't delete before play started.
            self.path = None

    # -------------------------------------------------------------
    @Slot()
    def close( self ):
        if self.midi_popen:
            self.midi_popen.kill()
            self.midi_popen = None

# --------------------------------------------------------------------------

class YouTube( QObject ):
    sig_youtube_starting = Signal()
    sig_youtube_shown = Signal( str )

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    # ----------------------------------------------------------

    def __init__( self ):
        if not hasattr( self, '_initialized' ):
            super().__init__()
            self._initialized = True    # Prevent multiple calls to super().__init__(), multiple QObject issue.
            self.youtube_popen = None
            self.fileInfo = FileInfo()
            s = Store()
            s.sigman.register_signal( "sig_youtube_shown", self.sig_youtube_shown )
            s.sigman.register_signal( "sig_youtube_starting", self.sig_youtube_starting )
            s.sigman.register_slot( "slot_stop_youtube", self.close )
            s.sigman.register_slot( "slot_show_youtube", self.show )
            s.sigman.register_slot( "slot_close_youtube", self.close )

    # ----------------------------------------------------------

    def OMIT_open_youtube_file( self, file ):
        s = Store()
        self.stop_audio_file()
        self.close_youtube_file()

        open_cmd = [ 'minitube', file ]
        self.youtube_popen = subprocess.Popen( open_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL )

    # --------------------------------------------------------------------------
    #   WRW 6-Apr-2025 - Problem here because a space in path to viewer on windows.
    #   Conflicts with splitting option to separate command-line option. Use shlex 
    #   instead of split and quote strings that contain spaces. No, add separate options
    #   in config file.

    @Slot( str )
    def show( self, yt_id ):
        s = Store()
        s.sigman.emit( "sig_youtube_starting" )

        self.fileInfo.save_filenames( '', '' )

        url = f"https://www.youtube.com/watch?v={yt_id}"

        viewer = s.conf.val( 'external_youtube_viewer' )
        options = s.conf.val( 'external_youtube_viewer_options' ) # WRW 9-Apr-2025
        options = list( options.split() )      # Convert optional args to array elements

        if not viewer:
            t = "No YouTube Viewer given in config file"
            # s.conf.do_popup( t )
            s.msgWarn( t )
            return                                             

        if shutil.which( viewer ):
            view_cmd = [ viewer, *options, url ]
            self.youtube_popen = subprocess.Popen( view_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL )
            s.sigman.emit( "sig_youtube_shown", f"YouTube: {str( url )}" )

        else:
            t = f"YouTube Viewer given in config file '{viewer}' not found."
            # s.conf.do_popup( t )
            s.msgWarn( t )
            return

    # --------------------------------------------------------------------------

    def close( self ):
        if self.youtube_popen:
            self.youtube_popen.kill()
            self.youtube_popen = None

# --------------------------------------------------------------------------
#   WRW 27 Apr 2022 - This is a bit exploratory, right I'm now not sure the best way to
#       convert a chordpro file to image but the chordpro command seems like a good choice.
#       Another option is to convert all in a batch first and just load one here.
#       After using it briefly it looks pretty good just as is.

class ChordPro( QObject ):
    sig_chordpro_shown = Signal( str )

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    # ----------------------------------------------------------

    def __init__( self ):
        if not hasattr( self, '_initialized' ):
            super().__init__()
            s = Store()
            self.fileInfo = FileInfo()
            self._initialized = True    # Prevent multiple calls to super().__init__(), multiple QObject issue.
            self.chord_popen = None
            s.sigman.register_signal( "sig_chordpro_shown", self.sig_chordpro_shown )
            s.sigman.register_slot( "slot_show_chord", self.show )
            s.sigman.register_slot( "slot_close_chord", self.close )

    # ----------------------------------------------------------

    @Slot( str, object )
    def show( self, path, callback ):
        s = Store()

        if not Path( path ).is_file():                  # Likely excessive but let's be safe.
            t = f"Can't find chordpro file '{path}'."
            # s.conf.do_popup( t )
            s.msgWarn( t )
            return

        chordpro = s.conf.val( 'chordpro_program' )
        if not chordpro:
            chordpro = 'chordpro'   # NOTE Hard-coded OK on linux and windows, have to give path on MacOS via option.

        tfile = tempfile.mkstemp( suffix='.pdf' )[1]           # Temp pdf file for chordpro output

        self.fileInfo.save_filenames( path, path )

        if shutil.which( chordpro ):
            # chordpro_cmd = [ chordpro, '-o', tfile, path.as_posix() ]      # Must be in path.
            chordpro_cmd = [ chordpro, '-o', tfile, path ]      # Must be in path.
            self.chord_popen = subprocess.Popen( chordpro_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL )
            self.chord_popen.wait()      # Wait till chordpro done and have pdf file.
            callback( tfile )       # Call back to birdland.py so don't have to have pdf and metaclasses here just for this.
            # os.remove( tfile )
            Path( tfile ).unlink(missing_ok=True)   # WRW 4-Mar-2025 - Porting to Windows
            s.sigman.emit( "sig_chordpro_shown", f"ChordPro: {str( path )}" )

        else:
            t = f"ChordPro command '{chordpro}' not found."
            # s.conf.do_popup( t )
            s.msgWarn( t )
            return

    # ----------------------------------------------------------

    def close( self ):
        if self.chord_popen:
            self.chord_popen.kill()
        self.chord_popen = None

# --------------------------------------------------------------------------

class JJazzLab( QObject ):
    sig_jjazzlab_shown = Signal( str )

    def __init__(self):
        super().__init__()
        s = Store()
        self.fileInfo = FileInfo()
        s.sigman.register_signal( "sig_jjazzlab_shown", self.sig_jjazzlab_shown )
        s.sigman.register_slot( "slot_show_jjazz", self.show )
        s.sigman.register_slot( "slot_close_jjazz", self.close )
        self.jjazz_popen = None

    def show( self, path ):
        s = Store()

        self.close()
    
        if not Path( path ).is_file():                  # Likely excessive but let's be safe.
            t = f"Can't find jjazz file '{path}'."
            # s.conf.do_popup( t )
            s.msgWarn( t )
            return
    
        self.fileInfo.save_filenames( path, path )

        jjazzlab = 'jjazzlab'                           # Must be in path.      # /// RESUME - put in option.
    
        if shutil.which( jjazzlab ):
            jjazzlab_cmd = [ jjazzlab, path ]
            self.jjazz_popen = subprocess.Popen( jjazzlab_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL )
          # self.jjazz_popen = subprocess.Popen( jjazzlab_cmd )         # keep for a while
            s.sigman.emit( "sig_jjazzlab_shown", str( path ))
    
        else:
            t = f"JJazzLab command '{jjazzlab}' not found."
            # s.conf.do_popup( t )
            s.msgWarn( t )
            return

    def xclose( self ):
        if self.jjazz_popen:
            self.jjazz_popen.kill()
        self.jjazz_popen = None

    def close( self ):
        if self.jjazz_popen:
            try:
                self.jjazz_popen.terminate()
                self.jjazz_popen.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.jjazz_popen.kill()
                self.jjazz_popen.wait()

        self.jjazz_popen = None

# ------------------------------------------------------------------------------------
#   WRW 28-Feb-2025 - Experimental, /// RESUME, think about
#       avoiding two calls to get_canonical and get_srcs,
#       one here and one elsewhere.
#   local_info not interesting, remove.
#   Do we have any files that have a canoical but are not indexed:

#   Moved file info from left panel into a on-demand popup in help menu.

# ----------------------------------------------------------
#   /// RESUME - maybe move into file with other popups?
#   Credit to chat.

class HtmlPopup(QDialog):
    def __init__(self, title, html_content, width=400, height=300):
        super().__init__()
        self.setWindowTitle(title)
        self.setFixedSize(width, height)
        self.setModal(True)  # Make the dialog modal

        layout = QVBoxLayout()
        
        # Text browser to display HTML
        self.text_browser = QTextBrowser()
        self.text_browser.setHtml(html_content)
        layout.addWidget(self.text_browser)
        
        # Close button
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close)
        layout.addWidget(self.close_button, alignment=Qt.AlignmentFlag.AlignRight)
        
        self.setLayout(layout)

# ----------------------------------------------------------

class FileInfo():
    # ---------------------------------------------
    #   WRW 30-Mar-2025 - convert to singleton so can use with files other than .pdf.

    _instance = None

    def __new__( cls ):
        if cls._instance is None:
            cls._instance = super().__new__( cls )
        return cls._instance

    # ---------------------------------------------

    def __init__(self):
        if hasattr( self, '_initialized' ):     # Chat prefers this over a flag initialized in __new__().
            return                              # No point initializing a singleton twice.
        self._initialized = True

        s = Store()
        self.relpath = None
        self.src_offset = None
        # self.srcs = None

    #   Save current filename for use in get_file_info()
    def save_filenames( self, path, relpath ):
        s = Store()
        self.path = path
        self.relpath = relpath
        s.sigman.emit( 'sig_show_file_info', self.get_file_info() )

    def OMIT_update_srcs( self, srcs ):
        self.srcs = srcs

    # ----------------------------------------------------------
    #   bu = '\U00002022', '\u2022' works fine.
    #   /// RESUME - Extend for some audio files - show metadata.

    def get_file_info( self ):
        s = Store()
        # if not self.relpath:
        #     print( "ERROR-DEV get_file_info() relpath not defined" )
        #     return None

        ext = Path( self.relpath ).suffix.lower()
        if ext == '.pdf':
            return self.get_pdf_file_info( self.relpath )

        elif ext in ['.mid', '.midi' ]:
            return self.get_midi_file_info( self.path )

        elif ext in ['.txt', '.text' ]:                     # Show text files, many in midi data.
            return self.get_text_file_info( self.path )

        #   Silently ignore unrecognized files, just return path.

        else:
            # s.msgWarn( f"/// No file informatin for file type '{ext}', file '{self.relpath}'" )

            if len(self.relpath) and len(self.relpath):             # Both are not empty
                if len(self.relpath) and (self.relpath == self.path):
                    return f"Path: {self.path}"
                else:
                    return f"RelPath: {self.relpath}<br><br>Path: {self.path}"
            else:
                if len( self.path):
                    return f"Path: {self.path}"
                if len( self.relpath):
                    return f"RelPath: {self.relpath}"
                return ''

    # ----------------------------------------------------------
    def get_pdf_file_info( self, relpath ):
        s = Store()
        bu = '\u2022'

        canonical = s.fb.get_canonical_from_file( relpath )
        if canonical:
            srcs = s.fb.get_srcs_by_canonical( canonical )
            canon_info = f"{canonical}"
            if srcs:
                src_info = f"{', '.join( srcs )}"
                locals = [ s.fb.get_local_from_src_canonical( src, canonical ) for src in srcs ]
                local_info = ', '.join( locals )
            else:
                src_info = "Not indexed"
                local_info = "None"
        else:
            canon_info = "Not mapped to canonical"
            src_info = "Not indexed"
            local_info = "None"
                               
        file_info = QFileInfo( self.path )          # NOTE: QFileInfo, not FileInfo
        file_size = file_info.size()
        mod_date = file_info.lastModified()
        smod_date = mod_date.toString("yyyy-MM-dd hh:mm:ss")
                               
        created_date = file_info.birthTime()
        screated_date = mod_date.toString("yyyy-MM-dd hh:mm:ss")
                               
        info_txt = []          
        info_txt.append( f"{bu} <b><i>File:</i></b> {Path( relpath ).name}" )
        info_txt.append( f"{bu} <b><i>Canonical:</i></b> {canon_info}" )
        info_txt.append( f"{bu} <b><i>Indexed by:</i></b> {src_info}" )
        info_txt.append( f"{bu} <b><i>Locals:</i></b> {local_info}" )
        info_txt.append( '' )  
        info_txt.append( f"{bu} <b><i>Size:</i></b> {file_size:,}" )
        info_txt.append( f"{bu} <b><i>Created:</i></b> {screated_date}" )
        info_txt.append( f"{bu} <b><i>Modified:</i></b> {smod_date}" )
                               
        return '<br>'.join( info_txt )

    # ----------------------------------------------------------
    #   WRW 30-Mar-202 - Add midi file information. 
    #   /// RESUME - more to extract?

    def get_midi_file_info( self, path ):
        bu = '\u2022'

        mid = mido.MidiFile( path )
        info_txt = []          
        
        info_txt.append( f"Path: {path}<br>" )

        info_txt.append( f"{bu} <b><i>Track count:</i></b> {len(mid.tracks)}" )

        note_count = 0
        instruments = set()
        
        for i, track in enumerate(mid.tracks):
            info_txt.append( f"&nbsp;&nbsp;{bu} <b><i>Track {i}:</i></b> {track.name}" )
            for msg in track:
                if msg.type == "note_on":
                    note_count += 1
                elif msg.type == "program_change":
                    instruments.add(msg.program)
        
        info_txt.append( f"{bu} <b><i>Total note count:</i></b> {note_count}" )
        info_txt.append( f"{bu} <b><i>Instrument (program change):</i></b> {sorted(instruments)}" )

        return '<br>'.join( info_txt )

    # ----------------------------------------------------------

    def get_text_file_info( self, path ):
        file_path = Path( path)
        size_in_bytes = file_path.stat().st_size
        return f"File size: {size_in_bytes} bytes"

# ----------------------------------------------------------
