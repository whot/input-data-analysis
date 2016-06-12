#!/usr/bin/python
#
# Input is a single-touch recording, this script does not handle slots and
# only looks at ABS_MT_WIDTH_MAJOR/MINOR.
# 

from __future__ import print_function

import evemu
import sys
import os
import math

def main(argv):
    d = evemu.Device(argv[1], create=False)

    xres = 1.0 * d.get_abs_resolution("ABS_MT_POSITION_X")
    yres = 1.0 * d.get_abs_resolution("ABS_MT_POSITION_Y")
    # Assume Apple trackpad resolutions
    if xres == 0 or yres == 0:
        print("WARNING: Using hardcoded resolutions");
        xres = 94
        yres = 90

    width, height = None, None
    ow, oh = 0, 0

    for e in d.events():
        if e.matches("EV_ABS", "ABS_MT_WIDTH_MAJOR"):
            width = e.value
        elif e.matches("EV_ABS", "ABS_MT_WIDTH_MINOR"):
            height = e.value
        elif e.matches("EV_SYN", "SYN_REPORT"):
            if width == None or height == None:
                continue
            w = width/xres
            h = height/yres
            if w == ow and h == oh:
                continue
            ow = w
            oh = h
            print("width: {} height {} phys: {}x{}mm".format(width, height, w, h))

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("Usage: %s events.evemu" % os.path.basename(sys.argv[0]))
        sys.exit(1)
    main(sys.argv)
