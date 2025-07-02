#!/usr/bin/python
# -----------------------------------------------------------------------
#   fb_search.py - Search functions, pulled out of birdland.py
#       WRW 30 Mar 2022

# -----------------------------------------------------------------------

from collections import defaultdict
from Store import Store

# -----------------------------------------------------------------------
#   Add a plus sign in front of each word in val.

def make_boolean( val ):
    parts = val.split()
    t = [ '+' + x for x in parts ]
    val = " ".join( t )
    return val

# --------------------------------------------------------------------------
#   Replace %s with ? if using SQLITE

def fix_query( query ):
    s = Store()
    MYSQL, SQLITE, FULLTEXT = s.driver.values()

    if SQLITE:
        query = query.replace( '%s', '?' )
    return query

# ---------------------------------------------------------------------------

def nested_dict(n, type):           # Small enough to just duplicate in a couple of sources.
    if n == 1:
        return defaultdict(type)
    else:
        return defaultdict(lambda: nested_dict(n-1, type))

# ---------------------------------------------------------------------------
#   Select one of each canonical by src priority
#   This, and the following, are now clean and simple. Not always so. It took quite
#   a while and a lot of frustration to figure out what I really wanted to do here.

def select_unique_canonicals( data ):
    results = []
    titles = nested_dict( 2, list )     # This is pretty cool.

    for row in data:            # Build dict by title and canonical containing incoming data
        titles[ row['title'] ][ row['canonical'] ].append( row )

    for title in titles:                                
        for canonical in titles[ title ]:
            row = sorted( titles[ title ][canonical], key = lambda x: int( x['src_priority']), reverse=False )[0]
            results.append( row )

    return results

# -----------------------------------------------------------------------
#   Select one of each src by canonical priority

def select_unique_srcs( data ):
    results = []
    titles = nested_dict( 2, list )     # So is this.

    for row in data:                    # Build a dict indexed by title and src
        titles[ row[ 'title' ] ][ row['src'] ].append( row )

    for title in titles:                                
        for src in titles[ title ]:
            row = sorted( titles[ title ][src], key = lambda x: int( x['canonical_priority']), reverse=False )[0]
            results.append( row )

    return results

# -----------------------------------------------------------------------
#   Select one of each title by canonical priority.
#   No need to deal further with srcs as they will disappear once I build the consolidated index.
#   WRW 9 Apr 2022 - Trying new approach using priority in canonical file.
#   Add priority columns to data, sort on canonical priority column, take first element, 
#        remove priority columns as last step before table update.

def select_unique_titles( data ):
    results = []
    titles = nested_dict( 1, list )     # This is pretty cool.

    for row in data:                    # Build dict by title
        title = row[ 'title' ]          # New named variables so we remember what we are doing.
        titles[ title ].append( row )

    #   Sort data for each title on canonical_priority_col and take top row.

    for title in titles:
        row = sorted( titles[ title ], key = lambda x: int( x['src_priority']), reverse=False )[0]
        results.append( row )

    return results

# -----------------------------------------------------------------------
#   WRW 10 Apr 2022 - Convert from dict to list and remove priority columns.

def strip_priority_data( data ):
    res = []
    for row in data:
        res.append( [ row['title'], 
                      row['composer'],
                      row['canonical'],
                      row['page'],
                      row['sheet'],
                      row['src'],
                      row['local'],
                      row['file'] 
                    ] )
    return res

# -----------------------------------------------------------------------

def do_query_music_file_index_with_join( title, composer, lyricist, album, artist, src, canonical ):

    s = Store()
    # fb = FB()
    # conf = Config()
    MYSQL, SQLITE, FULLTEXT = s.driver.values()

    Select_Limit = s.conf.val( 'select_limit' )

    table = []
    data = []
    wheres = []
    count = 0

    # query = "SET PROFILING = 1"
    # dc.execute( query )

    if title:
        if MYSQL:
            wheres.append( "MATCH( titles_distinct.title ) AGAINST( %s IN BOOLEAN MODE )" )
            data.append( title )

        if SQLITE:
            if FULLTEXT:
                wheres.append( f"""titles_distinct_fts.title MATCH ?""" )
                data.append( title )

            else:
                w, d = s.fb.get_fulltext( "titles_distinct.title", title )
                wheres.append( w )
                data.extend( d )

    if composer:
        if MYSQL:
            wheres.append( "MATCH( composer ) AGAINST( %s IN BOOLEAN MODE )" )
            data.append( composer )

        if SQLITE:
            if FULLTEXT:
                wheres.append( "composer MATCH ?" )
                data.append( composer )
            else:
                w, d = s.fb.get_fulltext( "composer", composer )
                wheres.append( w )
                data.extend( d )

    if lyricist:
        if MYSQL:
            wheres.append( "MATCH( lyricist ) AGAINST( %s IN BOOLEAN MODE )" )
            data.append( lyricist )

        if SQLITE:
            if FULLTEXT:
                wheres.append( f"""lyricist MATCH ?""" )
                data.append( lyricist )
            else:
                w, d = s.fb.get_fulltext( "lyricist", lyricist )
                wheres.append( w )
                data.extend( d )

    if src:
        if MYSQL:
            wheres.append( "titles.src = %s" )
            data.append( src )

        if SQLITE:
            if FULLTEXT:
                wheres.append( f"""titles.src MATCH ?""" )
                data.append( src )
            else:
                w, d = s.fb.get_fulltext( "titles.src", src )
                wheres.append( w )
                data.extend( d )

    if canonical:
        if MYSQL:
            wheres.append( "MATCH( local2canonical.canonical ) AGAINST( %s IN BOOLEAN MODE )" )
            data.append( canonical )

        if SQLITE:
            if FULLTEXT:
                wheres.append( f"""local2canonical.canonical MATCH ?""" )
                data.append( canonical )
            else:
                w, d = s.fb.get_fulltext( "local2canonical.canonical", canonical )
                wheres.append( w )
                data.extend( d )

    if album:
        if MYSQL:
            wheres.append( """titles_distinct.title IN
                                   ( SELECT title FROM audio_files
                                     WHERE MATCH( album ) AGAINST( %s IN BOOLEAN MODE ) )
                           """ )
            data.append( album )

        if SQLITE:
            if FULLTEXT:
                wheres.append( """titles_distinct.title IN
                    ( SELECT title FROM audio_files
                      WHERE album MATCH ? ) """ )
                data.append( album )
            else:
                w, d = s.fb.get_fulltext( "album", album )
                wheres.append( f"""titles_distinct.title IN
                                   ( SELECT title FROM audio_files WHERE {w} )
                                """ )
                data.extend( d )

    if artist:
        if MYSQL:
            wheres.append( """titles_distinct.title IN
                               ( SELECT title FROM audio_files
                                 WHERE MATCH( artist ) AGAINST( %s IN BOOLEAN MODE ) )
                           """ )
            data.append( artist )

        if SQLITE:
            if FULLTEXT:
                wheres.append( """titles_distinct.title IN
                    ( SELECT title FROM audio_files
                      WHERE artist MATCH ? ) """ )
                data.append( album )
            else:
                w, d = s.fb.get_fulltext( "artist", artist )
                wheres.append( f"""titles_distinct.title IN
                                   ( SELECT title FROM audio_files WHERE {w} )
                                """ )
                data.extend( d )


    # -----------------------------------------------------------------------
    #   WRW 24 Feb 2022 - I think I screwed up 'include_titles_missing_file' settings considering
    #       it for local2canonical instead of canonical2file.

    if len( data ):
        where_clauses = "WHERE " + " AND ".join( wheres )

        # local2canonical_join = 'JOIN local2canonical USING( local, src )'
        local2canonical_join = 'JOIN local2canonical ON (local2canonical.local = titles.local AND local2canonical.src = titles.src)'

        if s.conf.val( 'include_titles_missing_file' ):
            # canonical2file_join = 'LEFT JOIN canonical2file USING( canonical )'
            canonical2file_join = 'LEFT JOIN canonical2file ON canonical2file.canonical = canonicals.canonical'
        else:
            # canonical2file_join = 'JOIN canonical2file USING( canonical )'
            canonical2file_join = 'JOIN canonical2file ON canonical2file.canonical = canonicals.canonical'

        # ---------------------------------------------------------------------------
        if MYSQL:
            query = f"""
                SELECT titles_distinct.title, titles.composer, titles.sheet, titles.src, titles.local,
                local2canonical.canonical, canonical2file.file,
                src_priority.priority AS src_priority, canonicals.priority AS canonical_priority /* WRW 9 Apr 2022 - added */
                FROM titles_distinct
                JOIN titles USING( title_id )
                JOIN src_priority ON src_priority.src = titles.src                      /* WRW 9 Apr 2022 - added */
                {local2canonical_join}
                JOIN canonicals ON canonicals.canonical = local2canonical.canonical     /* WRW 9 Apr 2022 - added */
                {canonical2file_join}
                {where_clauses}
                ORDER BY titles_distinct.title, local2canonical.canonical, titles.src   
                LIMIT {Select_Limit}
            """

        # ---------------------------------------------------------------------------
        #   This was a real pain to get working. Turns out that fullword search in sqlite3 can't
        #   have an ORDER BY clause for anything but rank, at least that's what appears to be the
        #   case from some toy tests.
        #   WRW 10 Apr 2022 - Looks like sqlite3 and mysql treat JOIN a bit differently. After
        #   additions of 9 Apr 2022 mysql complained but sqlite3 did not. Had to change
        #   order of JOIN to resolve.

        if SQLITE:
            if FULLTEXT:
                query = f"""
                    SELECT titles_distinct_fts.title,
                    titles.composer, titles.sheet, titles.src, titles.local,
                    local2canonical.canonical, canonical2file.file,
                    src_priority.priority AS src_priority, canonicals.priority AS canonical_priority /* WRW 9 Apr 2022 - added */
                    FROM titles_distinct_fts
                    JOIN titles USING( title_id )
                    JOIN src_priority ON src_priority.src = titles.src                      /* WRW 9 Apr 2022 - added */
                    {local2canonical_join}
                    JOIN canonicals ON canonicals.canonical = local2canonical.canonical     /* WRW 9 Apr 2022 - added */
                    {canonical2file_join}
                    {where_clauses}
                    ORDER BY rank
                    LIMIT {Select_Limit}
                """

            else:
                query = f"""
                    SELECT titles_distinct.title,
                    titles.composer, titles.sheet, titles.src, titles.local,
                    local2canonical.canonical, canonical2file.file,
                    src_priority.priority AS src_priority, canonicals.priority AS canonical_priority    /* WRW 9 Apr 2022 - added */
                    FROM titles_distinct
                    JOIN titles USING( title_id )
                    JOIN src_priority ON src_priority.src = titles.src                      /* WRW 9 Apr 2022 - added */
                    {local2canonical_join}
                    JOIN canonicals ON canonicals.canonical = local2canonical.canonical     /* WRW 9 Apr 2022 - added */
                    {canonical2file_join}
                    {where_clauses}
                    ORDER BY titles_distinct.title, local2canonical.canonical, titles.src   
                    LIMIT {Select_Limit}
                """

        query = fix_query( query )      # Replace %s with ? for SQLITE

        if False:
            print( "Query", query )
            print( "Data", data )

        # ---------------------------------------------------------------------
        #   WRW 10 Apr 2022 - switch from list to dict.
        #   Only sheet, not page, is in the titles table.
        #   Populate page column of table with results of get_page_from_sheet.

        s.dc.execute( query, data )
        rows = s.dc.fetchall()

        # headings = [ "Title", "Composer", "Canonical Book Name", "Page", "Sheet", "Source", "Local Book Name", "File" ],

        if rows:
            for row in rows:
                # title = row[ 'title' ]
                # composer = row[ 'composer' ]
                # canonical = row[ 'canonical' ]
                # sheet = row[ 'sheet' ]
                # src = row[ 'src' ]
                # file = row[ 'file' ]
                # local = row[ 'local' ]
                # src_priority = row[ 'src_priority' ]             # WRW 9 Apr 2022 - added
                # canonical_priority = row[ 'canonical_priority' ]                              # WRW 9 Apr 2022 - added

                # page = s.fb.get_page_from_sheet( sheet, src, local )
                page = s.fb.get_page_from_sheet( row[ 'sheet' ], row[ 'src' ], row[ 'local' ] )

                # table.append( [ src_priority, canonical_priority, title, composer, canonical, page, sheet, src, local, file ] )

                table.append( { 'src_priority' : row[ 'src_priority' ],
                                'canonical_priority' : row[ 'canonical_priority' ],
                                'title' : row[ 'title' ],
                                'composer' : row[ 'composer' ],
                                'canonical' : row[ 'canonical' ],
                                'page' : page,
                                'sheet' : row[ 'sheet' ],
                                'src' : row[ 'src' ],
                                'local' : row[ 'local' ],
                                'file' : row[ 'file' ]
                               } )

        if MYSQL:
            query = f"""
                SELECT count(*) cnt
                FROM titles_distinct
                JOIN titles USING( title_id )
                {local2canonical_join}
                {where_clauses}
            """
        if SQLITE:
            if FULLTEXT:
                query = f"""
                    SELECT count(*) cnt
                    FROM titles_distinct_fts
                    JOIN titles USING( title_id )
                    {local2canonical_join}
                    {where_clauses}
                """
            else:
                query = f"""
                    SELECT count(*) cnt
                    FROM titles_distinct
                    JOIN titles USING( title_id )
                    {local2canonical_join}
                    {where_clauses}
                """

        query = fix_query( query )
        s.dc.execute( query, data )
        count = s.dc.fetchone()[ 'cnt' ]

    return (table, count)

# --------------------------------------------------------------------------
#   WRW 19 Feb 2022 - Toyed around with searching filename in audio_files
#       but don't think it is a good idea. Nothing in filename not already
#       in the metadata

#   wheres.append( "MATCH( file ) AGAINST( %s IN BOOLEAN MODE )" )
#   data.append( title )

#   wheres.append( f"""file MATCH ?""" )
#   data.append( title )

#   w, d = fb.get_fulltext( "file", title )
#   wheres.append( w )
#   data.extend( d )

def do_query_audio_files_index( title, album, artist ):
    s = Store()
    Select_Limit = s.Settings( 'select_limit' )
    MYSQL, SQLITE, FULLTEXT = s.driver.values()

    table = []
    wheres = []
    data = []
    count = 0

    if title:
        if MYSQL:
            wheres.append( "MATCH( title ) AGAINST( %s IN BOOLEAN MODE )" )
            data.append( title )

        if SQLITE:
            if FULLTEXT:
                wheres.append( f"""title MATCH ?""" )
                data.append( title )

            else:
                w, d = s.fb.get_fulltext( "title", title )
                wheres.append( w )
                data.extend( d )

    if album:
        if MYSQL:
            wheres.append( "MATCH( album ) AGAINST( %s IN BOOLEAN MODE )" )
            data.append( album )

        if SQLITE:
            if FULLTEXT:
                wheres.append( f"""album MATCH ?""" )
                data.append( album )
            else:
                w, d = s.fb.get_fulltext( "album", album )
                wheres.append( w )
                data.extend( d )

    if artist:
        if MYSQL:
            wheres.append( "MATCH( artist ) AGAINST( %s IN BOOLEAN MODE )" )
            data.append( artist)

        if SQLITE:
            if FULLTEXT:
                wheres.append( f"""artist MATCH ?""" )
                data.append( artist )
            else:
                w, d = s.fb.get_fulltext( "artist", artist )
                wheres.append( w )
                data.extend( d )

    # ---------------------------------------------------

    if len( data ):
        where = "WHERE " + " AND ".join( wheres )

        if MYSQL:
            query = f"""
                SELECT title, artist, album, file
                FROM audio_files
                {where}
                ORDER BY title, artist   
                LIMIT {Select_Limit}
            """
        if SQLITE:
            if FULLTEXT:
                query = f"""
                    SELECT title, artist, album, file
                    FROM audio_files_fts
                    {where}
                    ORDER BY title, artist   
                    LIMIT {Select_Limit}
                """
            else:
                query = f"""
                    SELECT title, artist, album, file
                    FROM audio_files
                    {where}
                    ORDER BY title, artist   
                    LIMIT {Select_Limit}
                """

        query = fix_query( query )
        s.dc.execute( query, data )
        rows = s.dc.fetchall()

        if rows:
            for row in rows:
                table.append( { 'title' : row[ 'title' ],
                                'artist' : row[ 'artist' ],
                                'album' : row[ 'album' ],
                                'file' : row[ 'file' ],
                               } )
        if MYSQL:
            query = f"""
                SELECT COUNT(*) cnt
                FROM audio_files
                {where}
            """
        if SQLITE:
            if FULLTEXT:
                query = f"""
                    SELECT COUNT(*) cnt
                    FROM audio_files_fts
                    {where}
                """
            else:
                query = f"""
                    SELECT COUNT(*) cnt
                    FROM audio_files    
                    {where}
                """

        query = fix_query( query )
        s.dc.execute( query, data )
        count = s.dc.fetchone()[ 'cnt' ]

    return table, count

# --------------------------------------------------------------------------

def do_query_music_filename( title ):
    s = Store()
    Select_Limit = s.Settings( 'select_limit' )
    MYSQL, SQLITE, FULLTEXT = s.driver.values()

    table = []
    wheres = []
    data = []
    count = 0

    if title:
        if MYSQL:
            wheres.append( "MATCH( rpath ) AGAINST( %s IN BOOLEAN MODE )" )
            data.append( title )

            wheres.append( "MATCH( file ) AGAINST( %s IN BOOLEAN MODE )" )
            data.append( title )

        if SQLITE:
            if FULLTEXT:
                wheres.append( f"""rpath MATCH ?""" )
                data.append( title )

                wheres.append( f"""file MATCH ?""" )
                data.append( title )

            else:
                w, d = s.fb.get_fulltext( "rpath", title )
                wheres.append( w )
                data.extend( d )

                w, d = s.fb.get_fulltext( "file", title )
                wheres.append( w )
                data.extend( d )

    if len( data ):

        where = "WHERE " + " OR ".join( wheres )

        if MYSQL:
            query = f"""
                SELECT rpath, file
                FROM music_files
                {where}
                ORDER BY rpath, file
                LIMIT {Select_Limit}
            """
        if SQLITE:
            if FULLTEXT:
                query = f"""
                    SELECT rpath, file
                    FROM music_files_fts
                    {where}
                    ORDER BY rpath, file   
                    LIMIT {Select_Limit}
                """
            else:
                query = f"""
                    SELECT rpath, file
                    FROM music_files
                    {where}
                    ORDER BY rpath, file   
                    LIMIT {Select_Limit}
                """

        query = fix_query( query )
        s.dc.execute( query, data )
        rows = s.dc.fetchall()

        if rows:
            for row in rows:
                table.append( { 'path' : row[ 'rpath' ], 
                                'file' : row[ 'file' ]
                              } )

        if MYSQL:
            query = f"""
                SELECT COUNT(*) cnt
                FROM music_files
                {where}
                LIMIT {Select_Limit}
            """
        if SQLITE:
            if FULLTEXT:
                query = f"""
                    SELECT COUNT(*) cnt
                    FROM music_files_fts
                    {where}
                    LIMIT {Select_Limit}
                """
            else:
                query = f"""
                    SELECT COUNT(*) cnt
                    FROM music_files
                    {where}
                    LIMIT {Select_Limit}
                """

        query = fix_query( query )
        s.dc.execute( query, data )
        count = s.dc.fetchone()[ 'cnt' ]

    return table, count

# --------------------------------------------------------------------------

def do_query_midi_filename( title, composer ):
    s = Store()
    Select_Limit = s.Settings( 'select_limit' )
    MYSQL, SQLITE, FULLTEXT = s.driver.values()

    table = []
    wheres = []
    data = []
    count = 0

    if title:
        if MYSQL:
            wheres.append( "MATCH( rpath ) AGAINST( %s IN BOOLEAN MODE )" )
            data.append( title )

            wheres.append( "MATCH( file ) AGAINST( %s IN BOOLEAN MODE )" )
            data.append( title )

            wheres.append( "MATCH( title ) AGAINST( %s IN BOOLEAN MODE )" )
            data.append( title )

        if SQLITE:
            if FULLTEXT:
                wheres.append( "rpath MATCH ?" )
                data.append( title )

                wheres.append( "file MATCH ?" )
                data.append( title )

                wheres.append( "title MATCH ?" )
                data.append( title )

            else:
                w, d = s.fb.get_fulltext( "rpath", title, full=False )
                wheres.append( w )
                data.extend( d )

                w, d = s.fb.get_fulltext( "file", title, full=False  )
                wheres.append( w )
                data.extend( d )

                w, d = s.fb.get_fulltext( "title", title, full=False  )
                wheres.append( w )
                data.extend( d )

    if composer:
        if MYSQL:
            wheres.append( "MATCH( composer ) AGAINST( %s IN BOOLEAN MODE )" )
            data.append( composer )

        if SQLITE:
            if FULLTEXT:
                wheres.append( "composer MATCH ?" )
                data.append( composer )
            else:
                w, d = s.fb.get_fulltext( "composer", composer, full=False )
                wheres.append( w )
                data.extend( d )

    if len( data ):
        where = "WHERE " + " OR ".join( wheres )
        if MYSQL:
            query = f"""
                SELECT title, composer, rpath, file
                FROM midi_files    
                {where}
                ORDER BY title, rpath, file
                LIMIT {Select_Limit}
            """
        if SQLITE:
            if FULLTEXT:
                query = f"""
                    SELECT title, composer, rpath, file
                    FROM midi_files_fts
                    {where}
                    ORDER BY title, rpath, file
                    LIMIT {Select_Limit}
                """
            else:
                query = f"""
                    SELECT title, composer, rpath, file
                    FROM midi_files
                    {where}
                    ORDER BY title, rpath, file
                    LIMIT {Select_Limit}
                """

        query = fix_query( query )

        s.dc.execute( query, data )
        rows = s.dc.fetchall()

        if rows:
            for row in rows:
                table.append( { 'path' : row[ 'rpath' ], 
                                'file' : row[ 'file' ],
                                'title' : row[ 'title' ],
                                'composer' : row[ 'composer' ],
                              } )

        if MYSQL:
            query = f"""
                SELECT COUNT(*) cnt
                FROM midi_files
                {where}
                LIMIT {Select_Limit}
            """
        if SQLITE:
            if FULLTEXT:
                query = f"""
                    SELECT COUNT(*) cnt
                    FROM midi_files_fts
                    {where}
                    LIMIT {Select_Limit}
                """
            else:
                query = f"""
                    SELECT COUNT(*) cnt
                    FROM midi_files
                    {where}
                    LIMIT {Select_Limit}
                """

        query = fix_query( query )
        s.dc.execute( query, data )
        count = s.dc.fetchone()[ 'cnt' ]

    return table, count

# --------------------------------------------------------------------------

def do_query_chordpro( title, artist ):
    s = Store()
    Select_Limit = s.Settings( 'select_limit' )
    MYSQL, SQLITE, FULLTEXT = s.driver.values()

    table = []
    wheres = []
    data = []
    count = 0

    if title:
        if MYSQL:
            wheres.append( "MATCH( title ) AGAINST( %s IN BOOLEAN MODE )" )
            data.append( title )

        if SQLITE:
            if FULLTEXT:
                wheres.append( "title MATCH ?" )
                data.append( title )

            else:
                w, d = s.fb.get_fulltext( "title", title )
                wheres.append( w )
                data.extend( d )

    if artist:
        if MYSQL:
            wheres.append( "MATCH( artist ) AGAINST( %s IN BOOLEAN MODE )" )
            data.append( artist )

        if SQLITE:
            if FULLTEXT:
                wheres.append( "artist MATCH ?" )
                data.append( artist )

            else:
                w, d = s.fb.get_fulltext( "artist", artist )
                wheres.append( w )
                data.extend( d )

    if len( data ):
        where = "WHERE " + " AND ".join( wheres )
        if MYSQL:
            query = f"""
                SELECT title, artist, file
                FROM chordpro_files
                {where}
                ORDER BY title, artist, file
                LIMIT {Select_Limit}
            """
        if SQLITE:
            if FULLTEXT:
                query = f"""
                    SELECT title, artist, file
                    FROM chordpro_files_fts
                    {where}
                    ORDER BY title, artist, file
                    LIMIT {Select_Limit}
                """
            else:
                query = f"""
                    SELECT title, artist, file
                    FROM chordpro_files
                    {where}
                    ORDER BY title, artist, file
                    LIMIT {Select_Limit}
                """

        query = fix_query( query )

        s.dc.execute( query, data )
        rows = s.dc.fetchall()

        if rows:
            for row in rows:
                table.append( { 'title' : row[ 'title' ],
                                'artist' : row[ 'artist' ],
                                'file' : row[ 'file' ]
                              } )
        if MYSQL:
            query = f"""
                SELECT COUNT(*) cnt
                FROM chordpro_files
                {where}
                LIMIT {Select_Limit}
            """
        if SQLITE:
            if FULLTEXT:
                query = f"""
                    SELECT COUNT(*) cnt
                    FROM chordpro_files_fts
                    {where}
                    LIMIT {Select_Limit}
                """
            else:
                query = f"""
                    SELECT COUNT(*) cnt
                    FROM chordpro_files
                    {where}
                    LIMIT {Select_Limit}
                """

        query = fix_query( query )
        s.dc.execute( query, data )
        count = s.dc.fetchone()[ 'cnt' ]

    return table, count

# --------------------------------------------------------------------------

def do_query_jjazz_filename( title ):
    s = Store()
    Select_Limit = s.Settings( 'select_limit' )
    MYSQL, SQLITE, FULLTEXT = s.driver.values()

    table = []
    wheres = []
    data = []
    count = 0

    if title:
        if MYSQL:
            wheres.append( "MATCH( title ) AGAINST( %s IN BOOLEAN MODE )" )
            data.append( title )

        if SQLITE:
            if FULLTEXT:
                wheres.append( "title MATCH ?" )
                data.append( title )

            else:
                w, d = s.fb.get_fulltext( "title", title )
                wheres.append( w )
                data.extend( d )

    if len( data ):
        where = "WHERE " + " OR ".join( wheres )
        if MYSQL:
            query = f"""
                SELECT title, file
                FROM jjazz_files
                {where}
                ORDER BY title, file
                LIMIT {Select_Limit}
            """
        if SQLITE:
            if FULLTEXT:
                query = f"""
                    SELECT title, file
                    FROM jjazz_files_fts
                    {where}
                    ORDER BY title, file
                    LIMIT {Select_Limit}
                """
            else:
                query = f"""
                    SELECT title, file
                    FROM jjazz_files
                    {where}
                    ORDER BY title, file
                    LIMIT {Select_Limit}
                """

        query = fix_query( query )

        s.dc.execute( query, data )
        rows = s.dc.fetchall()

        if rows:
            for row in rows:
                table.append( { 'title' : row[ 'title' ],
                                'file' : row[ 'file' ]
                              } )
        if MYSQL:
            query = f"""
                SELECT COUNT(*) cnt
                FROM jjazz_files
                {where}
                LIMIT {Select_Limit}
            """
        if SQLITE:
            if FULLTEXT:
                query = f"""
                    SELECT COUNT(*) cnt
                    FROM jjazz_files_fts
                    {where}
                    LIMIT {Select_Limit}
                """
            else:
                query = f"""
                    SELECT COUNT(*) cnt
                    FROM jjazz_files
                    {where}
                    LIMIT {Select_Limit}
                """

        query = fix_query( query )
        s.dc.execute( query, data )
        count = s.dc.fetchone()[ 'cnt' ]

    return table, count

# --------------------------------------------------------------------------
#   WRW 23-May-2025 - remove duration from select, no longer in title2youtube

def do_query_youtube_index( title ):
    s = Store()
    Select_Limit = s.Settings( 'select_limit' )
    MYSQL, SQLITE, FULLTEXT = s.driver.values()

    table = []
    data = []
    count = 0

    if title:
        if MYSQL:
            # title2youtube.duration,
            query = f"""
                SELECT titles_distinct.title,
                title2youtube.ytitle, title2youtube.yt_id
                FROM titles_distinct
                JOIN title2youtube ON title2youtube.title_id = titles_distinct.title_id
                WHERE MATCH( titles_distinct.title ) AGAINST( %s IN BOOLEAN MODE )
                ORDER BY titles_distinct.title, title2youtube.ytitle   
                LIMIT {Select_Limit}
            """
            data.append( title )

        if SQLITE:
            if FULLTEXT:
                # title2youtube.duration,
                query = f"""
                    SELECT title,
                    title2youtube.ytitle, title2youtube.yt_id
                    FROM titles_distinct_fts
                    JOIN title2youtube USING( title_id )
                    WHERE titles_distinct_fts.title MATCH ?
                    ORDER BY titles_distinct.title, title2youtube.ytitle   
                    LIMIT {Select_Limit}
                """
                data.append( title )

            else:
                w, d = s.fb.get_fulltext( "titles_distinct.title", title )
                data.extend( d )

                # title2youtube.duration,
                query = f"""
                    SELECT title,
                    title2youtube.ytitle, title2youtube.yt_id
                    FROM titles_distinct
                    JOIN title2youtube USING( title_id )
                    WHERE {w}
                    ORDER BY titles_distinct.title, title2youtube.ytitle   
                    LIMIT {Select_Limit}
                """

        query = fix_query( query )

    # --------------------------------------------------------------------

    if len( data ):
        s.dc.execute( query, data )
        rows = s.dc.fetchall()

        if rows:
            for row in rows:
                title = row[ 'title' ]
                ytitle = row[ 'ytitle' ]
                # duration = row[ 'duration' ]
                yt_id = row[ 'yt_id' ]
                # table.append( { 'title': title, 'ytitle': ytitle, 'duration':duration, 'yt_id': yt_id } )
                table.append( { 'title': title, 'ytitle': ytitle, 'yt_id': yt_id } )

        # data = []
        if MYSQL:
            query = f"""
                SELECT COUNT(*) cnt
                FROM titles_distinct
                JOIN title2youtube ON title2youtube.title_id = titles_distinct.title_id
                WHERE MATCH( titles_distinct.title ) AGAINST( %s IN BOOLEAN MODE )
            """
            # data.append( title )

        if SQLITE:
            if FULLTEXT:
                query = f"""
                    SELECT COUNT(*) cnt
                    FROM titles_distinct_fts
                    JOIN title2youtube USING( title_id )
                    WHERE titles_distinct_fts.title MATCH ?
                """
                # data.append( title )

            else:
                # w, d = s.fb.get_fulltext( "titles_distinct.title", title )
                query = f"""
                    SELECT COUNT(*) cnt
                    FROM titles_distinct
                    JOIN title2youtube USING( title_id )
                    WHERE {w}
                """
                # data.extend( d )

        query = fix_query( query )
        s.dc.execute( query, data )
        count = s.dc.fetchone()[ 'cnt' ]

    return table, count

# --------------------------------------------------------------------------
#   WRW 2-Mar-2025 - Moved from bl_media.py

def get_audio_from_titles( title ):
    s = Store()
    MYSQL, SQLITE, FULLTEXT = s.driver.values()

    if MYSQL:
        query = f"""
            SELECT title, artist, file
            FROM audio_files
            WHERE title = %s
        """

    if SQLITE:
        query = f"""
            SELECT title, artist, file
            FROM audio_files
            WHERE title = ?
        """

    data = (title,)
    s.dc.execute( query, data )
    rows = s.dc.fetchall()

    res = [ [row[ 'title' ], row[ 'artist' ], row[ 'file' ] ] for row in rows ] if rows else []

    return res

# --------------------------------------------------------------------------
#   WRW 2-Mar-2025 - Moved from bl_media.py

def get_midi_from_titles( title ):
    s = Store()
    MYSQL, SQLITE, FULLTEXT = s.driver.values()
    data = []

    if MYSQL:
        title = make_boolean( title )
        query = f"""
            SELECT rpath, file
            FROM midi_files
            WHERE MATCH( file ) AGAINST ( %s IN BOOLEAN MODE )
            ORDER BY file
        """
        data.append( title )

    if SQLITE:
        if FULLTEXT:
            query = f"""
                SELECT rpath, file
                FROM midi_files_fts
                WHERE file MATCH ?
                ORDER BY rank
            """
            data.append( title )

        else:
            w, d = s.fb.get_fulltext( "file", title )
            query = f"""
                SELECT rpath, file
                FROM midi_files
                WHERE {w}
                ORDER BY file
            """
            data.extend( d )

    # parts = title.split()
    # t = [ f'+{x}' for x in parts if len(x) >= 4]
    # title = " ".join( t )

    # print( query )
    # print( data )

    s.dc.execute( query, data )
    rows = s.dc.fetchall()

    res = [ [row[ 'rpath'], row[ 'file' ]] for row in rows ] if rows else []

    return res

# --------------------------------------------------------------------------
#   WRW 19-Jan-2025 - Quick and dirty test to identify bare minimum needed
#       to use fb_search.py module

#       /// later clean up to use conf facility, test other search items.

if __name__ == '__main__':

    import sys
    import sqlite3
    from pathlib import Path
    from bl_unit_test import UT
    from bl_style import StyleSheet

    s = UT()

    path = Path( s.conf.user_data_directory, s.conf.sqlite_database )

    if path.is_file():
        try:
            conn = sqlite3.connect( path )
            c = conn.cursor()
            dc = conn.cursor()
            dc.row_factory = sqlite3.Row

        except Exception as e:
            (extype, value, traceback) = sys.exc_info()
            print( f"ERROR on connect() or cursor(), type: {extype}, value: {value}", file=sys.stderr )

        else:
            s.dc = dc
            conn.create_function('my_match_c', 2, s.fb.my_match_c ) # This works great and is fast.

            data, pdf_count = do_query_music_file_index_with_join( "Bess", None, None, None, None, None, None )

            print( f"Pdf count: {pdf_count}" )
            for row in data:
                for k, v in row.items():
                    print( k, v )
                print( "" )

# --------------------------------------------------------------------------
