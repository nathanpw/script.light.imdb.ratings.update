# -*- coding: utf-8 -*-

#############################
# Light IMDb Ratings Update #
# by axlt2002               #
#############################

import xbmc
import sys, re
from core import update_context

def UpdateContext():
    update_context.open_context_menu( sys.listitem.getPath(), sys.listitem.getLabel() )

if (__name__ == "__main__"):
    UpdateContext()