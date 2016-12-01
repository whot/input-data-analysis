#!/usr/bin/python
# -*- coding: utf-8
#
# Measures the time between finger down and finger up per sequence.

import math
import sys

sys.path.append("..")
from shared import *

class TouchpadTapSpeed(EventProcessor):
    def add_args(self, parser):
        parser.description = (""
                "Process all touch sequences and calculate the time between "
                "finger down and finger up"
                "")
        parser.add_argument("--max-time", action="store", type=int,
                            default=250,
                            help="Ignore sequences lasting longer than X ms (default 250)")
        parser.add_argument("--max-move", action="store", type=int,
                            default=6,
                            help="Ignore sequences moving more than X mm (default 6)")
    def process_one_file(self, f, args):
        self.gnuplot.comment("processing {}".format(f))
        d = evemu.Device(f, create=False)

        seqs = TouchSequence.create_from_recording(d)
        singles = [s for s in seqs if s.is_single and s.points ]

        times = [ 0 ] * (args.max_time + 1)

        for s in singles:
            first = s.first
            last = s.last
            tdelta = s.last.time - s.first.time
            ms = int(tdelta/1000)
            if ms > args.max_time:
                continue

            delta = last - first
            dist = math.hypot(delta.x, delta.y)
            if dist > args.max_move:
                continue

            times[ms] += 1

        return times

    def process(self, args):
        self.gnuplot.labels("press-release time (ms)", "count")

        times = [ 0 ] * (args.max_time + 1)
        for f in self.sourcefiles:
            try:
                t = self.process_one_file(f, args)
                times = map(lambda x, y : x + y, times, t)
            except DeviceError as e:
                print("Skipping {} with error: {}".format(f, e))
        
        self.gnuplot.comment("# maximum time {}ms".format(args.max_time))
        for ms, count in enumerate(times):
            self.gnuplot.data("{} {}".format(ms, count))

        self.gnuplot.plot("using 1:2 notitle")

def main(sysargs):
    TouchpadTapSpeed().run()

if __name__ == "__main__":
    main(sys.argv)
