#!/usr/bin/python
#
# Detect slot jumps in a touchpad recording. These can be observed when slot A
# ends and slot B continues with slot A's coordinates.
# Only works for two slots

from __future__ import print_function

import evemu
import sys
import os
import math
import argparse

THRESHOLD=100

class SlotState:
    NONE = 0
    END = 1
    BEGIN = 2
    UPDATE = 3

class Slot:
    index = 0
    state = SlotState.NONE
    x = 0
    y = 0

    def near_enough_to(self, other):
        if other.state < SlotState.BEGIN:
            return False

        return abs(other.x - self.x) < THRESHOLD or \
            abs(other.y - self.y) < THRESHOLD

def main(argv):
    slots = []
    xres, yres = 1, 1

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
            s.dirty = True
        elif e.matches("EV_ABS", "ABS_MT_TRACKING_ID"):
            if e.value == -1:
                s.state = SlotState.END
            else:
                s.state = SlotState.BEGIN
        elif e.matches("EV_ABS", "ABS_MT_POSITION_X"):
            s.x = e.value
            s.dirty = True
        elif e.matches("EV_ABS", "ABS_MT_POSITION_Y"):
            s.y = e.value
            s.dirty = True
        elif e.matches("EV_SYN", "SYN_REPORT"):

            if (slots[0].state == SlotState.END and slots[0].near_enough_to(slots[1])) or \
                    (slots[1].state == SlotState.END and slots[1].near_enough_to(slots[0])):
                print("{:2d}.{:06d}: possible slot jump".format(e.sec, e.usec))

            for sl in slots:
                if sl.state == SlotState.BEGIN:
                    sl.state = SlotState.UPDATE
                elif sl.state == SlotState.END:
                    sl.state = SlotState.NONE


if __name__ == "__main__":
    main(sys.argv)
