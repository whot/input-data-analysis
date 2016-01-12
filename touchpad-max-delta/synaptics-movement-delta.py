#!/usr/bin/python
#
# Measures maximum delta between events on a touchpad evemu recording
# Touchpad must support ABS_MT_POSITION_X
# Recording of a single finger only

import evemu
import sys
import os
import math

def mean(data):
    return 1.0 * sum(data)/len(data)

def veclen(x, y):
    return math.sqrt(x * x + y * y)

def main(argv):
    deltas = []
    x, y = None, None
    dx, dy = 0, 0
    max_delta = [0, 0, 0]

    d = evemu.Device(argv[1], create=False)
    width = d.get_abs_maximum("ABS_MT_POSITION_X") - d.get_abs_minimum("ABS_MT_POSITION_X")
    height = d.get_abs_maximum("ABS_MT_POSITION_Y") - d.get_abs_minimum("ABS_MT_POSITION_Y")
    diag = veclen(width, height)
    xres = d.get_abs_resolution("ABS_MT_POSITION_X") * 1.0
    yres = d.get_abs_resolution("ABS_MT_POSITION_Y") * 1.0
    print "Touchpad dimensions: %dx%dmm" % (width/xres, height/yres)
    print "Touchpad diagonal: %.2f (0.25 == %.2f)" % (diag, 0.25 * diag)

    diag = veclen(width/xres, height/yres)
    print "Touchpad diagonal: %.2fmm (0.25 == %.2fmm)" % (diag, 0.25 * diag)

    for e in d.events():
        if e.matches("EV_ABS", "ABS_MT_TRACKING_ID"):
            if e.value == -1 and len(deltas) > 0:
                vdeltas = [ veclen(x/xres, y/xres) for (x, y) in deltas]
                print("%d deltas, average %.2f, max %.2f, total distance %.2f in mm" %
                        (len(vdeltas), mean(vdeltas), max(vdeltas), sum(vdeltas)))

                xdeltas = [ x/xres for (x, y) in deltas]
                ydeltas = [ y/yres for (x, y) in deltas]
                print("... x: average %.2f, max %.2f, total distance %.2f" %
                        (mean(xdeltas), max(xdeltas), sum(xdeltas)))
                print("... y: average %.2f, max %.2f, total distance %.2f" %
                        (mean(ydeltas), max(ydeltas), sum(ydeltas)))
                max_delta[0] = max(max_delta[0], max(vdeltas))
                max_delta[1] = max(max_delta[1], max(xdeltas))
                max_delta[2] = max(max_delta[2], max(ydeltas))
            else:
                deltas = []
                x, y = None, None
                dx, dy = 0, 0
        elif e.matches("EV_ABS", "ABS_MT_POSITION_X"):
            if x != None:
                dx = e.value - x
            x = e.value
        elif e.matches("EV_ABS", "ABS_MT_POSITION_Y"):
            if y != None:
                dy = e.value - y
            y = e.value
        elif e.matches("EV_SYN", "SYN_REPORT"):
            if dx != 0 and dy != 0:
                deltas.append((dx, dy))
            dx, dy = 0, 0

    print("Maximum recorded delta: %.2fmm" % (max_delta[0]))
    print("... x: %.2fmm" % max_delta[1])
    print("... y: %.2fmm" % max_delta[2])
    return

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print "Usage: %s events.evemu" % os.path.basename(sys.argv[0])
        sys.exit(1)
    main(sys.argv)
