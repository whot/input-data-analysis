#!/usr/bin/env python
# -*- coding: utf-8

import sys

sys.path.append("..")
from shared import *

class TouchpadFingerStartPoint(EventProcessor):

    def add_args(self, arg_parser):
        arg_parser.description = (""
        "Process all touch sequences and list the starting points of each "
        "touch sequence, relative to touchpad width/height. "
        "All recordings output to the same data file."
        "")
        arg_parser.add_argument("--last",
                                action="store_true",
                                help="use the last point of the touch sequence instead of the first")

    def process_one_file(self, f, args):
        self.gnuplot.comment("processing {}".format(f))
        d = evemu.Device(f, create=False)

        seqs = TouchSequence.create_from_recording(d)
        singles = [s for s in seqs if s.is_single and s.points ]

        for s in singles:
            if args.last:
                x, y = s.last.percent
            else:
                x, y = s.first.percent
            self.gnuplot.data("{} {}".format(x, y))

    def process(self, args):
        self.gnuplot.labels("touchpad width", "touchpad height")
        self.gnuplot.ranges("0.0:1.0", "0.0:1.0")

        for f in self.sourcefiles:
            try:
                self.process_one_file(f, args)
            except DeviceError as e:
                print("Skipping {} with error: {}".format(f, e))

        self.gnuplot.plot("using 1:2 notitle")

def main(sysargs):
    TouchpadFingerStartPoint().run()

if __name__ == "__main__":
    main(sys.argv)
