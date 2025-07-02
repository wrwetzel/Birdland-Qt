#!/usr/bin/python
# ---------------------------------------------------------------------------
#   WRW 21 Sept 2020 - fb_utils.py - utilities for building fakebook index
# ---------------------------------------------------------------------------

import json
import os
import sys
import glob
import re
import subprocess
from pathlib import Path
import gzip
import csv
from unidecode import unidecode

from PySide6.QtCore import QObject, QThread, Signal, Slot, Qt
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QPushButton, QLabel

from PySide6.QtCore import QSize
from PySide6.QtGui import QPixmap, QPainter, QColor, QIcon
from PySide6.QtSvg import QSvgRenderer

from Store import Store
from bl_constants import MT

try:                            # WRW 3 May 2022 - in case there is a problem with fullword module in some environments.
    import fullword             # Make bogus name 'xfullword' to test missing module
    Fullword_Available = True

except ImportError:             # WRW 13 June remove 'as e' for pylint
  # print( "OPERATIONAL: import fullword failed, using alternative", file=sys.stderr )
    Fullword_Available = False

# WRW 7-Apr-2025 - Fullword NG for serching piano roll midi because of filename structure.
#   Make use of it conditional on arg to get_fulltext()

# ---------------------------------------------------------------------------
#   Replace spaces with underscores and path separators with dash so can
#       keep these files in flat directory hierarchy.
#   WRW 14-May-2025 - Replace unicode with nearest ascii. Had an issue with unicode on Mac:
#       DL-Music_Books/Film/Am*lie_Soundtrack_YannTiersen.pdf

def clean_filename( name ):
    name = name.replace( " ", "_" )
    name = name.replace( "/", "-" )
    name = name.replace( ":", "" )          # /// RESUME - a few files have colons, just remove them.
    name = unidecode( name )                # WRW 14-May-2025
    return name

# ---------------------------------------------------------------------------
#   Replace %s with ? if using SQLITE

def fix_query( query ):
    s = Store()
    MYSQL, SQLITE, FULLTEXT = s.driver.values()

    if SQLITE:
        query = query.replace( '%s', '?' )
    return query

# ---------------------------------------------------------------------------
#   WRW 1-Feb-2025 Convert to singleton class so don't have to pass around s.fb
#       Only change is the little code at top.
#   
#   WRW 4-Feb-2025
#       FB() subclasses QObject so that FB can be given an object name, which
#       is needed for connecting to signals FB() emits.
#       This caused error with multiple inits of QObject, added _initialized flag
#       to suppress multiple QObject inits.
#       FB() must be instiated before connecting signals with Make_Connections().

class FB( QObject ):
    search_results_signal = Signal( str )                                      

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    # ----------------------------------------------------------

    def __init__( self ):
        if not hasattr( self, '_initialized' ):
            super().__init__()
            self._initialized = True    # Prevent multiple calls to super().__init__(), multiple QObject issue.

            s = Store()
            s.Const.Fullword_Available = Fullword_Available     # Defined in global context, don't want s in that.

            # ----------------------------------------------------

            self.books = {}
            self.music_files = {}
            self.log_data = []
            self.log_histo_data = {}
            self.svgRegistry = []           # WRW 10-Apr-2025 - so can redraw svg icons when theme changes
            self.groupBoxRegistry = []      # WRW 11-Apr-2025 - so can adjust group box border by theme
            self.saveIconColor = None

            # self.doc = None
            # self.cur_page = None
            # self.zoom = 1
            # self.zoom_set = False
            # self.fit = 'Height'
            # self.config_file = None
            # self.save_music_file = None

            # ----------------------------------------------------

            #   For testing fb_title_correction.py on the raw data.
            #       Set log below
            #       build-tables.py --convert_raw

            Show_Log = True
            Show_Log = False        # True to save log of corrections. Necessary to do it here as later logging is on clean data.

            if Show_Log:            # /// WRW 23-Mar-2025 ENCODING
                self.corrections_log  = open( "/tmp/Title-corrections.txt", "a", encoding='utf-8' )   # Remember to clear file before each execution of birdland.py
            else:
                self.corrections_log  = None

    # ------------------------------------------------------------------------
    #   Set configuration parameters in class variables.
    #   This is vestigal from when the parameters were included in this module.
    #   Eventually migrate to referencing conf.v directly. NO! conf.val( 'config-id' )

    # ------------------------------------------------------------------------
    #   Only used by add() for source-specific do_*.py, don't bother loading otherwise.
    #   WRW 14 Apr 2022 - Got broader corrections file work done. Want to include canonical
    #   in corrections file for titles corrections incase needed later.

    def load_corrections( self ):
        s = Store()
        self.corrections = {}

        for cfile in [
                Path( s.conf.val( 'corrections' )).with_suffix( '.A.txt' ),      # Built in fb_index_diff.py
                Path( s.conf.val( 'corrections' )).with_suffix( '.B.txt' )       # Built in build_tables.py build_the_corrections_file()
            ]:

            line_counter = 0
            with open( cfile, 'rt', encoding='utf-8'  ) as fd:       # /// WRW 23-Mar-2025 ENCODING
                for line in fd:
                    line_counter += 1
                    cnt = line.count( '|' )
                    if cnt == 2:
                        orig, corrected, canonical = line.split( '|' )
                    elif cnt == 1:
                        orig, corrected = line.split( '|' )
                    else:
                        print( f"ERROR: Unexpected field count {cnt} on line {line_counter} in correction file {str(cfile)}", file=sys.stderr )
                        sys.exit(1)

                    orig = orig.strip()
                    corrected = corrected.strip()
                    self.corrections[ orig ] = corrected

    # ----------------------------------------
    #   WRW 16-Mar-2026 - Had to add get_driver() back when tried to build database.
    #   Used in bl_menu_actions.py to run build_tables. Returns single value for driver.

    def get_driver( self ):
        s = Store()
        MYSQL, SQLITE, FULLTEXT = s.driver.values()

        if MYSQL:
            return 'mysql'
        if SQLITE:
            return 'sqlite'
        return None

    # ------------------------------------------------------------------------

    def get_fullword_available( self ):
        s = Store()
        return s.Const.Fullword_Available

    # ------------------------------------------------------------------------
    #   WRW 15 Feb 2022 - An another approach to full-text matching without using Sqlite 'USING fts5()'
    #       Either I'm missing something or fulltext is not working well in Sqlite.

    #       Quoted strings match exactly.
    #       Otherwise match all words.

    #       Save, now doing parameter substitution and don't need this:
    #           s = s.replace( "'", "''" )      # Escape single quote with ''
    #           s = s.replace( '\\', '\\\\' )   # Escape backslash with \\ so don't escape single quote when at end of field.

    #   From sqlite3 documentation:
    #       The REGEXP operator is a special syntax for the regexp() user
    #       function.  No regexp() user function is defined by default and so use of
    #       the REGEXP operator will normally result in an error message.  If an
    #       application-defined SQL function named "regexp" is added at run-time, then
    #       the "X REGEXP Y" operator will be implemented as a call to "regexp(Y,X)".

    #   Experimental pseudo fullword matching attempt. This has the potential to be really cool as
    #       I can tailor it specifically to the application.

    # ----------------------------------------
    #   WRW 16 Feb 2022 - I had a lot of problems with Sqlite3 select fulltext. Strange results and
    #       text-specific, search-string failures. It seem to improve as I cleaned up the code but
    #       still no clear idea of the cause of the failures, no useful error messages. Perhaps
    #       an issue with having multiple tables, one for normal search, one for fulltext search? Not sure.
    #       In desperation I tried other approaches. LIKE is fast but does not deal with punctuation.
    #       My_match() is quite a bit slower but works well. Perhaps Settings option to limit what tables
    #       are searched? No. Implemented my_match() in C, called from my_match_c(). That is faster and works great.
    #       Have not implemented ignore_words in that yet. Maybe never.

    # ----------------------------------------
    #   Match search string 'words' against column data 'data'. Return True if match.
    #       data: filename, song title
    #       words: 'love me tender'
    #   Keep this as may want to use it for testing later.

    def my_match( self, column, value ):
        ignore_words =  set( ['mid', 'pdf'] )                        
        column = set( re.split( r'\s|\.|/|,', column.lower() ))      # Split column on space . / , chars.
        value = value.lower().split()
        for val in column:
            if val in ignore_words:     # Ignore extensions on file names.
                return False
        for word in value:
            if word not in column:
                return False
        return True                 # True only if all elements of column match all elemnts of the search string.

    # ----------------------------------------
    #   Match search string 'value' against column data 'column'. Return True if match.
    #       data: filename, song title
    #       words: 'love me tender'

    #   WRW 18 Feb 2022 - Implemented my_match() in C as an external module. Works great, faster than Python.
    #   This is called by Sqlite during matching when 'WHERE my_match_c( column, value )" appears in query

    def my_match_c( self, column, value ):

        try:
            return fullword.match( column, value )

        except Exception:                                  # TESTING, no, keep, may generate exception on unexpected data length.
            (extype, value, traceback) = sys.exc_info()
            print( f"ERROR on my_match_c(), type: {extype}, value: {value}", file=sys.stderr )
            print( f"  Column: {column}", file=sys.stderr  )
            print( f"  Value: {value}", file=sys.stderr  )
            return False

    # ----------------------------------------
    #   WRW 16 Feb 2022 - Include this along with create_function() in do_main() to add SELECT REGEXP support.
    #   Was slow and never fully implemented.

    def regexp( self, y, x ):
        return bool( re.search(y, x) )
      # return True if re.search(y, x) else False

    # ----------------------------------------
    #   Another implementation

    # def regexp(expr, item):
    #   reg = re.compile(expr)
    #   t = reg.search(item)
    #   if t:
    #       print( item )
    #       print( expr )
    #   return reg.search(item) is not None

    # ----------------------------------------
    #   Called from do_query...() functions in birdland.py.
    #   Return a where clause and data for parameter substitution.
    #   Function my_match_c() is called by Sqlite when matching.
    #   Note: This ONLY used when SQLITE is True and FULLTEXT is False, which is the default case.
    #       It is never used when MYSQL is True.

    #   match_type = "simple-like"    # Select one of several approaches here. Keep if ever want to evaluate others again.
    #   match_type = "regexp"
    #   match_type = "like"
    #   match_type = "my_match"
    #   match_type = "my_match_c"

    def get_fulltext( self, col, ss, full=True ):          # WRW 29-Mar-2025 - change s to ss to avoid conflict with s = Store()
        s = Store()

        if full==True and s.Const.Fullword_Available:          # WRW 3 May 2022 - So can proceed if problem with availability of fullword module.
            match_type = "my_match_c"
        else:
            match_type = "like"

        ss = ss.strip()

        # ----------------------------------------------
        # Quoted strings match exactly for any match type.

        if( ss[0] == "'" and ss[-1] == "'" or
            ss[0] == '"' and ss[-1] == '"' ):
            w = ss[1:-1]                     # Remove leading and trailing quote
            return f"{col} = ? COLLATE NOCASE", [w]

        # ----------------------------------------------
        #   This is best and fast. Same as below but in C.

        elif match_type == "my_match_c":
            return f"my_match_c( {col}, ? )", [ss]

        # ----------------------------------------------
        #   This matches space-separated words.
        #       Faster than REGEXP and it works! Looks good.
        #       Add punctuation to this if ever want to use it in production.
        #   Found one-word issue with 'aparecida'.
        #   Remember, LIKE is case insensitive. Hence COLLATE NOCASE only on '=' match.
        #   Don't ignore some chars on value because they are in column and can't be ignored there as
        #       is possible with fullword module. Thus, no match when special chars in column.
        #       w = re.sub( '\"|\!|\?|\(|\)', '', w )  # Ignore same chars as in fullword module.

        elif match_type == "like":
            data = []
            query = []
            for w in ss.split():
                query.append( f"({col} = ? COLLATE NOCASE OR {col} LIKE ? OR {col} LIKE ? OR {col} LIKE ?)" )
                data.append( w )                    # One word title
                data.append( f"% {w}" )             # At end of line, preceeded by space
                data.append( f"{w} %" )             # At beginning of line, followed by space
                data.append( f"% {w} %" )           # In middle of line surrounded by spaces
            return ' AND '.join( query ), data

        # ----------------------------------------------
        #   This is best but a bit slow. Same as above but in Python.

        elif match_type == "my_match":
            return f"my_match( {col}, ? )", [ss]

        # ----------------------------------------------
        #    This may be good if I could get it to work

        elif match_type == "regexp":
            data = []
            query = []
            for w in ss.split():
                #   I couldn't get this to work. Also slower than LIKE.
                query.append( f"{col} REGEXP ?" )
                # data.append( f"^{w}$|^{w}\s+|\s+{w}$|\s+{w}\s+" )   WRW 24 May 2024, change f" to r", after upgrade to 3.12
                data.append( r"^{w}$|^{w}\s+|\s+{w}$|\s+{w}\s+" )
            return ' AND '.join( query ), data

        # --------------------------------------------
        #   This matches any place in title including within words. Not too useful.

        elif match_type == "simple-like":
            data = []
            query = []
            for w in ss.split():
                query.append( f"{col} LIKE ?" )
                data.append( f"%{w}%" )             # Must put the percent signs here, not in LIKE '%?%'. No substitution inside quotes.
            return ' AND '.join( query ), data

    # ------------------------------------------------------------------------

    def OMIT_set_window( self, window ):
        self.window = window                # /// WRW 1-Feb-2025

    # def set_display_keys( self, image, image_tab, page_number ):
    #     self.image_key = image
    #     self.image_tab_key = image_tab
    #     self.page_number_key = page_number

    # ------------------------------------------------------------------------
    #   add() and save() are use by source-specific routines to build
    #       data in Index.Json directory.
    #   WRW 6 Jan 2022 - Collapse multiple spaces to one in title
    #   WRW 3 Apr 2022 - Add title correction via corrections file.
    #   Reminder: This is called from the Index-Sources/do*.py routines to add an item
    #       from the raw index.

    def add( self, book, item ):
        import fb_title_correction                  # For extra caution to prevent circular import loop

        title = " ".join( item[ 'title' ].split())      # Tidy up white space.
        title = fb_title_correction.do_correction( self.corrections_log, title )   # WRW 3 Feb 2022 - Clean up the title
        if title in self.corrections:                 # Add 'The' to front of some titles where others already have it
            title = self.corrections[ title ]         # and others from index diff editing.
        item[ 'title' ] = title
        self.books.setdefault( book, [] ).append( item )

    # ------------------------------------------------------------------------

    def set_music_file( self, book, music_file ):
        if not book in self.music_files:
            self.music_files[ book ] = music_file

    # ------------------------------------------------------------------------

    def save( self, source, src ):
        s = Store()
        # with open( self.conf.localbooknames, "w" ) as ln_fd, \

        with open( s.conf.val( 'localbooknames', source ), "w", encoding='utf-8' ) as ln_fd, \
             open( s.Const.Proto_Local2Canon, "w", encoding='utf-8'  ) as pl2c_fd, \
             open( s.Const.Proto_Sheet_Offsets, "w", encoding='utf-8'  ) as ppo_fd,  \
             open( s.Const.Proto_Canonical2File, "w", encoding='utf-8'  ) as pc2f_fd:

            for book in sorted( self.books ):
                print( book, file=ln_fd )
                print( f"{book} | (1, 0)", file=ppo_fd )
                print( f"{book} | {book}", file=pl2c_fd )

                if book in self.music_files:
                    music_file = self.music_files[ book ]           
                else:
                    music_file = book + ".pdf"

                print( f"{book} | {music_file}", file=pc2f_fd )

                fbook = clean_filename( book )
                ofile = f'{s.conf.val( "music_index_dir" )}/{src}-{fbook}.json.gz'

                book = " ".join( book.split())
                source = " ".join( source.split())

                full_contents = {
                    'local': book,
                    'source' : source,
                    'contents': self.books[ book ],
                }                             

                #   WRW 11 Feb 2022 - Compress output

                json_text = json.dumps( full_contents, indent=2 )
                with gzip.open( ofile, 'wt', encoding='utf-8'  ) as ofd:    # /// WRW 23-Mar-2025 ENCODING
                    ofd.write( json_text )

                # with open( ofile, "w" ) as ofd:
                #     ofd.write( json.dumps( full_contents, indent=2 ))

    # ------------------------------------------------------------------------
    #   WRW 7 Mar 2022 - Added save_csv() so can avoid shipping the entire buffalo.html
    #       raw source file. Huge.

    def save_csv( self, source, src, ofile ):
        with gzip.open( ofile, 'wt', encoding='utf-8'  ) as ofd:    # /// WRW 23-Mar-2025 ENCODING
        # with open( ofile, "w" ) as ofd:
            csvwriter = csv.writer( ofd )
            for book in sorted( self.books ):
                book = " ".join( book.split())
                source = " ".join( source.split())
                for content in self.books[ book ]:
                    csvwriter.writerow( [book, content['title'], content[ 'sheet' ], content['composer'], content['lyricist'] ] )

    # ------------------------------------------------------------------------
    #   Call 'callback' for each source file in Index.Json matching 'src'

    def get_music_index_data_by_src( self, src, callback, **kwargs ):
        s = Store()
        curdir = os.getcwd()                            # OK on windows
        os.chdir( s.conf.val( 'music_index_dir' ))        # OK on windows
        files = glob.glob( f"{src}*.json.gz" )
        for file in files:
          # with open( file ) as ifd:
            with gzip.open( file, 'rt', encoding='utf-8'  ) as ifd: # /// WRW 23-Mar-2025 ENCODING
                data = json.load( ifd )
                callback( src, data, file, **kwargs )
        os.chdir ( curdir )

    # ------------------------------------------------------------------------
    #   WRW 2 Mar 2022 - Original returned array of arrays, now returns just array.

    def get_srcs( self ):
        s = Store()
        return sorted( list( s.conf.src_to_source.keys() ) )

    # ------------------------------------------------------------------------
    #   WRW 28 Apr 2022 - Get list of srcs for indexes for canonical. In order
    #       of src priority so index 0 is tops.

    def get_srcs_by_canonical( self, canonical ):
        s = Store()
        query = """SELECT src
                    FROM local2canonical
                    JOIN src_priority USING( src )
                    WHERE canonical = %s
                    ORDER BY priority
                 """
        data = [ canonical ]
        query = fix_query( query )

        try:
            s.dc.execute( query, data )

        except Exception:
            (extype, value, traceback) = sys.exc_info()
            print( f"ERROR on SELECT, type: {extype}, value: {value}", file=sys.stderr )
            print( f"  {query}", file=sys.stderr  )
            return None

        res = [ row['src'] for row in s.dc.fetchall() ]
        return res

    # ------------------------------------------------------------------------
    #   WRW 28 Apr 2022 - Need for 'browse-src-combo' default value.

    def get_priority_src( self ):
        s = Store()
        txt = """SELECT src
                 FROM src_priority
                 ORDER BY priority
                 LIMIT 1
              """
        try:
            s.dc.execute( txt )

        except Exception:
            (extype, value, traceback) = sys.exc_info()
            print( f"ERROR on SELECT, type: {extype}, value: {value}", file=sys.stderr )
            print( f"  {txt}", file=sys.stderr  )
            return None

        row = s.dc.fetchone()
        res = row[ 'src' ] if row else None
        return res

    # ------------------------------------------------------------------------
    #   WRW 7 Feb 2022 - For index diff work.
    #   Get list of canonicals with more than one index source

    def get_canonicals_with_index( self ):
        s = Store()
        txt = """SELECT canonical, local, src 
                 FROM local2canonical
                 GROUP BY canonical
                 HAVING COUNT( canonical )> 1
                 ORDER BY canonical
             """
        try:
            s.dc.execute( txt )

        except Exception:
            (extype, value, traceback) = sys.exc_info()
            print( f"ERROR on SELECT, type: {extype}, value: {value}", file=sys.stderr )
            print( f"  {txt}", file=sys.stderr  )
            return None
    
        else:
            res = [ { 'canonical': row['canonical'], 'src': row['src'], 'local': row['local'] } for row in s.dc.fetchall() ]
            return res

    # ------------------------------------------------
    #   WRW 24 Apr 2022 - Added specifically for Create Index feature. Don't reuse get_canonicals_with_index() or
    #       get_canonicals(). Here join with file as can't create index without a music file.
    #   WRW 25 Apr 2022 - Always include 'Usr' files for 'No-Index' as we may want to edit them after they were added to database.

    def get_canonicals_for_create( self, select ):
        s = Store()
        if select == 'All':
            txt = """SELECT DISTINCT canonicals.canonical
                     FROM canonicals
                     JOIN canonical2file USING( canonical )
                     ORDER BY canonicals.canonical
                 """

        elif select == 'No-Index':                              # This is default and only useful option.
            txt = """SELECT DISTINCT canonicals.canonical
                     FROM canonicals
                     JOIN canonical2file USING( canonical )
                     LEFT JOIN local2canonical USING( canonical )
                     WHERE (local2canonical.canonical IS NULL) OR
                     (local2canonical.src = 'Usr')
                     ORDER BY canonicals.canonical
                 """

        elif select == 'Only-Index':
            txt = """SELECT DISTINCT canonicals.canonical
                     FROM canonicals
                     JOIN canonical2file USING( canonical )
                     LEFT JOIN local2canonical USING( canonical )
                     WHERE local2canonical.canonical IS NOT NULL
                     ORDER BY canonicals.canonical
                 """
        else:
            txt = ''    # To suppress warning Volker saw.

        try:
            s.dc.execute( txt )

        except Exception:
            (extype, value, traceback) = sys.exc_info()
            print( f"ERROR on SELECT, type: {extype}, value: {value}", file=sys.stderr )
            print( f"  {txt}", file=sys.stderr  )
            return None
    
        else:
            res = [ [row['canonical']] for row in s.dc.fetchall() ]
            return res

    # ------------------------------------------------

    def get_canonicals( self ):
        s = Store()
        txt = 'SELECT canonical FROM canonicals ORDER BY canonical'

        try:
            s.dc.execute( txt )

        except Exception:
            (extype, value, traceback) = sys.exc_info()
            print( f"ERROR on SELECT, type: {extype}, value: {value}", file=sys.stderr )
            print( f"  {txt}", file=sys.stderr  )
            return None
    
        else:
            res = [ [row['canonical']] for row in s.dc.fetchall() ]
            return res

    # ------------------------------------------------

    def get_files( self, fb_flag ):
        s = Store()
        query = 'SELECT file FROM music_files where fb_flag = %s ORDER BY file'
        data = [ fb_flag ]

        query = fix_query( query )
        try:
            s.dc.execute( query, data )

        except Exception:
            (extype, value, traceback) = sys.exc_info()
            print( f"ERROR on SELECT, type: {extype}, value: {value}", file=sys.stderr )
            print( f"  {query}", file=sys.stderr  )
            return None
    
        else:
            res = [ [row['file']] for row in s.dc.fetchall() ]
            return res

    # ------------------------------------------------
    def get_local_from_canonical_src( self, canonical, src ):
        s = Store()
        query = "SELECT local FROM local2canonical WHERE canonical = %s AND src = %s"
        query = fix_query( query )
        data = [ canonical, src ]

        try:
            s.dc.execute( query, data )

        except Exception:
            (extype, value, traceback) = sys.exc_info()
            print( f"ERROR on SELECT, type: {extype}, value: {value}", file=sys.stderr )
            print( f"  {query}", file=sys.stderr  )
            return None
    
        else:
            row = s.dc.fetchone()
            res = row[ 'local' ] if row else None
            return res

    # ------------------------------------------------
    #   WRW 1 Apr 2022 - For editing raw index sources

    def get_raw_file( self, title, local, src ):
        s = Store()
        query = """SELECT file, line FROM raw_index
                   JOIN titles_distinct USING( title_id )
                   WHERE title = %s AND src = %s AND local = %s
                """
        query = fix_query( query )
        data = [ title, src, local ]

        try:
            s.dc.execute( query, data )

        except Exception:
            (extype, value, traceback) = sys.exc_info()
            print( f"ERROR on SELECT, type: {extype}, value: {value}", file=sys.stderr )
            print( f"  {query}", file=sys.stderr  )
            return None
    
        else:
            row = s.dc.fetchone()
            file = row[ 'file' ] if row else None
            line = row[ 'line' ] if row else None
            return file, line

    # ------------------------------------------------
    #    This is based on index files, not the database, now config file.
    #       Need both. This used by build-tables.py

    def get_srcs_from_index( self ):
        s = Store()
        srcs = set()
        cur = os.getcwd()
        # os.chdir ( self.MusicIndexDir )
        os.chdir ( s.conf.val('music_index_dir'))
        files = glob.glob( '*' )
        os.chdir ( cur )
      # [ srcs.add( re.sub( r'\-.*$', '', file )) for file in files ]       # Caught by pylint
        for file in files:
            srcs.add( re.sub( r'\-.*$', '', file ))

        return list( srcs )

    # ------------------------------------------------------------------------
    #   Get list of local names from MusicIndexDir for src
    #   (pattern, repl, string, count=0, flags=0)

    def get_locals_from_src( self, src ):
        s = Store()

        txt = "SELECT DISTINCT local FROM local2canonical WHERE src = %s ORDER BY local"  
        txt = fix_query( txt )
        data = [src]

        try:
            s.dc.execute( txt, data )

        except Exception:
            (extype, value, traceback) = sys.exc_info()
            print( f"ERROR on SELECT, type: {extype}, value: {value}", file=sys.stderr )
            print( f"  {txt}", file=sys.stderr  )
            print( f"  {data}", file=sys.stderr  )
            return None
    
        else:
            # res = []
            # for row in s.dc.fetchall():
            #     res.append( [row['local']] )

            res = [ [row['local']] for row in s.dc.fetchall() ]

            return res

    # ------------------------------------------------
    #   This is based on index files, not the database.
    def old_get_locals_from_src( self, src ):
        llocals = set()

        cur = os.getcwd()
        os.chdir ( self.MusicIndexDir )
        files = glob.glob( f'{src}-*' )
        os.chdir ( cur )
        for file in files:
            # m = re.match( f'{src}-(.*)\.json', file ) WRW 24 May 2024, change f' to r', after upgrade to 3.12
            m = re.match( r'{src}-(.*)\.json', file )   
            if m:
                llocals.add( m[1] )

        return list( llocals )

    # ------------------------------------------------------------------------
    #   This is similar to get_table_of_contents() but returns dict, ordered by sheet, and includes composer
    #   For Index Management support.

    def get_index_from_src_local( self, src, local ):
        s = Store()

        query = """SELECT title, sheet, composer FROM titles_distinct
                   JOIN titles USING( title_id )
                   WHERE src = %s
                   AND local = %s
                   ORDER BY sheet +0
                """
        query = fix_query( query )
        data = [src, local]
        s.dc.execute( query, data )

        res = [ { 'title': row[ 'title' ], 'sheet': row[ 'sheet' ], 'composer': row[ 'composer'] } for row in s.dc.fetchall() ]

        return res

    # --------------------------------------------------------------------------

    def old_get_index_from_src_local( self, src, local ):
        ifile = Path( self.MusicIndexDir, f"{src}-{local}.json" )
        with open( ifile, 'rt', encoding='utf-8'  ) as ifd:         # /// WRW 23-Mar-2025 ENCODING
            data = json.load( ifd )
            return data

    # ------------------------------------------------------------------------
    #   Translate src name (3-letter abbreviation) to full source name
    #   Do this only here, not in source-specific code.
    #   In conf:
    #       self.source_to_src[ ssource ] = src
    #       self.src_to_source[ src ] = ssource

    def get_source_from_src( self, src ):
        s = Store()
        if src in s.conf.src_to_source:
            return s.conf.src_to_source[ src ]
        return None

    # ------------------------------------------------------------------------
    #   Call callback for each source with data represented in Index.Json directory

    def traverse_sources( self, callback, **kwargs ):
        for src in self.get_srcs_from_index():
            callback( src, **kwargs )

    # ------------------------------------------------------------------------

    def get_title_id_from_title( self, title ):
        s = Store()

        txt = "SELECT title_id, title FROM titles_distinct WHERE title = %s"      # For testing.
        # txt = "SELECT title_id FROM titles_distinct WHERE title = %s"
        data = [title]

        txt = fix_query( txt )
        try:
            s.dc.execute( txt, data )
    
        except Exception:
            (extype, value, traceback) = sys.exc_info()
            print( f"ERROR on SELECT, type: {extype}, value: {value}", file=sys.stderr )
            print( f"  {txt}", file=sys.stderr  )
            print( f"  {data}", file=sys.stderr  )
            return None
    
        else:
            rows = s.dc.fetchall()
            if len(rows) > 1:
                print( f"ERROR: expected 1 row from titles_distinct, got {len(rows)}", file=sys.stderr )
                print( f"   '{title}'", file=sys.stderr  )
                for row in rows:
                    # print( row, file=sys.stderr )
                    print( f"title: '{row[ 'title' ]}', id: '{row['title_id']}'", file=sys.stderr )
                return None
    
            if len(rows) == 1:
                return rows[0]['title_id']
    
            # print( f"ERROR: no match in titles_distinct table for:", file=sys.stderr )
            # print( f"   {title}", file=sys.stderr  )
            return None

    # ------------------------------------------------------------------------
    #        AND %s >= sheet_start + sheet_offset
    #        AND %s >= sheet_start   
    #   WRW 28 Apr 2022 - This is not working with sqlite3 as it should
    #   WRW change ORDER BY id to ORDER BY offset_id. Can't do much with id in sqlite3.
    #   WRW 1 May 2022 - Realized not working. Added '+ sheet_offset' to 'AND %s >= sheet_start + sheet_offset'

    def get_sheet_offset_from_page( self, page, src, local ):
        s = Store()
        query = """
            SELECT sheet_offset
            FROM sheet_offsets
            WHERE src = %s
            AND local = %s
            AND %s >= sheet_start + sheet_offset
            ORDER BY offset_id DESC
            LIMIT 1
        """
        query = fix_query( query )
        data = [ src, local, page ]
        s.dc.execute( query, data )
        row = s.dc.fetchone()

        return row[ 'sheet_offset' ] if row else None

    # --------------------------------------------------------------------------
    #   Remember: 'sheet' is what is printed in the book, 'page' is the PDF page number.
    #       page  = sheet_offset + sheet
    #       sheet =  page - sheet_offset
    #   *** sheet_start - the first sheet where page = sheet_offset + sheet
    #   Returns page as a string

    #   WRW 1 Feb 2022 - Changed to return None, not page, when don't find match.
    #       Changed to do it all in SQL. Looks good.

    #   WRW 4 Feb 2022 - Change algorithm:
    #       Find last sheet_offsets entry where page >= (sheet_start + sheet_offset) ordered by sheet_start + sheet_offset
    #       Had error in earlier approach.
    #   WRW 1 May 2022 - Realized not working. Added '+ sheet_offset' to 'AND %s >= sheet_start + sheet_offset'

    def get_sheet_from_page( self, page, src, local ):

        s = Store()

        query = """SELECT %s - sheet_offset AS sheet
                   FROM sheet_offsets
                   WHERE src = %s
                   AND local = %s
                   AND %s >= sheet_start + sheet_offset
                   ORDER BY offset_id DESC
                   LIMIT 1
                """
        query = fix_query( query )
        data = [page, src, local, page]
        s.dc.execute( query, data )

        row = s.dc.fetchone()
        return str(int(row[ 'sheet' ])) if row else None

    # ----------------------------------------------------------------------------

    #   Remember: 'sheet' is (should be) what is printed in the book, 'page' is the PDF page number.
    #   sheet_start: The first sheet where page = sheet_offset + sheet
    #       page = sheet_offset + sheet
    #       sheet = page - sheet_offset
    #   Returns page as a string

    #   WRW 2 Feb 2022 - Trying this in place of adjust_page(). I don't see need for
    #       title, which adjust_page() uses. Looks fine.

    #   WRW 4 Feb 2022 - Change algorithm:
    #       Find last sheets_offsets entry where sheet >= (sheet_start - sheet_offset) ordered by sheet_start + sheet_offset
    #       Had error in earlier approach.

    #   WRW 5 Apr 2022 - I don't think this is working, always returns same value. Showed up in scatter plot
    #       of page vs sheet. Problem is with Sqlite, OK with MySql. Prob is use of primary key 'id'. Add
    #       a separate id value in table as offset_id. Solved problem

    def get_page_from_sheet( self, sheet, src, local ):
        s = Store()

        query = """SELECT %s + sheet_offset AS page
                   FROM sheet_offsets
                   WHERE src = %s
                   AND local = %s
                   AND %s >= sheet_start
                   ORDER BY offset_id DESC
                   LIMIT 1
                """

        query = fix_query( query )
        data = [sheet, src, local, sheet]
        s.dc.execute( query, data )

        # print( query )
        # print( data )

        row = s.dc.fetchone()

        # print( "/// sheet:", sheet, '-> page', row[ 'page' ], src, local )

        return str(int(row[ 'page' ])) if row else None

    # ----------------------------------------------------------------------------
    #   WRW 7 Jan 2022 - For First/Prev/Next/Last - do a higher level to update button box
    #       Show saved book with updated page. Oops, brain fart.

    # def show_music_file_saved( self, page ):
    #     t = self.save_music_file
    #     self.show_music_file( t['file'], page, t['title'], t['sheet'], t['src'], t['canonical'], t['local'], **t['kwargs'] )

    # --------------------------------------------------------------------------
    #   Get title given sheet number, src, and local.
    #   Need this to move back and forward by page and show title of new page.
    #   How reverse page offsets?

    def get_titles_from_sheet( self, sheet, src, local ):
        s = Store()

        query = """SELECT title FROM titles_distinct
                   JOIN titles USING( title_id )
                   WHERE sheet = %s
                   AND src = %s
                   AND local = %s
                   ORDER BY title
                """
        query = fix_query( query )
        data = [sheet, src, local]
        s.dc.execute( query, data )
        res = [ row[ 'title' ] for row in s.dc.fetchall() ]
        return res

    # --------------------------------------------------------------------------
    #   WRW 29 Apr 2022 - switch from sheet to page

    def get_table_of_contents( self, src, local ):
        s = Store()

        query = """SELECT title, sheet FROM titles_distinct
                   JOIN titles USING( title_id )
                   WHERE src = %s
                   AND local = %s
                   ORDER BY title
                """
        query = fix_query( query )
        data = [src, local]
        s.dc.execute( query, data )

        res = [ [ row[ 'title' ], row[ 'sheet' ] ] for row in s.dc.fetchall() ]
        return res

    # --------------------------------------------------------------------------
    #   WRW 22 Jan 2022 - Couple of back mappings needed to get TOC from file or canonical.

    def get_canonical_from_file( self, file ):
        s = Store()
        query = """SELECT canonical FROM canonical2file
                   WHERE file = %s
                """
        query = fix_query( query )

        data = [file]
        s.dc.execute( query, data )
        row = s.dc.fetchone()
        return row[ 'canonical' ] if row else None

    # --------------------------------------------------------------------------
    #   Get music filename from canonical
    
    def get_file_from_canonical( self, canonical ):
        s = Store()
    
        query = """SELECT file FROM canonical2file
                   WHERE canonical = %s
                """
        query = fix_query( query )
        data = [canonical]
    
        s.dc.execute( query, data )
        rows = s.dc.fetchall()

        if len(rows) != 1:
            # print( f"ERROR: get_file_by_canonical( {canonical} ) returned {len(rows)}, expected 1", file=sys.stderr )
            # sys.exit(1)
            return None
    
        return rows[0]['file']
    
    # --------------------------------------------------------------------------

    def get_canonical_from_src_local( self, src, local ):
        s = Store()
        query = """SELECT canonical FROM local2canonical
                   WHERE src = %s
                   AND local = %s
                """
        query = fix_query( query )
        data = [ src, local ]
        s.dc.execute( query, data )
        rows = s.dc.fetchall()

        if len(rows) != 1:
            # print( f"ERROR: get_file_by_canonical( {canonical} ) returned {len(rows)}, expected 1", file=sys.stderr )
            # sys.exit(1)
            return None
    
        return rows[0]['canonical']

    # --------------------------------------------------------------------------
    #   Note that there is a one to many relationship that is disambiguated
    #       with join to src_priority and LIMIT 1

    def get_src_local_from_canonical( self, canonical ):
        s = Store()

        query = """SELECT l2c.src, l2c.local FROM local2canonical l2c
                   JOIN src_priority p USING( src )
                   WHERE l2c.canonical = %s
                   ORDER BY priority
                   LIMIT 1
                """
        query = fix_query( query )
        data = [ canonical ]
        s.dc.execute( query, data )

        res = [ [ row[ 'src' ], row[ 'local' ]] for row in s.dc.fetchall() ]

        return res

    # --------------------------------------------------------------------------

    def get_local_from_src_canonical( self, src, canonical ):
        s = Store()

        query = """SELECT l2c.local FROM local2canonical l2c
                   WHERE l2c.src = %s AND
                   l2c.canonical = %s    
                   LIMIT 1
                """
        query = fix_query( query )
        data = [ src, canonical ]
        s.dc.execute( query, data )
        row = s.dc.fetchone()
        return row[ 'local' ] if row else None

    # --------------------------------------------------------------------------
    #   Query specifically to support index diff
    #   Get all titles for canonical from all index srcs

    def get_diff_data( self, canonical ):
        s = Store()

        query = """
            SELECT title, titles.src, local, sheet
            FROM titles
            JOIN titles_distinct USING( title_id )
            JOIN local2canonical USING( local, src )
            WHERE canonical = %s
            ORDER BY sheet+0
        """
        query = fix_query( query )
        data = [canonical]
        s.dc.execute( query, data )
        res = [ { 'title' : row[ 'title' ], 'src': row[ 'src' ], 'local': row[ 'local' ], 'sheet': row[ 'sheet' ] } for row in s.dc.fetchall() ]
        return res

    # --------------------------------------------------------------------------
    #   WRW 28-May-2025 - Try to get count of indexed titles given a file
    #

    def get_index_count_from_file( self, file ):
        s = Store()

        query = """
            SELECT COUNT(*) cnt, src
            FROM  (
                SELECT src          
                FROM canonical2file
                JOIN local2canonical USING( canonical )
                JOIN titles USING( src, local )
                JOIN titles_distinct USING( title_id )
                WHERE file = %s
            ) AS sub
            GROUP BY src ORDER BY cnt DESC LIMIT 1
        """

        query = fix_query( query )
        data = [file]
        s.dc.execute( query, data )
        row = s.dc.fetchone()
        return (row[ 'cnt' ], row[ 'src' ]) if row else (None, None)

    # --------------------------------------------------------------------------
    #   os.walk( folder ) returns generator that returns list of folders and list of files
    #       in 'folder'.
    
    def listfiles( self, folder ):
        for root, folders, files in os.walk(folder):    # OK on Windows
            for file in files:
                yield (root, file)
                # yield os.path.join(root, file)

    # ----------------------------------------------------------------------------
    def log( self, event, value ):
        self.log_data.append( [event, value] )
        if len( self.log_data ) > 500:
            self.log_data.pop( 0 )

    # ----------------------------------------------------------------------------
    def log_histo( self, event, value ):

        self.log_histo_data[ event ] = self.log_histo_data.setdefault( event, {} )

        if isinstance( value, str ):
            self.log_histo_data[ event ][ value ] = self.log_histo_data[ event ].setdefault( value, 0 ) + 1

        elif isinstance( value, list ):
            t = [ f"{str(x)}" for x in value ]    # value may contain ints, which cannot be joined. First convert to stt.
            t = ', '.join(t)
            t = f"[{t}]"
            self.log_histo_data[ event ][ t ] = self.log_histo_data[ event ].setdefault( t, 0 ) + 1

        elif isinstance( value, tuple ):
            t = [ f"{str(x)}" for x in value ]    # value may contain ints, which cannot be joined. First convert to stt.
            t = ', '.join(t)
            t = f"({t})"
            self.log_histo_data[ event ][ t ] = self.log_histo_data[ event ].setdefault( t, 0 ) + 1


        else:
            # print( "///", event, value, type(event), type(value ))
            self.log_histo_data[ event ][ 'unknown' ] = self.log_histo_data[ event ].setdefault( 'unknown', 0 ) + 1

    # ---------------------------------------------------
    #   WRW 8 Feb 2022 - Get all offsets for a given src/local

    def get_offsets( self, src, local ):
        s = Store()
        query = """SELECT sheet_start, sheet_offset
                   FROM sheet_offsets
                   WHERE src = %s
                   AND local = %s
                   ORDER BY sheet_start DESC
                """
        query = fix_query( query )
        data = [src, local]
        s.dc.execute( query, data )

        return [ { 'start': row[ 'sheet_start' ], 'offset': row[ 'sheet_offset' ] } for row in s.dc.fetchall() ]

    # ---------------------------------------------------

    def get_log( self ):
        return self.log_data

    def get_log_histo( self ):
        return self.log_histo_data

    # --------------------------------------------------------------------------
    #   WRW 27 Mar 2022 - Move from birdland.py into here so can call from fb_config.py
    #       for some initialization
    #   Used only for bl-build-tables (build_tables.py) and bl-diff-index.
    #   WRW 17-Mar-2025 - clean up to eliminate command as module and add threads.

    #   run_external_command( command ) - Original, include success/error reporting.
    #   run_external_command_quiet( command ) - Same without success/error reporting, for initialization.

    #   WRW 18-Mar-2025 - Run external command with text output to results tab line-by-line
    #       /// RESUME - change name to run_external_command_text()

    # ----------------------------------------------------------------------------

    def run_external_command( self, command ):
        self.run_external_command_quiet( command=command, show_flag=True, sig_finished=None )

    def run_external_command_binary( self, command, sig_finished, aux_data=None ):
        self.run_external_command_quiet( command=command, show_flag=False, sig_finished=sig_finished, aux_data=aux_data )

    # ----------------------------------------------------------------------------
    #   WRW 18-Mar-2025 - Moved inside class for consistency.

    def run_external_command_quiet( self, command, show_flag, sig_finished, aux_data=None ):
        s = Store()
        self.sig_finished = sig_finished
        self.aux_data = aux_data
        self.command = command              # Save for possible error message popup of command fails
    
        s.app.setOverrideCursor( QCursor(Qt.WaitCursor) )
        if show_flag:
            s.setTabVisible( MT.Results, True )
            s.selectTab( MT.Results )
            s.sigman.emit( "sig_clear_results" )

        # --------------------------------------------------------------------
        #   WRW 28-Mar-2025 - when running in pyinstaller frozen environment we are actually
        #   running the main program, which is birdstart.py, again with an argument indicating
        #   which module to import and run. Thus, build_tables and diff_index must have a
        #   .py extension but identified without it in birdstart.py

        #    s.fb.run_external_command( [ s.python, './build_tables.py', '--all', '-c', str( s.conf.confdir), '-d', s.fb.get_driver() ] )
        #    s.fb.run_external_command( [ s.python, './diff_index.py', '--summary', '--all', '-c', str(s.conf.confdir), '-d', s.fb.get_driver() ] )

        if s.Const.Frozen:
            if command[1] == './build_tables.py':
                command[1] = 'build_tables'

            elif command[1] == './diff_index.py':
                command[1] = 'diff_index'

        # --------------------------------------------------------------------

        s.sigman.emit( "sig_search_results", f'Starting command: {' '.join(command)}' )
    
        # --------------------------------------------------------------------------
        #   Run command as external process.
        #   WRW 17-Mar-2025 - looks like I'll have to run it in a separate thread to keep application alive.
        #       Big thanks to ChatGPT for the worker_thread

        if hasattr( s, 'worker_thread' ) and s.worker_thread and s.worker_thread.isRunning():
            s.worker_thread.stop()        # Stop existing thread before starting new one
    
        s.worker_thread = WorkerThread( command, show_flag )

        if show_flag:
            s.worker_thread.sig_data.connect( lambda x: s.sigman.emit( "sig_addto_results", x ))

        s.worker_thread.sig_finished.connect( lambda x: s.sigman.emit( "sig_search_results", f'Command completed with exit code {x}' ))
        s.worker_thread.sig_finished.connect( self.external_command_finished )

        s.worker_thread.start()

        if False:
            try:                                                                               
                pass
            except Exception:
                (extype, value, traceback) = sys.exc_info()
                t = f"subprocess.Popen( {self.command} failed.\ntype: {extype}\nvalue: {value}"
                print( "ERROR:", t )
                s.msgCritical( t )           # External command failed
                # self.sig_finished.emit( -1, None, None )
    
    # ----------------------------------------------------------------------------
    #   /// RESUME - think about aux_data a bit more after finish all uses of external commands
    #   For now, use it to carry data from the calling program to the finished signal handler.
    #   /// RESUME stdout (probably stderr) is None on Windows, decode() is failing with stdout of None
    
    @Slot( int, object )
    def external_command_finished( self, rcode, stdout, stderr ):
        s = Store()
        s.app.restoreOverrideCursor()

        if rcode:
            stdout_txt = f"Stdout: {stdout.decode()}" if stdout is not None else 'None'
            stderr_txt = f"Stderr: {stderr.decode()}" if stderr is not None else 'None'

            txt = []
            txt.append( f"ERROR: External command failed, exit code: {rcode}" )
            txt.append( f"Command: {' '.join(self.command)}" )
            txt.append( '' )
            txt.append( stdout_txt )
            txt.append( '' )
            txt.append( stderr_txt )

            # s.conf.do_popup( '\n'.join( txt ) )
            s.msgCritical( '\n'.join( txt ) )           # External command failed

        res = [ self.aux_data, stdout, stderr ]
        if self.sig_finished:
            s.sigman.emit( self.sig_finished, rcode, res )

    # ----------------------------------------------------------------------------
    #   WRW 10-Apr-2025 - Want to color svg QIcon() but 'fill:currentColor' is not
    #   picking up the styled color. From chat. With this approach the icons
    #   are not drawn immediately but on call to updateSvgIcons()

    def colorSvgIcon( self, svg_path: str, size: QSize, color: QColor ) -> QIcon:
        renderer = QSvgRenderer(svg_path)
        pixmap = QPixmap(size)
        pixmap.fill(Qt.transparent)
    
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        renderer.render(painter)
        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter.fillRect(pixmap.rect(), color)
        painter.end()
    
        return QIcon(pixmap)

    # ----------------------------------------------------------------
    #   This is used in configuration popup where we redraw icons on each
    #       display of popup. No need for registration as not redrawn
    #       on theme change.

    #   WRW 21-May-2025 - may not have an icon color yet early in the
    #       first-start sequence when need to show the config window
    #       to get a user/password for mysql DB.
    #       Provide a color compatible with startup appearance of 'Dark-Blue'.

    def getColoredSvgIcon( self, icon, size ):
        if self.saveIconColor:
            return self.colorSvgIcon( icon, size, self.saveIconColor )
        else:
            # print( "ERROR-DEV: saveIconColor not defined at getColoredSvgIcon()" )
            # sys.exit(1)
            return self.colorSvgIcon( icon, size, QColor( '#f0f0ff' ))      # Compatible with Dark-Blue

    # ----------------------------------------------------------------
    #   WRW 1-May-2025 - add group in support of disabled audio icons.

    def registerSvgIcon( self, widget, icon, size, group ):
        self.svgRegistry.append( { 'widget' : widget, 'svg_icon' : icon, 'size' : size, 'group' : group } )

    def registerGroupBox( self, widget ):
        self.groupBoxRegistry.append( widget )

    # ----------------------------------------------------------------
    #   WRW 1-May-2025 - add group parameter so can update just audio icons for disabled state

    def updateSvgIcons( self, color: QColor, group=None ):
        self.saveIconColor = color              # Save for unregistered icons, occur in configuration popup

        for entry in self.svgRegistry:
            if group and group != entry[ 'group' ]:
                continue

            icon = self.colorSvgIcon(entry["svg_icon"], entry["size"], color )
            widget = entry[ 'widget' ]

            if isinstance(widget, QPushButton ):
                widget.setIcon(icon)

            elif isinstance(widget, QLabel):
                icon = self.colorSvgIcon(entry["svg_icon"], entry["size"], color )
                widget.setPixmap( icon.pixmap( entry[ 'size' ] ))

            else:
                print( f"ERROR-DEV: Unexpected widget type {type(widget)} at updateSvgIcons()" )
                sys.exit(1)

# ============================================================================
#   WRW 18-Mar-2025 - expand for use with line-by-line text output or buffered
#       binary data.
#   For now: show_flag: True implies text, False implies binary

class WorkerThread(QThread):
    sig_data = Signal( str )                        # Signal to send output to the main thread
    sig_finished = Signal( int, object, object )    # Signal when finished, possibly send binary data to main thread

    # -----------------------------------------------------------------------
    def __init__( self, command, show_flag ):
        super().__init__()
        self.command = command
        self.process = None
        self.show_flag = show_flag
    
    # -----------------------------------------------------------------------
    #   run() called by Qt thread facility.

    def run(self):              # Runs a subprocess and captures output line by line.
        s = Store()

        self.process = subprocess.Popen(
            self.command,
            stdout = subprocess.PIPE,
         #  stderr = subprocess.PIPE,       # Issue here, looks like must also readline from stderr if do this.
            stderr = subprocess.STDOUT,
            text = True if self.show_flag else False,
            bufsize = 1 if self.show_flag else 16384,
        )

        # Read stdout line by line and emit signal for each line

        if self.show_flag:
            stdout = None
            stderr = None
            if self.show_flag:
                for line in iter(self.process.stdout.readline, ''):
                    self.sig_data.emit( line )  # Emit line to be updated in UI
        else:
            stdout, stderr = self.process.communicate()

        self.process.stdout.close()
        self.process.wait()              # Ensure the process is finished
        rcode = self.process.returncode

        self.sig_finished.emit( rcode, stdout, stderr )

    # -----------------------------------------------------------------------
    # Stops the thread and subprocess

    def stop(self):
        self._is_running = False
        if self.process:
            self.process.terminate()  # Send SIGTERM to subprocess

            try:
                self.process.wait(timeout=2)  # Wait for process to exit
            except subprocess.TimeoutExpired:
                self.process.kill()  # Force kill if it doesn't exit

        self.quit()     # stops the event loop of the thread if it's running but does not stop the thread
        self.wait()     # blocks execution until the thread actually finishes.

# ============================================================================

def continuation_lines( fd ):
    for line in fd:
        line = line.rstrip('\n')
        while line.endswith('\\'):
            line = line[:-1] + next(fd).rstrip('\n')
        yield line

# ----------------------------------------------------------------------------

def do_main():
    import MySQLdb
    from bl_unit_test import UT
    from bl_style import StyleSheet

    s = UT( mysql=True )

    # conf.set_cwd( os.getcwd() )
    # os.chdir( os.path.dirname(os.path.realpath(__file__)))  # Non-operational
    # conf.set_install_cwd( os.getcwd() )

    conn = MySQLdb.connect( "localhost", s.conf.val( 'database_user' ), s.conf.val( 'database_password' ), s.conf.mysql_database )
    s.dc = conn.cursor(MySQLdb.cursors.DictCursor)
    
    print( "srcs:", s.fb.get_srcs() )
    print( "title_id, valid name", s.fb.get_title_id_from_title( "Bess You Is My Woman Now" ) )
    print( "title_id, bogus name", s.fb.get_title_id_from_title( "Bess You Is My Woman Now Foobar" ) )

    # --------------------------------------------------------------

    print( s.conf.val('music_file_folders'))
    print( s.conf.val('music_file_root'), s.conf.val('audio_file_root'))
    print( s.conf.val('canonicals'), s.conf.val('canonical2file'), s.conf.val('youtube_index'))

    print( s.conf.val('audio_folders'))

    # --------------------------------------------------------------

    for sheet in [ 526, 527, 528, 529, 530 ]:
        page = s.fb.get_page_from_sheet( str( sheet ), 'Skr', 'firehouse_jazzband' )
        print( f"sheet {sheet}, page: {page}" )

    print()
    for page in [ 526, 527, 528, 529, 530 ]:
        sheet = s.fb.get_sheet_from_page( str( page ), 'Skr', 'firehouse_jazzband' )
        print( f"page: {page}, sheet: {sheet}" )

    print()
    for page in [ 526, 527, 528, 529, 530 ]:
        offset = s.fb.get_sheet_offset_from_page( page, 'Skr', 'firehouse_jazzband' )
        print( f"page: {page}, offset: {offset}" )

    print()
    print('-'*60)
    print( "get_page_from_sheet()" )
    for sheet in range( 1, 20 ):
        page = s.fb.get_page_from_sheet( str( sheet ), 'Shr', 'Standards Real Book' )
        print( f"sheet {sheet} -> page: {page}" )

    print()
    print( "get_sheet_from_page()" )
    for page in range( 1, 30 ):
        sheet = s.fb.get_sheet_from_page( page, 'Shr', 'Standards Real Book' )
        print( f"page: {page} -> sheet: {sheet}" )

    print()
    print( "get_sheet_offset_from_page()" )
    for page in range( 1, 30 ):
        offset = s.fb.get_sheet_offset_from_page( page, 'Shr', 'Standards Real Book' )
        print( f"page: {page} -> offset: {offset}" )

    lrows = s.fb.get_local_from_src_canonical( 'Shr', 'Standards Real Book - Chuck Sher' )
    print( lrows )

    conn.close()    # non-operational

# ----------------------------------------------------------------------------

if __name__ == '__main__':
    do_main()

# ----------------------------------------------------------------------------
