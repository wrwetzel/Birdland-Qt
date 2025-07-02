#!/usr/bin/env python
# ---------------------------------------------------------------------
#   AudioPlayer - Built-in (local) audio player as alternate to external one.
#       With a lot of help from ChatGPT to get started.

# ---------------------------------------------------------------------
#   Find all file extensions in directory hierarchy:
#       find $dir -type f | sed -E 's|.*/||' | grep -oE '\.[^.]+$' | sort | uniq -c | sort -nr

#   WRW 22-May-2025 - A real pain getting python-vlc working in Linux bundle.
#       Now it is not failing gracefully if vlc application not installed on MacOS.
#       Put try/except around the import.

# ---------------------------------------------------------------------

import os
import sys
import contextlib               # WRW 16-Apr-2025 - After uppgrade, pyside6 6.9 got very chatty
from pathlib import Path

try:
    import vlc
    VlcImport_OK = True             # A global, too early to put in Store()
except:
    VlcImport_OK = False

from PySide6.QtCore import QUrl, Qt, Signal, Slot, QBuffer, QByteArray, QSize, QTimer, QMetaObject, QSettings
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QSlider, QLabel

from Store import Store
from bl_style import getOneStyle

# ---------------------------------------------------------------------

# music_file = "/home/wrw/Music/Art Tatum/20th Century Piano Genius/04 Body and Soul.flac"
# music_file = "/home/wrw//Music/Rip/Jaimie Cullum - Pointless Nostalgia/Jaimie Cullum - track2.flac"

# ---------------------------------------------------------------------

class AudioPlayer(QWidget):                         # Only called once but make a singleton to be safe.
    sig_play_audio_local_stopped = Signal( object )
    sig_play_audio_local_buffer = Signal( object )
    sig_play_audio_local_started = Signal()         # WRW 18-Mar-2025 - /// TESTING remove midi audio after started

    _instance = None                                # Class-level attribute to hold the singleton instance

    def __new__(cls):
        if cls._instance is None:                   # Check if an instance already exists
            cls._instance = super().__new__(cls)    # Create a new instance
        return cls._instance                        # Return the existing instance

    def __init__(self):
        s = Store()
        super().__init__()
        self.audioEnabled = False                   # WRW 30-Apr-2025                            
        self.suppressed = False
        self.vlc_initialized = False                # WRW 24-May-2025, deferred vlc init

        s.sigman.register_signal( "sig_play_audio_local_stopped", self.sig_play_audio_local_stopped )
        s.sigman.register_signal( "sig_play_audio_local_buffer", self.sig_play_audio_local_buffer )
        s.sigman.register_signal( "sig_play_audio_local_started", self.sig_play_audio_local_started )
        s.sigman.register_slot( "slot_play_audio_local", self.slot_play_audio_local )
        s.sigman.register_slot( "slot_play_audio_local_buffer", self.slot_play_audio_local_buffer )
        s.sigman.register_slot( "slot_stop_audio_local", self.slot_stop_audio_local )
        s.sigman.register_slot( "slot_audio_appearance", self.audio_appearance )

        # --------------------------------------------------------------

        if not VlcImport_OK:
            text = """Birdland requires the installation of <i>vlc</i> application
                      to use the built-in audio and midi player.  Please install
                      <i>vlc</i> or install other audio and midi players and indicate such
                      in the configuration window.  This only applies to the Windows and
                      MacOS platforms.  The <i>vlc</i> player is included in the bundled
                      distribution for the Linux platform.  Continuing without built-in
                      audio.  This message will not be repeated.
                   """
            s.msgWarnOnce( 'audio-state', text )
            self.OK = False
            return

        else:
            s.msgOnceReset( 'audio-state' )

        # --------------------------------------------------------------
        #   WRW 24-May-2025 - Refactored. Don't initialize vlc unill play() and again when soundfont changes.
        #   No, really need to get self.mediaplayer defined early, used throughout code. Init but
        #   reinit when soundfont changes.

        self.OK = self._init_vlc( )
        if not self.OK:                     # don't build audio player gui if don't have vlc support.
            return

        # --------------------------------------------------------------
        #    self.prev_button = QPushButton( )
        #    s.fb.registerSvgIcon( self.prev_button, ":NIcons/zoom-previous.svg", iconSize, 'aud' )

        iconSize = QSize( 32, 32 )

        self.play_button = QPushButton( self )
        s.fb.registerSvgIcon( self.play_button, ":NIcons/media-playback-start.svg", iconSize, 'aud' )

        self.pause_button = QPushButton( self  )
        s.fb.registerSvgIcon( self.pause_button, ":NIcons/media-playback-pause.svg", iconSize, 'aud' )
        self.pause_button.hide()

        self.stop_button = QPushButton( self )
        s.fb.registerSvgIcon( self.stop_button, ":NIcons/media-playback-stop.svg", iconSize, 'aud' )

        self.forward_button = QPushButton( self )
        s.fb.registerSvgIcon( self.forward_button, ":NIcons/media-seek-forward.svg", iconSize, 'aud' )

        self.rewind_button = QPushButton( self )
        s.fb.registerSvgIcon( self.rewind_button, ":NIcons/media-seek-backward.svg", iconSize, 'aud' )

        # Progress slider
        self.position_slider = QSlider(Qt.Horizontal, self)
        self.position_slider.setRange(0, 1000)                         
        self.position_label = QLabel( "00:00 / 00:00", self )

        # Volume slider
        self.volume_slider = QSlider(Qt.Horizontal, self )
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(self.volume)                                                          

        # Layouts
        control_layout = QHBoxLayout()
        control_layout.addWidget(self.play_button)
        control_layout.addWidget(self.pause_button)
        control_layout.addWidget(self.stop_button)
        control_layout.addWidget(self.rewind_button)
        control_layout.addWidget(self.forward_button)

        progress_layout = QHBoxLayout()
        progress_layout.addWidget(self.position_slider)
        progress_layout.addWidget(self.position_label)      # WRW 20-May-2025 Label to right of slider

        slider_layout = QVBoxLayout()
        slider_layout.addLayout( progress_layout )

        volume_layout = QHBoxLayout()
        volume_layout.addWidget(QLabel("Volume:"))
        volume_layout.addWidget(self.volume_slider)

        main_layout = QVBoxLayout()
        main_layout.addLayout(control_layout)
        main_layout.addLayout(slider_layout)
        main_layout.addLayout(volume_layout)
        self.setLayout(main_layout)

        # Connections
        self.play_button.clicked.connect( self.play_button_clicked )
        self.pause_button.clicked.connect( lambda: ( self.pause_button.hide(), 
                                                     self.play_button.show(),
                                                     self.mediaplayer.pause() ))

        self.stop_button.clicked.connect( lambda: ( self.pause_button.hide(), self.play_button.show(), 
                                          self.mediaplayer.stop(),
                                          self.timer.stop(),
                                          self.position_slider.setValue(0),
                                          self.position_label.setText("00:00 / 00:00")
                                        ))

        self.forward_button.clicked.connect(self.forward)
        self.rewind_button.clicked.connect(self.rewind)
        self.volume_slider.valueChanged.connect(self.set_volume)
        self.position_slider.sliderMoved.connect(self.set_position)

        # Timer to update UI
        self.timer = QTimer(self)
        self.timer.setInterval(500)
        self.timer.timeout.connect(self.update_ui)

    # --------------------------------------------------------------
    #   WRW 24-May-2025 - with help from chat in stopping vlc.
    #   Similar to original code with addition of stopping logic.

    def _init_vlc( self ):
        s = Store()

        #   ----------------------------------------
        #   First stop any prior instance of vlc.

        if hasattr(self, 'mediaplayer') and self.mediaplayer:
            self.mediaplayer.stop()
            self.mediaplayer.release()
            self.mediaplayer = None

        if hasattr(self, 'instance') and self.instance:
            self.instance.release()
            self.instance = None

        if not VlcImport_OK:
            return False

        # --------------------------------------------------
        #   define self.volume before create instance

        settings = QSettings( str( Path( s.Const.stdConfig, s.Const.Settings_Config_File )), QSettings.IniFormat )
        self.volume = settings.value("Audio-volume")
        if self.volume is None:
            self.volume = 75
        else:
            self.volume = int( self.volume )

        # --------------------------------------------------
        #   Determine soundfont, if any, and create Instance. 
        #   The --soundfont arg is ignored for audio, useful for midi.

        #   WRW 26-May-2025 This is getting to be a can of worms. Vlc on MacOS does not
        #   support fluidsynth and complains about a --soundfont argument. But somehow
        #   it still plays midi without a sounnfont file specificied.

        self.soundfont = s.Settings( 'soundfont_file' )

        self.instance = False

        if self.soundfont and Path( self.soundfont ).is_file():                 # Try with soundfont
            self.instance = vlc.Instance( f"--soundfont={self.soundfont}" )

        if not self.instance:                   # If NG try without soundfont
            self.instance = vlc.Instance( )

        if not self.instance:                   # Still may fail if no vlc support
            s.msgWarn( f"""ERROR: Unable to load vlc library, built-in player disabled.
                          """ )
            return False

        self.mediaplayer = self.instance.media_player_new()
        self.mediaplayer.audio_set_volume( self.volume )
        self.mediaplayer.event_manager().event_attach( vlc.EventType.MediaPlayerEndReached, self.onEndReached )
        return True

    # --------------------------------------------------------------

    def update_ui(self):
        if self.mediaplayer.is_playing():
            length = self.mediaplayer.get_length()
            current = self.mediaplayer.get_time()
            if length > 0:
                self.position_slider.blockSignals(True)
                self.position_slider.setValue(int(current / length * 1000))
                self.position_slider.blockSignals(False)
                self.position_label.setText(f"{self.format_time(current)} / {self.format_time(length)}")

    # --------------------------------------------------------------

    @Slot()
    def _reset_ui_after_end( self ):
        self.mediaplayer.stop()
        self.mediaplayer.set_media( self.media )  # Reset the media
        self.timer.stop()
        self.position_slider.setValue(0)
        self.position_label.setText("00:00 / 00:00")
        self.play_button.show()
        self.pause_button.hide()
        self.suppressVlcOutput_stop()

    #   onEndReached() is a callback from a non-Qt native thread (from libVLC). Can't use QTimer here,
    #   need to get back to Qt event loop, which is what invokeMethod / QueuedConnection does.
    #   Chat is brighter than I though it took chat a few tries to get it.

    def onEndReached( self, event ):
        QMetaObject.invokeMethod( self, "_reset_ui_after_end", Qt.QueuedConnection
        )

    # --------------------------------------------------------------
    #   python-vlc library play() is a bit chatty. Suppress its output.
    #   WRW 22-May-2025 - sys.stdout is None in bundle on windows.
    #   Just ignore on windows.

    if False:
        @contextlib.contextmanager
        def suppressVlcOutput( self ):
            s = Store()

            with open(os.devnull, 'w') as devnull:
                if s.Const.Platform != 'Windows':
                    sys.stdout.flush()              # Flush Python-level buffers
                    sys.stderr.flush()

                    old_stdout_fd = os.dup(1)       # Save actual file descriptors
                    old_stderr_fd = os.dup(2)

                    os.dup2(devnull.fileno(), 1)    # Redirect stdout/stderr to /dev/null
                    os.dup2(devnull.fileno(), 2)

                try:
                    yield

                finally:
                    if s.Const.Platform != 'Windows':
                        os.dup2(old_stdout_fd, 1)   # Restore original file descriptors
                        os.dup2(old_stderr_fd, 2)
                        os.close(old_stdout_fd)
                        os.close(old_stderr_fd)

    # --------------------------------------------------------------
    #   WRW 22-May-2025 - sys.stdout is None in bundle on windows.
    #   Just ignore on windows.
    #   WRW 23-May-2025 - Original approach with context manager does not work because
    #   play_audio() just queues playback returns immediately.
    #   Chat says this may be unreliable on Windows even in non-bundled environment
    #   so ignore on windows. Only an issue when running from terminal, which only
    #   happens with windows during testing.

    def suppressVlcOutput_start( self ):
        s = Store()
        if s.Options.debug:
            return

        if s.Const.Platform != 'Windows':
            self.devnull = open(os.devnull, 'w')
            sys.stdout.flush()              # Flush Python-level buffers
            sys.stderr.flush()

            self.old_stdout_fd = os.dup(1)       # Save actual file descriptors
            self.old_stderr_fd = os.dup(2)

            os.dup2(self.devnull.fileno(), 1)    # Redirect stdout/stderr to /dev/null
            os.dup2(self.devnull.fileno(), 2)
            self.suppressed = True
    
    def suppressVlcOutput_stop( self ):
        s = Store()
        if s.Options.debug:
            return

        if s.Const.Platform != 'Windows':
            if self.suppressed:
                os.dup2(self.old_stdout_fd, 1)   # Restore original file descriptors
                os.dup2(self.old_stderr_fd, 2)
                os.close(self.old_stdout_fd)
                os.close(self.old_stderr_fd)
                self.devnull.close()
                self.suppressed = False

    # --------------------------------------------------------------
    #   WRW 1-May-2025 - need to check state before showing buttons.

    def play_button_clicked( self ):
        if( self.audioEnabled ):
            self.pause_button.show()
            self.play_button.hide()
            # self.player.play()

            if self.mediaplayer.play() == 0:
                self.timer.start()

    # --------------------------------------------------------------
    #   Play file
    #   Attempt to suppress output at setSource() and play() was ineffective because play() only
    #   scheduled the playback. The messages were sent after play() returned.
    #   WRW 24-May-2025 - vlc is not initialized at first entry, do it here if necessary and
    #   and when soundfont changes.

    @Slot( object )
    def slot_play_audio_local( self, path ):
        s = Store()

        # ------------------------------------------------------
        #   Reinit before play if soundfont changes.

        new_soundfont = s.Settings( 'soundfont_file' )
        if self.soundfont != new_soundfont:
            # Message used for testing, will be annoying to user. 
            #    s.msgInfo( f"Soundfont changed from: {self.soundfont} to: {new_soundfont}" )

            if not new_soundfont:                  # If set soundfont to empty remind the user on next play midi 
                s.msgOnceReset( 'vlc-sf-reqd' )    #    that a soundfont may be required.
            self.OK = self._init_vlc()

        # ------------------------------------------------------
        #   Defer OK test until after new soundfont test so can recover if a 
        #   prior soundfont was bogus and caused a failure above.
        #   Can change it and try playing again.

        if not self.OK:
            return

        self.audioEnabled = True           # WRW 30-Apr-2025                            
        self.updateAudioAppearance()
        self.pause_button.show()
        self.play_button.hide()

        ext = Path( path ).suffix              
        if ext.lower() not in s.Const.audioFileTypes:
            s.msgWarn( f"The extension '{ext}' of audio file '{path}' not supported for audio playback." )
            return

        self.update_counter = 0

        self.media = self.instance.media_new( path )
        self.mediaplayer.set_media( self.media )

        self.suppressVlcOutput_start()      # Instead, suppress here, reenable when audio stops.
        self.play_audio()

    # --------------------------------------------------------------

    def play_audio( self ):
        if self.mediaplayer.play() == 0:
            self.timer.start()

    # --------------------------------------------------------------
    #   Play data contained in a buffer, may have problems
    #   This has not been maintained, likely bogus, not used.

    @Slot( object )
    def slot_play_audio_local_buffer( self, data ):
        if not self.OK:
            return

        self.pause_button.show()
        self.play_button.hide()
        buffer = QBuffer()
        buffer.setData(QByteArray(data))
        buffer.open(QBuffer.ReadOnly)
        self.player.setSourceDevice(buffer, QUrl())
        self.player.play()

        # /// RESUME - copied, not tested

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            tmp.write(buffer)
            tmp.flush()
            media = vlc.Media(tmp.name)

        player.set_media(self.media)

        with self.suppressVlcOutput():
            player.play()

    # --------------------------------------------------------------

    @Slot()
    def slot_stop_audio_local( self ):
        if not self.OK:
            return

        s = Store()
        self.pause_button.hide()
        self.play_button.show(),

        self.mediaplayer.stop()
        self.timer.stop()
        self.position_slider.setValue(0)
        self.position_label.setText("00:00 / 00:00")
        s.sigman.emit( "sig_play_audio_local_stopped", '' )
        self.audioEnabled = False                   # WRW 1-May-2025 - Not sure if want this here or not.
        self.updateAudioAppearance()
        self.suppressVlcOutput_stop()

        settings = QSettings( str( Path( s.Const.stdConfig, s.Const.Settings_Config_File )), QSettings.IniFormat )
        settings.setValue("Audio-volume", self.volume )

    # ------------------------------------------------------------------
    def set_volume(self, value):
        self.volume = value
        self.mediaplayer.audio_set_volume( self.volume )

    def set_position(self, position):
        if self.mediaplayer.get_length() > 0:
            new_time = self.position_slider.value() / 1000 * self.mediaplayer.get_length()
            self.mediaplayer.set_time(int(new_time))

    def forward(self):
        current_time = self.mediaplayer.get_time()
        self.mediaplayer.set_time(max(0, current_time + 5 * 1000))

    def rewind(self):
        current_time = self.mediaplayer.get_time()
        self.mediaplayer.set_time(max(0, current_time - 5 * 1000))

    def format_time(self, ms):
        """Convert milliseconds to mm:ss format"""
        seconds = ms // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02}:{seconds:02}"

    # ------------------------------------------------------------------
    #   WRW 1-May-2025 - Struggling to find the best way to change audio icon colors
    #       when enabled state changes
    #       audio_appearance() is called on signal from updateIcons() in Config() and
    #       change in enabled state.

    @Slot( object )
    def audio_appearance( self, appearance ):
        if not self.OK:
            return

        self.appearance = appearance
        s = Store()
        if self.audioEnabled:
            icon_color = getOneStyle( appearance, 'qwidget_text' )
        else:
            icon_color = getOneStyle( appearance, 'qwidget_text_dis' )

        s.fb.updateSvgIcons( QColor( icon_color ), group='aud' )

    def updateAudioAppearance( self ):
        self.audio_appearance( self.appearance )

# ---------------------------------------------------------------------

if __name__ == "__main__":
    from bl_unit_test import UT
    from bl_style import StyleSheet

    s = UT()

    s.app = QApplication(sys.argv)
    s.window = AudioPlayer()
    s.window.setStyleSheet( StyleSheet )            # OK Unit test
    s.window.setWindowTitle("Audio Player with PySide6")
    s.window.show()
    sys.exit(s.app.exec())

# ---------------------------------------------------------------------
