#!/usr/bin/python
# ---------------------------------------------------------------------------
#   WRW 20 Sept 2020 - Found a bunch of csv fakebook indexes at github

#   WRW 12 Mar 2022 - Moved all .csv from subordinate dir to this one
#       for compatibility with python setuptools build process.

# ---------------------------------------------------------------------------

import sys
import os
import csv
import collections
from pathlib import Path

import fb_utils
import fb_config
from Store import Store
from bl_constants import Const

# ---------------------------------------------------------------------------
#   WRW 5 Apr 2022 - Ouch! After going crazy trying to align the offsets 
#   it turns out that the, csv files here have inconsistent formats.
#   Make a book-specific format spec.
#   Value is number of columns, not offset to sheet number.

col_count = {
    '557Standards' : 3,
    'Colorado' : 3,
    'FirehouseJazzBand' : 3,
    'JazzLTD' : 3,
    'KathyBook' : 3,
    'LatinRealBkC' : 3,
    'SJCBookC2018' : 3,
    'cbxmas' : 3,
    'djangoinjune' : 3,
    'newrbk1C' : 2,
    'newrbk2C' : 2,
    'newrbk3C' : 2,
    'nrealbk1d' : 3,
    'parkeromnibookbc' : 3,
    'realbk1' : 3,
    'realbk1h' : 3,
    'realbk2' : 3,
    'realbk2h' : 3,
    'realbk3' : 3,
    'realbk3h' : 3,
    'realbk4h' : 2,
    'realxmasC' : 3,
    'sinatra101C' : 3,
    'standardsrbkC' : 2,
    'swingjamC' : 3,
}

# ---------------------------------------------------------------------------
#   Note, some files have 4th column with page count for title.

Root = 'Raw-Index'

# ---------------------------------------------------------------------------

def proc_file( fb, path, book ):
    base = os.path.basename( path )

    if col_count[ book ] == 3:
        cols = [ 0, 1, 2 ]
        col_names = [ 'title', 'book', 'sheet' ]

    elif col_count[ book ] == 2:
        cols = [ 0, 1 ]
        col_names = [ 'title', 'sheet' ]

    else:
        print( f"ERROR-DEV: Unexpected col_count for book '{book}', {col_count[ book]}", flush=True )

    # df = pd.read_csv( path, usecols=cols, names=col_names, header=None, dtype=str, sep=','  )
    # df.sheet = df.sheet.fillna( '-' )
    # for n, s in df.iterrows():
    lineno = 0

    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f, fieldnames=col_names)
        lineno = 0
        for row in reader:
            lineno += 1
            # Ensure 'sheet' has a fallback value
            row['sheet'] = row.get('sheet') or '-'
            title = row['title']
            item = {
                'title' : row[ 'title' ],
                'sheet' :  row[ 'sheet' ],
                'file'  : Path( path ).name,
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
    
    excludes = [ x.strip() for x in Path( 'Local-Exclusions.txt' ).read_text().split('\n') ]
    
    included_names = set()
    omitted_names = set()
    
    for dir, dirs, files in os.walk( Root ):
        print( f'Directory: {dir}', flush=True  )
        for file in files:
            if file.startswith( ',' ):
                continue
    
            path = os.path.join( dir, file )
            base, ext = os.path.splitext(path)
            book = os.path.basename( base )
    
            if ext == '.csv':
                if book not in excludes:
                    # print( f'  {book}', flush=True )
                    proc_file( fb, path, book )
                    included_names.add( book )
    
                else:
                    omitted_names.add( book )
                    print( f'  {book} excluded', flush=True )
    
    fb.save( 'MikelNelson', 'Mik' )
    t = '\n   '.join( sorted( included_names ) )
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
