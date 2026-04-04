# -*- coding: utf-8 -*-

#############################
# Light IMDb Ratings Update #
# by axlt2002               #
#############################

import xbmc
from core import update_main

def StartUpdate():
    update_main.perform_update()

if (__name__ == "__main__"):
    StartUpdate()