#!/usr/bin/env python
# ---------------------------------------------------------------------------
#   birdstart.py - WRW 28-Mar-2025 - An dispatch multiple
#       python programs from within one pyinstaller bundle.
# ---------------------------------------------------------------------------

import os
import sys
from pathlib import Path
from contextlib import contextmanager
import traceback

# -----------------------------------------------------------

@contextmanager
def myPrep( source ):
    old_cwd = Path.cwd()

    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        path = Path(__file__).resolve().parent / "Index-Sources" / source       # The frozen layout does not include 'src', just flat
        path = Path( sys._MEIPASS, path )

    else:
        path = Path(__file__).resolve().parent.parent / "Index-Sources" / "AdamSpiers"

    os.chdir( path )
    old_sys_path = sys.path.copy()
    sys.path.insert( 0, str( path ))

    try:
        yield

    finally:
        os.chdir( old_cwd )
        sys.path = old_sys_path
        sys.exit(0)

# -----------------------------------------------------------

def main():
    if len( sys.argv ) > 1:
        sys.argv.pop(0)
        if sys.argv[0] == "build_tables":
            import build_tables
            build_tables.main()

        elif sys.argv[0] == "diff_index":
            import diff_index
            diff_index.main()

        # -------------------------------------

        elif sys.argv[0] == "do_adamspiers":
            with myPrep( 'AdamSpiers' ):
                import do_adamspiers
                do_adamspiers.main()

        elif sys.argv[0] == "do_buffalo":
            with myPrep( 'Buffalo' ):
                import do_buffalo
                do_buffalo.main()

        elif sys.argv[0] == "do_extractedindex":
            with myPrep( 'ExtractedIndex' ):
                import do_extractedindex
                do_extractedindex.main()

        elif sys.argv[0] == "do_jasondonenfeld":
            with myPrep( 'JasonDonenfeld' ):
                import do_jasondonenfeld
                do_jasondonenfeld.main()

        elif sys.argv[0] == "do_mikelnelson":
            with myPrep( 'MikelNelson' ):
                import do_mikelnelson
                do_mikelnelson.main()

        elif sys.argv[0] == "do_sher":
            with myPrep( 'Sher' ):
                import do_sher
                do_sher.main()

        elif sys.argv[0] == "do_skrivarna":
            with myPrep( 'Skrivarna' ):
                import do_skrivarna
                do_skrivarna.main()

        elif sys.argv[0] == "do_stompbox":
            with myPrep( 'StompBox' ):
                import do_stompbox
                do_stompbox.main()

        elif sys.argv[0] == "do_user":
            with myPrep( 'User' ):
                import do_user
                do_user.main()
        else:
            print( f"ERROR: Unexpected command '{sys.argv[0]}' in birdstart.py" )
            sys.exit(1)

    else:
        # WRW 22-May-2025 - For bundling with vlc in Linux. Vlc binaries addeded to 'lib' in .spec file.

        # if getattr( sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        #     lib_path = Path( sys._MEIPASS, "lib" )
        #     os.environ['LD_LIBRARY_PATH'] = str(lib_path) + ':' + os.environ.get('LD_LIBRARY_PATH', '')

        import birdland_qt
        birdland_qt.main()

if __name__ == "__main__":
    #   WRW 13-May-2025 - getting an immediate failure on older Linux, add try/except
    #       to find out why.

    try:
        main()

    except Exception:
        (extype, value, xtraceback) = sys.exc_info()
        print( f"ERROR in main() type: {extype}, value: {value}", file=sys.stderr )
        traceback.print_exc()               # WRW 21-Apr-2025 - Want entire stack as if not caught.


# ---------------------------------------------------------------------------
