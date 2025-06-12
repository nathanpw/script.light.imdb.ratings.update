# -*- coding: utf-8 -*-

#############################
# Light IMDb Ratings Update #
# by axlt2002               #
#############################

import xbmc, xbmcgui
import sys
if sys.version_info[0] >= 3:
	import json as jSon
	from _thread import start_new_thread, allocate_lock
else:
	import simplejson as jSon
	from thread import start_new_thread, allocate_lock
from datetime import datetime, timedelta
from support.common import *
from support.httptools import wait_for_internet
from core.update_common import *
from core.imdb_scraper import parse_IMDb_page

max_threads = int(NumberOfThreads) - 1	#0 - 1 thread, 1 - 2 threads ...
num_threads = 0

def thread_parse_IMDb_page(updateitem, updateitem_id, IMDb, TVDB, TMDB, title, season, progress, percentage, lock, flock):
	global num_threads
	if updateitem == "movie" or updateitem == "tvshow" or updateitem == "episode":
		(updatedRating, updatedVotes, updatedTop250, statusInfo) = parse_IMDb_page(IMDb)
		if updatedRating != None:
			statusInfo = "Rating: %s, Votes: %s" % (updatedRating, updatedVotes)
			if updateitem == "movie":
				if updatedTop250 == 0:
					statusInfo = statusInfo + ", Top250: n/a"
				else:
					statusInfo = statusInfo + ", Top250: %s" % str(updatedTop250)
		if updatedRating == None or CompleteLog == "true":
			sIMDb, sTVDB, sTMDB = printable_IDs(IMDb, TVDB, TMDB)
			flock.acquire()
			try:
				statusLog( title + " (IMDb ID: " + sIMDb + ", TVDB ID: " + sTVDB + ", TMDB ID: "+ sTMDB + ")" + "\n" + statusInfo )
				if updatedRating == None and ShowLogMessage == "true":
					addonSettings.setSetting( "LogDialog", "true" )
			finally:
				flock.release()
		if updatedRating != None:
			if updateitem == "movie":
				jSonQuery = '{"jsonrpc":"2.0","method":"VideoLibrary.SetMovieDetails","params":{"movieid":' + str( updateitem_id ) + ',"uniqueid": {"imdb": "' + IMDb + '"},"ratings":{"imdb":{"rating":' + str( updatedRating ) + ',"votes":' + str( updatedVotes ).replace(",", "") + ',"default":' + IMDbDefault + '}},"top250":' + str( updatedTop250 ) + '},"id":1}'
			elif updateitem == "tvshow":
				jSonQuery = '{"jsonrpc":"2.0","method":"VideoLibrary.SetTVShowDetails","params":{"tvshowid":' + str( updateitem_id ) + ',"ratings":{"imdb":{"rating":' + str( updatedRating ) + ',"votes":' + str( updatedVotes ).replace(",", "") + ',"default":' + IMDbDefault + '}}},"id":1}'
			elif updateitem == "episode":
				jSonQuery = '{"jsonrpc":"2.0","method":"VideoLibrary.SetEpisodeDetails","params":{"episodeid":' + str( updateitem_id ) + ',"uniqueid": {"imdb": "' + IMDb + '"},"ratings":{"imdb":{"rating":' + str( updatedRating ) + ',"votes":' + str( updatedVotes ).replace(",", "") + ',"default":' + IMDbDefault + '}}},"id":1}'
			jSonResponse = xbmc.executeJSONRPC( jSonQuery )
	elif updateitem == "season":
		doUpdateEpisodesBySeason(updateitem_id, IMDb, season, progress, percentage, flock)
	lock.acquire()
	num_threads -= 1
	lock.release()
	return

class Movies:
	def __init__(self):
		self.lock = allocate_lock()
		self.flock = allocate_lock()

	def doUpdate(self):
		self.AllMovies = []
		self.getDBMovies()
		if len( self.AllMovies ) == 0:
			xbmcgui.Dialog().ok( "%s" % ( addonName ), addonLanguage(32840) )
			return
		if ShowNotifications == "true":
			doNotify( addonLanguage(32255), 5000 )
			xbmc.sleep(5000)
		statusLog( datetime.now().strftime("%H:%M:%S") + " - " + "Scheduled/manual ratings update for movies started" )
		dump_settings_StatusLog("movie")
		self.doUpdateMovies()
		statusLog( datetime.now().strftime("%H:%M:%S") + " - " + "Scheduled/manual ratings update for movies finished" )
		if ShowNotifications == "true":
			doNotify( addonLanguage(32258), 5000 )
			xbmc.sleep(8000)
		return

	def getDBMovies(self):
		dateAfter = 0
		if UpdateTime > 0:
			dateAfter = (datetime.now() - timedelta(days=UpdateTime)).strftime('%Y-%m-%d')
			jSonQuery = '{"jsonrpc":"2.0","method":"VideoLibrary.GetMovies","params":{"properties":["uniqueid","title"], "filter": {"field": "dateadded", "operator": "greaterthan", "value": "' + str( dateAfter ) + '"}, "sort":{"method": "dateadded","order":"descending"}},"id":1}'
		else:
			jSonQuery = '{"jsonrpc":"2.0","method":"VideoLibrary.GetMovies","params":{"properties":["uniqueid","title"], "sort":{"method": "dateadded","order":"descending"}},"id":1}'
		jSonResponse = xbmc.executeJSONRPC( jSonQuery )
		jSonResponse = jSon.loads( jSonResponse )
		try:
			if 'movies' in jSonResponse['result']:
				for item in jSonResponse['result']['movies']:
					IMDb = None; TVDB = None; TMDB = None
					unique_id = item.get('uniqueid')
					if unique_id != None:
						IMDb = unique_id.get('imdb')
						TVDB = unique_id.get('tvdb')
						TMDB = unique_id.get('tmdb')
						IMDb, TVDB, TMDB = normalize_IDs(IMDb, TVDB, TMDB)
					movieid = item.get('movieid')
					title = item.get('title')
					self.AllMovies.append((movieid, IMDb, TVDB, TMDB, title))
		except: pass
		return

	def doUpdateMovies(self):
		global num_threads
		AllMovies = len( self.AllMovies ); Counter = 0;
		progress = None
		if ShowProgress == "true":
			progress = xbmcgui.DialogProgressBG()
			progress.create( addonLanguage(32260) )
		for Movie in self.AllMovies:
			while num_threads > max_threads*2:
				xbmc.sleep(500)
			if ShowProgress == "true":
				Counter = Counter + 1
				progress.update( int((Counter*100)/AllMovies), addonLanguage(32260), Movie[4] )
			IMDb = Movie[1]
			if IMDb == None:
				(IMDb, statusInfo) = get_IMDb_ID_from_TMDb("movie", Movie[3])
				if IMDb == None:
					sIMDb, sTVDB, sTMDB = printable_IDs(IMDb, Movie[2], Movie[3])
					self.flock.acquire()
					try:
						statusLog( Movie[4] + " (IMDb ID: " + sIMDb + ", TVDB ID: " + sTVDB + ", TMDB ID: "+ sTMDB + ")" + "\n" + statusInfo )
						if ShowLogMessage == "true":
							addonSettings.setSetting( "LogDialog", "true" )
					finally:
						self.flock.release()
					continue
			start_new_thread(thread_parse_IMDb_page,("movie", Movie[0], IMDb, Movie[2], Movie[3], Movie[4], -1, progress, 0, self.lock, self.flock))
			self.lock.acquire()
			num_threads += 1
			self.lock.release()
		while num_threads > 0:
			xbmc.sleep(500)
		if ShowProgress == "true":
			xbmc.sleep(1000)
			progress.close()
		return

class TVShows:
	def __init__(self):
		self.lock = allocate_lock()
		self.flock = allocate_lock()

	def doUpdate(self):
		self.AllTVShows = []
		self.getDBTVShows()
		if len( self.AllTVShows ) == 0:
			xbmcgui.Dialog().ok( "%s" % ( addonName ), addonLanguage(32841) )
			return
		if ShowNotifications == "true":
			doNotify( addonLanguage(32256), 5000 )
			xbmc.sleep(5000)
		statusLog( datetime.now().strftime("%H:%M:%S") + " - " + "Scheduled/manual ratings update for TV shows started" )
		dump_settings_StatusLog("tvshow")
		self.doUpdateTVShows()
		statusLog( datetime.now().strftime("%H:%M:%S") + " - " + "Scheduled/manual ratings update for TV shows finished" )
		if ShowNotifications == "true":
			doNotify( addonLanguage(32259), 5000 )
			xbmc.sleep(5000)
		return

	def getDBTVShows(self):
		if UpdateTime > 0:
			dateAfter = (datetime.now() - timedelta(days=UpdateTime)).strftime('%Y-%m-%d')
			jSonQuery = '{"jsonrpc":"2.0","method":"VideoLibrary.GetTVShows","params":{"properties":["uniqueid","title"], "filter": {"field": "dateadded", "operator": "greaterthan", "value": "' + str( dateAfter ) + '"}, "sort":{"method": "dateadded","order":"descending"}},"id":1}'
		else:
			jSonQuery = '{"jsonrpc":"2.0","method":"VideoLibrary.GetTVShows","params":{"properties":["uniqueid","title"], "sort":{"method": "dateadded","order":"descending"}},"id":1}'
		jSonResponse = xbmc.executeJSONRPC( jSonQuery )
		jSonResponse = jSon.loads( jSonResponse )
		try:
			if 'tvshows' in jSonResponse['result']:
				for item in jSonResponse['result']['tvshows']:
					IMDb = None; TVDB = None; TMDB = None
					unique_id = item.get('uniqueid')
					if unique_id != None:
						IMDb = unique_id.get('imdb')
						TVDB = unique_id.get('tvdb')
						TMDB = unique_id.get('tmdb')
						IMDb, TVDB, TMDB = normalize_IDs(IMDb, TVDB, TMDB)
					tvshowid = item.get('tvshowid')
					title = item.get('title')
					self.AllTVShows.append((tvshowid, IMDb, TVDB, TMDB, title))
		except: pass
		return

	def doUpdateTVShows(self):
		global num_threads
		AllTVShows = len( self.AllTVShows ); Counter = 0;
		percentage = 0
		progress = None
		if ShowProgress == "true":
			progress = xbmcgui.DialogProgressBG()
			progress.create( addonLanguage(32260) )
		for TVShow in self.AllTVShows:
			while num_threads > max_threads:
				xbmc.sleep(500)
			if ShowProgress == "true":
				Counter = Counter + 1
				percentage = (Counter*100)/AllTVShows
				progress.update( int(percentage), addonLanguage(32260), TVShow[4] )
			IMDb = TVShow[1]
			if IMDb == None:
				IMDb, statusInfo = get_tvshow_IMDb_ID("tvshow", TVShow[0], TVShow[2], TVShow[3], TVShow[4])
			if IMDb == None:
				sIMDb, sTVDB, sTMDB = printable_IDs(IMDb, TVShow[2], TVShow[3])
				self.flock.acquire()
				try:
					statusLog( TVShow[4] + " (IMDb ID: " + sIMDb + ", TVDB ID: " + sTVDB + ", TMDB ID: "+ sTMDB + ")" + "\n" + statusInfo )
					if ShowLogMessage == "true":
						addonSettings.setSetting( "LogDialog", "true" )
				finally:
					self.flock.release()
				continue
			start_new_thread(thread_parse_IMDb_page,("tvshow", TVShow[0], IMDb, TVShow[2], TVShow[3], TVShow[4], -1, progress, 0, self.lock, self.flock))
			self.lock.acquire()
			num_threads += 1
			self.lock.release()
			if IncludeEpisodes == "true":
				if int(UpdateMode) == 0:
					self.doUpdateEpisodes(TVShow[0], TVShow[3], -1, progress, percentage)
				else:
					self.doUpdateSeasons(TVShow[0], IMDb, progress, percentage)
		while num_threads > 0:
			xbmc.sleep(500)
		if ShowProgress == "true":
			xbmc.sleep(1000)
			progress.close()
		return

	def doUpdateSeasons(self, tvshowid, IMDb, progress, percentage):
		global num_threads
		if UpdateTime > 0:
			dateAfter = (datetime.now() - timedelta(days=UpdateTime)).strftime('%Y-%m-%d')
			jSonQuery = '{"jsonrpc":"2.0","method":"VideoLibrary.GetSeasons","params":{"tvshowid":' + str( tvshowid ) + ',"properties":["season"], "filter": {"field": "dateadded", "operator": "greaterthan", "value": "' + str( dateAfter ) + '"}},"id":1}'
		else:
			jSonQuery = '{"jsonrpc":"2.0","method":"VideoLibrary.GetSeasons","params":{"tvshowid":' + str( tvshowid ) + ',"properties":["season"]},"id":1}'
		jSonResponse = xbmc.executeJSONRPC( jSonQuery )
		jSonResponse = jSon.loads( jSonResponse )
		try:
			if 'seasons' in jSonResponse['result']:
				for item in jSonResponse['result']['seasons']:
					while num_threads > max_threads:
						xbmc.sleep(500)
					start_new_thread(thread_parse_IMDb_page,("season", tvshowid, IMDb, None, None, "", item.get('season'), progress, percentage, self.lock, self.flock))
					self.lock.acquire()
					num_threads += 1
					self.lock.release()
		except: pass
		return

	def doUpdateEpisodes(self, tvshowid, tvshowTMDB, season, progress, percentage):
		global num_threads
		if season != -1 :
			if UpdateTime > 0:
				dateAfter = (datetime.now() - timedelta(days=UpdateTime)).strftime('%Y-%m-%d')
				jSonQuery = '{"jsonrpc":"2.0","method":"VideoLibrary.GetEpisodes","params":{"tvshowid":' + str( tvshowid ) + ', "season":' + str( season ) + ', "properties":["uniqueid","episode","season","showtitle"], "filter": {"field": "dateadded", "operator": "greaterthan", "value": "' + str( dateAfter ) + '"}, "sort":{"method": "episode"}},"id":1}'
			else:
				jSonQuery = '{"jsonrpc":"2.0","method":"VideoLibrary.GetEpisodes","params":{"tvshowid":' + str( tvshowid ) + ', "season":' + str( season ) + ', "properties":["uniqueid","episode","season","showtitle"], "sort":{"method": "episode"}},"id":1}'
		else:
			if UpdateTime > 0:
				dateAfter = (datetime.now() - timedelta(days=UpdateTime)).strftime('%Y-%m-%d')
				jSonQuery = '{"jsonrpc":"2.0","method":"VideoLibrary.GetEpisodes","params":{"tvshowid":' + str( tvshowid ) + ', "properties":["uniqueid","episode","season","showtitle"], "filter": {"field": "dateadded", "operator": "greaterthan", "value": "' + str( dateAfter ) + '"}, "sort":{"method": "episode"}},"id":1}'
			else:
				jSonQuery = '{"jsonrpc":"2.0","method":"VideoLibrary.GetEpisodes","params":{"tvshowid":' + str( tvshowid ) + ', "properties":["uniqueid","episode","season","showtitle"], "sort":{"method": "episode"}},"id":1}'
		jSonResponse = xbmc.executeJSONRPC( jSonQuery )
		jSonResponse = jSon.loads( jSonResponse )
		try:
			if 'episodes' in jSonResponse['result']:
				for item in jSonResponse['result']['episodes']:
					IMDb = None
					TVDB = None
					TMDB = None
					while num_threads > max_threads:
						xbmc.sleep(500)
					episodeid = item.get('episodeid')
					season = item.get('season')
					episode = "%02d"%item.get('episode')
					Title = item.get('showtitle') + " " + str(season) + "x" + str(episode)
					unique_id = item.get('uniqueid')
					if unique_id != None:
						IMDb = unique_id.get('imdb')
						TVDB = unique_id.get('tvdb')
						TMDB = unique_id.get('tmdb')
						IMDb, TVDB, TMDB = normalize_IDs(IMDb, TVDB, TMDB)
					if ShowProgress == "true":
						progress.update(int(percentage), addonLanguage(32260), Title)
					if IMDb == None:
						IMDb, statusInfo = get_IMDb_ID_from_TMDb("episode", tvshowTMDB, season, episode)
					if IMDb == None:
						sIMDb, sTVDB, sTMDB = printable_IDs(IMDb, TVDB, TMDB)
						self.flock.acquire()
						try:
							statusLog(Title + " (IMDb ID: " + sIMDb + ", TVDB ID: " + sTVDB + ", TMDB ID: "+ sTMDB + ")" + "\n" + statusInfo)
							if ShowLogMessage == "true":
								addonSettings.setSetting("LogDialog", "true")
						finally:
							self.flock.release()
						continue
					else:
						start_new_thread(thread_parse_IMDb_page,("episode", episodeid, IMDb, TVDB, TMDB, Title, season, progress, percentage, self.lock, self.flock))
						self.lock.acquire()
						num_threads += 1
						self.lock.release()
		except: pass
		return

def perform_update():
	if not wait_for_internet(wait=3, retry=1):
		xbmcgui.Dialog().ok( "%s" % ( addonName ), addonLanguage(32257) )
		return
	if addonSettings.getSetting( "PerformingUpdate" ) == "true":
		xbmcgui.Dialog().ok( "%s" % ( addonName ), addonLanguage(32251) )
		return
	if onMovies == "false" and onTVShows == "false":
		xbmcgui.Dialog().ok( "%s" % ( addonName ), addonLanguage(32842) )
		return
	addonSettings.setSetting( "PerformingUpdate", "true" )
	if onMovies == "true":
		Movies().doUpdate()
	if onTVShows == "true":
		TVShows().doUpdate()
	addonSettings.setSetting( "PerformingUpdate", "false" )
	if ShowLogMessage == "true" and addonSettings.getSetting( "LogDialog") == "true":
		xbmcgui.Dialog().ok( "%s" % ( addonName ), addonLanguage(32824) )
		addonSettings.setSetting( "LogDialog", "false" )
	return