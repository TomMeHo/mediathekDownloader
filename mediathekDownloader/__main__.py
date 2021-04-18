import click
import re
import sys
import os
import feedparser
import wget
import shutil
import multiprocessing as mp

from datetime import datetime
from vsmetaEncoder import VsMetaInfo, VsMetaMovieEncoder, VsMetaSeriesEncoder, VsMetaBase
#from vsMetaInfoGenerator import VsMetaInfoGenerator
#from downloadQueueItem import DownloadQueueItem
from mediathekDownloader import DownloadQueueItem, VsMetaInfoGenerator
from urllib import parse

from cli_logger import MessageClass, log, information, set_minimum_severity_level, error, debug, warning, returnCode, printProgressBar

@click.command(context_settings = dict( help_option_names = ['-h', '--help'] ))
@click.argument('path', type = click.Path(exists=True), required=True)
@click.option('--feed', '-f', help='Specify either the feed URL (RSS) or the search string from mediathekviewweb.', default = '')
@click.option('--search', '-s', help='Specify either the feed URL (RSS) or the search string from mediathekviewweb.', default = '')
@click.option('--threads', '-p', help='The app supports multithreading. How many threads should be started?', type=int, default=1, show_default=True)
@click.option('--maxfiles', '-m', help='When collecting a search result, several larger files might be downloaded. Here, specify max=0 to download all, or the maximum number to download.', type=int, default=8, show_default=True)
@click.option('--verbous', '-v', help='Print program output at lowest level.', default=False, is_flag=True, show_default=True)
@click.option('--veryverbous', '-V', help='Print program output at lowest level plus feed items.', default=False, is_flag=True, show_default=True)
@click.option('--test', '-t', help='Do not really download or write files.', default=False, is_flag=True, show_default=True)
@click.option('--series', '-S', 'mediaType', help='First option to set the media type: use it when downloading episodes of a series.', flag_value='series')
@click.option('--movie', '-M', 'mediaType', help='Second option to set the media type: use it when downloading movies.', flag_value='movie')
def main(path:str, feed = '', search = '', maxfiles = 1, verbous = False, veryverbous = False, test = False, mediaType:str = 'series', threads = 1):
	"""
	The app allows to retrieve videos from German, Austrian and Suisse TV station media libraries (\"Mediathek\"). Central accesspoint to these resources is https://mediathekviewweb.de/. Either the search string used there or the provided RSS-feed passed to the script using options --search or --feed.

	Idea is to write the file to a Synology NAS with DS Video app installed. This is why a .vsmeta file is being generated with the media, to feed Synology's indexer.
	"""

	# check variables
	path = os.path.normpath(path)
	if os.path.exists(path) == False:
		error('The output path %s has not been found.' % path)
		sys.exit()
	
	if  (len(feed) == 0 and len(search) == 0) or (len(feed) > 0 and len(search) > 0):
		error('Provide either a feed URL or a searchstring.')
		sys.exit()

	if verbous == True or test == True or veryverbous == True: 
		set_minimum_severity_level(MessageClass.DEBUG)
	else:
		set_minimum_severity_level(MessageClass.WARNING)

	if threads < 0 or maxfiles < 0:
		error('Please provide a positive parameter value.')
		sys.exit()

	# start program
	debug('Starting retrieval of feed.')
	if search != '':
		feedUrl = constructFeedUrl(search)

	downloadQueue = retrieveFeed(feedUrl, path, veryverbous)

	queueItemCounter = len(downloadQueue)
	if queueItemCounter == 0:
		warning("No items found for this search.")
		sys.exit()

	queueItemLimit = maxfiles
	if maxfiles == 0: queueItemLimit = queueItemCounter
	queueItemLimit = min(queueItemLimit, queueItemCounter)
	debug('Retrieved %s elements for download. Limitation is %s.' % (queueItemCounter, maxfiles))

	if test == False:
		downloadQueue = downloadQueue[:queueItemLimit]

		if mediaType == "movie":
			encoder = VsMetaMovieEncoder()
		if mediaType == "series":
			encoder = VsMetaSeriesEncoder()
			encoder.rewriteEpisodeInfo = True
		if mediaType == "other":
			raise NotImplementedError()
		if encoder is None:
			error("No mediatype specified or encoder not implemented.")

		#single-threaded or multi-threaded?
		if threads > 1:

			threads=min(os.cpu_count(), threads)
			information('Starting %s download thread(s).' % threads)

			pool = mp.Pool(threads)
			for dlQuItem in downloadQueue:
				pool.apply_async(func=downloadAndWriteVsmetaFile, args=[dlQuItem, encoder])

			pool.close()
			pool.join()

		else:

			for dlQuItem in downloadQueue:
				downloadFeedItem(dlQuItem, True)
				writeVsmetaFile(dlQuItem, encoder)

	debug('Program ended.')
	sys.exit()

def downloadAndWriteVsmetaFile(dlQuItem:DownloadQueueItem, encoder:VsMetaBase):
	downloadFeedItem(dlQuItem, False)
	writeVsmetaFile(dlQuItem, encoder)

def writeVsmetaFile(dlQuItem:DownloadQueueItem, encoder:VsMetaBase):

	metaFileName = '%s.vsmeta' % dlQuItem.fullFilePath()
	debug('VsMetaFile to be written: %s' % metaFileName)
	fileContent = encoder.encode(dlQuItem.vsInfo)

	with open(metaFileName, 'wb') as vsmetaFile:
		vsmetaFile.write(fileContent)
		vsmetaFile.close()

def skipDedicatedEpisodeVariants(episodeTitle : str) -> bool:

	skip = False

	if episodeTitle.find('Hörfassung') != -1: skip = True
	if episodeTitle.find('Gebärdensprache') != -1: skip = True
	if episodeTitle.find('Audiodeskription') != -1: skip = True
	if episodeTitle.find('(mit Untertitel)') != -1: skip = True
	if episodeTitle.find('(Englisch)') != -1: skip = True

	if skip: debug('Skipped, is  a special version.')

	return skip

def determineFileAlreadyExists(filePath : str) -> bool:

	exists = False
	if os.path.exists(filePath): 
		exists = True
		debug('File already exists.')

	return exists
	
def notedownDownload(outPath : str, fileName : str):

	historyFile = os.path.normpath('%s/downloaded.txt' % outPath)
	with open( historyFile, 'at') as history:
		history.write( '%s\n' % fileName )

def fileIsInHistory(outPath : str, fileName : str) -> bool:

	isInHistory = False

	try:
		historyFile = '%s/downloaded.txt' % outPath
		with open( historyFile, 'rt') as history:
			for line in history:
				if line.rstrip() == fileName: 
					isInHistory = True
					debug('File already in download history.')
					break
	except:
		pass
	return isInHistory

localQueue = []

def isFileInLocalQueue(term : str) -> bool:

	global localQueue
	isQueued = False

	for queuedItem in localQueue:
		if term == queuedItem:
			isQueued = True
			debug('File already considered for queue.')
			break

	if isQueued == False:
		localQueue.append(term)

	return isQueued

def retrieveFeed(feedUrl:str, outputPath:str, printFeedItems:bool=False)->[]:

	downloadQueueItems = []
	debug('Fetching feed %s.' % feedUrl)
	newsFeed = feedparser.parse(feedUrl)

	for entry in newsFeed.entries:

		vsInfo = VsMetaInfoGenerator(entry)

		if vsInfo.isUsable():

			fileName = vsInfo.episodeTitle if len(vsInfo.episodeTitle) > 0 else vsInfo.showTitle
			fileName = '%s.mp4' % fileName

			downloadQueueItem = DownloadQueueItem(vsInfo, outputPath)

			skip = skipDedicatedEpisodeVariants(vsInfo.episodeTitle)
			existsAlready = determineFileAlreadyExists(downloadQueueItem.fullFilePath())
			isInHistory = ( fileIsInHistory(downloadQueueItem.path, downloadQueueItem.fileName) ) or ( fileIsInHistory(downloadQueueItem.path, vsInfo.identifyingTerm ) ) 
			isInPast = True if (vsInfo.episodeReleaseDate < datetime.now().date()) else False

			if skip == False and existsAlready == False and isInHistory == False and isInPast == True: 
				isAlreadyQueued = isFileInLocalQueue( vsInfo.identifyingTerm )

			if skip == False and existsAlready == False and isInHistory == False and isInPast == True and isAlreadyQueued == False:
				downloadQueueItems.append(downloadQueueItem)
				if printFeedItems: printFeedItem(entry)
			else:
				debug('Skipped: %s' % vsInfo.episodeTitle)

		else:
			error("Not interpretable feed item.")

	return downloadQueueItems


def downloadFeedItem(dlQuItem:DownloadQueueItem, barIndicator:bool=True) -> bool:

	success = False
	barFunction = wget.bar_adaptive if barIndicator else None

	if barIndicator: information("Download started: %s" % dlQuItem.vsInfo.episodeTitle)

	try:
		wget.download(dlQuItem.vsInfo.download_url, out=dlQuItem.fullFilePath(), bar=barFunction)
	except FileNotFoundError:
		error('File for download not found.')
		error('Title: %s' % dlQuItem.vsInfo.episodeTitle)
		error('URL  : \"%s\"' % dlQuItem.vsInfo.download_url)
		error('File : \"%s\"' % dlQuItem.fullFilePath)
		success = False
		return success

	if barIndicator: print('\n') # ... the bar indicator does not end the output line when finished.

	information('File downloaded: %s' % (dlQuItem.vsInfo.episodeTitle))
	notedownDownload(dlQuItem.path, dlQuItem.fileName)
	notedownDownload(dlQuItem.path, dlQuItem.vsInfo.identifyingTerm)
	success = True

	return success


def printFeedItem(feedItem):

	debug('='*20)

	debug('')
	debug("{:<20}\t{:<100}\t{:<3}".format(*['Key', 'Value (first 100 chars)', 'Len']))
	debug("{:<20}\t{:<100}\t{:<3}".format(*['-'*20, '-'*100, '---']))
	for key, value in feedItem.items():
		value = str(value)
		length = str(len(value))
		iteration = 1
		while len(value) > 0:
			iteration += 1
			text = [key, str(value)[:100], length]
			debug("{:<20}\t{:<100}\t{:<3}".format(*text))
			value = value[100:]
			key = ''
			length = ''


	debug('='*20)

def constructFeedUrl(feedSearchStr:str)->str:

	feedSearchStrEnc = parse.quote(feedSearchStr)
	feedUrl = "https://mediathekviewweb.de/feed?query=%s%s" % (feedSearchStrEnc, '&future=false')

	debug('Search string retrieved: %s' % feedSearchStr)
	debug('URL, encoded. . . . . .: %s' % feedSearchStrEnc)
	debug('URL used for retrieval : %s' % feedUrl)

	return feedUrl

if __name__ == "__main__":

	main()