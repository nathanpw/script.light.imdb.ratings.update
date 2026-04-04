# -*- coding: utf-8 -*-

#############################
# Light IMDb Ratings Update #
# by axlt2002               #
#############################

import sys, os
import xbmcgui, xbmcplugin
from datetime import date
from six.moves import urllib
from update import StartUpdate
from core.database import update_database
from support.common import *

def main_menu():
	item = xbmcgui.ListItem(addonLanguage(32890))
	item.setArt({'thumb': addonIcon})
	xbmcplugin.addDirectoryItem(int(sys.argv[1]), "plugin://script.light.imdb.ratings.update/?url=&mode=1", item)
	item = xbmcgui.ListItem(addonLanguage(32891))
	item.setArt({'thumb': addonIcon})
	xbmcplugin.addDirectoryItem(int(sys.argv[1]), "plugin://script.light.imdb.ratings.update/?url=&mode=2", item)
	item = xbmcgui.ListItem(addonLanguage(32892))
	item.setArt({'thumb': addonIcon})
	xbmcplugin.addDirectoryItem(int(sys.argv[1]), "plugin://script.light.imdb.ratings.update/?url=&mode=3", item)
	xbmcplugin.endOfDirectory(int(sys.argv[1]))

def get_params():
	param=[]
	paramstring=sys.argv[2]
	if len(paramstring)>=2:
		params=sys.argv[2]
		cleanedparams=params.replace('?','')
		if (params[len(params)-1]=='/'):
			params=params[0:len(params)-2]
		pairsofparams=cleanedparams.split('&')
		param={}
		for i in range(len(pairsofparams)):
			splitparams={}
			splitparams=pairsofparams[i].split('=')
			if (len(splitparams))==2:
				param[splitparams[0]]=splitparams[1]                 
	return param

params=get_params()
url=None
name=None
mode=None
iconimage=None

try: url=urllib.unquote_plus(params["url"])
except: pass
try: name=urllib.unquote_plus(params["name"])
except: pass
try: mode=int(params["mode"])
except: pass
try: iconimage=urllib.unquote_plus(params["iconimage"])
except: pass

if mode == None:
	main_menu()
elif mode==1:
	StartUpdate()
elif mode==2:
	if not update_database():
		xbmcgui.Dialog().ok( "%s" % ( addonName ), addonLanguage(32257) )
	else:
		addonSettings.setSetting( "LastDatabaseUpdate", date.today().isoformat())
elif mode==3:
	addonSettings.openSettings()