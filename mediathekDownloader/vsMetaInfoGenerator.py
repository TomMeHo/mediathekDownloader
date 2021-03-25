import re
from vsmetaEncoder import vsmetaInfo
from datetime import datetime, date


class VsMetaInfoGenerator(vsmetaInfo.VsMetaInfo):

    def __init__(self, feedItem):

        super(VsMetaInfoGenerator, self).__init__()

        self.feedItem = feedItem
        self.download_url = ''

        # parse feedItem
        if hasattr(feedItem, 'title'):          self.episodeTitle           = feedItem.title
        if hasattr(feedItem, 'category'):       self.showTitle              = feedItem.category
        if hasattr(feedItem, 'summary'):        self.chapterSummary         = feedItem.summary
        if hasattr(feedItem, 'description'):    self.chapterSummary         = feedItem.description
        if hasattr(feedItem, 'link'):           self.download_url           = feedItem.link
        #if hasattr(feedItem, 'published'):      self.episodeReleaseDate     = datetime.strptime(feedItem.published, "%a, %d %b %Y %H:%M:%S GMT" )
        if hasattr(feedItem, 'published'):      self.setEpisodeDate(datetime.strptime(feedItem.published, "%a, %d %b %Y %H:%M:%S GMT").date())
        if hasattr(feedItem, 'description'):    self.chapterSummary         = feedItem.description

        #cleaning some parts
        self.chapterSummary = self.chapterSummary.replace('![CDATA[', '')
        self.chapterSummary = self.chapterSummary.replace(']]', '')

        self.tvshowLocked = True
        self.episodeLocked = True

        episodeFound = re.search('[(](\d*)\/\d[)]',self.episodeTitle)
        if episodeFound != None: 
            self.episode = int(episodeFound.group(1))
        
        seasonFound = re.search(' Staffel (\d*) ',self.episodeTitle)
        if seasonFound != None: 
            self.season = int(seasonFound.group(1))

        # set other defaults
        self.episodeLocked = False
        self.tvshowLocked = False

        self.identifyingTerm = '%s - %s -s%se%s' % (self.showTitle, self.episodeTitle, self.season, self.episode)

    def isUsable(self) ->bool:
        if (len(self.episodeTitle) > 0 or len(self.showTitle) > 0 or len(self.showTitle2) > 0) and len(self.download_url) > 0: 
            return True
        else:
            return False