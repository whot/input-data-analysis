#!/usr/bin/env python
# -*- coding: utf-8

import abc
import argparse
import evemu
import sys

sys.path.append("..")
from shared import *

class Velocity:
    """
    A class representing one velocity value at a given time.

    Members
    -------

    vel : int
        velocity in mm/s

    time : int
        timestamp in µs
        The timestamp is that of the last point considered, i.e. if 4 points
        are considered for the calculation of the velocity, the timestamp is
        that of the fourth point
    """

    def __init__(self, vel, time):
        self.vel = vel
        self.time = time

class VelocityCalculator:
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __init__():
        pass

    def calculate(sequence):
        """
        Params:
        ------
        points : TouchSequence

        Return:
        -------
        A list of Velocity objects
        """
        return

class VelocityCalculator2point(VelocityCalculator):
    """
    Calculates velocity values between each two points of a TouchSequence
    """
    def __init__():
        pass

    def calculate(sequence):
        vels = []
        for idx in range(1, len(sequence.points)):
            dx = (points[idx].x - points[idx-1].x)
            dy = (points[idx].y - points[idx-1].y)
            dt = points[idx].time - points[idx-1].time
            vel = math.hypot(dx, dy)/dt
            vels.append(Velocity(vel, points[idx].time))
        return vels

class VelocityCalculator4point(VelocityCalculator):
    def __init__():
        pass

    def calculate(points):
        vels = []
        for idx in range(3, len(sequence.points)):
            dx = (points[idx].x + points[idx-1].x - points[idx-2].x - points[idx-3].x)/4.0
            dy = (points[idx].y + points[idx-1].y - points[idx-2].y - points[idx-3].y)/4.0
            dt = points[idx].time - points[idx-3].time
            vel = math.hypot(dx, dy)/dt
            vels.append(Velocity(vel, points[idx].time))
        return vels

class EventProcessor:
    """
    Members
    -------
        sourcefiles : [ str ]
            All source files given on the command line
    """
    def __init__(self):
        parser = argparse.ArgumentParser(description="")
        parser.add_argument("path", metavar="recording", nargs="*", help="Path to evemu recording")
        self.add_args(parser)
        self.args = parser.parse_args()

        self.sourcefiles = self.args.path

    def add_args(self, arg_parser):
        pass

    def process(self, parsed_cmdline_args):
        pass

    def run(self):
        self.gnuplot = GnuPlot(self.__class__.__name__)
        with self.gnuplot as f:
            self.process(self.args)
