#!/usr/bin/python
#
# Input is a single-touch recording, this script does not handle slots and
# only looks at ABS_MT_PRESSURE.
# 

from __future__ import print_function

import evemu
import sys
import os
import math

def main(argv):
    d = evemu.Device(argv[1], create=False)

    pressure = None
    dpressure = None
    vals = []

    for e in d.events():
        if e.matches("EV_ABS", "ABS_MT_TRACKING_ID"):
            if e.value == -1:
                pressure = None
                dpressure = None
        elif e.matches("EV_ABS", "ABS_PRESSURE"):
            if pressure is not None:
                dpressure = e.value - pressure
            pressure = e.value
        elif e.matches("EV_SYN", "SYN_REPORT"):
            if dpressure is not None and abs(dpressure) <= 2:
                continue
            vals.append((pressure, dpressure))
    
    print("Pressure deltas <= 2 are filtered")
    for p, dp in vals:
        print("Pressure: {} delta {}".format(p, dp))

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("Usage: %s events.evemu" % os.path.basename(sys.argv[0]))
        sys.exit(1)
    main(sys.argv)
