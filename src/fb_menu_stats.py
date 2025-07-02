# --------------------------------------------------------------------------
#   fb_menu_stats.py

#   WRW 30 Mar 2022 - Pulled out of birdland.py
# --------------------------------------------------------------------------

import os


from fb_utils import FB
from Store import Store
from fb_config import Config
from bl_constants import MT

from PySide6.QtGui import QFont
from PySide6.QtGui import QStandardItem

# --------------------------------------------------------------------------

#   Form of row in database_tables: [ label, table, query ]

database_tables = [                                     # for show stats.
    [ "All Music Files", "music_files", None ],
    [ "Indexed Music Files", None, 
        """SELECT COUNT(*) cnt
           FROM (
                SELECT COUNT(*) FROM titles
                JOIN local2canonical USING( local, src )
                GROUP BY canonical
           ) AS sub
        """
    ],
    [ "Titles in Indexed Music Files", "titles", None ],
    [ "Distinct Titles in Indexed Music Files", "titles_distinct", None ],
    [ "Titles in Indexed Music Files With Composer", None,
        """SELECT COUNT(*) cnt
           FROM titles 
           WHERE composer IS NOT NULL
        """
    ],
    [ "Titles in Indexed Music Files With Lyricist", None,
        """SELECT COUNT(*) cnt
           FROM titles 
           WHERE lyricist IS NOT NULL
        """
    ],
    [ "Titles in Audio Files", "audio_files", None],
    [ "Titles in Audio Files With Artist", None,
        """SELECT COUNT(*) cnt
           FROM audio_files
           WHERE artist IS NOT NULL
        """
    ],
    [ "Titles in Audio Files With Album", None,
        """SELECT COUNT(*) cnt
           FROM audio_files
           WHERE album IS NOT NULL
        """
    ],
    [ "Titles in Midi Files", None,
        """SELECT COUNT(*) cnt
           FROM midi_files
        """
    ],
    [ "Titles in ChordPro Files", None,
        """SELECT COUNT(*) cnt
           FROM chordpro_files
        """
    ],
    [ "Titles in JJazzLab Files", None,
        """SELECT COUNT(*) cnt
           FROM jjazz_files
        """
    ],
    [ "Titles in YouTube Files", None,
        """SELECT COUNT(*) cnt
           FROM title2youtube
        """
    ],
    [ "Distinct Titles in Indexed Music Files Matching Titles in YouTube Files", None,
        """SELECT COUNT(*) cnt
           FROM title2youtube
           JOIN titles_distinct USING( title_id )
        """
    ],
    [ "Distinct Titles in Indexed Music Files Matching Titles in Audio Files", None,
        """SELECT COUNT(*) cnt
           FROM titles_distinct
           JOIN audio_files USING( title );
        """
    ],

    [ "Rows in canonical2file table", None,
        """SELECT COUNT(*) cnt
           FROM canonical2file;
        """
    ],

    [ "Rows in canonicals table", None,
        """SELECT COUNT(*) cnt
           FROM canonicals;
        """
    ],

    [ "Rows in local2canonical table", None,
        """SELECT COUNT(*) cnt
           FROM local2canonical;
        """
    ],

    [ "Rows in raw_index table", None,
        """SELECT COUNT(*) cnt
           FROM raw_index;
        """
    ],

    [ "Rows in sheet_offsets table", None,
        """SELECT COUNT(*) cnt
           FROM sheet_offsets;
        """
    ],

    [ "Rows in src_priority table", None,
        """SELECT COUNT(*) cnt
           FROM src_priority;
        """
    ],
]

# --------------------------------------------------------------------------

def do_menu_stats( report ):
    fb = FB()
    s = Store()

    s.selectTab( MT.Reports )
    s.setTabVisible( MT.Reports, True )

    dc = s.dc

    res = []
    if report == 'all':
        res.extend( db_stats( dc, fb ))
        res.append( ['', ''] )
        res.extend( title_count_canon_src( dc, fb ))
        res.append( ['', ''] )
        res.extend( title_count_src( dc, fb ))
        res.append( ['', ''] )
        res.extend( title_coverage_by_canonical( dc, fb ))
        res.append( ['', ''] )
        res.extend( canon_coverage_alpha( dc, fb ))
        res.append( ['', ''] )
        res.extend( canon_coverage_count( dc, fb ))
        res.append( ['', ''] )
        res.extend( canon_missing_in_c2f( dc, fb ))
        res.append( ['', ''] )
        res.extend( c2f_missing_in_canon( dc, fb ) )
        res.append( ['', ''] )
        res.extend( canon_missing_in_l2c( dc, fb ) )
        res.append( ['', ''] )
        res.extend( c2f_missing_in_music( dc, fb ))
        res.append( ['', ''] )
        res.extend( canon_names( dc, fb ))
        res.append( ['', ''] )
        res.extend( top_forty( dc, fb))

    elif report == 'database':
        res.extend( db_stats( dc, fb ))

    elif report == 'title-count-canon-src':
        res.extend( title_count_canon_src( dc, fb ))

    elif report == 'title-count-src':
        res.extend( title_count_src( dc, fb ))

    elif report == 'title-coverage-by-canonical':
        res.extend( title_coverage_by_canonical( dc, fb ))

    elif report == 'dcanon-coverage-alpha':
        res.extend( canon_coverage_alpha( dc, fb ))

    elif report == 'canon-coverage-count':
        res.extend( canon_coverage_count( dc, fb ))

    elif report == 'canon-missing-c2f':
        res.extend( canon_missing_in_c2f( dc, fb ))

    elif report == 'c2f-missing-canon':
        res.extend( c2f_missing_in_canon( dc, fb ) )

    elif report == 'canon-missing-l2c':
        res.extend( canon_missing_in_l2c( dc, fb ) )

    elif report == 'canon-missing-music':
        res.extend( c2f_missing_in_music( dc, fb ))

    elif report == 'canonical-names':
        res.extend( canon_names( dc, fb ))

    elif report == 'top-forty':
        res.extend( top_forty( dc, fb))

    data = []
    for row in res:
        if len(row) == 2:
            # irow = [ QStandardItem(row[0]), QStandardItem(str(row[1])) ]
            irow = [ row[0], str(row[1]) ]
        else:
            # irow = [ QStandardItem(row[0]), '' ]
            irow = [ row[0], '' ]

        data.append( irow )

    s.sigman.emit( "sig_update_reports_table", data )


# ------------------------------------------------------------------------------
#   Make titles of reports bigger and bold.

def getTitle( txt ):
    item = QStandardItem( txt )
    font = QFont()
    font.setPointSize(10)   # Set the font size to 12 points
    font.setBold(True)      # Set the font to bold
    item.setFont(font)      # Apply the font to the QTableWidgetItem
    return item

# ------------------------------------------------------------------------------
#   DB Stats

def db_stats( dc, fb ):
    res = []

    res.append( [getTitle( 'Overall Statistics:'), ''] )

    for label, table, query in database_tables:

        if not query:
            query = f'SELECT COUNT(*) cnt FROM {table}'

        dc.execute( query )
        rows = dc.fetchall()

        for row in rows:
            res.append( [ f"   {label}", row['cnt']] )

    return res

# ------------------------------------------------------------------------------
#   Next, show stats that have to be described seperately

def title_count_canon_src( dc, fb ):
    res = []
    res.append( [getTitle( 'Title Count by Src and Canonical for Indexed Music Files:'), '' ] )

    query = """SELECT COUNT(*) cnt, title, src, local, canonical, file            
               FROM titles 
               JOIN titles_distinct USING( title_id )
               JOIN local2canonical USING( src, local )
               JOIN canonical2file USING( canonical )
               GROUP BY canonical, src
               ORDER BY canonical, src
            """

    dc.execute( query )
    rows = dc.fetchall()

    found = False
    for row in rows:
        res.append( [ f"   ({row['src']})   {row['canonical']}", row['cnt'] ] )
        found = True

    if not found:
        res.append( ['    None found', '' ] )

    return res

# ------------------------------------------------

def title_count_src( dc, fb ):
    res = []

    res.append( [getTitle('Title Count by Src for Indexed Music Files:'), ''] )

    query = """SELECT COUNT(*) cnt, title, src, local, canonical, file            
               FROM titles 
               JOIN titles_distinct USING( title_id )
               JOIN local2canonical USING( src, local )
               JOIN canonical2file USING( canonical )
               GROUP BY src
               ORDER BY src
    """
    dc.execute( query )
    rows = dc.fetchall()

    found = False
    for row in rows:
        res.append( [ f"   {row['src']}", row['cnt']] )
        found = True

    if not found:
        res.append( ['    None found', '' ] )

    return res

# ------------------------------------------------

def title_coverage_by_canonical( dc, fb ):
    res = []

    res.append( [getTitle( 'Title Coverage (title-count/page-count) by Src and Canonical for Indexed Music Files:'), ''] )
    res.append( ['    Coverage can exceed 100% because of multiple titles per page.', ''] )
    res.append( ['    Coverage can be less than 100% because of front and back matter, photos, etc.', ''] )
    res.append( ['    Coverage can be in the mid-range because of partial src coverage.', ''] )

    query = """SELECT 1.0 * COUNT(*) / page_count AS coverage, title, src, local, canonical, file, page_count, priority
               FROM titles
               JOIN titles_distinct USING( title_id )
               JOIN local2canonical USING( src, local )
               JOIN canonical2file USING( canonical )
               JOIN page_count USING( file )
               JOIN src_priority USING( src )
               GROUP BY canonical, src
               ORDER BY canonical, src
            """

    dc.execute( query )
    rows = dc.fetchall()

    found = False
    for row in rows:
        res.append( [ f"        ({row['src']})  {row['canonical']}", f"{row['coverage']:.0%}" ] )
        found = True

    if not found:
        res.append( ['    None found', '' ] )

    return res

# ------------------------------------------------
def OLD_canon_coverage_alpha( dc, fb ):
    res = []

    res.append( [ getTitle( 'Coverage of Canonical Books Ordered by Canonical Name:'), ''] )

    query = "SELECT canonical, src FROM local2canonical ORDER BY canonical, src"
    dc.execute( query )

    results = {}
    rows = dc.fetchall()
    for row in rows:
        canon = row[ 'canonical' ]
        src = row[ 'src' ]
        results.setdefault( canon, [] ).append( src )

    found = False
    for canon in results:
        res.append( [ f"   {canon}", ' '.join( results[ canon ] )] )
        found = True

    if not found:
        res.append( ['    None found', '' ] )

    return res

# ------------------------------------------------
#   WRW 29-May-2025 - Include title count for each src - Last feature?

def canon_coverage_alpha( dc, fb ):
    res = []

    res.append( [ getTitle( 'Coverage of Canonical Books Ordered by Canonical Name:'), ''] )

    query = """
        SELECT COUNT(*) cnt, src, canonical
        FROM  (
            SELECT src, canonical
            FROM local2canonical
            JOIN titles USING( src, local )
        ) AS sub
        GROUP BY canonical, src ORDER BY canonical, src     
    """

    dc.execute( query )

    results = {}
    rows = dc.fetchall()
    for row in rows:
        canon = row[ 'canonical' ]
        src = row[ 'src' ]
        cnt = row[ 'cnt' ]
        results.setdefault( canon, [] ).append( f'{src}: {cnt}' )

    found = False
    for canon in results:
        res.append( [ f"   {canon}", ', '.join( results[ canon ] )] )
        found = True

    if not found:
        res.append( ['    None found', '' ] )

    return res

# ------------------------------------------------

def OLD_canon_coverage_count( dc, fb ):

    res = []
    res.append( [getTitle('Coverage of Canonical Books Ordered Index Source Count:'), ''] )

    query = "SELECT canonical, src FROM local2canonical ORDER BY canonical, src"
    dc.execute( query )

    results = {}                # Dict indexed by canon, value is list of srcs
    rows = dc.fetchall()
    for row in rows:
        canon = row[ 'canonical' ]
        src = row[ 'src' ]
        results.setdefault( canon, [] ).append( src )

    #   Note: sorted() always returns a list, convert back to dict. Must use items(), too.
    results = sorted( results.items(), key = lambda x: len( x[1] ), reverse=True )
    results = dict( results )

    found = False
    for canon in results:
        res.append( [ f"   {canon}", ' '.join( results[ canon ] )] )
        found = True

    if not found:
        res.append( ['    None found', '' ] )

    return res

# ------------------------------------------------
#   WRW 29-May-2025 - Include title count for each src - Last feature?

def canon_coverage_count( dc, fb ):

    res = []
    res.append( [getTitle('Coverage of Canonical Books Ordered Index Source Count:'), ''] )

    query = """
        SELECT COUNT(*) cnt, src, canonical
        FROM  (
            SELECT src, canonical
            FROM local2canonical
            JOIN titles USING( src, local )
        ) AS sub
        GROUP BY canonical, src ORDER BY cnt DESC        
    """
    dc.execute( query )

    results = {}                # Dict indexed by canon, value is list of srcs
    rows = dc.fetchall()
    for row in rows:
        canon = row[ 'canonical' ]
        src = row[ 'src' ]
        cnt = row[ 'cnt' ]
        results.setdefault( canon, [] ).append( f'{src}: {cnt}' )

    #   Note: sorted() always returns a list, convert back to dict. Must use items(), too.
    results = sorted( results.items(), key = lambda x: len( x[1] ), reverse=True )
    results = dict( results )

    found = False
    for canon in results:
        res.append( [ f"   {canon}", ', '.join( results[ canon ] )] )
        found = True

    if not found:
        res.append( ['    None found', '' ] )

    return res

# ------------------------------------------------

def canon_missing_in_c2f( dc, fb ):
    res = []

    res.append( [getTitle('Canonical Names in Canonical Missing in Canonical2File:'), '' ] )
    res.append( ['Review to identify files in your library not yet linked to canonicals.', '' ] )
    query = """SELECT canonical, file FROM canonicals
            LEFT JOIN canonical2file USING( canonical )
            WHERE canonical2file.file is Null
            """
    dc.execute( query )

    rows = dc.fetchall()
    found = False
    for row in rows:
        res.append( [f"   {row['canonical']}",  '' ] )
        found = True

    if not found:
        res.append( ['    None found', '' ] )

    return res

# ------------------------------------------------
#   WRW 7 Apr 2022

def c2f_missing_in_canon( dc, fb ):
    res = []

    res.append( [getTitle('Canonical Names in Canonical2File Missing in Canonical:'), '' ] )
    query = """SELECT canonical FROM canonical2file
            LEFT JOIN canonicals USING( canonical )
            WHERE canonicals.canonical is Null
            """
    dc.execute( query )

    rows = dc.fetchall()
    found = False
    for row in rows:
        res.append( [f"   {row['canonical']}",  '' ] )
        found = True

    if not found:
        res.append( ['    None found', '' ] )

    return res

# ------------------------------------------------
#   WRW 7 Apr 2022

def canon_missing_in_l2c( dc, fb ):
    res = []

    res.append( [getTitle('Canonical Names in Local2Canonical Missing in Canonical:'), '' ] )
    query = """SELECT canonical, src, local FROM local2canonical
            LEFT JOIN canonicals USING( canonical )
            WHERE canonicals.canonical is Null
            """
    dc.execute( query )

    rows = dc.fetchall()
    found = False
    for row in rows:
        res.append( [f"   {row['canonical']}",  f"{row['src']:3}   {row['local']:20}"  ] )
        found = True

    if not found:
        res.append( ['    None found', '' ] )

    return res

# ------------------------------------------------

def c2f_missing_in_music( dc, fb ):
    s = Store()
    res = []

    res.append( [getTitle('Files in Canonical2File Missing in Music Library:'), '' ] )

    query = """SELECT file FROM canonical2file
            """

    dc.execute( query )
    rows = dc.fetchall()
    found = False
    for row in rows:
        file = row['file']
        path = os.path.join( s.conf.val( 'music_file_root' ), file )
        if not os.path.isfile( path ) or not os.access( path, os.R_OK):
            res.append( [f"   {file}",  '' ] )
            found = True

    if not found:
        res.append( ['    None found', '' ] )
    return res

# ------------------------------------------------

def top_forty( dc, fb):
    res = []
    res.append( [getTitle('Top 100 Titles in Music Index Ordered by Frequency:'), '' ] )

    query = """SELECT COUNT(*) cnt, title FROM titles
               JOIN titles_distinct USING( title_id )
               GROUP BY title
               ORDER BY cnt DESC
               LIMIT 102
            """

    dc.execute( query )
    rows = dc.fetchall()
    found = False
    for row in rows:
        cnt = row['cnt']
        title = row[ 'title' ]
        if False:   # WRW 28-May-2025 - remove _TitleFirst and _TitleLast
            if title == '_TitleFirst' or title == '_TitleLast':
                continue
        res.append( [ f"    {title}", cnt ] )
        found = True

    if not found:
        res.append( ['    None found', '' ] )

    return res


# ------------------------------------------------
#   WRW 31-May-2025 - Add list of just canonical names, not used
#       as part of another report.

def canon_names( dc, fb):
    res = []
    res.append( [getTitle('Canonical Book Names:'), '' ] )

    query = """SELECT canonical FROM canonicals
               ORDER BY canonical
            """

    dc.execute( query )
    rows = dc.fetchall()
    found = False
    for row in rows:
        canonical = row[ 'canonical' ]
        res.append( [ canonical ] )
        found = True

    if not found:
        res.append( ['None found' ] )

    return res

# --------------------------------------------------------------------------
