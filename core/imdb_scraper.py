# -*- coding: utf-8 -*-

#############################
# Light IMDb Ratings Update #
# by axlt2002               #
#############################
# changes by dziobak        #
#############################

import re
import xbmc
from support.common import *
from support.httptools import get_page

base_url = "https://www.imdb.com/title/"

def parse_IMDb_page(imdb_id):
	url = base_url + imdb_id + "/"
	do_loop = 1
	while do_loop > 0 :
		(html, status, statusInfo) = get_page(url)
		if status == "socket":
			xbmc.sleep(1000 * do_loop)
			do_loop += 1
			if do_loop == 4: return (None,None,0,statusInfo)
		elif status == "HTTP": return (None,None,0,statusInfo)
		else: do_loop = 0
	htmlline = html.replace('\n', ' ').replace('\r', '')
	matchVotes = re.findall(r'title=\"(\d\.\d) based on (\d*,?\d*,?\d+) user ratings\"', htmlline)
	if matchVotes:
		rating = matchVotes[0][0]
		votes = matchVotes[0][1]
	else:
		#matchVotes = re.findall(r'"ratingCount":(\d*,?\d*,?\d+),"bestRating":\d+,"worstRating":\d+,"ratingValue":(\d+\.?\d?)}', htmlline)
		matchVotes = re.findall(r'"ratingCount":(\d*,?\d*,?\d+),"bestRating":\"?\d+\.?\d?\"?,"worstRating":\"?\d+\.?\d?\"?,"ratingValue":\"?(\d+\.?\d?)\"?', htmlline.replace(' ', ''))
		if matchVotes:
			rating = matchVotes[0][1]
			votes = matchVotes[0][0]
		else:
			rating = None
			votes = None
			statusInfo = "Method parse_IMDb_page - IMDb ID: " + url + " -> no rating"
	matchTop250 = re.findall(r'href="/chart/top\?ref_=tt_awd" > Top Rated Movies #(\d+) </a>', htmlline) 
	if matchTop250:
		top250 = matchTop250[0]
	else:
		matchTop250 = re.findall(r'>Top rated movie #(\d+)</a>', htmlline)
		if matchTop250:
			top250 = matchTop250[0]
		else:
			top250 = 0
	return (rating, votes, top250, statusInfo)

def parse_IMDb_episodes_page(imdb_id, season):
	url = base_url + imdb_id + "/episodes/?season=" + str(season)
	do_loop = 1
	while do_loop > 0 :
		(html, status, statusInfo) = get_page(url)
		if status == "socket":
			xbmc.sleep(1000 * do_loop)
			do_loop += 1
			if do_loop == 4: return (None, statusInfo)
		elif status == "HTTP": return (None, statusInfo)
		else: do_loop = 0
	#imdb_ids = re.findall(r'<input type="[^"]+" class="ipl-rating-interactive__state" id="checkbox-[^"]+" data-tconst="([^"]+)" data-reftag="ttep_ep\d+">', html)
	#regex = r'<span class="ipl-rating-star__rating">([^"]+)<[^"]span>[\s]+<span class="ipl-rating-star__total-votes">[^"]([^"]+)[^"]<[^"]span>'
	regex = r'"aggregateRating":([^"]+),"voteCount":([^"]+),"canRate":true,"'
	ratings_and_votes = re.findall(regex, html)
	if not ratings_and_votes:
		statusInfo = "Method parse_IMDb_episodes_page - Check the season " + str(season) + " page on IMDb site at url: " + url
		return (None, statusInfo)
	return (ratings_and_votes, "OK")