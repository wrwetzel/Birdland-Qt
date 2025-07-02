#!/usr/bin/python
# ---------------------------------------------------------------------------
#   WRW 20 Sept 2020 - Found a bunch of csv fakebook indexes at github
#   WRW 9 Jan 2022 - Change name from Splitter to Jason Donenfeld

# ---------------------------------------------------------------------------

import os
import sys
from pathlib import Path

import fb_utils
import fb_config
from Store import Store
from bl_constants import Const

# ---------------------------------------------------------------------------
#   Note, some files have 4th column with page count for title.

Ifile = Path( 'Raw-Index', 'index.raw' )

# ---------------------------------------------------------------------------

def proc_file( fb, ifile ):

    excludes = [ x.strip() for x in Path( 'Local-Exclusions.txt' ).read_text().split('\n') ]

    omitted_names = set()
    included_names = set()

    with open( ifile ) as ifd:
        lineno = 0
        for line in ifd:
            lineno += 1
            line = line.strip()
            words = line.split()

            sheet = words[ -1 ]
            book = words[ -2 ]

            #   WRW 1 Mar 2022 - Process all books unless in excluded list.

            if book not in excludes:
                included_names.add( book )
                title = " ".join( words[ 0:-2] )

                item = {
                    'title' : title,
                    'sheet' : sheet,
                    'file'  : ifile.name,
                    'line'  : lineno,
                }

                fb.add( book, item )
            else:
                omitted_names.add( book )

    t = '\n   '.join( sorted( included_names ))
    print( f"Included books: \n   {t}", file=sys.stderr, flush=True )

    t = '\n   '.join( omitted_names )
    print( f"Omitted books: \n   {t}", file=sys.stderr, flush=True )

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
    
    proc_file( fb, Ifile )
    fb.save( 'JasonDonenfeld', 'Jad' )

# ---------------------------------------------------------------------------

def main():
    do_main()

# ---------------------------------------------------------------------------

if __name__ == '__main__':
    do_main()

# ---------------------------------------------------------------------------
