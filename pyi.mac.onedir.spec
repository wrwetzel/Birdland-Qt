# ----------------------------------------------------------------------------------------
#   pyi.mac.onedir.spec - WRW 26-Mar-2025  - finally trying to package birdland-qt

#   Called by build.mac.onedir.sh

#   WRW 4-May-2025 - Trying onedir to help building a .dmg file.

# ----------------------------------------------------------------------------------------
#   Trying to executable reduce size:
#   Little benefit, reversed all, back to original.

#       strip=True
#           Saved about 7Mb

#       a.datas = [d for d in a.datas if 'PySide6/Qt/translations' not in d[0]]                                    
#           Saved about 2Mb

#       Excluding a list of likely unused modules recommended by chat did nothing.

#   exclude_binaries:
#        When set to True:
#           "Exclude binary dependencies from the archive file (EXE), to be collected
#           and bundled later by COLLECT()."
        
#        When set to False (default):
#           "Embed binary files (from a.binaries) directly into the EXE file."

#           This behavior makes sense in --onefile mode, where all assets are packed
#           into a single file but it breaks --onedir assumptions if you're
#           also passing those binaries to COLLECT().

# ----------------------------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_submodules
import os
import sys

# Add the src directory to the module search path
# spec_dir = os.path.abspath(os.getcwd())  # fallback to current working directory
# src_path = os.path.join(spec_dir, 'src')
# sys.path.insert(0, src_path)

spec_dir = os.path.abspath(os.path.dirname('.'))  # or use os.getcwd()
sys.path.insert(0, spec_dir)

from src import fb_version

# ----------------------------------------------------------------------------------------

sys.setrecursionlimit(3000)
block_cipher = None

# ----------------------------------------------------------------------------------------

def collect_data_files( src_dir, dest_subdir=""):
    """
    Recursively collects (dest_path, src_path) tuples for use in PyInstaller .spec file.

    :param src_dir: Source directory to walk through (absolute or relative)
    :param dest_subdir: Subdirectory inside the bundle to place files (optional)
    :return: List of tuples for the `datas` entry
    """

    data_files = []
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            if ( file.startswith( ',' ) or
                 file.startswith( '.e' ) or
                 file.endswith( '.py' ) ):
                continue

            full_src_path = os.path.join(root, file)
            # Preserve folder structure inside the bundle
            relative_path = os.path.relpath(full_src_path, src_dir)
            full_dest_path = os.path.join(dest_subdir, os.path.dirname(relative_path))
            data_files.append( (full_src_path, full_dest_path ) )

    return data_files

# ----------------------------------------------------------------------------------------

# Paths
# project_root = os.path.abspath(os.path.dirname(__file__))

project_root = os.path.abspath(os.getcwd())
src_dir = os.path.join(project_root, "src")

# Collect all .py files manually if needed
# e.g. src/, src/utils/, src/models/, etc.

source_files = [
    os.path.join( src_dir, "birdstart.py"),             # Main entry point, dispatches to different files
    os.path.join( src_dir, "birdland_qt.py"),
    os.path.join( src_dir, "build_tables.py"),
    os.path.join( src_dir, "diff_index.py"),
    os.path.join( src_dir, "AudioPlayer_Vlc.py"),
    os.path.join( src_dir, "bl_actions.py"),
    os.path.join( src_dir, "bl_analysis.py"),
    os.path.join( src_dir, "bl_canon2file_tab.py"),
    os.path.join( src_dir, "bl_connections.py"),
    os.path.join( src_dir, "bl_constants.py"),
    os.path.join( src_dir, "bl_index_management_tab.py"),
    os.path.join( src_dir, "bl_left_panel.py"),
    os.path.join( src_dir, "bl_main_menu.py"),
    os.path.join( src_dir, "bl_main_tabbar.py"),
    os.path.join( src_dir, "bl_main_window.py"),
    os.path.join( src_dir, "bl_media.py"),
    os.path.join( src_dir, "bl_menu_actions.py"),
    os.path.join( src_dir, "bl_metadata_panel.py"),
    os.path.join( src_dir, "bl_resources_rc.py"),
    os.path.join( src_dir, "bl_search_panel.py"),
    os.path.join( src_dir, "bl_style.py"),
    os.path.join( src_dir, "bl_tables.py"),
    os.path.join( src_dir, "bl_title_panel.py"),
    os.path.join( src_dir, "fb_config.py"),
    os.path.join( src_dir, "fb_dialog.py"),
    os.path.join( src_dir, "fb_local2canon_mgmt.py"),
    os.path.join( src_dir, "fb_menu_stats.py"),
    os.path.join( src_dir, "fb_search.py"),
    os.path.join( src_dir, "fb_setlist.py"),
    os.path.join( src_dir, "fb_title_correction.py"),
    os.path.join( src_dir, "fb_utils.py"),
    os.path.join( src_dir, "fb_version.py"),
    os.path.join( src_dir, "MyGroupBox.py"),
    os.path.join( src_dir, "MyTable.py"),
    os.path.join( src_dir, "PDF_Viewer.py"),
    os.path.join( src_dir, "SignalManager.py"),
    os.path.join( src_dir, "Store.py"),

    "Index-Sources/AdamSpiers/do_adamspiers.py",
    "Index-Sources/Buffalo/do_buffalo.py",
    "Index-Sources/ExtractedIndex/do_extractedindex.py",
    "Index-Sources/JasonDonenfeld/do_jasondonenfeld.py",
    "Index-Sources/MikelNelson/do_mikelnelson.py",
    "Index-Sources/Sher/do_sher.py",
    "Index-Sources/Skrivarna/do_skrivarna.py",
    "Index-Sources/StompBox/do_stompbox.py",
    "Index-Sources/User/do_user.py",
]


# ----------------------------------------------------------------------------------------
#   Add data files (relative path inside bundle, source path)
#       Format: (source_file_path, target_directory_in_bundle)

data_files = [
]

for item in collect_data_files( os.path.join(project_root, 'Book-Lists'), 'Book-Lists' ):
    data_files.append( item )

for item in collect_data_files( os.path.join(project_root, 'Canonical'), 'Canonical' ):
    data_files.append( item )

for item in collect_data_files( os.path.join(project_root, 'Index-Sources'), 'Index-Sources' ):
    data_files.append( item )

# for item in collect_data_files( os.path.join(project_root, 'Music-Index'), 'Music-Index' ):
#     data_files.append( item )

for item in collect_data_files( os.path.join(project_root, 'YouTube-Index'), 'YouTube-Index' ):
    data_files.append( item )

# ----------------------------------------------------------------------------------------
# Collect hidden modules (useful for PySide6 sometimes)
#   hiddenimports = collect_submodules('PySide6')
#   Tested below on python and it looks OK.

hiddenimports = [
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
    "PySide6.QtMultimedia",
#     "pkg_resources._vendor.packaging",    # Not found, produces an ERROR message.
]

a = Analysis(
    source_files,                   # birdstart.py is first
    pathex=[ src_dir ],
    binaries=[],
    datas=data_files,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=['PyQt5', 'PyQt6', "pkg_resources", "setuptools", "jaraco", "jaraco.text", 
              "pandas", "numpy", "tkinter" ],
    cipher=block_cipher,
)

#   a.binaries[] format:
#       (target_filename, source_path, type)

a.binaries += [
    ( 'fullword.cpython-313-x86_64-linux-gnu.so',
     os.path.join( src_dir, 'fullword.cpython-313-x86_64-linux-gnu.so' ),
    'BINARY' )
]

# ----------------------------------------------------------------------------------------
#   WRW 6-May-2025 - Finally solved a problem causing the executable for a onedir build
#       to fail. The exclude_binaries parameter was False. Wasted almost two days on it.

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,              # Smoking gun! exclude_binaries=False caused a big, big headache.
    name='birdland_qt',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,                      # True if you want to see a console for output.

    disable_windowed_traceback=False,   # These five copied from .spec file built automatically for simple test
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='src/Icons/Saxophone.icns',    # WRW 4-May-2025 - must be .icns on mac, a collection of many sizes of icon.
)

#   Include Collect() for onedir

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='birdland_qt.dist'
)

#   This is just for MacOS

app = BUNDLE(
    coll,
    name='birdland_qt.app',
    icon='src/Icons/Saxophone.icns',        # WRW 4-May-2025 - must be .icns on mac
    bundle_identifier=None,

    info_plist={
        'CFBundleDisplayName': 'Birdland-Qt',
        'CFBundleName': 'Birdland-Qt',
        'CFBundleVersion' : f"{fb_version.__version__}.{fb_version.__build__}",
        'CFBundleShortVersionString' : f"{fb_version.__version__}",
    },
)


