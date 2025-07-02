#!/usr/bin/python
# ----------------------------------------------------------------------------------
#   WRW 4 Dec 2021
#   Exploring makeing a file/page of YouTube links from a list of titles in fakebook.
#   Migrate to using existing .json files
#   Save YouTube data in .json file, not html, so can build DB with data without going back
#       to Youtube.

#   Install: 'youtube-search-python' from AUR with paru

#   WRW 9 Dec 2021 - A slightly different approach. Build one output file
#       not distinguished by source or book, just by title.
#       Work from distinct titles table

#   Works from titles_distinct. Run this after that is built. Will have to rerun build-tables.py again
#       to build title2youtube table with data obtained here.

#   WRW 26 Mar 2022 - Convert to current conventions of config file and database
#   WRW 23-May-2025 - Split it two with progress logging so can interrupt and restart.

# ----------------------------------------------------------------------------------

from yt_dlp import YoutubeDL

import sys
import os
import json
import gzip
import click
import sqlite3
from pathlib import Path

from fb_config import Config
from fb_utils import FB
from Store import Store
from bl_constants import Const      # Defines values used by Config

# ----------------------------------------------------------------------------------

Progress_File = "~/Uploads/yt-progress.txt"
YouTube_File =  "~/Uploads/yt-data.txt"

# ----------------------------------------------------------------------------------
#   For debugging

def show_results( results ):
    for result in results:
        print( "=============================" )
        print( result[ 'title' ] )
        print( "  link:", result[ 'link' ] )
        print( "  type:", result[ 'type' ] )
        print( "  duration:", result[ 'duration' ] )
        print( "  publishedTime:", result[ 'publishedTime' ] )
        print( "  view count:" )
        print( "    text:", result[ 'viewCount' ][ 'text' ] )
        print( "    short:", result[ 'viewCount' ][ 'short'] )
        print( "  channel:" )
        print( "    name:", result[ 'channel' ][ 'name' ] )
        print( "    id:", result[ 'channel' ][ 'id' ] )
        print( "    link:", result[ 'channel' ][ 'link' ] )
    
        print( "  shelfTitle:", result[ 'shelfTitle' ] )
        print( "  descriptionSnippet:" )
        if result[ 'descriptionSnippet' ]:
            for ds in result[ 'descriptionSnippet' ]:
                print( "    ", ds[ 'text' ] )
    
        if True:
            print( "-----------------------------" )
            for k in result.keys():
                 print( f"       {k}: {result[ k ]}" )
    
        print( "" )

# ----------------------------------------------------------------------------------

class Options():        # Just to hold command-line options
    pass

# ----------------------------------------------------------------------------------

@click.command( context_settings=dict(max_content_width=120) )
@click.option( "-c", "--confdir",                       help="Use alternate config directory" )
@click.option( "-u", "--userdatadir",                   help="Use alternate user-data directory" )
@click.option( "-d", "--database",                      help="Use database sqlite or mysql, default sqlite", default='sqlite' )
@click.option( "-g", "--get",         is_flag=True,     help="Get YouTube links" )
@click.option( "-b", "--build",       is_flag=True,     help="Build YouTube file from links" )

def do_main( confdir, userdatadir, database, get, build ):
    s = Store()
    s.Const = Const()

    if not confdir:
        confdir = s.Const.Confdir                                                                  

    if not userdatadir:
        userdatadir = s.Const.Datadir

    s.conf = Config( confdir, userdatadir )    # OK - appropriate
    s.fb = FB()

    s.conf.get_config()
    s.conf.set_class_variables( )     # Update conf.v data and source <--> src mapping.

    # s.Options = Options()
    # s.Options.confdir = confdir

    # ------------------------------------

    if get:
        do_query( database )
    elif build:
        do_build()

    else:
        print( "Please select -g or -b", file=sys.stderr )
        sys.exit()

# --------------------------------------------------------------

def do_query( database ):

    s = Store()

    match database:
        case 'sqlite':
            s.driver = { 'mysql' : False, 'sqlite' : True, 'fullword' : False }         # always do this early, used elsewhere

        case 'mysql':
            s.driver = { 'mysql' : True, 'sqlite' : False, 'fullword' : False }         # always do this early, used elsewhere

        case _:
            print( f"ERROR: Unexpected --database option value {database}", file=sys.stderr )
            sys.exit(1)

    MYSQL, SQLITE, FULLTEXT = s.driver.values()

    if database == 'mysql':
        s.conf.update_dict()    # Add MYSQL specific items to data dictionary. After s.driver defined.

    # ---------------------------------------------------------------

    # conf = fb_config.Config()
    # conf.set_driver( MYSQL, SQLITE, False )

    os.chdir( os.path.dirname(os.path.realpath(__file__)))      # Run in directory where this lives.

    s.conf.get_config( )
    s.conf.set_class_variables()      # WRW 6 Mar 2022 - Now have to do this explicitly

    # ---------------------------------------------------------------

    if MYSQL:
        import MySQLdb
        conn = MySQLdb.connect( "localhost", s.conf.val( 'database_user' ), s.conf.val( 'database_password' ), s.conf.mysql_database )
        s.c = conn.cursor()
        s.dc = conn.cursor(MySQLdb.cursors.DictCursor)

    elif SQLITE:
        conn = sqlite3.connect( Path( s.conf.user_data_directory, s.conf.sqlite_database ))     # Note: always in data directory
        s.c = conn.cursor()
        s.dc = conn.cursor()
        s.dc.row_factory = sqlite3.Row

    else:
        print( "ERROR: No database type specified", file=sys.stderr, flush=True  )
        sys.exit(1)

    # ---------------------------------------------------------------
    #   WRW 23-May-2025 - Add support to keep track of progress so can
    #   restart without redoing all prior work.
               
    ppath = Path( Progress_File ).expanduser()
    try:
        t = ppath.read_text()
        existing_progress = t.split('\n')
        existing_progress = set( existing_progress )
    except FileNotFoundError:
        existing_progress = set()

    prog_fd = open( ppath, 'a' )

    dpath = Path( YouTube_File ).expanduser()
    data_fd =  open( dpath, 'a' )

    # ---------------------------------------------------------------

    limit = 0
    title_counter = 0
    contents = []

    query = "SELECT title FROM titles_distinct ORDER BY title"
    s.dc.execute( query )
    rows = s.dc.fetchall()
    for row in rows:

        title = row['title']
        if title in existing_progress:
            continue

        links = []

        print( f"{row['title']}")

        # --------------------------------------------------------------
        #   Note that results limit is number following ytsearch below
        #   Increasing to ten took ages, an unreasonable amount of time, possibly a minute.
        #   Leave at 1 for now, should return 'best' match.

        ydl_opts = {
            'socket_timeout': 10,  # seconds
            'quiet' : True,
            'no_warnings': True,
            'skip_download': True,
            'extract_flat': True,  # Speeds up search
            'nocheckcertificate': True, # Saves a little time on handshake
        }

        with YoutubeDL( ydl_opts ) as ydl:
            try:
                t = ydl.extract_info( f"ytsearch10:{title}", download=False)

                results = t[ 'entries' ]
                rlimit = min( 10, len(results) )

                for result in results[ 0:rlimit ]:

                    ytitle = result.get('title' )
                    id = result.get( 'id' )
                    # duration = result.get( 'duration' )       # Not available with 'extract_flat'

                    # t = { 'ytitle' : ytitle, 'duration': duration, 'id' : id }
                    t = { 'ytitle' : ytitle, 'id' : id }
                    links.append( t )
                    print( "///", t )

            except Exception as e:
                (type, value, traceback) = sys.exc_info()
                print( f"YoutubeDL() failed on search for {title}: type: {type}, value: {value}", file=sys.stderr )
                continue

        # --------------------------------------------------------------
        #   WRW 23-May-2025 Write immediately to intermediate output file.

        t = { 'title' : title, 'links' : links }
        json_text = json.dumps( t, indent=2 )
        data_fd.write( json_text )
        data_fd.flush()
        prog_fd.write( title + "\n" )
        prog_fd.flush()

        title_counter += 1
        if limit != 0 and title_counter >= limit:
            break

        # --------------------------------------------------------------

    conn.close()    # WRW 5 June 2022 - Oops, typo, added parens and moved into do_query()

# ----------------------------------------------------------------------------------

def parse_concatenated_json(filepath):
    decoder = json.JSONDecoder()
    items = []

    with open(filepath, 'r') as f:
        content = f.read()

    idx = 0
    while idx < len(content):
        content = content.lstrip()  # skip whitespace
        try:
            obj, end = decoder.raw_decode(content[idx:])
            items.append(obj)
            idx += end
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON at index {idx}: {e}")
            break

    return items

# ----------------------------------------------------------------------------------

def do_build( ):
    s = Store()

    ipath = Path( YouTube_File ).expanduser()

    print( f"Reading {ipath} into memory", file=sys.stderr )
    contents = parse_concatenated_json( ipath )

    # Wrap in a structure if needed
    full_contents = {
        'contents': contents
    }

    full_contents = { 'contents' : contents }

    print( f"Converting memory to json", file=sys.stderr )
    json_text = json.dumps( full_contents, indent=2 )

    opath = Path( s.conf.val( 'youtube_index' ) )
    print( f"Writing json to {opath}", file=sys.stderr )

    with gzip.open( opath, 'wt' ) as ofd:
        ofd.write( json_text )

# ----------------------------------------------------------------------------------

if __name__ == '__main__':
    do_main()

# ----------------------------------------------------------------------------------

