# ------------------------------------------------------------------------------------
#   WRW 20-Mar-2025 - Moved from main module, qbird.py at present.
# ------------------------------------------------------------------------------------
#   Connect the signals to the slots. All connections done here and done symbolically. 

#   Signals are registered in namespace containing the definition of the signal
#   Some signals are registered here when they are otherwide used outside of a class.
#       sig_foo = Signal( str, int, object )

#   Slots are registered in namespace containing the function implementing the slot:
#       @Slot
#       def slot_foo( a, b, c ):

# ---------------------------------------------------

from PySide6.QtCore import QObject, Signal                    

from Store import Store

# ---------------------------------------------------

class MakeConnections():
    def __init__( self ):
        s = Store()
        Connections = (
            ( "sig_search_box_return_pressed",          "slot_search_box_return_pressed"),
            ( "sig_search_results",                     "slot_update_status"),
            ( "sig_menu_action",                        "slot_menu_action" ),

            ( "sig_play_audio_starting",                "slot_stop_audio"),
            ( "sig_play_audio_starting",                "slot_stop_audio_local"),
            ( "sig_play_audio_started",                 "slot_stop_midi"),
            ( "sig_play_audio_started",                 "slot_stop_youtube"),
            ( "sig_play_audio_started",                 "slot_update_status"),
            ( "sig_play_audio_local",                   "slot_play_audio_local" ),
            ( "sig_play_audio_local_buffer",            "slot_play_audio_local_buffer" ),
            ( "sig_play_audio_local_stopped",           "slot_update_status" ),
            ( "sig_play_audio_local_started",           "slot_play_audio_local_started" ),

            ( "sig_play_midi_starting",                 "slot_stop_midi"),
            ( "sig_play_midi_starting",                 "slot_stop_audio"),
            ( "sig_play_midi_starting",                 "slot_stop_audio_local"),
            ( "sig_play_midi_starting",                 "slot_stop_youtube"),
            ( "sig_play_midi_started",                  "slot_update_status"),

            ( "sig_youtube_starting",                   "slot_stop_youtube"),
            ( "sig_youtube_starting",                   "slot_stop_audio"),
            ( "sig_youtube_starting",                   "slot_stop_audio_local"),
            ( "sig_youtube_starting",                   "slot_stop_midi"),
            ( "sig_youtube_shown",                      "slot_update_status"),
            ( "sig_chordpro_shown",                     "slot_update_status"),

            ( "sig_music_table_cell_clicked",           "slot_music_table_cell_clicked" ),
            ( "sig_music_table_cell_right_clicked",     "slot_music_table_cell_right_clicked" ),
            ( "sig_music_files_table_cell_clicked",     "slot_music_files_table_cell_clicked" ),
            ( "sig_audio_table_cell_clicked",           "slot_audio_table_cell_clicked" ),
            ( "sig_audio_table_cell_right_clicked",     "slot_audio_table_cell_right_clicked" ),
            ( "sig_midi_table_cell_clicked",            "slot_midi_table_cell_clicked" ),
            ( "sig_midi_table_cell_right_clicked",      "slot_midi_table_cell_right_clicked" ),
            ( "sig_midi_ext_command_finished",          "slot_midi_ext_command_finished" ),
            ( "sig_midi_to_audio_ext_command_finished", "slot_midi_to_audio_ext_command_finished" ),

            ( "sig_chordpro_table_cell_clicked",        "slot_chordpro_table_cell_clicked" ),
            ( "sig_chordpro_table_cell_right_clicked",  "slot_chordpro_table_cell_right_clicked" ),
            ( "sig_jjazzlab_table_cell_clicked",        "slot_jjazzlab_table_cell_clicked" ),
            ( "sig_youtube_table_cell_clicked",         "slot_youtube_table_cell_clicked" ),

            ( "sig_music_browser_clicked",              "slot_music_browser_clicked" ),
            ( "sig_audio_browser_clicked",              "slot_audio_browser_clicked" ),
            ( "sig_midi_browser_clicked",               "slot_midi_browser_clicked" ),
            ( "sig_chordpro_browser_clicked",           "slot_chordpro_browser_clicked" ),
            ( "sig_jjazz_browser_clicked",              "slot_jjazz_browser_clicked" ),
            ( "sig_audio_of_title_table_cell_clicked",  "slot_audio_table_cell_clicked" ),
            ( "sig_midi_of_title_table_cell_clicked",   "slot_midi_table_cell_clicked" ),
            ( "sig_toc_cell_clicked",                   "slot_toc_cell_clicked"  ),

            ( "sig_music_table_data",                   "slot_music_table_data" ),
            ( "sig_music_files_table_data",             "slot_music_files_table_data" ),
            ( "sig_audio_table_data",                   "slot_audio_table_data" ),
            ( "sig_midi_table_data",                    "slot_midi_table_data" ),
            ( "sig_chordpro_table_data",                "slot_chordpro_table_data" ),
            ( "sig_jjazzlab_table_data",                "slot_jjazzlab_table_data" ),
            ( "sig_chordpro_table_data",                "slot_chordpro_table_data" ),
            ( "sig_youtube_table_data",                 "slot_youtube_table_data" ),
            ( "sig_setlist_table_data",                 "slot_setlist_table_data" ),

            ( "sig_update_meta_title",                  "slot_update_meta_title" ),
            ( "sig_update_meta_canon",                  "slot_update_meta_canon" ),
            ( "sig_update_meta_local",                  "slot_update_meta_local" ),
            ( "sig_update_meta_file",                   "slot_update_meta_file"  ),
            ( "sig_update_meta_page",                   "slot_update_meta_page"  ),
            ( "sig_update_meta_sheet",                  "slot_update_meta_sheet"  ),

            ( "sig_update_meta_current_audio",          "slot_update_meta_current_audio"  ),
            ( "sig_update_meta_current_audio",          "slot_update_audio_of_tab" ),
            ( "sig_update_meta_current_audio",          "slot_update_audio_of_statusbar" ),

            ( "sig_update_meta_current_midi",           "slot_update_meta_current_midi"  ),
            ( "sig_update_meta_current_midi",           "slot_update_midi_of_tab" ),
            ( "sig_update_meta_current_midi",           "slot_update_midi_of_statusbar" ),

            ( "sig_update_meta_toc",                    "slot_update_meta_toc"  ),

            ( "sig_update_reports_table",               "slot_update_reports_table" ),

            ( "sig_stop_media",                         "slot_stop_audio"),
            ( "sig_stop_media",                         "slot_stop_audio_local"),
            ( "sig_stop_media",                         "slot_stop_midi" ),
            ( "sig_stop_media",                         "slot_stop_youtube"),

            ( "sig_change_pdf_page",                    "slot_change_pdf_page" ),
            ( "sig_pdf_page_changed",                   "slot_pdf_page_changed" ),
            ( "sig_update_src_offset",                  "slot_update_src_offset" ),
            ( "sig_src_offset_changed",                 "slot_src_offset_changed" ),
            ( "sig_show_file_info",                     "slot_show_file_info" ),
            ( "sig_set_src_offset_visible",             "slot_set_src_offset_visible" ),

            ( "sig_setlist_add",                        "slot_setlist_add" ),
            ( "sig_setlist_add_select",                 "slot_setlist_add_select" ),
            ( "sig_setlist_manage_select",              "slot_setlist_manage_select" ),
            ( "sig_setlist_move_up",                    "slot_setlist_move_up" ),
            ( "sig_setlist_move_down",                  "slot_setlist_move_down" ),
            ( "sig_setlist_delete",                     "slot_setlist_delete" ),
            ( "sig_setlist_save",                       "slot_setlist_save" ),
            ( "sig_setlist_current_data",               "slot_setlist_current_data" ),

            ( "sig_setlist_update_add_select",          "slot_setlist_update_add_select" ),
            ( "sig_setlist_select_add_select",          "slot_setlist_select_add_select" ),

            ( "sig_setlist_update_manage_select",       "slot_setlist_update_manage_select" ),
            ( "sig_setlist_select_manage_select",       "slot_setlist_select_manage_select" ),
            ( "sig_setlist_table_cell_clicked",         "slot_setlist_table_cell_clicked" ),
            ( "sig_setlist_table_cell_clicked_full",    "slot_setlist_table_cell_clicked_full" ),
            ( "sig_setlist_table_row_clicked",          "slot_setlist_table_row_clicked" ),
            ( "sig_setlist_table_row_clicked_full",     "slot_setlist_table_row_clicked_full" ),

            ( "sig_setlist_edit_state_change",          "slot_setlist_edit_state_change" ),
            ( "sig_addto_results",                      "slot_addto_results" ),
            ( "sig_clear_results",                      "slot_clear_results" ),
            ( "sig_load_pdf",                           "slot_load_pdf" ),

            ( "sig_pdf_changed",                        "slot_pdf_changed"),

            ( "sig_play_audio",                         "slot_play_audio" ),
            ( "sig_close_audio",                        "slot_close_audio" ),
            ( "sig_show_jjazz",                         "slot_show_jjazz" ),
            ( "sig_show_chord",                         "slot_show_chord" ),
            ( "sig_close_chord",                        "slot_close_chord" ),
            ( "sig_play_midi",                          "slot_play_midi" ),
            ( "sig_close_midi",                         "slot_close_midi" ),
            ( "sig_show_youtube",                       "slot_show_youtube" ),
            ( "sig_close_youtube",                      "slot_close_youtube" ),

            ( "sig_showFt",                             "slot_showFt" ),
            ( "sig_showFs",                             "slot_showFs" ),
            ( "sig_showFi",                             "slot_showFi" ),

            ( "sig_select_tab",                         "slot_select_tab" ),
            ( "sig_select_left_tab",                    "slot_select_left_tab" ),

            ( "sig_set_tab_visibility",                 "slot_set_tab_visibility" ),
            ( "sig_toggle_tab_visibility",              "slot_toggle_tab_visibility" ),


            ( "sig_close_jjazz",                        "slot_close_jjazz" ),

            ( "sig_stopping",                           "slot_close_audio" ),
            ( "sig_stopping",                           "slot_stop_audio_local"),
            ( "sig_stopping",                           "slot_close_jjazz" ),
            ( "sig_stopping",                           "slot_close_chord" ),
            ( "sig_stopping",                           "slot_close_midi" ),
            ( "sig_stopping",                           "slot_close_youtube" ),

          # ( "sig_starting",                           "slot_restore_tab_order" ),         # WRW 3-June-2025 no longer used
          # ( "sig_stopping",                           "slot_save_tab_order" ),            # WRW 3-June-2025 no longer used

            ( "sig_toggle_fullscreen",                  "slot_toggle_fullscreen" ),
            ( "sig_do_fullscreen",                      "slot_do_fullscreen" ),                 # 27-May-2025
            ( "sig_do_fullscreen",                      "slot_announce_do_fullscreen" ),        # 28-May-2025
            ( "sig_exit_fullscreen",                    "slot_exit_fullscreen" ),
            ( "sig_exit_fullscreen",                    "slot_announce_exit_fullscreen" ),      # 28-May-2025

            ( "sig_announce_do_fullscreen",             "slot_announce_do_fullscreen" ),        # 2-June-2025
            ( "sig_announce_exit_fullscreen",           "slot_announce_exit_fullscreen" ),      # 2-June-2025

            ( "sig_preparing_to_exit",                  "slot_preparing_to_exit" ),
            ( "sig_appearance",                         "slot_audio_appearance" ),              # WRW 1-May-2025
            ( "sig_appearance",                         "slot_pdf_appearance" ),                # WRW 1-May-2025
            ( "sig_title_focus",                        "slot_title_focus" ),                   # WRW 20-May-2025
            ( "sig_make_thumbnails",                    "slot_make_thumbnails" ),               # WRW 25-May-2025
            ( "sig_fullscreen_button_clicked",          "slot_fullscreen_button_clicked" ),     # WRW 28-May-2025
            ( "sig_update_browsers_root",               "slot_update_browsers_root" ),          # WRW 31-May-2025
            ( "sig_canon_name_table_cell_clicked",      "slot_canon_name_table_cell_clicked" ), # WRW 1-June-2025
            ( "sig_canon_file_table_cell_clicked",      "slot_canon_file_table_cell_clicked" ), # WRW 1-June-2025
        )

        for signal_name, slot_name in Connections:
            s.sigman.connect( signal_name, slot_name )

# ------------------------------------------------------------------------------------
#   Support for signals not defined in a class
#   Signal() Allowed types: int, float, str, bool, object
#       Use object for lists or dicts

class RegisterNonClassSignals( QObject ):
    sig_search_results = Signal(str)
    sig_music_table_data = Signal( object )
    sig_music_files_table_data = Signal( object )
    sig_audio_table_data = Signal( object )
    sig_midi_table_data = Signal( object )
    sig_chordpro_table_data = Signal( object )
    sig_jjazzlab_table_data = Signal( object )
    sig_youtube_table_data = Signal( object )
    sig_setlist_table_data = Signal( object, object )   # Need 'object' as second argument to pass None

    sig_update_meta_title = Signal( str )    # These four are names generated programmatically
    sig_update_meta_canon = Signal( str )
    sig_update_meta_local = Signal( str )
    sig_update_meta_file = Signal( str )
    sig_update_meta_page = Signal( str )
    sig_update_meta_sheet = Signal( str )
    sig_update_meta_current_audio = Signal( object )
    sig_update_meta_current_midi = Signal( object )
    sig_update_meta_toc = Signal( object )
    sig_music_toc_clicked = Signal( str, str )
    sig_update_reports_table = Signal( object )
    sig_update_src_offset = Signal( object )
    sig_show_file_info = Signal( str )
    sig_addto_results = Signal( str )
    sig_clear_results = Signal()
    sig_load_pdf = Signal( object, str, int )                                                                          
    sig_change_pdf_page = Signal( int )     # WRW 22-Mar-2025

    sig_play_audio = Signal( str )          # WRW 20-Mar-2025
    sig_close_audio = Signal()              # WRW 20-Mar-2025
    sig_show_jjazz = Signal( str )          # WRW 20-Mar-2025
    sig_close_jjazz = Signal()              # WRW 20-Mar-2025
    sig_show_chord = Signal( str, object )  # WRW 20-Mar-2025
    sig_close_chord = Signal()              # WRW 20-Mar-2025
    sig_play_midi = Signal( str, str )      # WRW 20-Mar-2025
    sig_close_midi = Signal()               # WRW 20-Mar-2025
    sig_show_youtube = Signal( str)         # WRW 20-Mar-2025
    sig_close_youtube = Signal()            # WRW 20-Mar-2025

    sig_showFt = Signal( str, str, str )    # WRW 20-Mar-2025
    sig_showFs = Signal( str, str )         # WRW 20-Mar-2025
    sig_showFi = Signal( str, object )      # WRW 20-Mar-2025

    sig_select_tab = Signal( object )       # WRW 21-Mar-2025
    sig_select_left_tab = Signal( object )       # WRW 27-May-2025
    sig_set_tab_visibility = Signal( object, int )  # WRW 21-Mar-2025
    sig_toggle_tab_visibility = Signal( object )
    sig_starting = Signal()                 # WRW 22-Mar-2025
    sig_stopping = Signal()                 # WRW 22-Mar-2025
    sig_preparing_to_exit = Signal()        # WRW 30-Mar-2025
    sig_appearance = Signal( object )       # WRW 1-May-2025
    sig_title_focus = Signal()              # WRW 20-May-2025
    sig_make_thumbnails = Signal()          # WRW 25-May-2025
    sig_fullscreen_button_clicked = Signal() # WRW 28-May-2025

    sig_update_browsers_root = Signal()     # WRW 31-May-2025
    sig_announce_do_fullscreen = Signal()   # WRW 2-June-2025
    sig_announce_exit_fullscreen = Signal()   # WRW 2-June-2025

    _instance = None

    def __new__(cls):

        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    # ----------------------------------------------------------

    def __del__(self):
        print( "RegisterNonClassSignals has been deleted!")

    # ----------------------------------------------------------
    #   WRW 15-Apr-2025 - A curious issue after an upgrade to pyside6. Previously the
    #   super().__init__() was below the signals = () assignment. After the upgrade
    #   the signals here were no longer defined at the registration at the bottom.
    #   Moved it to the top and now OK.

    def __init__( self ):

        if not hasattr( self, '_initialized' ):
            super().__init__()
            self._initialized = True    # Prevent multiple calls to super().__init__(), multiple QObject issue.
        else:
            return      # We only instiatiate once but to be safe.

        signals = (
            ( "sig_search_results",             self.sig_search_results ),
            ( "sig_music_table_data",           self.sig_music_table_data ),
            ( "sig_music_files_table_data",     self.sig_music_files_table_data ),
            ( "sig_audio_table_data",           self.sig_audio_table_data ),
            ( "sig_midi_table_data",            self.sig_midi_table_data ),
            ( "sig_chordpro_table_data",        self.sig_chordpro_table_data ),
            ( "sig_jjazzlab_table_data",        self.sig_jjazzlab_table_data ),
            ( "sig_youtube_table_data",         self.sig_youtube_table_data ),
            ( "sig_setlist_table_data",         self.sig_setlist_table_data ),

            ( "sig_update_meta_title",          self.sig_update_meta_title ),
            ( "sig_update_meta_canon",          self.sig_update_meta_canon ),
            ( "sig_update_meta_local",          self.sig_update_meta_local ),
            ( "sig_update_meta_file",           self.sig_update_meta_file ),
            ( "sig_update_meta_page",           self.sig_update_meta_page ),

            ( "sig_update_meta_sheet",          self.sig_update_meta_sheet ),
            ( "sig_update_meta_current_audio",  self.sig_update_meta_current_audio ),
            ( "sig_update_meta_current_midi",   self.sig_update_meta_current_midi ),
            ( "sig_update_meta_toc",            self.sig_update_meta_toc ),
            ( "sig_music_toc_clicked",          self.sig_music_toc_clicked ),
            ( "sig_update_reports_table",       self.sig_update_reports_table ),
            ( "sig_update_src_offset",          self.sig_update_src_offset ),
            ( "sig_show_file_info",             self.sig_show_file_info ),
            ( "sig_addto_results",              self.sig_addto_results ),
            ( "sig_clear_results",              self.sig_clear_results ),
            ( "sig_load_pdf",                   self.sig_load_pdf ),
            ( "sig_change_pdf_page",            self.sig_change_pdf_page ),

            ( "sig_play_audio",                 self.sig_play_audio ),
            ( "sig_close_audio",                self.sig_close_audio ),

            ( "sig_show_jjazz",                 self.sig_show_jjazz ),
            ( "sig_close_jjazz",                self.sig_close_jjazz ),

            ( "sig_show_chord",                 self.sig_show_chord ),
            ( "sig_close_chord",                self.sig_close_chord ),

            ( "sig_play_midi",                  self.sig_play_midi ),
            ( "sig_close_midi",                 self.sig_close_midi ),

            ( "sig_show_youtube",               self.sig_show_youtube ),
            ( "sig_close_youtube",              self.sig_close_youtube ),

            ( "sig_showFt",                     self.sig_showFt ),
            ( "sig_showFs",                     self.sig_showFs ),
            ( "sig_showFi",                     self.sig_showFi ),
            ( "sig_select_tab",                 self.sig_select_tab ),
            ( "sig_select_left_tab",            self.sig_select_left_tab ),
            ( "sig_set_tab_visibility",         self.sig_set_tab_visibility ),
            ( "sig_toggle_tab_visibility",      self.sig_toggle_tab_visibility ),
            ( "sig_starting",                   self.sig_starting ),
            ( "sig_stopping",                   self.sig_stopping ),
            ( "sig_preparing_to_exit",          self.sig_preparing_to_exit ),
            ( "sig_appearance",                 self.sig_appearance ),
            ( "sig_title_focus",                self.sig_title_focus ),
            ( "sig_make_thumbnails",            self.sig_make_thumbnails ),
            ( "sig_fullscreen_button_clicked",  self.sig_fullscreen_button_clicked ),
            ( "sig_update_browsers_root",       self.sig_update_browsers_root ),
            ( "sig_announce_do_fullscreen",     self.sig_announce_do_fullscreen ),
            ( "sig_announce_exit_fullscreen",   self.sig_announce_exit_fullscreen ),
        )

        # ----------------------------------------------------------
        s = Store()

        for signal_name, signal in signals:
            s.sigman.register_signal( signal_name, signal )

# ------------------------------------------------------------------------------------
