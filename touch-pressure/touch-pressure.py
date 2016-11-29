#!/usr/bin/env python
# -*- coding: utf-8

import math
import sys
sys.path.append("..")
from shared import *

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

        # three-dimensional plot:
        #   left: touch sequence number
        #   right: pressure value
        #   up: count of pressure values

        data = []
        for s in singles:
            pvals = [ 0 ] * pmax
            for point in s.points:
                p = point.pressure
                pvals[p] += 1
            data.append(pvals)

        gridx = min(len(data), 150)
        gridy = min(pmax, 150)
        self.gnuplot.cmd("set dgrid3d {},{}".format(gridx, gridy))
        
        return data

    def process(self, args):
        self.gnuplot.labels("touch sequence number", "pressure value", "count")

        self.gnuplot.comment("# dist-mm xdist-mm ydist-mm")

        sums = []

        if len(self.sourcefiles) > 1:
            print("Only processing first source file");

        f = self.sourcefiles[0]
        data = self.process_one_file(f, args)

        self.gnuplot.comment("touch-sequence-number pressure-value event-count")
        for sidx, sequence in enumerate(data):
            for pidx, count in enumerate(sequence):
                self.gnuplot.data("{} {} {}".format(sidx, pidx, count))

        self.gnuplot.cmd("set hidden3d")
        self.gnuplot.splot("using 1:2:3 notitle with lines")

def main(sysargs):
    TouchPressure().run()

if __name__ == "__main__":
    main(sys.argv)
