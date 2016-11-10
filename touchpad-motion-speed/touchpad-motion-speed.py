#!/usr/bin/python
# -*- coding: utf-8
#
# Measures the relative motion between touch events (based on slots)
# and calculates the speed in mm/s for each event.
# This gives an indicator of the min/max speed reached by the user, which in
# turn tells us how far a pointer acceleration curve needs to go to really
# be useful.

from __future__ import print_function

from tabulate import *
import evemu
import sys
import os
import math
import argparse

class SlotState:
    NONE = 0
    BEGIN = 1
    UPDATE = 2
    END = 3

class Slot:
    index = 0
    state = SlotState.NONE
    x = 0
    y = 0
    dx = 0
    dy = 0
    dirty = False
    time = 0
    dt = 0

def parse_recordings_file(path):
    vels = []

    d = evemu.Device(path, create=False)
    nslots = d.get_abs_maximum("ABS_MT_SLOT") + 1
    slots = [Slot() for _ in range(0, nslots)]
    xres = 1.0 * d.get_abs_resolution("ABS_MT_POSITION_X")
    yres = 1.0 * d.get_abs_resolution("ABS_MT_POSITION_Y")
    slot = 0
    for e in d.events():
        s = slots[slot]
        if e.matches("EV_ABS", "ABS_MT_SLOT"):
            slot = e.value
            s = slots[slot]
            s.dirty = True
        elif e.matches("EV_ABS", "ABS_MT_TRACKING_ID"):
            if e.value == -1:
                s.state = SlotState.END
            else:
                s.state = SlotState.BEGIN
                s.time = e.sec * 1e6 + e.usec
                s.dx = 0
                s.dy = 0
            s.dirty = True
        elif e.matches("EV_ABS", "ABS_MT_POSITION_X"):
            if s.state == SlotState.UPDATE:
                s.dx = e.value - s.x
            s.x = e.value
            s.dirty = True
        elif e.matches("EV_ABS", "ABS_MT_POSITION_Y"):
            if s.state == SlotState.UPDATE:
                s.dy = e.value - s.y
            s.y = e.value
            s.dirty = True
        elif e.matches("EV_SYN", "SYN_REPORT"):
            for sl in slots:
                if sl.state != SlotState.NONE and sl.dirty:
                    t = e.sec * 1e6 + e.usec
                    sl.dt = t - sl.time
                    sl.time = t

                if  sl.state == SlotState.UPDATE and sl.dirty:
                    dist = math.hypot(sl.dx/xres, sl.dy/yres) # in mm
                    dt = sl.dt # in µs
                    vel = 1000 * dist/dt # mm/ms == m/s
                    vel = 1000 * vel # mm/s
                    vels.append(vel)
                    # print("{}".format(vel))

                if sl.state == SlotState.BEGIN:
                    sl.state = SlotState.UPDATE
                elif sl.state == SlotState.END:
                    sl.state = SlotState.NONE
                sl.dirty = False

    nevents = len(vels)
    maxvel = max(vels)
    print("# Number of data points: {}".format(nevents))
    print("# Highest velocity: {} mm/s".format(maxvel))

    # divide into buckets for each 10mm/s increment
    increment = 10
    nbuckets = int(maxvel/increment) + 1
    buckets = [0] * nbuckets
    print("# Starting with {} buckets".format(nbuckets))
    min_events = 5
    for v in vels:
        bucket = int(v/increment)
        buckets[bucket] += 1

    reduced_nevents = nevents
    for i in range(len(buckets) - 1, -1, -1):
        if buckets[i] >= min_events:
            break
        reduced_nevents -= buckets[i]
        # make sure we don't drop more than 5% of the data
        if nevents * 0.95 > reduced_nevents:
            break

    print("# Reducing to {} buckets ({} required per bucket)".format(i + 1, min_events))
    del buckets[i+1:]

    nevents_new = sum(buckets)
    print("# Left with {} data points ({:.1f}% of data)".format(nevents_new, 100.0 * nevents_new/nevents))

    speed = increment
    total_percent = 0
    datapoints = {}

    for b in buckets:
        percent = 100.0 * b/nevents_new
        total_percent += percent
        datapoints[speed] = {
            "speed" : speed,
            "nevents" : b,
            "percent" : percent,
            "total-percent" : total_percent,
        }

        #print(".. {}mm/s: {:5} events, {:.1f}% {:.1f}% total".format(speed, b, percent, total_percent))
        speed += increment

    return datapoints

def print_one_dataset(data):
    """
    data is a dict with speed as the key and a dict with info for each speed
    """

    speeds = data.keys()
    speeds.sort()
    datapoints = [ data[key] for key in speeds ]

    print(tabulate(datapoints, headers='keys'))


def print_all_datasets(datasets):
    """
    data is a list of lists with dict objects with the various bits
    attached. So the first recording data is data[0], etc.

    The output we want is each individual set in a column, ready for gnuplot.
    so for the speeds s0, s1, s2,... in recordings r1, r2, r3 the output is

    r1s0 r2s0 r3s0
    r1s1 r2s1 r3s1
    r1s2 r2s2 r3s2
    ...

    """

    longest_speed_list = datasets[0].keys()

    for dataset in datasets[1:]:
        speeds = dataset.keys()
        if len(speeds) > longest_speed_list:
            longest_speed_list = speeds

    speeds = longest_speed_list
    speeds.sort()

    for speed in speeds:
        print('{} "mm/s" "nevents:" '.format(speed), end="")
        for dataset in datasets:
            try:
                data = dataset[speed]
                print("{} ".format(data["nevents"]), end="")
            except KeyError as e:
                print("0 ", end="")

        print('"percent:" ', end="")
        for dataset in datasets:
            try:
                data = dataset[speed]
                print("{} ".format(data["percent"]), end="")
            except KeyError as e:
                print("0 ", end="")

        print('"total_percent:" ', end="")
        for dataset in datasets:
            try:
                data = dataset[speed]
                print("{} ".format(data["total-percent"]), end="")
            except KeyError as e:
                # If we don't get here by definition we must be at 100%
                print("100 ", end="")

        print("")

def main(argv):
    parser = argparse.ArgumentParser(description="Measure delta between event frames for each slot")
    parser.add_argument("path", metavar="recording",
                        nargs="*", help="Path to evemu recording")
    args = parser.parse_args()

    data = []
    for path in args.path:
        data.append(parse_recordings_file(path))

    if len(data) == 1:
        print_one_dataset(data[0])
    else:
        print_all_datasets(data)

if __name__ == "__main__":
    main(sys.argv)
