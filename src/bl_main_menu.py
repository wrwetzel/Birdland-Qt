#!/usr/bin/python
# ------------------------------------------------------------------------------
#   WRW 6-Feb-2025 - Move menu definition and construction here
# ------------------------------------------------------------------------------

from PySide6.QtCore import Signal, QObject
from PySide6.QtGui import QAction       
from Store import Store

# ------------------------------------------------------------------------------

#   This taken directly from PySimpleGui version of fb_layout.py, might as well use it
#       instead of reinventing as it shows the entire menu structure.

development_menu = [
    ['&Development',  [
                        'Global Store::menu-show-global-store',
                        'Globals::menu-show-globals',
                        'Constants::menu-show-constants',
                        '_Settings::menu-show-settings',
                        'Screens::menu-show-screens',
                        'Styles::menu-show-styles',
                        'Data Dictionary::menu-show-datadict',
                        'Palette::menu-show-palette',
                        'Splash Screen::menu-show-splash',
                        '----',
                        'UI Structure::menu-show-children',
                        'Class Hierarchy::menu-show-class-hierarchy',
                        'Widgets::menu-show-widgets',
                        'Named Objects::menu-show-objects',
                        'Managed Signals::menu-show-managed-signals',
                        'Native Signals::menu-show-native-signals',
                        '----',
                        'Message Box::menu-show-message-box',
                        'Message Box Once::menu-show-message-box-once',
                        'Message Box Once Reset::menu-show-message-box-once-reset',
                        'Div-Zero Error::menu-show-div-zero',

                     #   '----',
                     #   'Initialize Data Dir::menu-initialize-data-dir',       # Already tested, don't want in menu
                     #   'Initialize Config Dir::menu-initialize-config-dir',
              ]
    ]
]

main_menu_definition = [
#   [ 'None', []],                                  # /// RESUME testing on MacOS

    ['&File',  [                                   # This is removed on MacOS, moved into app menu
                'Settings::menu-configure',        # Settings and Exit are reserved in MacOS, were intercepted
                'Exit::menu-exit',
               ]
    ],
#   ['&Edit',  ['Settings::menu-configure' ]],
    ['&Reports', [
               'All::menu-stats-all',
               '----',
               'Database Stats::menu-stats-database',
               'Title Count by Src::menu-stats-title-count-src',
               'Title Count by Src and Canonical::menu-stats-title-count-canon-src',
               'Title Coverage by Src and Canonical::menu-stats-title-coverage-by-canonical',
               'Canonical Coverage by Canonical Name::menu-stats-canon-coverage-alpha',
               'Canonical Coverage by Src Count::menu-stats-canon-coverage-count',
               'Canonical Names in Canonical Missing in Canonical2File::menu-stats-canon-missing-c2f',
               'Canonical Names in Local2Canonical Missing in Canonical::menu-stats-canon-missing-l2c',
               'Canonical Names in Canonical2File Missing in Canonical::menu-stats-c2f-missing-canon',
               'Files in Canonical2File Missing in Music Library::menu-stats-canon-missing-music',
               'Canonical Names::menu-stats-canonical-names',
               'Top 100 Titles in Music Index::menu-stats-top-forty',
               ]
    ],
    ['&Database', [
               'Rebuild All Tables::menu-rebuild-all',
               'Rebuild Sheet-Offset Table::menu-rebuild-page-offset',
               'Rebuild Canonical to File Table::menu-rebuild-canon2file',
             # 'Rebuild Source Priority Table::menu-rebuild-source-priority',
               '----',
               'Build Cover Browser Thumbnails (slow for large book library)::make-thumbnails',
               'Scan Audio Library (slow for large audio library)::menu-rebuild-audio',
              ]
    ],

    ['&Index Management', [
               'Process Raw Index Sources::menu-convert-raw-sources',
               '----',
               'Show Page Mismatch and Src Coverage Summary::menu-summary',
               'Show Page Number Differences Summary::menu-page-summary',
               'Show Page Mismatch and Src Coverage Detail::menu-verbose',
                ]
    ],

    [ '&View', [
                'Toggle Index Management Tab::menu-index-mgmt-tabs',
                'Toggle Edit Canonical->File Tab::menu-canon2file-tab',
                'Toggle Edit Command Output Tab::menu-command-output-tab',
               ]
    ],

    ['&Help',  ['Documentation::menu-tutorial',
                'Quick-Start Guide::menu-quickstart-guide',
                'Birdland Guide::menu-configuration-guide',
                'License::menu-license',
              # 'Show Recent &Log::menu-show-recent-log',
              # 'Show Recent &Event Histogram::menu-show-recent-event-histo',
              # 'Current Media File Information::menu-file-info',       # Moved to window in left-panel.
                'Contact::menu-contact',
                'Birdland Website::menu-website',
                'Storage Locations::menu-locations',
                'About Birdland::menu-about',
                'About Qt::menu-about-qt',
              ]
    ],
]
    
# ------------------------------------------------------------------------------
#       Defer interpretation of menu_action to common slot processor

class Main_Menu( QObject ):
    sig_menu_action = Signal( str )

    def __init__( self ):
        s = Store()
        super().__init__()
        s.sigman.register_signal( "sig_menu_action", self.sig_menu_action )

    def build_menu(self, main_window ):
        s = Store()
        menu_bar = main_window.menuBar()

        full_menu = main_menu_definition                    

        if s.Options.debug:
            full_menu += development_menu

        for menu_def in full_menu:
            menu_name = menu_def[0]
            if menu_name == 'None':
                    menu_bar.addMenu( "" )          # /// RESUME Testing on MacOS
                    continue

            menu = menu_bar.addMenu( menu_name )

            for sub_menu in menu_def[1]:
                if sub_menu == '----':
                    menu.addSeparator()
                else:
                    sub_name, menu_action = sub_menu.split( "::" )
                    action = QAction( sub_name, main_window )
                    menu.addAction( action )

                    # menu.menuAction().setMenuRole(QAction.NoRole)       # /// TESTING

                    action.triggered.connect( lambda checked, item=menu_action: s.sigman.emit( "sig_menu_action", item ))
    
# ------------------------------------------------------------------------------
