# -*- coding: utf-8 -*-

#############################
# Light IMDb Ratings Update #
# by axlt2002               #
#############################

import socket, six
import xbmc, xbmcgui
from six.moves import urllib
from six.moves.urllib.request import Request, urlopen
from six.moves.urllib.error import HTTPError, URLError
from support.common import *
import io, gzip

User_Agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36"
Accept_Encoding = "gzip"

class download_tools():
	def downloader(self,url,dest,description,heading):
		dp = xbmcgui.DialogProgressBG()
		dp.create(heading,description)
		dp.update(0)
		urllib.request.urlretrieve(url,dest,lambda nb, bs, fs, url=url: self._pbhook(nb,bs,fs,dp))
		xbmc.sleep(2000)
		dp.close()
		
	def _pbhook(self,numblocks, blocksize, filesize,dp=None):
		try:
			percent = int((int(numblocks)*int(blocksize)*100)/int(filesize))
			dp.update(percent)
		except:
			percent = 100
			dp.update(percent)

def get_page(url):
	req = Request(url)
	req.add_header('User-Agent', User_Agent)
	req.add_header('Accept-encoding', Accept_Encoding)
	socket.setdefaulttimeout(30)
	html = ""
	try:
		response = urlopen(req)
		if response.info().get('Content-Encoding') == 'gzip':
			buf = io.BytesIO(response.read())
			f = gzip.GzipFile(fileobj=buf)
			html = f.read().decode("utf-8")
		else:
			html=response.read().decode("utf-8")
		response.close()
		return (html, "OK", "OK")
	except HTTPError as err:
		error = str(err.code) + " " + err.reason
		statusInfo = "Method get_page - " + url + " -> Error accessing IMDb site (" + error + ")"
		return (html, "HTTP", statusInfo)
	except socket.error as err:
		statusInfo = "Method get_page - " + url + " -> Error accessing IMDb site (" + str (err) + ")"
		return (html, "socket", statusInfo)
	except URLError as err:
		#handling as timeout
		if not isinstance(err, six.string_types):
			error = err.reason
		else:
			error = str(err)
		statusInfo = "Method get_page - " + url + " -> Error accessing IMDb site (" + error + ")"
		return (html, "socket", statusInfo)

def internet():
	try:
		import requests
		headers = {'User-Agent': User_Agent}
		response = requests.get('https://www.imdb.com', headers=headers, timeout=3)
		return True
	except: 
		return False

def wait_for_internet(wait=30, retry=5):
	monitor = xbmc.Monitor()
	count = 0
	while True:
		if internet():
			return True
		count += 1
		if count >= retry or monitor.abortRequested():
			return False
		monitor.waitForAbort(wait)

def verify_url(url):
    try:
        import requests
        response = requests.head(url, allow_redirects=True, timeout=10)
        if response.status_code in [403, 405]:
            response = requests.get(url, stream=True, timeout=10)
            response.close()
        if response.status_code == 200:
            return "Verified\n"
        else:
            return "Issue with the address {url}. Status: {}\n".format(response.status_code)
    except requests.exceptions.RequestException as e:
        return "Connection error: {}\n".format(e)