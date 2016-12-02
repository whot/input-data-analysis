#!/usr/bin/env python
# -*- coding: utf-8

import math
import sys

sys.path.append("..")
from shared import *
from shared.gnuplot import *

class TouchpadMovementDistance(EventProcessor):

    def add_args(self, arg_parser):
        arg_parser.description = (""
        "Process all touch sequences and calculate the total distance moved"
        "All recordings output to the same data file."
        "")

    def process_one_file(self, f, args):
        self.gnuplot.comment("processing {}".format(f))
        d = evemu.Device(f, create=False)

        seqs = TouchSequence.create_from_recording(d)
        singles = [s for s in seqs if s.is_single and s.points ]

        sums = []

        for s in singles:
            sum_x = 0
            sum_y = 0
            sum_mm = 0
            for this, next in zip(s.points[:-1], s.points[1:]):
                delta = next - this
                dist = math.hypot(delta.x, delta.y)
                sum_x += abs(delta.x)
                sum_y += abs(delta.y)
                sum_mm += abs(dist)
            sums.append((sum_mm, sum_x, sum_y))

        return sums

    def process(self, args):
        self.gnuplot = GnuPlot.from_object(self)
        with self.gnuplot as g:
            g.labels("touch", "distance (mm)")

            g.comment("# dist-mm xdist-mm ydist-mm")

            sums = []

            for f in self.sourcefiles:
                try:
                    sums += self.process_one_file(f, args)
                except DeviceError as e:
                    print("Skipping {} with error: {}".format(f, e))

            for sum_mm, sum_x, sum_y in sorted(sums, key=lambda s : s[0]):
                g.data("{} {} {}".format(sum_mm, sum_x, sum_y))

            g.plot("using 0:1 notitle")

def main(sysargs):
    TouchpadMovementDistance().run()

if __name__ == "__main__":
    main(sys.argv)
