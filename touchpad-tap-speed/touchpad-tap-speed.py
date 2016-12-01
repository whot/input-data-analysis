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
        parser.add_argument("--sort-by-mm", action="store_true", help="Sort by mm rather than time")

    def process_one_file(self, f, args):
        self.gnuplot.comment("processing {}".format(f))
        d = evemu.Device(f, create=False)

        seqs = TouchSequence.create_from_recording(d)
        singles = [s for s in seqs if s.is_single and s.points ]

        mm = [ 0 ] * (args.max_move + 1) * 10
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

            mm[int(dist * 10)] += 1

            times[ms] += 1

        return times, mm

    def process(self, args):
        times = [ 0 ] * (args.max_time + 1)
        mm = [ 0 ] * (args.max_move + 1) * 10

        for f in self.sourcefiles:
            try:
                t, m = self.process_one_file(f, args)
                times = map(lambda x, y : x + y, times, t)
                mm = map(lambda x, y : x + y, mm, m)
            except DeviceError as e:
                print("Skipping {} with error: {}".format(f, e))
        
        self.gnuplot.comment("# maximum distance {}mm".format(args.max_move))
        self.gnuplot.comment("# maximum time {}ms".format(args.max_time))

        if args.sort_by_mm:
            self.gnuplot.labels("movement distance (in 0.1mm)", "count")
            for mm, count in enumerate(mm):
                self.gnuplot.data("{} {}".format(mm, count))
        else:
            self.gnuplot.labels("press-release time (ms)", "count")
            for ms, count in enumerate(times):
                self.gnuplot.data("{} {}".format(ms, count))

        self.gnuplot.plot("using 1:2 notitle")

def main(sysargs):
    TouchpadTapSpeed().run()

if __name__ == "__main__":
    main(sys.argv)
