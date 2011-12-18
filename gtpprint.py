from gtpfile import *

def print_string_in_bar(bar, string, min_duration):
    result = "--"
    for beat in bar.beats:
        duration_delta = min_duration - beat.duration
        extra_dashes = 2 ** duration_delta
        note = beat.note_at_string(string)
        if note:
            result += "%d-" % note.fret
        else:
            result += "--"
        if duration_delta: result += "-" * extra_dashes
    print result

def print_bar(track, bar, min_duration=None):
    """
    :type track: GTPTrack
    :type bar: GTPBar
    """
    if min_duration is None:
        min_duration = bar.shortest_beat()
    for string in range(track.strings, 0, -1):
        print_string_in_bar(bar, string, min_duration)
