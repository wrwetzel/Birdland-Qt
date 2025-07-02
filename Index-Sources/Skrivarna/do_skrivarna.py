#!/usr/bin/python
# ---------------------------------------------------------------------------
#   WRW 20 Sept 2020 - Found a bunch of csv fakebook indexes at github

#   Not sure how I got the links-related files, probably manually.
#   Made books.txt and books-unique.txt manually.

#   WRW 12 Mar 2022 - Convert to flat directory for compatibility with
#       python setuptools build process.

#   WRW 6 Apr 2022 - I was going crazy last night trying to harmonize the indexes for
#   'Real Book Vol 2 - Orig'. I'd make a change to the Sheet-Offsets.txt and other
#   pages got shifted. Nothing made sense. Fatigue didn't help. While I'm filtering
#   books with the 'exclude' file here they were leaking back in with the glob() because
#   some of the excluded names are subsets of the included ones and matched. 
#   The leaked books conflicted with the intended ones.
#   A single '_' solved the problem. Not a big deal as I found a couple of other problems
#   along the way.

# ---------------------------------------------------------------------------

import os
import sys
import glob
import csv
from pathlib import Path

import fb_utils
import fb_config
from Store import Store
from bl_constants import Const

# ---------------------------------------------------------------------------
#   Note, some files have 4th column with page count for title.

Idir = 'Raw-Index'
Books = 'books-unique.txt'

# ---------------------------------------------------------------------------
#        page;title;last;first;aka;style;tempo;signature;comment;
#   WRW 30 Mar 2020 - Had header=1, should be 0. There is one line of header we are ignoring.

def proc_file( fb, path, book ):

    cols = [0, 1, 2, 3, 4, 5, 6, 7 ]
    col_names = [ 'sheet', 'title', 'last', 'first', 'aka', 'style', 'signature', 'comment' ]

    if False:
        # df = pd.read_csv( path, usecols=cols, names=col_names, header=0, dtype=str, sep=';'  )

        # df[ 'first' ] = df[ 'first' ].fillna(0).infer_objects(copy=False)
        # df[ 'last' ] = df[ 'last' ].fillna(0).infer_objects(copy=False)

        #   WRW 20-Mar-2025 - got errors from pandas.
        #   Downcasting object dtype arrays on .fillna, .ffill, .bfill is deprecated and will change in a future version.
        #   Chat recommended fix. Worked fine.

        if df["first"].dtype == "object":
            df["first"] = df["first"].fillna("0").astype(str)  # Keep as string
        else:
            df["first"] = df["first"].fillna(0).astype(df["first"].dtype)  # Preserve original dtype

        if df["last"].dtype == "object":
            df["last"] = df["last"].fillna("0").astype(str)  # Keep as string
        else:
            df["last"] = df["last"].fillna(0).astype(df["last"].dtype)  # Preserve original dtype

        df.sheet = df.sheet.fillna( '-' )
        # for n, s in df.iterrows():

    # ------------------------------------------------------------

    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f, fieldnames=col_names,  delimiter=';')
        lineno = 1                      # Start at one because of header on first line.
        header = next(reader)           # Eat the header

        for row in reader:
            lineno += 1
            # Ensure 'sheet' has a fallback value
            row['first'] = row.get('first') or '0'
            row['last'] = row.get('last') or '0'
            row['sheet'] = row.get('sheet') or '-'
            if not row[ 'title' ]:
                continue

            lineno += 1
            composer = ''
            if row[ 'last' ]:
                composer = row[ 'last' ]
            if row[ 'first' ]:
                if composer:
                    composer = composer + " " + row[ 'first' ]
                else:
                    composer = row[ 'first' ]

            item = {
                'title' : row[ 'title' ],
                'sheet' :  row[ 'sheet' ],
                'composer' : composer,
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
    omitted_names = set()
    included_names = set()
    
    with open( Books ) as bookfd:
        for book in bookfd:
            book = book.strip()
            if book not in excludes:
                included_names.add( book )
                for file in glob.glob( f'{Idir}/{book}_*.pdfb' ):       # WRW 6 Apr 2022 - Adding the '_' resolved an issue bugging me.
                    proc_file( fb, file, book )
            else:
                omitted_names.add( book )
    
    fb.save( 'Skrivarna', 'Skr' )
    
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
