from gtpfile import *

def effect_character(note, bar, beat, string):
    if not note.slide and not note.hammer: return "-"
    if beat < len(bar.beats)-1:
        next_beat = bar.beats[beat+1]
        next_note = next_beat.note_at_string(string)
        if not next_note: return "-"
        if note.slide:
            if next_note.fret > note.fret: return "/"
            if next_note.fret < note.fret: return "\\"
        if note.hammer:
            if next_note.fret > note.fret: return "h"
            if next_note.fret < note.fret: return "p"
    return "-"


def print_string_in_bar(bar, string, min_duration):
    result = "--"
    for i, beat in enumerate(bar.beats):
        duration_delta = min_duration - beat.duration
        extra_dashes = 2 ** duration_delta
        note = beat.note_at_string(string)
        if note:
            result += "%d" % note.fret + effect_character(note, bar, i, string)
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
    for string in range(track.strings):
        print_string_in_bar(bar, string, min_duration)
