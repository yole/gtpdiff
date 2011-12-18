from gtpfile import *
from gtpprint import *
import sys
from optparse import OptionParser

class GTPTrackComparator:
    def __init__(self, track1, track2):
        self.track1 = track1
        self.track2 = track2
        self.ignore_fingerings = True

    def normalize(self, fret, string, track):
        """
        :type fret: int
        :type string: int
        :type track: GTPTrack
        """
        while string > 0:
            pitch_diff = track.string_pitches[string] - track.string_pitches[string-1]
            if pitch_diff >= fret:
                string -= 1
                fret -= pitch_diff
            else:
                break
        return fret, string

    def notes_equal(self, note1, note2):
        if note1.duration != note2.duration:
            return False
        if note1.fret != note2.fret or note1.string != note2.string:
            if self.ignore_fingerings:
                fret1, string1 = self.normalize(note1.fret, note1.string, self.track1)
                fret2, string2 = self.normalize(note2.fret, note2.string, self.track2)
                return fret1 != fret2 or string1 != string2
            else:
                return False
        return True

    def beats_equal(self, beat1, beat2):
        if len(beat1.notes) != len(beat2.notes):
            return False
        for note1, note2 in zip(beat1.notes, beat2.notes):
            if not self.notes_equal(note1, note2): return False
        return True

    def bars_equal(self, bar1, bar2):
        if len(bar1.beats) != len(bar2.beats):
            return False
        for b1, b2 in zip(bar1.beats, bar2.beats):
            if not self.beats_equal(b1, b2): return False
        return True

    def compare_tracks(self):
        for i in range(len(self.track1.bars)):
            bar1 = self.track1.bars[i]
            bar2 = self.track2.bars[i]
            if not self.bars_equal(bar1, bar2):
                yield i+1, bar1, bar2


parser = OptionParser(usage="%prog [options] track1 track2")
parser.add_option("-1", "--track1", help="Track to compare in first file", dest="track1")
parser.add_option("-2", "--track2", help="Track to compare in second file", dest="track2")

options, args = parser.parse_args()

if len(args) != 2:
    parser.print_help()
    sys.exit()

f1 = open(args[0], "rb")
loader = loader_for_file(f1)
gtp1 = loader.load(f1)

f2 = open(args[1], "rb")
loader = loader_for_file(f2)
gtp2 = loader.load(f2)

print "Tracks in %s:" % args[0]
for t in gtp1.tracks:
    print t.name
print "Bars in %s: %d" % (args[0], len(gtp1.tracks[0].bars))

print "Tracks in %s:" % args[1]
for t2 in gtp2.tracks:
    print t2.name
print "Bars in %s: %d" % (args[1], len(gtp2.tracks[0].bars))

if options.track1:
    track1 = gtp1.find_track(options.track1)
else:
    track1 = gtp1.tracks[0]

if options.track2:
    track2 = gtp2.find_track(options.track2)
else:
    track2 = gtp2.tracks[0]
if len(track1.bars) != len(track2.bars):
    print "Number of bars is different, cannot proceed"
    sys.exit(1)

comparator = GTPTrackComparator(track1, track2)
differences = False
for index, bar1, bar2 in comparator.compare_tracks():
    differences = True
    print "Difference in bar %d" % index
    shortest_beat = max(bar1.shortest_beat(), bar2.shortest_beat())
    print_bar(track1, bar1, shortest_beat)
    print ""
    print_bar(track2, bar2, shortest_beat)
    print ""
if not differences:
    print "Tracks are identical"
