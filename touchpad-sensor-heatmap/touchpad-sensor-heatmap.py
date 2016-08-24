#!/usr/bin/python
#
# Collects all x/y positions reported by the sensor. Looks at single-touch
# emulation only (ABS_X, ABS_Y).
#
# Output is a png file with black background. Any x/y location captured by
# the recording draws a horizontal/vertical line through the whole range, so
# the remaing black spots are those where the sensor never caught any
# event. e.g. a black spot at 10/10 means that no event every had an x
# coordinate of 10, and no event ever had a y coordinate of 10.
# 

OUTPUT_FILE="heatmap.png"

import evemu
import sys
import os
import math
from PIL import Image
import array

def main(argv):
    d = evemu.Device(argv[1], create=False)

    locations = {}
    x, y = 0, 0

    for e in d.events():
        if e.matches("EV_ABS", "ABS_X"):
            x = e.value
        elif e.matches("EV_ABS", "ABS_Y"):
            y = e.value
        elif e.matches("EV_SYN", "SYN_REPORT"):
            val = locations.get((x, y), 0)
            locations[(x, y)] = val + 1

    xmax = d.get_abs_maximum("ABS_X")
    xmin = d.get_abs_minimum("ABS_X")
    ymax = d.get_abs_maximum("ABS_Y") 
    ymin = d.get_abs_minimum("ABS_Y")

    # adjust for out-of-range coordinates
    xmax = max([x for (x, y) in locations.keys()] + [xmax])
    ymax = max([y for (x, y) in locations.keys()] + [ymax])
    xmin = min([x for (x, y) in locations.keys()] + [xmin])
    ymin = min([y for (x, y) in locations.keys()] + [ymin])

    w = xmax - xmin
    h = ymax - ymin
    stride = w

    imgdata = [0] * (stride * (h + 1))

    for (x, y) in locations.keys():
        px, py = x - xmin, y - ymin
        for px in range(0, w):
            imgdata[py * stride + px] = 255

        px, py = x - xmin, y - ymin
        for py in range(0, h):
            imgdata[py * stride + px] = 255

    im = Image.new('L', (w, h + 1))
    im.putdata(imgdata)
    im.save(OUTPUT_FILE)

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("Usage: %s events.evemu" % os.path.basename(sys.argv[0]))
        sys.exit(1)
    main(sys.argv)
