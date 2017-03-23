import re
import urllib.request

from subprocess import Popen, PIPE

from AppKit import NSApplication, NSStatusBar, NSMenu, NSMenuItem, NSTimer, NSRunLoop, NSEventTrackingRunLoopMode
from PyObjCTools import AppHelper
from bs4 import BeautifulSoup


class Pyet(NSApplication):
    def finishLaunching(self):
        # Get current track info
        curr_track = get_current_track()

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

        # Create our timer for song title updates
        self.timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(1, self, 'update:', '',
                                                                                              True)

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
        # hack to enable menuItems by passing them this method as action
        # setEnabled_ isn't working, so this should do for now (achieves
        # the same thing)
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
    curr_artist = curr_track_full.split(' - ')[0]
    curr_song = curr_track_full.split(' - ')[1]

    return {
        'curr_track_full': curr_track_full,
        'curr_artist': curr_artist,
        'curr_song': curr_song
    }


def get_lyrics(artist: str, song_title: str) -> str:
    """
    Scrape the lyrics from azlyrics.com

    :param artist: Artist name in the original format from Spotify.
    :param song_title: Song title in the original format from Spotify.
    :return: Lyrics as a string with html closing tags stripped.
    """
    artist = artist.lower()
    song_title = song_title.lower()

    # remove all except alphanumeric characters from artist and song_title
    artist = re.sub('[^A-Za-z0-9]+', "", artist)
    song_title = re.sub('[^A-Za-z0-9]+', "", song_title)

    if artist.startswith("the"):  # remove starting 'the' from artist e.g. the who -> who
        artist = artist[3:]
    url = "http://azlyrics.com/lyrics/" + artist + "/" + song_title + ".html"

    try:
        content = urllib.request.urlopen(url).read()
        soup = BeautifulSoup(content, 'html.parser').prettify(formatter=None)
        lyrics = str(soup)

        # lyrics lies between up_partition and down_partition
        up_partition = '<!-- Usage of azlyrics.com content by any third-party lyrics provider is prohibited by our licensing agreement. Sorry about that. -->'
        down_partition = '<!-- MxM banner -->'
        lyrics = lyrics.split(up_partition)[1]
        lyrics = lyrics.split(down_partition)[0]
        lyrics = lyrics.replace('</br>', '').replace('</div>', '').strip()
        return lyrics

    except:
        return 'Lyrics not found. :('


def main():
    app = Pyet.sharedApplication()
    AppHelper.runEventLoop()


if __name__ == '__main__':
    main()
