#!/usr/bin/python
#
# Measures the relative motion between touch events (based on slots)

from __future__ import print_function

import evemu
import sys
import os
import math

class Slot:
    index = 0
    state = -1
    x = 0
    y = 0
    dx = 0
    dy = 0

def main(argv):
    slots = [[0, 0], [0, 0]]
    tracking_ids = [-1, -1]
    distances = []

    d = evemu.Device(argv[1], create=False)
    nslots = d.get_abs_maximum("ABS_MT_SLOT") + 1
    slots = [Slot() for _ in range(0, nslots)]
    print("Tracking %d slots" % nslots)

    slot = 0
    for e in d.events():
        s = slots[slot]
        if e.matches("EV_ABS", "ABS_MT_SLOT"):
            slot = e.value
            s = slots[slot]
        elif e.matches("EV_ABS", "ABS_MT_TRACKING_ID"):
            s.state = e.value
            if e.value == -1:
                s.dx = 0
                s.dy = 0
            dirty = True
        elif e.matches("EV_ABS", "ABS_MT_POSITION_X"):
            s.dx = e.value - s.x
            s.x = e.value
            dirty = True
        elif e.matches("EV_ABS", "ABS_MT_POSITION_Y"):
            s.dy = e.value - s.y
            s.y = e.value
            dirty = True
        elif e.matches("EV_SYN", "SYN_REPORT"):
            print("{:2d}.{:06d}: ".format(e.sec, e.usec), end='')
            if not dirty:
                for sl in slots:
                    if sl.state == -1:
                        print("********* | ", end='')
                    else:
                        print("          | ", end='')
            else:
                for sl in slots:
                    if sl.state == -1:
                        print("********* | ", end='')
                    else:
                        print("{:4d}/{:4d} | ".format(sl.dx, sl.dy), end='')
            print("")
            dirty = False


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("Usage: %s events.evemu" % os.path.basename(sys.argv[0]))
        sys.exit(1)
    main(sys.argv)
