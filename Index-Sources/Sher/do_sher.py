#!/usr/bin/python
# ---------------------------------------------------------------------------
#   WRW 20 Sept 2020 - Found a bunch of csv fakebook indexes at github
# ---------------------------------------------------------------------------

#   WRW 28 Apr 2022 - Want to edit input but tsv is problematic. Converted to csv with:

# awk 'BEGIN { FS="\t"; OFS="," } {
#   rebuilt=0
#   for(i=1; i<=NF; ++i) {
#     if ($i ~ /,/ && $i !~ /^".*"$/) {
#       gsub("\"", "\"\"", $i)
#       $i = "\"" $i "\""
#       rebuilt=1
#     }
#   }
#   if (!rebuilt) { $1=$1 }
#   print
# }' sher.tsv > sher.csv

import sys
import os
import csv

import fb_utils
import fb_config
from pathlib import Path
from Store import Store
from bl_constants import Const

# ---------------------------------------------------------------------------

# Ifile = 'sher.tsv'
Ifile = Path( 'Raw-Index', 'sher.csv' )

# ---------------------------------------------------------------------------

def proc_file( fb, ifile ):

    omitted_names = set()
    included_names = set()
    local_names = set()

    cols = [0, 1, 2, 3 ]
    col_names = [ 'title', 'composer', 'book', 'sheet' ]

    # df = pd.read_csv( ifile.as_posix(), usecols=cols, names=col_names, header=None, dtype=str )
    # df.sheet = df.sheet.fillna( '-' )
    # df.composer = df.composer.fillna( '-' )
    # local_names = df.book.unique().tolist()
    # for n, s in df.iterrows():

    excludes = [ x.strip() for x in Path( 'Local-Exclusions.txt' ).read_text().split('\n') ]

    with open(ifile.as_posix(), newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f, fieldnames=col_names)

        for row in reader:
            book = row[ 'book' ]
            local_names.add( book )

        for x in excludes:                  # Remove file names in Local-Exclusions.text from local_names
            if x in local_names:
                local_names.remove(x)

    with open(ifile.as_posix(), newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f, fieldnames=col_names)
        lineno = 0

        for row in reader:
            lineno += 1
            # Ensure 'sheet' has a fallback value
            row['sheet'] = row.get('sheet') or '-'
            row['composer'] = row.get('composer') or '-'

            lineno += 1
            book = row[ 'book' ]
            if book in local_names:
                item = {
                    'title' : row[ 'title' ],
                    'composer' : row[ 'composer' ],
                    'sheet' :  row[ 'sheet' ],
                    'file'  : ifile.name,
                    'line'  : lineno,
                }
                fb.add( book, item )
                included_names.add( book )

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
    fb.save( 'Sher', 'Shr' )

# ---------------------------------------------------------------------------

def main():
    do_main()

# ---------------------------------------------------------------------------

if __name__ == '__main__':
    do_main()

# ---------------------------------------------------------------------------
