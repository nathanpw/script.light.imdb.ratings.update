# -*- coding: utf-8 -*-

#############################
# Light IMDb Ratings Update #
# by axlt2002               #
#############################
# changes by dziobak        #
#############################

import sys, six
if sys.version_info[0] >= 3:
	import json as jSon
else:
	import simplejson as jSon
from support.common import *
import socket, six
from six.moves.urllib.request import Request, urlopen
from six.moves.urllib.error import HTTPError, URLError

user_agent = "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (Kresp, like Gecko) Chrome/28.0.1468.0 Safari/537.36"
base_url = "https://api.themoviedb.org/3/"
API_KEY = "5a1a77e2eba8984804586122754f969f"

def get_IMDb_ID_from_TMDb(updateitem, tmdb_id, season = 0, episode = 0):
	if tmdb_id == "" or tmdb_id == None or tmdb_id == addonLanguage(32528):
		return (None, "Method get_IMDb_ID_from_TMDb - Missing TMDB ID")
	#request
	if updateitem == "movie":
		request = "movie/%s/external_ids?api_key=%s" % (tmdb_id, API_KEY)
	elif updateitem == "tvshow":
		request = "tv/%s/external_ids?api_key=%s" % (tmdb_id, API_KEY)
	elif updateitem == "episode":
		request = "tv/%s/season/%s/episode/%s/external_ids?api_key=%s" % (tmdb_id, season, episode, API_KEY)
	(response, status, statusInfo) = send_API_request(base_url + request)
	if statusInfo != "OK":
		return (None, statusInfo)
	#external_ids
	try:
		imdb_id = jSon.loads(response)['imdb_id']
	except:
		imdb_id = None
		pass
	#no IMDb ID
	if imdb_id == None or imdb_id == "":
		return (None, "Method get_IMDb_ID_from_TMDb - " + base_url + request + " -> missing IMDb ID")
	return (imdb_id, "OK")

def send_API_request(request):
	req = Request(request)
	req.add_header('User-Agent', user_agent)
	socket.setdefaulttimeout(30)
	resp = ""
	try:
		response = urlopen(req)
		resp=response.read().decode("utf-8")
		response.close()
		return (resp, "OK", "OK")
	except HTTPError as err:
		error = str( err.code ) + " " + err.reason
		statusInfo = "Method get_IMDb_ID_from_TMDb - " + request + " -> API request error (" + error + ")"
		return (resp, "HTTP", statusInfo)
	except socket.error as err:
		statusInfo = "Method get_IMDb_ID_from_TMDb - " + request + " -> API request error (" + err + ")"
		return (resp, "socket", statusInfo)
	except URLError as err:
		#handling as timeout
		if not isinstance(err, six.string_types):
			error = err.reason
		else:
			error = err
		statusInfo = "Method get_IMDb_ID_from_TMDb - " + request + " -> API request error (" + error + ")"
		return (resp, "socket", statusInfo)