# -*- coding: utf-8 -*-

#############################
# Light IMDb Ratings Update #
# by axlt2002               #
#############################

import shutil, gzip, csv, re
import sqlite3
from support.common import *
from support.httptools import *

database_folder = os.path.join(addonProfile, "database")

IMDb_dataset_url = "https://datasets.imdbws.com/title.ratings.tsv.gz"
Top250_info_url = "http://top250.info/"
Top250_charts = ("charts",) #("charts", "tvcharts") includes Top 250 for TV shows (currently not implemented in Kodi)

def update_database():
	database_log = datetime.now().strftime("%H:%M:%S") + " - " + "Database update\n"
	database_log += "----------------------------------------------------------------------------------------------------------------\n"
	database_log += "Verifying IMDb dataset url...\n"
	verified = verify_url(IMDb_dataset_url)
	database_log += verified
	if verified != "Verified\n":
		dump_database_StatusLog(database_log)
		return False

	download = download_tools()
	database_log += "Deleting old database...\n"
	if os.path.exists(database_folder):
		shutil.rmtree(database_folder)
	os.makedirs(database_folder)
	gz_file = os.path.join(database_folder, "title.ratings.tsv.gz")
	tsv_file = os.path.join(database_folder, "title.ratings.tsv")

	database_log += "Downloading IMDb ratings dataset...\n"
	download.downloader(IMDb_dataset_url, gz_file, addonName, addonLanguage(32880))
	with gzip.open(gz_file, 'rb') as f_in:
		with open(tsv_file, 'wb') as f_out:
			shutil.copyfileobj(f_in, f_out)

	database_log += "Creating new database...\n"
	try:
		conn = sqlite3.connect(os.path.join(database_folder, "database.db"))
	except sqlite3.OperationalError as e:
		database_log += "Connection error: {}\n".format(e)
		dump_database_StatusLog(database_log)
		return False
	except sqlite3.Error as e:
		database_log += "SQLite generic error: {}\n".format(e)
		dump_database_StatusLog(database_log)
		return False
	cursor = conn.cursor()
	cursor.execute('''CREATE TABLE IF NOT EXISTS ratings (imdb_id TEXT, rating TEXT, votes TEXT)''')
	database_log += "Inserting ratings dataset into database...\n"
	with open(tsv_file, 'r') as f:
		reader = csv.reader(f, delimiter='\t')
		next(reader) # Skip header row if it exists
		cursor.executemany('''INSERT INTO ratings (imdb_id, rating, votes) VALUES (?, ?, ?)''', reader)
	conn.commit()

	database_log += "Removing temp files...\n"
	os.remove(gz_file)
	os.remove(tsv_file)

	if IncludeTop250 == "true":
		for chart in Top250_charts:
			database_log += "Verifying Top 250 {} url...\n".format(chart)
			verified = verify_url(Top250_info_url + chart + "/")
			database_log += verified
			if verified != "Verified\n":
				conn.close()
				dump_database_StatusLog(database_log)
				return False
			database_log += "Downloading Top 250 {}...\n".format(chart)
			(html, status, statusInfo) = get_page(Top250_info_url + chart + "/")
			regex = r'movie/[?](\d+)"><'
			list_top250 = [(i, "tt{}".format(imdb_id)) for i, imdb_id in enumerate(re.findall(regex, html), start=1)]
			database_log += "Inserting Top 250 {} into database...\n".format(chart)
			cursor.execute("CREATE TABLE IF NOT EXISTS {} (position TEXT, imdb_id TEXT)".format(chart))
			cursor.executemany("INSERT INTO {} (position, imdb_id) VALUES (?, ?)".format(chart), list_top250)
			conn.commit()

	conn.close()
	database_log += "The database has been successfully updated\n"
	dump_database_StatusLog(database_log)
	if ShowNotifications == "true":
		doNotify( addonLanguage(32881), 5000 )
	return True

def check_database():
	if not os.path.exists(os.path.join(database_folder, "database.db")):
		return False
	conn = sqlite3.connect(os.path.join(database_folder, "database.db"))
	cursor = conn.cursor()
	cursor.execute('''SELECT count(name) FROM sqlite_master WHERE type='table' AND name=?''', ("ratings",))
	if cursor.fetchone()[0] != 1:
		conn.close()
		return False

	if IncludeTop250 == "true":
		for chart in Top250_charts:
			cursor.execute('''SELECT count(name) FROM sqlite_master WHERE type='table' AND name=?''', (chart,))
			if cursor.fetchone()[0] != 1:
				conn.close()
				return False

	conn.close()
	return True

def get_database(imdb_id, updateitem):
	rating_and_votes = (None, None)
	top250 = 0
	StatusInfo = "IMDb ID not found in the database"

	conn = sqlite3.connect(os.path.join(database_folder, "database.db"))
	cursor = conn.cursor()

	cursor.execute('''SELECT rating, votes FROM ratings WHERE imdb_id = ?''', (imdb_id,))
	rating_votes = cursor.fetchone()
	if rating_votes != None:
		rating_and_votes = (rating_votes[0], rating_votes[1])

	"""if IncludeTop250 == "true":
		if updateitem == "movie" or updateitem == "tvshow":
			if updateitem == "movie":
				table = "charts"
			else:
				table = "tvcharts"
			cursor.execute("SELECT position FROM {} WHERE imdb_id = ?".format(table), (imdb_id,))
			position = cursor.fetchone()
			if position != None:
				top250 = int(position[0])"""

	if IncludeTop250 == "true":
		if updateitem == "movie":
			cursor.execute('''SELECT position FROM charts WHERE imdb_id = ?''', (imdb_id,))
			position = cursor.fetchone()
			if position != None:
				top250 = int(position[0])

	conn.close()
	return (rating_and_votes[0], rating_and_votes[1], top250, StatusInfo)