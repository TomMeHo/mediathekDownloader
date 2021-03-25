import os
from vsMetaInfoGenerator import VsMetaInfoGenerator

# TODO Filename Param ausbauen

class DownloadQueueItem():
    def __init__(self, vsInfo: VsMetaInfoGenerator, path: str):

        self.vsInfo = vsInfo

        downloadUrl = self.vsInfo.download_url
        startPos = downloadUrl.rfind('/') + 1
        endPos   = len(downloadUrl)
        fileName = downloadUrl[startPos:endPos]
        
        fileName = fileName.replace('\\', '')
        fileName = fileName.replace('/', '')

        self.fileName = fileName
        self.path = path

    def fullFilePath(self)->str:
        path = os.path.normpath('%s/%s' % (self.path, self.fileName))
        return path