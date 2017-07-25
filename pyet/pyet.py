import logging
import random
import re
from subprocess import Popen, PIPE
from urllib.request import Request, urlopen

from AppKit import NSApplication, NSStatusBar, NSMenu, NSMenuItem, NSTimer, NSRunLoop, NSEventTrackingRunLoopMode
from PyObjCTools import AppHelper
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class Pyet(NSApplication):
    """
    Class representing the base of the application.
    """

    def finishLaunching(self):
        # Get current track info
        curr_track = get_current_track()

        self.lyrics = get_lyrics(curr_track['curr_artist'], curr_track['curr_song']).split('<br>')

        # Remove empty lines
        self.lyrics = [x for x in self.lyrics if x]

        # Cache current track to avoid unnecessary requests
        self.curr_track_hash = abs(hash(curr_track['curr_track_full'])) % (10 ** 8)

        # Create the status & menu bar
        statusBar = NSStatusBar.systemStatusBar()
        self.statusItem = statusBar.statusItemWithLength_(-1)
        self.statusItem.setTitle_(curr_track['curr_track_full'])

        self.menuBar = NSMenu.alloc().init()

        # Lyrics block
        for i, row in enumerate(self.lyrics):
            row = re.sub('<[^<]+?>', '', row).strip()
            setattr(self, 'row_{}'.format(i),
                    NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(row, 'doNothing:', ''))
            self.menuBar.addItem_(getattr(self, 'row_{}'.format(i)))

        self.SEPERATOR = NSMenuItem.separatorItem()
        self.menuBar.addItem_(self.SEPERATOR)

        # Quit option
        self.QUIT = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_('Quit', 'terminate:', '')
        self.SEPERATOR = NSMenuItem.separatorItem()
        self.menuBar.addItem_(self.SEPERATOR)
        self.menuBar.addItem_(self.QUIT)

        # Add menu to status bar
        self.statusItem.setMenu_(self.menuBar)

        # Create our timer for song title updates
        self.timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            1, self, 'update:', '', True
        )

        # Add our timer to the runloop
        NSRunLoop.currentRunLoop().addTimer_forMode_(self.timer, NSEventTrackingRunLoopMode)

    def update_(self, timer):
        curr_track = get_current_track()
        self.statusItem.setTitle_(curr_track['curr_track_full'])
        self.next_track_hash = abs(hash(curr_track['curr_track_full'])) % (10 ** 8)

        if self.curr_track_hash != self.next_track_hash:
            self.lyrics = get_lyrics(curr_track['curr_artist'], curr_track['curr_song']).split('<br>')

            # Remove empty lines
            self.lyrics = [x for x in self.lyrics if x]
            self.curr_track_hash = abs(hash(curr_track['curr_track_full'])) % (10 ** 8)

            # Create the status & menu bar
            statusBar = NSStatusBar.systemStatusBar()
            self.statusItem = statusBar.statusItemWithLength_(-1)
            self.statusItem.setTitle_(curr_track['curr_track_full'])

            self.menuBar = NSMenu.alloc().init()

            # Lyrics block
            for i, row in enumerate(self.lyrics):
                row = re.sub('<[^<]+?>', '', row).strip()
                setattr(self, 'row_{}'.format(i),
                        NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(row, 'doNothing:', ''))
                self.menuBar.addItem_(getattr(self, 'row_{}'.format(i)))

            self.SEPERATOR = NSMenuItem.separatorItem()
            self.menuBar.addItem_(self.SEPERATOR)

            # Quit option
            self.QUIT = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_('Quit', 'terminate:', '')
            self.SEPERATOR = NSMenuItem.separatorItem()
            self.menuBar.addItem_(self.SEPERATOR)
            self.menuBar.addItem_(self.QUIT)

            # Add menu to status bar
            self.statusItem.setMenu_(self.menuBar)

    def doNothing_(self, sender):
        """
        Hack to enable menuItems by passing them this method as action
        setEnabled_ isn't working, so this should do for now (achieves
        the same thing)

        :param sender:
        :return:
        """
        pass


def get_current_track() -> dict:
    """
    Small applescript to talk to Spotify and get the current artist - song combo.

    :return: Dictionary containing the artist/track combo and separate values.
    """
    as_get_curr_song = """
    tell application "Spotify"
        set currentArtist to artist of current track as string
        set currentTrack to name of current track as string
        return currentArtist & " - " & currentTrack
    end tell
    """

    p = Popen(['osascript', '-'], stdin=PIPE, stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate(as_get_curr_song.encode())

    curr_track_full = stdout.decode().rstrip()

    song_metadata = {
        'curr_track_full': curr_track_full,
        'curr_artist': curr_track_full.split(' - ')[0],
        'curr_song': curr_track_full.split(' - ')[1]
    }

    return song_metadata


def get_lyrics(artist: str, song_title: str) -> str:
    """
    Scrape the lyrics from lyrics.az

    :param artist: Artist name in the original format from Spotify.
    :param song_title: Song title in the original format from Spotify.
    :return: Lyrics as a string with html closing tags stripped.
    """
    artist = artist.lower()
    song_title = song_title.lower()

    # remove all except alphanumeric characters from artist and song_title
    artist = re.sub('[^\w]+', "-", artist)
    song_title = re.sub('[^\w]+', "-", song_title)

    if artist.startswith("the"):  # remove starting 'the' from artist e.g. the who -> who
        artist = artist[3:]
    url = "https://lyrics.az/" + artist + "/-/" + song_title + ".html"

    user_agent_collection = [
        'Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.8.1.11) Gecko/20071127 Firefox/2.0.0.11',
        'Opera/9.25 (Windows NT 5.1; U; en)',
        'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)',
        'Mozilla/5.0 (compatible; Konqueror/3.5; Linux) KHTML/3.5.5 (like Gecko) (Kubuntu)',
        'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.142 Safari/535.19',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:11.0) Gecko/20100101 Firefox/11.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:8.0.1) Gecko/20100101 Firefox/8.0.1',
        'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.151 Safari/535.19'
    ]
    user_agent = {
        'User-agent': random.choice(user_agent_collection)
    }

    try:
        req = Request(url, headers=user_agent)
        content = urlopen(req)
        soup = BeautifulSoup(content, 'html.parser')
        soup = soup.find_all("p", class_="lyric-text")[0]
        lyrics = str(soup)

        if 'nobody has submitted' in lyrics:
            raise ValueError('Missing lyrics')

        lyrics = lyrics.replace('<br/>', '<br>').replace('</div>', '').strip()
        return lyrics

    except Exception as e:
        return 'Unable to find lyrics on lyrics.az \U0001F614'


def main():
    app = Pyet.sharedApplication()
    AppHelper.runEventLoop()


if __name__ == '__main__':
    main()
