import os, struct

def read_pstring(f):
    length = ord(f.read(1))
    return f.read(length)

class GTPNote:
    def __init__(self):
        self.fret = None
        self.string = None
        self.duration = None
        self.hammer = False
        self.slide = False

    def __str__(self):
        result = "note("
        if self.fret is not None:
            result += "string=%s fret=%s" % (self.string, self.fret)
        return result + ")"

class GTPBeat:
    def __init__(self):
        self.notes = []

    def note_at_string(self, string):
        """
        :type string: int
        :rtype: GTPNote
        """
        for note in self.notes:
            if note.string == string: return note

class GTPBar:
    def __init__(self):
        self.beats = []

    def shortest_beat(self):
        """
        :return: the length of the shortest beat in this bar
        :rtype: int
        """
        min_duration = -2
        for beat in self.beats:
            if beat.duration > min_duration:
                min_duration = beat.duration
        return min_duration

class GTPTrack:
    def __init__(self):
        self.bars = []
        self.strings = 0
        self.string_pitches = []

class GTPFile:
    def __init__(self):
        self.title = None
        self.subtitle = None
        self.interpret = None
        self.notice = []
        self.tracks = []

    def find_track(self, name):
        for t in self.tracks:
            if t.name == name: return t

class GTPLoader:
    def load(self, f):
        self.file = f
        f.seek(0x1f)
        self.result = GTPFile()
        self.load_header(f, self.result)
        bar_count = self.long()
        track_count = self.long()
        self.load_bar_info(bar_count)
        self.load_track_info(track_count)
        for b in range(bar_count):
            self.current_bar = b
            for t in self.result.tracks:
                self.current_track = t
                self.load_bar(t)
        return self.result

    def skip(self, bytes):
        self.file.seek(bytes, os.SEEK_CUR)

    def byte(self):
        return ord(self.file.read(1))

    def sbyte(self):
        return struct.unpack("b", self.file.read(1))[0]

    def long(self):
        return struct.unpack("i", self.file.read(4))[0]

    def string(self, full_length):
        length = ord(self.file.read(1))
        result = self.file.read(length)
        self.skip(full_length-length)
        return result

    def long_string(self):
        l1, l2 = struct.unpack("IB", self.file.read(5))
        s = self.file.read(l1-1)
        return s[:l2]

    def load_header(self, f, result):
        """
        :param f: file
        :type f: file
        """
        result.title = self.long_string()
        result.subtitle = self.long_string()
        result.interpret = self.long_string()
        result.album = self.long_string()
        result.author = self.long_string()
        result.copyright = self.long_string()
        result.tablature_author = self.long_string()
        result.description = self.long_string()
        notice_lines = self.long()
        for i in range(notice_lines):
            result.notice.append(self.long_string())
        result.triplet_feel = self.byte()
        self.load_lyrics()
        result.tempo = self.long()
        f.seek(4+64*12, os.SEEK_CUR)

    def load_lyrics(self):
        pass

    def load_bar_info(self, bar_count):
        for i in range(bar_count):
            flags = self.byte()
            if flags & 1:
                t1 = self.byte()
            if flags & 2:
                t2 = self.byte()
            if flags & 8:
                repeat_count = self.byte()
            if flags & 16:
                alternative_ending = self.byte()
            if flags & 32:
                marker_name = self.long_string()
                marker_color = self.long()
            if flags & 64:
                key = self.byte()

    def load_track_info(self, track_count):
        for i in range(track_count):
            flags = self.byte()
            track = GTPTrack()
            track.name = self.string(40)
            track.strings = self.long()
            for i in range(track.strings):
                track.string_pitches.append(self.long())
            self.skip((7-track.strings)*4)
            track.midi_port = self.long()
            track.main_channel = self.long()
            track.fx_channel = self.long()
            track.num_frets = self.long()
            track.capo_position = self.long()
            track.color = self.long()
            self.result.tracks.append(track)

    def load_bar(self, track):
        bar = GTPBar()
        beats = self.long()
        for i in range(beats):
            self.load_beat(bar, track.strings)
        track.bars.append(bar)

    def load_beat(self, bar, track_strings):
        beat = GTPBeat()
        bar.beats.append(beat)
        beat_type = self.byte()
        if beat_type & 64:
            status = self.byte()
        beat.duration = self.sbyte()
        if beat_type & 1:
            beat.dotted = True
        if beat_type & 32:
            ntuplet = self.long()
        if beat_type & 2:
            self.load_chord()
        if beat_type & 4:
            beat.text = self.long_string()
        if beat_type & 8:
            self.load_beat_special_effect(beat)
        if beat_type & 16:
            self.load_mix_table_change(beat)
        strings = self.byte()
        for string in range(8):
            if strings & (1 << string):
                self.load_note(beat, track_strings-string)

    def load_beat_special_effect(self, beat):
        effect = self.byte()
        if effect & 1:
            beat.vibrato = True
        if effect & 2:
            beat.wide_vibrato = True
        if effect & 4:
            beat.natural_harmonic = True
        if effect & 16:
            beat.fade_in = True
        if (effect & 32) or (effect & 64):
            raise Exception("unsupported effect")

    def load_mix_table_change(self, beat):
        new_instrument = self.byte()
        new_volume = self.byte()
        new_pan = self.byte()
        new_chorus = self.byte()
        new_reverb = self.byte()
        new_phaser = self.byte()
        new_tremolo = self.byte()
        new_tempo = self.long()
        if new_volume != 255: volume_transition = self.byte()
        if new_pan != 255: pan_transition = self.byte()
        if new_chorus != 255: chorus_transition = self.byte()
        if new_reverb != 255: reverb_transition = self.byte()
        if new_phaser != 255: phaser_transition = self.byte()
        if new_tremolo != 255: tremolo_transition = self.byte()
        if new_tempo != -1: tempo_transition = self.byte()

    def load_chord(self):
        complete = self.byte()
        if complete:
            raise Exception("complete chords not supported")
        else:
            chord_name = self.long_string()
        diagram_top_fret = self.long()
        if diagram_top_fret:
            raise Exception("diagram not supported")

    def load_note(self, beat, string):
        note = GTPNote()
        note.string = string
        flag = self.byte()
        if flag & 32:
            note.alteration = self.byte()
            if flag & 1:
                note.duration = self.sbyte()
                self.skip(1)
            if flag & 16:
                note.nuance = self.byte()
            note.fret = self.byte()
        if flag & 128:
            note.left_hand_finger = self.byte()
            note.right_hand_finger = self.byte()
        if flag & 8:
            self.load_effect(note)

        beat.notes.append(note)

    def load_effect(self, note):
        type = self.byte()
        if type & 1:
            self.load_bend(note)
        if type & 2:
            note.hammer = True
        if type & 4:
            note.slide = True
        if type & 8:
            note.let_ring = True
        if type & 16:
            self.load_grace_note(note)

    def load_bend(self, note):
        bend_type = self.byte()
        bend_value = self.long()
        points = self.long()
        for i in range(points):
            t = self.long()
            p = self.long()
            vibrato = self.byte()

    def load_grace_note(self, note):
        fret = self.byte()
        dynamic = self.byte()
        transition = self.byte()
        duration = self.byte()

def loader_for_file(f):
    """
    :type f:
    :rtype: GTPLoader
    """
    signature = read_pstring(f)
    return GTPLoader()

