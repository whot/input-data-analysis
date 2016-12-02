#!/usr/bin/python
# -*- coding: utf-8
#
# Measures the time between finger down and finger up per sequence.

import math
import sys
import numpy

sys.path.append("..")
from shared import *
from shared.gnuplot import *

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
        parser.add_argument("--use-location", action="store_true",
                            help="Only print the start location for each tap")

    def process_one_file(self, f, args):
        """
        Processes one evemu recording and returns the calculated times,
        distances and finger down locations for detected tap sequences.

        Returns
        -------
         ( times, dist, locations )
                where times[ms] is the count of events for sequences with a
                duration of ms
                where dist[d] is the count of events for sequences with a
                movement distances of d (in 0.1 mm)
                where locations[i] is the (x, y) tuple of finger down for
                all detected sequences
        """
        d = evemu.Device(f, create=False)

        seqs = TouchSequence.create_from_recording(d)
        singles = [s for s in seqs if s.is_single and s.points and s.buttons is None]

        mm = [ 0 ] * (args.max_move + 1) * 10
        times = [ 0 ] * (args.max_time + 1)
        locations = []

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

            # ignore the left/right 10% of the touchpad, could be palms or
            # edge scroll
            if first.percent[0] > 0.90 or first.percent[0] < 0.10:
                continue

            mm[int(dist * 10)] += 1
            times[ms] += 1
            locations.append(first.percent)

        return times, mm, locations

    def plot_distance(self, args, mms, g):
        g.comment("# maximum distance {}mm".format(args.max_move))
        g.comment("# maximum time {}ms".format(args.max_time))
        g.labels("movement distance (in 0.1mm)", "count")
        for mm, count in enumerate(mms):
            g.data("{} {}".format(mm, count))

        g.plot("using 1:2 notitle")

        # mean of distances
        flat = [ [idx] * count for idx, count in enumerate(mms) ]
        flat = numpy.concatenate(flat)
        mean = numpy.mean(flat)
        g.plot("{}, t title 'mean ({:.1f})'".format(mean, mean))

        tmin, tmax = 0, max(mms)
        # 50, 90, 95 percentiles
        percentiles = numpy.percentile(flat, [50, 90, 95])
        g.cmd("set parametric")
        g.cmd("set trange [{}:{}]".format(tmin, tmax))
        g.plot("{}, t title '50% ({:3.1f})'".format(percentiles[0], percentiles[0]))
        g.plot("{}, t title '90% ({:3.1f})'".format(percentiles[1], percentiles[1]))
        g.plot("{}, t title '95% ({:3.1f})'".format(percentiles[2], percentiles[2]))

    def plot_locations(self, args, locations, g):
        g.labels("x", "y")
        g.ranges("0:100", "0:100")
        for x, y in locations:
            g.data("{} {}".format(x * 100, y * 100))
        g.plot("using 1:2 notitle")


    def plot_times(self, args, times, g):
        g.comment("# maximum distance {}mm".format(args.max_move))
        g.comment("# maximum time {}ms".format(args.max_time))

        g.labels("press-release time (ms)", "count")
        for ms, count in enumerate(times):
            g.data("{} {}".format(ms, count))

        g.plot("using 1:2 notitle")

        # mean of times distances
        flat = [ [idx] * count for idx, count in enumerate(times) ]
        flat = numpy.concatenate(flat)
        mean = numpy.mean(flat)
        tmin, tmax = 0, max(times)
        g.cmd("set parametric")
        g.cmd("set trange [{}:{}]".format(tmin, tmax))
        g.plot("{}, t title 'mean ({:.1f})'".format(mean, mean))

        # 50, 90, 95 percentiles
        percentiles = numpy.percentile(flat, [50, 90, 95])
        g.plot("{}, t title '50% ({:3.1f})'".format(percentiles[0], percentiles[0]))
        g.plot("{}, t title '90% ({:3.1f})'".format(percentiles[1], percentiles[1]))
        g.plot("{}, t title '95% ({:3.1f})'".format(percentiles[2], percentiles[2]))

    def process(self, args):

        times = [ 0 ] * (args.max_time + 1)
        mms = [ 0 ] * (args.max_move + 1) * 10
        locations = []

        gnuplot_times, gnuplot_dist, gnuplot_loc = GnuPlot.from_object(self, suffixes = ['times', 'distance', 'location'])

        for f in self.sourcefiles:
            try:
                t, m, l = self.process_one_file(f, args)
                times = map(lambda x, y : x + y, times, t)
                mms = map(lambda x, y : x + y, mms, m)
                locations += l
            except DeviceError as e:
                print("Skipping {} with error: {}".format(f, e))

        with gnuplot_dist as g:
            self.plot_distance(args, mms, g)

        with gnuplot_loc as g:
            self.plot_locations(args, locations, g)

        with gnuplot_times as g:
            self.plot_times(args, times, g)

def main(sysargs):
    TouchpadTapSpeed().run()

if __name__ == "__main__":
    main(sys.argv)
