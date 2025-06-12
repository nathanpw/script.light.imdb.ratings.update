# -*- coding: utf-8 -*-

#############################
# Light IMDb Ratings Update #
# by axlt2002               #
#############################

import xbmc
import sys, re
if sys.version_info[0] >= 3:
	import json as jSon
else:
	import simplejson as jSon
from support.common import *
from core.imdb_scraper import parse_IMDb_episodes_page
from core.tmdb_api import get_IMDb_ID_from_TMDb

def doUpdateEpisodesBySeason(tvshowid, IMDb, season, progress, percentage, flock):
	if season != -1 :
		if UpdateTime > 0:
			dateAfter = (datetime.now() - timedelta(days=UpdateTime)).strftime('%Y-%m-%d')
			jSonQuery = '{"jsonrpc":"2.0","method":"VideoLibrary.GetEpisodes","params":{"tvshowid":' + str( tvshowid ) + ', "season":' + str( season ) + ', "properties":["episode","season","showtitle"], "filter": {"field": "dateadded", "operator": "greaterthan", "value": "' + str( dateAfter ) + '"}, "sort":{"method": "episode"}},"id":1}'
		else:
			jSonQuery = '{"jsonrpc":"2.0","method":"VideoLibrary.GetEpisodes","params":{"tvshowid":' + str( tvshowid ) + ', "season":' + str( season ) + ', "properties":["episode","season","showtitle"], "sort":{"method": "episode"}},"id":1}'
	else:
		if UpdateTime > 0:
			dateAfter = (datetime.now() - timedelta(days=UpdateTime)).strftime('%Y-%m-%d')
			jSonQuery = '{"jsonrpc":"2.0","method":"VideoLibrary.GetEpisodes","params":{"tvshowid":' + str( tvshowid ) + ', "properties":["episode","season","showtitle"], "filter": {"field": "dateadded", "operator": "greaterthan", "value": "' + str( dateAfter ) + '"}, "sort":{"method": "episode"}},"id":1}'
		else:
			jSonQuery = '{"jsonrpc":"2.0","method":"VideoLibrary.GetEpisodes","params":{"tvshowid":' + str( tvshowid ) + ', "properties":["episode","season","showtitle"], "sort":{"method": "episode"}},"id":1}'
	jSonResponse = xbmc.executeJSONRPC( jSonQuery )
	jSonResponse = jSon.loads( jSonResponse )
	try:
		if 'episodes' in jSonResponse['result']:
			current_season = -1
			for item in jSonResponse['result']['episodes']:
				episodeid = item.get('episodeid')
				season = item.get('season')
				episode = "%02d"%item.get('episode')
				Title = item.get('showtitle') + " " + str( season ) + "x" + str( episode )
				if ShowProgress == "true":
					progress.update( int(percentage), addonLanguage(32260), Title )
				if current_season != season:
					current_season = season
					episodes_ratings_and_votes, statusInfo = parse_IMDb_episodes_page(IMDb, season)
					if episodes_ratings_and_votes == None:
						sIMDb, sTVDB, sTMDB = printable_IDs(IMDb, None, None)
						if flock != None:
							flock.acquire()
							try:
								statusLog( item.get('showtitle') + " (TV show IMDb ID: " + sIMDb + ")" + "\n" + statusInfo )
								if ShowLogMessage == "true":
									addonSettings.setSetting( "LogDialog", "true" )
							finally:
								flock.release()
						else:
							statusLog( item.get('showtitle') + " (TV show IMDb ID: " + sIMDb + ")" + "\n" + statusInfo )
							if ShowLogMessage == "true":
								addonSettings.setSetting( "LogDialog", "true" )
						continue
				if episodes_ratings_and_votes != None:
					statusInfo = ""
					try:
						updatedRating = episodes_ratings_and_votes[int(episode)-1][0]
						updatedVotes = episodes_ratings_and_votes[int(episode)-1][1]
						if CompleteLog == "true":
							statusInfo = "Rating: %s, Votes: %s" % (updatedRating, updatedVotes)
						jSonQuery = '{"jsonrpc":"2.0","method":"VideoLibrary.SetEpisodeDetails","params":{"episodeid":' + str( episodeid ) + ',"ratings":{"imdb":{"rating":' + str( updatedRating ) + ',"votes":' + str( updatedVotes ).replace(",", "") + ',"default":' + IMDbDefault + '}}},"id":1}'
						jSonResponse = xbmc.executeJSONRPC( jSonQuery )
					except:
						statusInfo = "Method parse_IMDb_episodes_page - Episode " + episode + " not found"
						if ShowLogMessage == "true":
							addonSettings.setSetting( "LogDialog", "true" )
						pass
					if statusInfo != "":
						sIMDb, sTVDB, sTMDB = printable_IDs(IMDb, None, None)
						if flock != None:
							flock.acquire()
							try:
								statusLog( Title + " (TV show IMDb ID: " + sIMDb + ")" + "\n" + statusInfo )
							finally:
								flock.release()
						else:
							statusLog( Title + " (TV show IMDb ID: " + sIMDb + ")" + "\n" + statusInfo )
	except: pass
	return

def get_tvshow_IMDb_ID(updateitem, tvshowid, TVDB, TMDB, Title):
	IMDb = None
	if updateitem != "tvshow":
		TVDB = None; TMDB = None
		jSonQuery = '{"jsonrpc":"2.0","method":"VideoLibrary.GetTVShowDetails","params":{"tvshowid":' + str( tvshowid ) + ',"properties":["uniqueid","title"]},"id":1}'
		jSonResponse = xbmc.executeJSONRPC( jSonQuery )
		jSonResponse = jSon.loads( jSonResponse )
		item = jSonResponse['result']['tvshowdetails']
		Title = item.get('title')
		unique_id = item.get('uniqueid')
		if unique_id != None:
			IMDb = unique_id.get('imdb')
			TVDB = unique_id.get('tvdb')
			TMDB = unique_id.get('tmdb')
			IMDb, TVDB, TMDB = normalize_IDs(IMDb, TVDB, TMDB)
	sIMDb, sTVDB, sTMDB = printable_IDs(IMDb, TVDB, TMDB)
	statusInfo = "Method get_tvshow_IMDb_ID - " + Title + " (IMDb ID: " + sIMDb + ", TVDB ID: " + sTVDB + ", TMDB ID: "+ sTMDB + ")"
	if IMDb == None:
		(IMDb, add_statusInfo) = get_IMDb_ID_from_TMDb("tvshow", TMDB)
		statusInfo = statusInfo + "\n" + add_statusInfo
		if IMDb == None:
			return(None, statusInfo)
		else:
			jSonQuery = '{"jsonrpc":"2.0","method":"VideoLibrary.SetTVShowDetails","params":{"tvshowid":' + str( tvshowid ) + ',"uniqueid": {"imdb": "' + IMDb + '"}},"id":1}'
			jSonResponse = xbmc.executeJSONRPC( jSonQuery )
	return (IMDb, "OK")

def printable_IDs(imdb, tvdb, tmdb):
	if imdb == None: imdb = addonLanguage(32528)
	if tvdb == None: tvdb = addonLanguage(32528)
	if tmdb == None: tmdb = addonLanguage(32528)
	return imdb, tvdb, tmdb

def normalize_IDs(imdb, tvdb, tmdb):
	if imdb == "": imdb = None
	if tvdb == "": tvdb = None
	if tmdb == "": tmdb = None
	return imdb, tvdb, tmdb