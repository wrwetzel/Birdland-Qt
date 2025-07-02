#!/usr/bin/python
# ---------------------------------------------------------------------------
#   WRW 20 Sept 2020 - Found a bunch of csv fakebook indexes

#  wget --recursive --no-parent http://diystompboxes.com/unrealbook/csvindexes/

#   Cleaned up resultant directories by hand. Removed USER stuff, LibreOffice
#       stuff.

#   WRW 12 Mar 2022 - Converted to flat directory structure for compatibility
#       with python setuptools packaging.

# ---------------------------------------------------------------------------

import sys
import os
import csv
from pathlib import Path

import fb_utils
import fb_config
from Store import Store
from bl_constants import Const

# ---------------------------------------------------------------------------
#   Note, some files have 4th column with page count for title.

Root = 'Raw-Index'

# ---------------------------------------------------------------------------
#   WRW 30 Mar 2022 - Changed header=0 to header=None.

def proc_file( fb, path, book ):

    cols = [0, 1, 2 ]
    col_names = [ 'title', 'book', 'sheet' ]

    # df = pd.read_csv( path, usecols=cols, names=col_names, header=None, dtype=str, sep=','  )
    # lineno = 0
    # for n, s in df.iterrows():
    #    pass

    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f, fieldnames=col_names)
        lineno = 0
        for row in reader:

            lineno += 1
            item = {
                'title' : row[ 'title' ],
                'sheet' : row[ 'sheet' ],
                'file'  : path.name,
                'line'  : lineno,
            }

            fb.add( book, item )

# ---------------------------------------------------------------------------

def do_main():
    
    s = Store()
    s.Const = Const()
    confdir = sys.argv[1]
    userdatadir = sys.argv[2]

    s.conf = fb_config.Config( confdir, userdatadir )         # Used in fb.load_corrections()
    s.conf.get_config()
    s.conf.set_class_variables()
    
    fb = fb_utils.FB()
    fb.load_corrections()
    
    omitted_names = set()
    included_names = set()
    
    excludes = [ x.strip() for x in Path( 'Local-Exclusions.txt' ).read_text().split('\n') ]
    
    for dir, dirs, files in os.walk( Root ):
        for file in files:
    
            path = Path( dir, file )
            ext = path.suffix
            name = path.name
            stem = path.stem
    
            if stem.startswith( ',' ):
                continue
    
            if ext == '.csv':
                if stem not in excludes:
                    proc_file( fb, path, stem )
                    included_names.add( stem )
                else:
                    omitted_names.add( stem )
    
    fb.save( 'StompBox', 'Stm' )
    
    t = '\n   '.join( sorted( included_names ))
    print( f"Included books: \n   {t}", file=sys.stderr, flush=True )
    
    t = '\n   '.join( omitted_names )
    print( f"Omitted books: \n   {t}", file=sys.stderr, flush=True )
    
# ---------------------------------------------------------------------------

def main():
    do_main()

# ---------------------------------------------------------------------------

if __name__ == '__main__':
    do_main()

# ---------------------------------------------------------------------------
