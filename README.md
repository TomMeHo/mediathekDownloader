# mediathekDownloader
## Summary
 Downloads series and movies from German public media libraries (Öffentlich-Rechtliche Sender) to your Synology NAS, for use with Synology Video Station. It works from the command line and should be used from scripts.

## How to use

### Using the search string

- Go to [https://mediathekviewweb.de](https://mediathekviewweb.de) and search for your download.

    Example: ```!ARD #Maus >10``` to search for all episodes of "Die Sendung mit der Maus" at station "ARD" that are longer than 10 minutes (they provide a lot of short cuts for each episode, which is not really helpful if you want to retrieve an episode as broadcasted each Sunday morning).


### Command line

```sh
$:>python -m mediathekDownloader -h
Usage: mediathekDwnld.py [OPTIONS] PATH

  The app allows to retrieve videos from German, Austrian and Suisse TV
  station media libraries ("Mediathek").  Central accesspoint to these
  resources is https://mediathekviewweb.de/. Either the search string used
  there or the provided RSS-feed passed to the script using options
  --search or --feed. Idea is to write the file to a Synology NAS with DS
  Video app installed. This is why a .vsmeta file is being  generated with
  the media, to feed Synology's indexer.

Options:
  -f, --feed TEXT         Specify either the feed URL (RSS) or the search
                          string from mediathekviewweb.

  -s, --search TEXT       Specify either the feed URL (RSS) or the search
                          string from mediathekviewweb.

  -p, --threads INTEGER   The app supports multithreading. How many threads
                          should be started?  [default: 1]

  -m, --maxfiles INTEGER  When collecting a search result, several larger
                          files might be downloaded. Here, specify max=0 to
                          download all, or the maximum number to download.
                          [default: 8]

  -v, --verbous           Print program output at lowest level.  [default:
                          False]

  -V, --veryverbous       Print program output at lowest level plus feed
                          items.  [default: False]

  -t, --test              Do not really download or write files.  [default:
                          False]

  -S, --series            First option to set the media type: use it when
                          downloading episodes of a series.

  -M, --movie             Second option to set the media type: use it when
                          downloading movies.

  -h, --help              Show this message and exit.
```


### Example script

```bash
#!/bin/sh
#encoding: utf8 

#go to the work directory
cd /volumeX/[path]

#Download using the venv
bin/python3 cleanup-generic.py /volume1/video/Kinder/Löwenzahn "https://mediathekviewweb.de/feed?query=%23L%C3%B6wenzahn%20%20%3E20"

#Index neu aufbauen
/usr/syno/bin/synoindex -R /volume1/video/Kinder/Löwenzahn &
#/usr/syno/bin/synoindex -R /volume1/video/Kinder/Maus &
#/usr/syno/bin/synoindex -R /volume1/video/Kinder/MausSpezial/ &
```

## Installation

### Command line

Prerequisites:
* Make sure the Python 3.8 package is installed.

Steps:
  1. Access your NAS via SSH.
  1. Choose a folder, e.g. home (```cd ~```), and create a virtual environment. Activate it.
  ```bash
      python3 -m venv mediathekDL
      cd mediathekDL
      source scripts/activate
  ```
  3. Install pip.
  3. Install the mediathekdownloader: 
  ```bash
      pip --install mediathekdownloader
  ```
  3. Test your installation: ```python3 