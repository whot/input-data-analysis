#!/usr/bin/python
#
# Measures min/max finger spread between two fingers when the second slot
# starts. Touchpad must support ABS_MT_POSITION_X
#
# Data must be in slots 0 and 1

import evemu
import sys
import os
import math

def main(argv):
    slot = 0
    slots = [[0, 0], [0, 0]]
    tracking_ids = [-1, -1]
    tracking_ids_old = [-1, -1]
    distances = []
    mm = []
    horiz = []
    vert = []

    d = evemu.Device(argv[1], create=False)
    width = d.get_abs_maximum("ABS_MT_POSITION_X") - d.get_abs_minimum("ABS_MT_POSITION_X")
    height = d.get_abs_maximum("ABS_MT_POSITION_Y") - d.get_abs_minimum("ABS_MT_POSITION_Y")
    xres = max(1.0, d.get_abs_resolution("ABS_MT_POSITION_X") * 1.0)
    yres = max(1.0, d.get_abs_resolution("ABS_MT_POSITION_Y") * 1.0)
    print "Touchpad dimensions: %dx%dmm (%dx%d units)" % (width/xres, height/yres, width, height)

    for e in d.events():
        if e.matches("EV_ABS", "ABS_MT_SLOT"):
            slot = e.value
        elif e.matches("EV_ABS", "ABS_MT_TRACKING_ID"):
            tracking_ids[slot] = e.value
        elif e.matches("EV_ABS", "ABS_MT_POSITION_X"):
            slots[slot][0] = e.value
        elif e.matches("EV_ABS", "ABS_MT_POSITION_Y"):
            slots[slot][1] = e.value
        elif e.matches("EV_SYN", "SYN_REPORT"):
            if tracking_ids[0] != -1 and tracking_ids[1] != -1 and \
                (tracking_ids_old[0] == -1 or tracking_ids_old[1] == -1):
                dist = math.hypot(slots[0][0] - slots[1][0],
                                  slots[0][1] - slots[1][1])
                distances.append(dist)

                dist = math.hypot(slots[0][0]/xres - slots[1][0]/xres,
                                  slots[0][1]/yres - slots[1][1]/yres)
                mm.append(dist)
                h = abs(slots[0][0]/xres - slots[1][0]/xres)
                horiz.append(h)
                v = abs(slots[0][1]/yres - slots[1][1]/yres)
                vert.append(v)

                print "New 2fg touch: distance %dmm (h %dmm v %dmm)" % (dist, h, v)

            tracking_ids_old[0] = tracking_ids[0]
            tracking_ids_old[1] = tracking_ids[1]

    print "Max distance: %dmm, %d units" % (max(mm), max(distances))
    print "Min distance %dmm, %d units" % (min(mm), min(distances))

    print "Max distance: %dmm horiz %dmm vert" % (max(horiz), max(vert))
    print "Min distance %dmm horiz, %dmm vert" % (min(horiz), min(vert))

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print "Usage: %s events.evemu" % os.path.basename(sys.argv[0])
        sys.exit(1)
    main(sys.argv)
