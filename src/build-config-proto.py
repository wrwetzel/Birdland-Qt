#!/usr/bin/python
# ---------------------------------------------------------------------------
#   WRW 3 Mar 2022 - Make a sanatized copy of birdland.conf in birdland.conf.proto
#   I got tired changing birdland.conf and then having to edit it for the proto version.
#   Source is ~/.birdland/birdland.conf or birdland.conf in directory given by --confdir.

#   WRW 4 Mar 2022 - Extract Host-specific tags from source so have only one point of definition.
# ---------------------------------------------------------------------------

from pathlib import Path
import datetime
from configobj import ConfigObj
import click
from Store import Store
from fb_config import Config
from bl_constants import Const

# ---------------------------------------------------------------------------

@click.command()
@click.option( "-c", "--confdir", help="Use alternate config directory" )

def do_main( confdir ):
    s = Store()
    s.Const = Const()

    if not confdir:
        confdir = s.Const.Confdir  
    userdatadir = s.Const.Datadir

    s.conf = Config( confdir, userdatadir  )

    conf_file = Path( confdir, s.Const.Config_File )
    config = ConfigObj( str( conf_file ) )

    # -------------------------------------------------------------------
    #   Preserve comments in hostname section as aid to user.

    config[ 'System' ][ 'database_user' ] = '***'
    config[ 'System' ][ 'database_password' ] = '***'

    for host in config[ 'Host' ]:                           # Traverse all hostname sections
        last_comments = config[ 'Host'][ host ].comments    # Save last comments for below
        last = config[ 'Host' ].pop( host )                 # Remove each hostname section and save last

    config[ 'Host' ][ 'ProtoHostnameSection' ] = { tag : '' for tag in last }                 # Init to empty values
    config[ 'Host' ][ 'ProtoHostnameSection' ]['canonical2file'] = 'Canonical2File.txt'       # Hard-wired name.
    config[ 'Host' ][ 'ProtoHostnameSection' ]['c2f_editable_map'] = 'Canonical2File.txt'     # Hard-wired name. WRW 29-May-2025 - Added.
    config[ 'Host' ][ 'ProtoHostnameSection' ].comments = { tag : last_comments[ tag ] for tag in last_comments }

    # ----------------------------------------------------------------------------
    #   Insert proto source and date/time at end of initial comment

    initial_comment = config.initial_comment

    s = datetime.datetime.today().strftime( '%a, %d-%b-%Y, %H:%M:%S')
    t = conf_file.relative_to( Path( '~' ).expanduser() )
    additional_comments = [ f'  This built from {t}', f'    on {s}', '']
    for x in additional_comments:
        initial_comment.insert( -2, x )

    config.initial_comment = initial_comment

    # ----------------------------------------------------------------------------
    #   Add comments to dummy ProtoHostnameSection.

    config[ 'Host' ].comments = {
        'ProtoHostnameSection' : [ '', 'This is a prototype for the hostname sub-section, which is',
                                        'added the first time Birdland is launched in each host.',
                                        'Do not change or remove it.',
                                        '' 
                                 ]
    }

    config.comments[ 'Host' ] = [ '', f"{'-'*50}", 'Sections here are for each host on which Birdland is run.', '' ]

    # -------------------------------------------------------------------

    proto_file = Path( '.', 'birdland.conf.proto' )
    config.filename = proto_file
    config.write()

# ---------------------------------------------------------------------------

if __name__ == '__main__':
    do_main( None )
