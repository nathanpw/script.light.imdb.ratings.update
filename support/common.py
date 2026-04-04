# -*- coding: utf-8 -*-

#############################
# Light IMDb Ratings Update #
# by axlt2002               #
#############################

import json, sys

import xbmc, xbmcaddon, xbmcvfs, xbmcgui
import os, unicodedata
from datetime import datetime, timedelta

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

onMovies              = addonSettings.getSetting( "Movies" )
onTVShows             = addonSettings.getSetting( "TVShows" )
ShowNotifications     = addonSettings.getSetting( "ShowNotifications" )
ShowProgress          = addonSettings.getSetting( "ShowProgress" )
ShowErrorMessage      = addonSettings.getSetting( "ShowErrorMessage" )
CompleteLog           = addonSettings.getSetting( "CompleteLog" )
IncludeEpisodes       = addonSettings.getSetting( "IncludeEpisodes" )
IncludeTop250         = addonSettings.getSetting( "IncludeTop250" )
UpdateMode            = addonSettings.getSetting( "UpdateMode" )
UpdateTime            = addonSettings.getSetting("UpdateTime") or 0
IMDbDefault           = addonSettings.getSetting( "IMDbRatingDefault" )
Sound                 = addonSettings.getSetting( "NotificationsSound" )
ScheduleEnabled       = addonSettings.getSetting( "ScheduleEnabled" )
ScheduledWeekDay      = addonSettings.getSetting( "ScheduledWeekDay" )
DayTime               = addonSettings.getSetting( "DayTime" )
LastDatabaseUpdate    = addonSettings.getSetting( "LastDatabaseUpdate" )
UpdateDatabaseStartup = addonSettings.getSetting( "UpdateDatabaseStartup" )

NumberOfThreads = addonSettings.getSetting( "NumberOfThreads" )

'''UpdatePeriod = addonSettings.getSetting( "UpdatePeriod" )
NumberOfDays = int(addonSettings.getSetting( "NumberOfDays" ))
datethreshold = (datetime.now() - timedelta( days = NumberOfDays ))'''

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
	f.write( doNormalize( "Build: " + xbmc.getInfoLabel('System.BuildVersion') + "\n" ) )
	f.write( doNormalize( "Movies update: " + onMovies + "\n" ) )
	f.write( doNormalize( "TV shows update: " + onTVShows + "\n" ) )
	f.write( doNormalize( "UpdateDatabaseStartup: " + UpdateDatabaseStartup + "\n" ) )
	if UpdateDatabaseStartup == "true":
		f.write( doNormalize( "LastDatabaseUpdate: " + LastDatabaseUpdate + "\n" ) )
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
		'''if int(UpdateMode) == 0:
			updatemode = "episode"
		else:
			updatemode = "season"
		f.write( doNormalize( "UpdateMode: " + updatemode + "\n" ) )'''
	'''if UpdatePeriod == "true":
		f.write( doNormalize( "UpdatePeriod: from " + datethreshold.strftime('%Y-%m-%d') + ' to ' + datetime.now().strftime('%Y-%m-%d') + "\n" ) )
	else:
		f.write( doNormalize( "UpdatePeriod: all\n" ) )'''
	f.write( doNormalize( "IMDbDefault: " + IMDbDefault + "\n" ) )
	f.write( doNormalize( "NumberOfThreads: " + str(NumberOfThreads) + "\n" ) )
	f.write( doNormalize( "----------------------------------------------------------------------------------------------------------------\n" ) )
	f.close()

def dump_database_StatusLog( log ):
	f = open( addonProfile + "/update.log", 'ab' )
	f.write( doNormalize( "\n" + log ) )
	f.write( doNormalize( "----------------------------------------------------------------------------------------------------------------\n" ) )
	f.close()

def statusLog( textMessage ):
	f = open( addonProfile + "/update.log", 'ab' )
	f.write( doNormalize( "\n" + textMessage + "\n" ) )
	f.close()

def get_kodi_version():
	codenames = {
		22: "Piers",
		21: "Omega",
		20: "Nexus",
		19: "Matrix",
		18: "Leia",
		17: "Krypton",
		16: "Jarvis"
	}

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
		return str(version_installed['major']) + "." + str(version_installed['minor']) + " (" + codenames.get(version_installed['major'], "Unknown") + ")"
	else:
		return ""