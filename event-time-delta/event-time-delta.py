#!/usr/bin/python
#
# Measures time delta between SYN_REPORT events on an evemu recording

from __future__ import print_function

import evemu
import sys
import os

def usec(sec, usec):
    return sec * 1000000 + usec

def main(argv):
    last_time = 0

    deltas = {}

    d = evemu.Device(argv[1], create=False)
    for e in d.events():

        if not e.matches("EV_SYN", "SYN_REPORT"):
            print("        %s %s %d" % (evemu.event_get_name(e.type), \
                                        evemu.event_get_name(e.type, e.code), \
                                        e.value))
            continue

        time = usec(e.sec, e.usec)
        dt = (time - last_time)/1000
        last_time = time
        print("%4dms  ---- %s %s ----" % (dt, evemu.event_get_name(e.type), \
                                          evemu.event_get_name(e.type, e.code)))
                
        deltas[dt] = dict.get(deltas, dt, 0) + 1

    print("\nDistribution of deltas in ms:")
    for key, value in dict.iteritems(deltas):
        print("  %dms: %d" % (key, value))

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("Usage: %s events.evemu" % os.path.basename(sys.argv[0]))
        sys.exit(1)
    main(sys.argv)
