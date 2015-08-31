#!/usr/bin/python
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
    parser.add_argument("path", metavar="recording",
                        nargs=1, help="Path to evemu recording")
    args = parser.parse_args()

    d = evemu.Device(args.path[0], create=False)
    nslots = d.get_abs_maximum("ABS_MT_SLOT") + 1
    slots = [Slot() for _ in range(0, nslots)]
    print("Tracking %d slots" % nslots)

    marker_begin_slot = "   +++    | "
    marker_end_slot =   "   ---    | "
    marker_empty_slot = "********* | "
    marker_no_data =    "          | "

    if args.use_mm:
        xres = 1.0 * d.get_abs_resolution("ABS_MT_POSITION_X")
        yres = 1.0 * d.get_abs_resolution("ABS_MT_POSITION_Y")
        marker_empty_slot = "*********** | "
        marker_no_data =    "            | "
        marker_begin_slot = "    +++     | "
        marker_end_slot =   "    ---     | "

    slot = 0
    for e in d.events():
        s = slots[slot]
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
        elif e.matches("EV_SYN", "SYN_REPORT"):
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
                    if args.use_mm:
                        sl.dx /= xres
                        sl.dy /= yres
                        print("{:+3.2f}/{:+03.2f} | ".format(sl.dx, sl.dy), end='')
                    else:
                        print("{:4d}/{:4d} | ".format(sl.dx, sl.dy), end='')
                if sl.state == SlotState.BEGIN:
                    sl.state = SlotState.UPDATE
                elif sl.state == SlotState.END:
                    sl.state = SlotState.NONE

                sl.dirty = False
            print("")


if __name__ == "__main__":
    main(sys.argv)
