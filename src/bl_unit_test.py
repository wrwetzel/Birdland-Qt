# ------------------------------------------------------------------------
#   WRW 18-Apr-2025 - Encapsulate all includes more than needed for most,
#       and initialization needed for unit tests.
#       Returns s as obtained from Store() so caller does not have to.
# ------------------------------------------------------------------------

from functools import partial

from bl_constants import Const
from fb_utils import FB
from fb_config import Config
from Store import Store
from SignalManager import SigMan

# ------------------------------------------------------------------------

def UT( mysql=False ):
    s = Store()
    if mysql:
        s.driver = { 'mysql' : True, 'sqlite' : False, 'fullword' : False }
    else:
        s.driver = { 'mysql' : False, 'sqlite' : True, 'fullword' : False }

    s.Const = Const()
    confdir = s.Const.Confdir
    userdatadir = s.Const.Datadir

    s.conf = Config( confdir, userdatadir )
    s.conf.update_dict()
    s.fb = FB()
    s.sigman = SigMan()
    s.conf.get_config()
    s.conf.set_class_variables()

    s.msgInfo =     partial( print, "Info" )
    s.msgWarn =     partial( print, "Warn" )
    s.msgCritical = partial( print, "Critical" )
    s.msgQuestion = partial( print, "Question" )

    return s

# ------------------------------------------------------------------------
