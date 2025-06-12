# -*- coding: utf-8 -*-

#############################
# Light IMDb Ratings Update #
# by axlt2002               #
#############################

import json, sys

import xbmc, xbmcaddon, xbmcvfs, xbmcgui
import os, unicodedata
from datetime import datetime

try:
    xbmc.translatePath = xbmcvfs.translatePath
except AttributeError:
    pass

addonSettings = xbmcaddon.Addon( "script.light.imdb.ratings.update" )
addonName     = addonSettings.getAddonInfo( "name" )
addonVersion  = addonSettings.getAddonInfo( "version" )
addonIcon     = os.path.join( addonSettings.getAddonInfo( "path" ), "icon.png" )
addonProfile  = xbmc.translatePath( addonSettings.getAddonInfo( "profile" ) )
addonLanguage = addonSettings.getLocalizedString

onMovies          = addonSettings.getSetting( "Movies" )
onTVShows         = addonSettings.getSetting( "TVShows" )
ShowNotifications = addonSettings.getSetting( "ShowNotifications" )
ShowProgress      = addonSettings.getSetting( "ShowProgress" )
ShowLogMessage    = addonSettings.getSetting( "ShowLogMessage" )
CompleteLog       = addonSettings.getSetting( "CompleteLog" )
IncludeEpisodes   = addonSettings.getSetting( "IncludeEpisodes" )
UpdateMode        = addonSettings.getSetting( "UpdateMode" )
match int(addonSettings.getSetting( "UpdateTime" )):
	case 1:
		UpdateTime = 32
	case 2:
		UpdateTime = 93
	case 3:
		UpdateTime = 183
	case 4:
		UpdateTime = 366
	case _:
		UpdateTime = 0
IMDbDefault       = addonSettings.getSetting( "IMDbRatingDefault" )
Sound             = addonSettings.getSetting( "NotificationsSound" )
ScheduleEnabled   = addonSettings.getSetting( "ScheduleEnabled" )
ScheduledWeekDay  = addonSettings.getSetting( "ScheduledWeekDay" )
DayTime           = addonSettings.getSetting( "DayTime" )

def_threads = [8, 16, 1, 2, 4]
NumberOfThreads = def_threads[int(addonSettings.getSetting( "NumberOfThreads" ))]

def doUnicode( textMessage ):
    try: textMessage = unicode( textMessage, 'utf-8' )
    except: pass
    return textMessage

def doNormalize( textMessage ):
    try: textMessage = unicodedata.normalize( 'NFKD', doUnicode( textMessage ) ).encode( 'utf-8' )
    except: pass
    return textMessage

def defaultLog( textMessage ):
    xbmc.log( "[%s] - %s" % ( addonName, doNormalize( textMessage ) ) )

def debugLog( textMessage ):
    xbmc.log( "[%s] - %s" % ( addonName, doNormalize( textMessage ) ), level = xbmc.LOGDEBUG )

def doNotify( textMessage, millSec ):
    dialog = xbmcgui.Dialog()
    if Sound == "true":
        playSound = True
    else:
        playSound = False
    dialog.notification(addonName, textMessage, addonIcon, millSec, playSound)

def start_StatusLog():
	if xbmcvfs.exists( addonProfile + "/update.old.log" ):
		os.remove( addonProfile + "/update.old.log" )
	if xbmcvfs.exists( addonProfile + "/update.log" ):
		os.rename( addonProfile + "/update.log", addonProfile + "/update.old.log" )
	f = open( addonProfile + "/update.log", 'wb' )
	f.write( doNormalize( "----------------------------------------------------------------------------------------------------------------\n" ) )
	f.write( doNormalize( "Starting " + addonName + " (" + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ")\n" ) )
	f.write( doNormalize( "Add-on version: " + addonVersion + "\n" ) )
	f.write( doNormalize( "Kodi version: " + get_kodi_version() + "\n" ) )
	f.write( doNormalize( "onMovies: " + onMovies + "\n" ) )
	f.write( doNormalize( "onTVShows: " + onTVShows + "\n" ) )
	f.write( doNormalize( "ScheduleEnabled: " + ScheduleEnabled + "\n" ) )
	if ScheduleEnabled == "true":
		f.write( doNormalize( addonLanguage(32655) % (ScheduledWeekDay, DayTime) + "\n" ) )
	f.write( doNormalize( "----------------------------------------------------------------------------------------------------------------\n" ) )
	f.close()

def dump_settings_StatusLog( updateitem ):
	f = open( addonProfile + "/update.log", 'ab' )
	f.write( doNormalize( "----------------------------------------------------------------------------------------------------------------\n" ) )
	if updateitem == "tvshow" or updateitem == "season":
		f.write( doNormalize( "IncludeEpisodes: " + IncludeEpisodes + "\n" ) )
		if int(UpdateMode) == 0:
			updatemode = "episode"
		else:
			updatemode = "season"
		f.write( doNormalize( "UpdateMode: " + updatemode + "\n" ) )
	f.write( doNormalize( "IMDbDefault: " + IMDbDefault + "\n" ) )
	f.write( doNormalize( "NumberOfThreads: " + str(NumberOfThreads) + "\n" ) )
	f.write( doNormalize( "----------------------------------------------------------------------------------------------------------------\n" ) )
	f.close()

def statusLog( textMessage ):
	f = open( addonProfile + "/update.log", 'ab' )
	f.write( doNormalize( "\n" + textMessage + "\n" ) )
	f.close()

def get_kodi_version():
	query = {
		"jsonrpc": "2.0",
		"method": "Application.GetProperties",
		"params": {
			"properties": ["version", "name"]
		},
		"id": 1
	}
	json_query = xbmc.executeJSONRPC(json.dumps(query))
	if sys.version_info[0] >= 3:
		json_query = str(json_query)
	else:
		json_query = unicode(json_query, 'utf-8', errors='ignore')
	json_query = json.loads(json_query)
	version_installed = []
	if 'result' in json_query and 'version' in json_query['result']:
		version_installed = json_query['result']['version']
		return str(version_installed['major']) + "." + str(version_installed['minor'])
	else:
		return ""