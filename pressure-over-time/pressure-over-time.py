#!/usr/bin/python
#
# Input is an evemu, this script does not handle slots and
# only looks at ABS_PRESSURE.
# 

from __future__ import print_function

import evemu
import sys
import os
import math

def time_to_us(sec, usec):
    return sec + usec/1000000.0

def main(argv):
    d = evemu.Device(argv[1], create=False)

    pmax = d.get_abs_maximum("ABS_PRESSURE")
    pmin = d.get_abs_minimum("ABS_PRESSURE")

    pressure = pmin
    time_offset = -1

    print("#!/usr/bin/gnuplot")
    print("# This is a self-executing gnuplot file")
    print("#")
    print("set xlabel \"time\"")
    print("set ylabel \"pressure\"")
    print("set style data lines")
    print("plot '-' using 1:2 title 'pressure'")

    for e in d.events():
        if time_offset < 0:
            time_offset = time_to_us(e.sec, e.usec)

        if e.matches("EV_ABS", "ABS_PRESSURE"):
            t = time_to_us(e.sec, e.usec) - time_offset
            print("%f %d" % (t, e.value))

    print("e")
    print("pause -1")

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("Usage: %s events.evemu" % os.path.basename(sys.argv[0]))
        sys.exit(1)
    main(sys.argv)
