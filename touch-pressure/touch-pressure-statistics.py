#!/usr/bin/env python
# -*- coding: utf-8

import math
import sys
sys.path.append("..")
from shared import *
from shared.gnuplot import *

class TouchPressure(EventProcessor):
    def process_one_file(self, f, args):
        """
        Returns
        -------
           A nested list of num-touchpoints elements, each of which is a
           list of range min-pressure:max-pressure containting the item
           count for that pressure. i.e. data[4][60] is the number of events
           in sequence 4 with pressure value 60.
        """
        d = evemu.Device(f, create=False)

        seqs = TouchSequence.create_from_recording(d)
        singles = [s for s in seqs if s.is_single and s.points ]

        pmin = d.get_abs_minimum("ABS_MT_PRESSURE")
        pmax = d.get_abs_maximum("ABS_MT_PRESSURE")

        self.gnuplot.ranges(None, "{}:{}".format(pmin, pmax))

        pvals = [ 0 ] * (pmax + 1)
        for s in singles:
            for point in s.points:
                p = point.pressure
                try:
                    pvals[p] += 1
                except:
                    print(p)

        return pvals

    def process(self, args):
        self.gnuplot = GnuPlot.from_object(self)
        with self.gnuplot as g:
            g.labels("pressure value", "count")

            sums = None


            for f in self.sourcefiles:
                f = self.sourcefiles[0]

                data = self.process_one_file(f, args)
                if sums is None:
                    sums = data
                else:
                    sums = [ (x + y) for x, y in zip(sums, data)]

                g.comment("pressure-value event-count")
                for pidx, count in enumerate(sums):
                    g.data("{} {}".format(pidx, count))

                g.plot("using 1:2 notitle with lines")

def main(sysargs):
    TouchPressure().run()

if __name__ == "__main__":
    main(sys.argv)
