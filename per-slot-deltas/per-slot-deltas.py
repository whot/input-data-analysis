#!/usr/bin/python
# -*- coding: utf-8
#
# Measures the relative motion between touch events (based on slots)

from __future__ import print_function

import evemu
import sys
import os
import math
import argparse

class SlotState:
    NONE = 0
    BEGIN = 1
    UPDATE = 2
    END = 3

class Slot:
    index = 0
    state = SlotState.NONE
    x = 0
    y = 0
    dx = 0
    dy = 0
    dirty = False

def main(argv):
    slots = []
    xres, yres = 1, 1

    parser = argparse.ArgumentParser(description="Measure delta between event frames for each slot")
    parser.add_argument("--use-mm", action='store_true', help="Use mm instead of device deltas")
    parser.add_argument("--use-st", action='store_true', help="Use ABS_X/ABS_Y instead of device deltas")
    parser.add_argument("--use-absolute", action='store_true', help="Use absolute coordinates, not deltas")
    parser.add_argument("path", metavar="recording",
                        nargs=1, help="Path to evemu recording")
    args = parser.parse_args()

    d = evemu.Device(args.path[0], create=False)
    nslots = d.get_abs_maximum("ABS_MT_SLOT") + 1
    print("Tracking %d slots" % nslots)
    if nslots > 10:
        nslots = 10
        print("Capping at %d slots" % nslots)

    slots = [Slot() for _ in range(0, nslots)]

    marker_begin_slot = "   ++++++    | "
    marker_end_slot =   "   ------    | "
    marker_empty_slot = " *********** | "
    marker_no_data =    "             | "

    if args.use_mm:
        xres = 1.0 * d.get_abs_resolution("ABS_MT_POSITION_X")
        yres = 1.0 * d.get_abs_resolution("ABS_MT_POSITION_Y")
        marker_empty_slot = " ************* | "
        marker_no_data =    "               | "
        marker_begin_slot = "    ++++++     | "
        marker_end_slot =   "    ------     | "

    if args.use_st:
        print("Warning: slot coordinates on FINGER/DOUBLETAP change may be incorrect")

    slot = 0
    for e in d.events():
        s = slots[slot]
        if args.use_st:
            # Note: this relies on the EV_KEY events to come in before the
            # x/y events, otherwise the last/first event in each slot will
            # be wrong.
            if e.matches("EV_KEY", "BTN_TOOL_FINGER"):
                slot = 0
                s = slots[slot]
                s.dirty = True
                if e.value:
                    s.state = SlotState.BEGIN
                else:
                    s.state = SlotState.END
            elif e.matches("EV_KEY", "BTN_TOOL_DOUBLETAP"):
                slot = 1
                s = slots[slot]
                s.dirty = True
                if e.value:
                    s.state = SlotState.BEGIN
                else:
                    s.state = SlotState.END
            elif e.matches("EV_ABS", "ABS_X"):
                if s.state == SlotState.UPDATE:
                    s.dx = e.value - s.x
                s.x = e.value
                s.dirty = True
            elif e.matches("EV_ABS", "ABS_Y"):
                if s.state == SlotState.UPDATE:
                    s.dy = e.value - s.y
                s.y = e.value
                s.dirty = True
        else:
            if e.matches("EV_ABS", "ABS_MT_SLOT"):
                slot = e.value
                s = slots[slot]
                s.dirty = True
            elif e.matches("EV_ABS", "ABS_MT_TRACKING_ID"):
                if e.value == -1:
                    s.state = SlotState.END
                else:
                    s.state = SlotState.BEGIN
                    s.dx = 0
                    s.dy = 0
                s.dirty = True
            elif e.matches("EV_ABS", "ABS_MT_POSITION_X"):
                if s.state == SlotState.UPDATE:
                    s.dx = e.value - s.x
                s.x = e.value
                s.dirty = True
            elif e.matches("EV_ABS", "ABS_MT_POSITION_Y"):
                if s.state == SlotState.UPDATE:
                    s.dy = e.value - s.y
                s.y = e.value
                s.dirty = True

        if e.matches("EV_SYN", "SYN_REPORT"):
            print("{:2d}.{:06d}: ".format(e.sec, e.usec), end='')
            for sl in slots:
                if sl.state == SlotState.NONE:
                    print(marker_empty_slot, end='')
                elif sl.state == SlotState.BEGIN:
                    print(marker_begin_slot, end='')
                elif sl.state == SlotState.END:
                    print(marker_end_slot, end='')
                elif not sl.dirty:
                    print(marker_no_data, end='')
                else:
                    if sl.dx != 0 and sl.dy != 0:
                        t = math.atan2(sl.dx, sl.dy)
                        t += math.pi # in [0, 2pi] range now

                        if t == 0:
                            t = 0.01;
                        else:
                            t = t * 180.0 / math.pi

                        directions = [ '↖↑', '↖←', '↙←', '↙↓', '↓↘', '→↘', '→↗', '↑↗']
                        direction = "{:3.0f}".format(t)
                        direction = directions[int(t/45)]
                    else:
                        direction = '..'

                    if args.use_mm:
                        sl.dx /= xres
                        sl.dy /= yres
                        print("{} {:+3.2f}/{:+03.2f} | ".format(direction, sl.dx, sl.dy), end='')
                    elif args.use_absolute:
                        print("{} {:4d}/{:4d} | ".format(direction, sl.x, sl.y), end='')
                    else:
                        print("{} {:4d}/{:4d} | ".format(direction, sl.dx, sl.dy), end='')
                if sl.state == SlotState.BEGIN:
                    sl.state = SlotState.UPDATE
                elif sl.state == SlotState.END:
                    sl.state = SlotState.NONE

                sl.dirty = False
            print("")


if __name__ == "__main__":
    main(sys.argv)
