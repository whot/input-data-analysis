#!/usr/bin/python

from __future__ import print_function
import sys
import os

import evemu

EV_SYN = 0x00
EV_ABS = 0x03
ABS_X = 0x00
ABS_Y = 0x01

def error(*msg):
    """Print an error message to stderr"""
    print("ERROR: ", msg, file=sys.stderr)
    sys.exit(1)

def map_to_range(point, xaxis, yaxis):
    """
    Map the tuple point into the axis ranges for x/y, returning a
    tuple with normalized coordinates between [0, 1]
    """
    x = 1.0 * (point[0] - xaxis[0])/(xaxis[1] - xaxis[0])
    y = 1.0 * (point[1] - yaxis[0])/(yaxis[1] - yaxis[0])
    return (x, y)

def get_xy(device):
    """extract x/y information, return as list"""

    xaxis = (device.get_abs_minimum(ABS_X), device.get_abs_maximum(ABS_X))
    yaxis = (device.get_abs_minimum(ABS_Y), device.get_abs_maximum(ABS_Y))
    x = xaxis[0]
    y = yaxis[0]
    events = device.events()
    dirty = False

    xydata = []

    for e in events:
        if e.type == EV_ABS:
            if e.code == ABS_X:
                x = e.value
                dirty = True
            elif e.code == ABS_Y:
                y = e.value
                dirty = True
        elif e.type == EV_SYN and dirty:
            dirty = False
            xydata.append((map_to_range((x, y), xaxis, yaxis)))
    return xydata

def print_gnuplot_header():
    print("#!/usr/bin/gnuplot")
    print("set multiplot")
    print("set xlabel 'normalized to [0, 1]'")
    print("set ylabel 'normalized to [0, 1]'")
    print("set xrange [0:1]")
    print("set yrange [1:0]")

def print_gnuplot_footer():
    print("pause -1")

def main(args):
    path = args[1]

    device = evemu.Device(path, create=False)
    if not device.has_event(EV_ABS, ABS_X) or not device.has_event(EV_ABS, ABS_Y):
        error("Invalid device, missing X/Y")

    xaxis = (device.get_abs_minimum(ABS_X), device.get_abs_maximum(ABS_X))
    yaxis = (device.get_abs_minimum(ABS_Y), device.get_abs_maximum(ABS_Y))

    print_gnuplot_header()

    xy = get_xy(device)

    print("plot \"-\" using 1:2 title 'touches'")

    for (x, y) in xy:
        print("\t%f\t%f" % (x, y))
    print("\te")
    print_gnuplot_footer()

if __name__ == "__main__":
    main(sys.argv)
