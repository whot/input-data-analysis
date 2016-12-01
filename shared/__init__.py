#!/usr/bin/env python
# -*- coding: utf-8

from __future__ import print_function

import evemu
import itertools
import sys
import argparse

from gnuplot import *

def _tv2us(sec, usec):
    return sec * 1e6 + usec

class TouchPoint(object):
    """
    A single point during a touch sequence, a tuple of time and coordinates.

    Members
    -------
        x : (double)
        y : (double)
                x/y coordinate in mm relative to the origin
        pressure : int
                pressure data per touch point. If None, this recording has
                no per-slot pressure.
        mm : (double, double)
                x/y coordinate in mm relative to the origin as tuple
        percent : (double, double)
                x/y coordinate in percent relative to width/height normalized to [0.0, 1.0]
        time : int
                timestamp in µs, relative to the sequence's start time
    """
    def __init__(self, time = None, mm = None, percent = None, pressure = None):
        if mm is None:
            mm = (None, None)
        if percent is None:
            percent = (None, None)

        self.time = time
        self.mm  = mm
        self.percent = percent
        self.pressure = pressure

    @property
    def x(self):
        return self.mm[0]

    @property
    def y(self):
        return self.mm[1]

    def __sub__(self, other):
        mm = tuple(a - b for a, b in zip(self.mm, other.mm))
        time = self.time - other.time
        percent = tuple(a - b for a, b in zip(self.percent, other.percent))

        return TouchPoint(time, mm, percent)

    def __repr__(self):
        return "TouchPoint({}, {}, {})".format(self.time, self.mm, self.percent)

class _TouchPointRecording(TouchPoint):
    """
    Internal use only. Same as TouchPoint but with some extra stuff to
    handle the touchpoints during processing
    """

    def __init__(self):
        TouchPoint.__init__(self)
        self.dirty = False
        self.pressure = None

    @property
    def x(self):
        return self.mm[0]

    @x.setter
    def x(self, x):
        self.mm = (x, self.mm[1])
        self.dirty = True

    @property
    def y(self):
        return self.mm[1]

    @y.setter
    def y(self, y):
        self.mm = (self.mm[0], y)
        self.dirty = True

    @property
    def x_percent(self):
        return self.percent[0]

    @x_percent.setter
    def x_percent(self, x):
        self.percent = (x, self.percent[1])
        self.dirty = True

    @property
    def y_percent(self):
        return self.percent[1]

    @y_percent.setter
    def y_percent(self, y):
        self.percent = (self.percent[0], y)
        self.dirty = True

    @property
    def press(self, pressure):
        return self.pressure

    @press.setter
    def press(self, pressure):
        self.pressure = pressure
        self.dirty = True

    def clean_copy(self):
        assert(self.time != None)
        assert(self.mm[0] != None)
        assert(self.mm[1] != None)
        assert(self.percent[0] != None)
        assert(self.percent[1] != None)

        ts = TouchPoint(self.time, self.mm, self.percent, self.pressure)
        self.time = None
        self.dirty = False

        return ts

class DeviceError(Exception):
    """
    Base class for all device-related exceptions in this module
    """
    def __init__(self):
        self.msg = "Generic device error"

    def __str__(self):
        return self.msg

class InvalidDeviceError(DeviceError):
    """
    The device is an incompatible device
    """
    def __init__(self):
        self.msg = "Incompatible device"

class InvalidDeviceError(DeviceError):
    """
    The device is an incompatible device
    """
    pass

class NoResolutionError(DeviceError):
    """
    The device to be handled does not have an x or y resolution.
    """
    def __init__(self):
        self.msg = "Missing resolution on x/y"

class TouchSequence:
    """
    A full touch sequence starting with ABS_MT_TRACKING_ID x through to
    ABS_MT_TRACKING_ID -1.

    Members
    -------
        points : [ TouchPoint ]
                The list of points comprising this sequence
        times : (start, end)
                The start and finish time in µs
        is_single : bool
                Returns true if this sequence was the only finger down for
                its lifetime.
        max_fingers : int
                Returns the maximum number of fingers down while this touch
                sequence was active. This includes BTN_TOOL_*TAP beyond the
                slot range, i.e. it may be that max_fingers > len(linked)

        linked : [ TouchSequence ]
                A list of other TouchSequences that occured at the same time
                as this one.

        buttons : [ BTN_LEFT, BTN_RIGHT, ...] or None
                A list of buttons down during this touch sequence (or None)
    """

    def __init__(self, slot, id, time):
        self.points = []
        self.linked = []
        self.buttons = None

        # By default, we assume a touch sequence is a single finger
        # sequence.
        self.is_single = True
        # By default, a touch sequence has one finger. If is_single is
        # false, this gives the max number of fingers down at any time.
        self.max_fingers = 1

        # for internal use
        self._id = id
        self._slot = slot
        self._start_time = time
        self._finish_time = None
        self._is_active = True

    def _append(self, tp):
        assert(self._is_active)
        self.points.append(tp)

    def _finalize(self, time):
        self._is_active = False
        self._finish_time = time

    def _link(self, others):
        for o in others:
            if o is not self and o not in self.linked:
                self.linked.append(o)

    @property
    def times(self):
        """Return a tuple of the start and end time in µs"""
        return (self._start_time, self._finish_time)

    @property
    def first(self):
        """Return the first touch point, i.e. the one that started the touch"""
        return self.points[0]

    @property
    def last(self):
        """Return the last touch point, i.e. the one before the end of the sequence"""
        return self.points[-1]

    @classmethod
    def new_seq_from_event(self, slot, event):
        return TouchSequence(slot, event.value, _tv2us(event.sec, event.usec))

    @classmethod
    def _next_id(self, c = itertools.count()):
        return next(c)

    @classmethod
    def _new_fake_seq_from_event(self, slot, event):
        return TouchSequence(slot, self._next_id(), _tv2us(event.sec, event.usec))


    @classmethod
    def _percent_from_event(self, event, evemu_device):
        min = evemu_device.get_abs_minimum(event.code)
        max = evemu_device.get_abs_maximum(event.code)

        return 1.0  * (event.value - min)/(max - min)

    @classmethod
    def _mm_from_event(self, event, evemu_device):
        min = evemu_device.get_abs_minimum(event.code)
        res = evemu_device.get_abs_resolution(event.code)

        return 1.0 * (event.value - min) / res

    @classmethod
    def create_from_recording(self, evemu_device):
        """
        Return a list of touch sequences ordered by start time.

        Params
        ------

        evemu_device : evemu.EvemuDevice
                An initialized evemu device, ready to read events from

        Return
        ------
        [TouchSequence, ...]

        Exceptions
        ----------
        NoResolutionError ... the device does not have x/y resolution

        """

        if not evemu_device.has_event("EV_ABS", "ABS_X") or \
           not evemu_device.has_event("EV_KEY", "BTN_LEFT") or \
           not evemu_device.has_event("EV_KEY", "BTN_TOUCH"):
               raise InvalidDeviceError()

        if evemu_device.has_event("EV_ABS", "ABS_MT_SLOT"):
            is_st = False
            nslots = evemu_device.get_abs_maximum("ABS_MT_SLOT") + 1
            xaxis = "ABS_MT_POSITION_X"
            yaxis = "ABS_MT_POSITION_Y"
        else:
            is_st = True
            nslots = 1
            xaxis = "ABS_X"
            yaxis = "ABS_Y"

        xres = evemu_device.get_abs_resolution(xaxis)
        yres = evemu_device.get_abs_resolution(yaxis)

        if (xres == 0 or yres == 0):
            raise NoResolutionError()

        sequences = []
        slot = 0
        current_seqs = [None] * nslots
        current_points = [ _TouchPointRecording() ] * nslots
        cp = current_points[slot]
        max_fingers_this_frame = 0

        try:
            for e in evemu_device.events():
                if e.matches("EV_ABS", "ABS_MT_SLOT"):
                    if cp.dirty:
                        current_seqs[slot]._append(cp.clean_copy())
                    slot = e.value
                    cp = current_points[slot]
                elif e.matches("EV_ABS", "ABS_MT_TRACKING_ID"):
                    if e.value > -1:
                        current_seqs[slot] = self.new_seq_from_event(slot, e)
                        sequences.append(current_seqs[slot])
                    else:
                        current_seqs[slot]._finalize(_tv2us(e.sec, e.usec))
                        current_seqs[slot] = None
                elif e.matches("EV_ABS", xaxis):
                    if is_st and current_seqs[slot] is None:
                        current_seqs[slot] = self._new_fake_seq_from_event(slot, e)
                        sequences.append(current_seqs[slot])

                    cp.x = self._mm_from_event(e, evemu_device)
                    cp.x_percent = self._percent_from_event(e, evemu_device)
                    toffset = current_seqs[slot].times[0]
                    cp.time = _tv2us(e.sec, e.usec) - toffset
                elif e.matches("EV_ABS", yaxis):
                    if is_st and current_seqs[slot] is None:
                        current_seqs[slot] = self._new_fake_seq_from_event(slot, e)
                        sequences.append(current_seqs[slot])

                    cp.y = self._mm_from_event(e, evemu_device)
                    cp.y_percent = self._percent_from_event(e, evemu_device)
                    toffset = current_seqs[slot].times[0]
                    cp.time = _tv2us(e.sec, e.usec) - toffset
                elif e.matches("EV_ABS", "ABS_MT_PRESSURE"):
                    cp.press = e.value
                    toffset = current_seqs[slot].times[0]
                    cp.time = _tv2us(e.sec, e.usec) - toffset
                elif is_st and e.matches("EV_KEY", "BTN_TOUCH"):
                    if e.value == 0:
                        current_seqs[slot]._finalize(_tv2us(e.sec, e.usec))
                        current_seqs[slot] = None
                elif e.matches("EV_KEY", "BTN_TOOL_DOUBLETAP"):
                    if e.value > 0:
                        max_fingers_this_frame = 2
                elif e.matches("EV_KEY", "BTN_TOOL_TRIPLETAP"):
                    if e.value > 0:
                        max_fingers_this_frame = 3
                elif e.matches("EV_KEY", "BTN_TOOL_QUADTAP"):
                    if e.value > 0:
                        max_fingers_this_frame = 4
                elif e.matches("EV_KEY", "BTN_TOOL_QUINTTAP"):
                    if e.value > 0:
                        max_fingers_this_frame = 5
                elif e.matches("EV_KEY", "BTN_LEFT") or \
                     e.matches("EV_KEY", "BTN_MIDDLE") or \
                     e.matches("EV_KEY", "BTN_RIGHT"):
                    seq = current_seqs[slot]
                    if seq is not None:
                        if seq.buttons is None:
                            current_seqs[slot]
                            seq.buttons = [ e.code ]
                        elif not e.code in seq.buttons:
                            seq.buttons.append(e.code)
                elif e.matches("EV_SYN", "SYN_REPORT"):
                    if cp.dirty:
                        current_seqs[slot]._append(cp.clean_copy())

                    active = [ s for s in current_seqs if s is not None ]
                    if len(active) > 1 or max_fingers_this_frame > 1:
                        for s in active:
                            s.is_single = False
                            s._link(active)
                            s.max_fingers = max(s.max_fingers, max_fingers_this_frame)
                    max_fingers_this_frame = 0
        except Exception as error:
            print("ERROR: in line {}".format(e))
            import traceback
            traceback.print_exc()
            print("-----")
            raise error

        return sequences

class EventProcessor:
    """
    Members
    -------
        sourcefiles : [ str ]
            All source files given on the command line
    """
    def __init__(self):
        parser = argparse.ArgumentParser(description="")
        parser.add_argument("path", metavar="recording", nargs="*", help="Path to evemu recording")
        self.add_args(parser)
        self.args = parser.parse_args()

        self.sourcefiles = self.args.path

    def add_args(self, arg_parser):
        pass

    def process(self, parsed_cmdline_args):
        pass

    def run(self):
        self.gnuplot = GnuPlot(self.__class__.__name__)
        with self.gnuplot as f:
            self.process(self.args)

def main(argv):
    d = evemu.Device(argv[0], create=False)

    seqs = TouchSequence.create_from_recording(d)
    print("Number of sequences: {}".format(len(seqs)))

    single = [ s for s in seqs if s.is_single ]
    print("Number of single sequences: {}".format(len(single)))

    double = [ s for s in seqs if s.max_fingers == 2 ]
    print("Number of double sequences: {}".format(len(double)))
    triple = [ s for s in seqs if s.max_fingers == 3 ]
    print("Number of triple sequences: {}".format(len(triple)))

if __name__ == "__main__":
    main(sys.argv[1:])
