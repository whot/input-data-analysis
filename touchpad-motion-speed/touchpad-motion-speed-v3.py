#!/usr/bin/python
# -*- coding: utf-8
#
# Measures the relative motion between touch events (based on slots)
# and calculates the speed in mm/s for each event.
# This gives an indicator of the min/max speed reached by the user, which in
# turn tells us how far a pointer acceleration curve needs to go to reall
# be useful.h

import math
import sys

sys.path.append("..")
from shared import *
from shared.gnuplot import *

class TouchpadMotionSpeed(EventProcessor):
    def add_args(self, parser):
        parser.description = (""
                "Process all touch sequences and calculate the velocity "
                "between motion events"
                "")
        parser.add_argument("--bucketsize", action="store", type=int,
                default=10, help="Bucket size in mm/s")
        parser.add_argument("--require-minimum", action="store", type=int,
                default=10, help="Minimum number of events at top end of bucket list")

    def convert_to_buckets(self, bucketsize, vels):
        """
        Return:
        ------

        { bucket : count }, a dictionary with the bucket as key and the
        vels within this bucket as value

        """
        buckets = {}

        for v in vels:
            b = int(v/bucketsize)
            buckets[b] = buckets.get(b, 0) + 1

        return buckets

    def reduce_buckets(self, buckets, min):
        for key in sorted(buckets.keys(), reverse=True):
            if buckets[key] < min:
                del buckets[key]

        return buckets

    def process_one_file(self, f, args):
        self.gnuplot.comment("processing {}".format(f))
        d = evemu.Device(f, create=False)

        seqs = TouchSequence.create_from_recording(d)
        singles = [s for s in seqs if s.is_single and s.points ]

        vels = []

        for s in singles:
            for this, next in zip(s.points[:-1], s.points[1:]):
                delta = next - this
                vel = 1e6 * math.hypot(delta.x, delta.y)/delta.time
                vels.append(vel)

        return vels

    def process(self, args):
        self.gnuplot = GnuPlot.from_object(self)
        with self.gnuplot as g:
            g.labels("speed(mm/s)", "count")

            vels = []

            for f in self.sourcefiles:
                try:
                    vels += self.process_one_file(f, args)
                except DeviceError as e:
                    print("Skipping {} with error: {}".format(f, e))

            buckets = self.convert_to_buckets(args.bucketsize, vels)
            buckets = self.reduce_buckets(buckets, args.require_minimum)
            g.comment("# bucket-speed(mm/s) event-count")
            for b, c in buckets.iteritems():
                g.data("{} {}".format(b, c))

            g.plot("using 1:2 notitle")

def main(sysargs):
    TouchpadMotionSpeed().run()

if __name__ == "__main__":
    main(sys.argv)
