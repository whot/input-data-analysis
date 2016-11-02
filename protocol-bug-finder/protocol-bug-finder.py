#!/usr/bin/python
#
# Input is an evemu.

from __future__ import print_function

import evemu
import os
import sys
import unittest

evemu_path = None

def is_abs_device(path):
        d = evemu.Device(argv[1], create=False)
        return d.has_event("EV_ABS", "ABS_X")

def is_rel_device(path):
        d = evemu.Device(argv[1], create=False)
        return d.has_event("EV_REL", "REL_X")

class TestEvdevDevice(unittest.TestCase):
    def setUp(self):
        self.d = evemu.Device(evemu_path, create=False)

    def test_no_SYN_DROPPED(self):
        for e in self.d.events():
            self.assertFalse(e.matches("EV_SYN", "SYN_DROPPED"))

class TestAbsoluteDevice(TestEvdevDevice):
    def setUp(self):
        super(TestAbsoluteDevice, self).setUp()

        required = ["ABS_X", "ABS_Y"]
        is_abs = False

        for r in required:
            if self.d.has_event("EV_ABS", r):
                is_abs = True
                break

        if not is_abs:
            raise unittest.SkipTest

    def test_has_single_emulation(self):
        self.assertTrue(self.d.has_event("EV_ABS", "ABS_X"))
        self.assertTrue(self.d.has_event("EV_ABS", "ABS_Y"))

    def test_has_both_abs_x_and_y(self):
        self.assertTrue(self.d.has_event("EV_ABS", "ABS_X"))
        self.assertTrue(self.d.has_event("EV_ABS", "ABS_Y"))

    def test_does_not_exceed_axis_ranges(self):
        xmin = self.d.get_abs_minimum("ABS_X")
        xmax = self.d.get_abs_maximum("ABS_X")
        ymin = self.d.get_abs_minimum("ABS_Y")
        ymax = self.d.get_abs_maximum("ABS_Y")

        for e in self.d.events():
            if e.matches("EV_ABS", "ABS_X"):
                self.assertGreaterEqual(e.value, xmin)
                self.assertLessEqual(e.value, xmax)
            elif e.matches("EV_ABS", "ABS_Y"):
                self.assertGreaterEqual(e.value, ymin)
                self.assertLessEqual(e.value, ymax)

    def test_has_resolution(self):
        axes = ["ABS_X", "ABS_Y"]
        for a in axes:
            if self.d.has_event("EV_ABS", a):
                self.assertGreater(self.d.get_abs_resolution(a), 0)

class TestAbsoluteMultitouchDevice(TestAbsoluteDevice):
    def setUp(self):
        super(TestAbsoluteMultitouchDevice, self).setUp()

        required = ["ABS_MT_POSITION_X", "ABS_MT_POSITION_Y"]
        is_abs = False

        for r in required:
            if self.d.has_event("EV_ABS", r):
                is_abs = True
                break

        if not is_abs:
            raise unittest.SkipTest

    def test_has_both_abs_mt_x_and_y(self):
        if self.d.has_event("EV_ABS", "ABS_MT_POSITION_X") or \
           self.d.has_event("EV_ABS", "ABS_MT_POSITION_Y"):
           self.assertTrue(self.d.has_event("EV_ABS", "ABS_MT_POSITION_X"))
           self.assertTrue(self.d.has_event("EV_ABS", "ABS_MT_POSITION_Y"))
        else:
           self.skipTest("No multitouch axes")

    def test_mt_axis_ranges_equal_to_st(self):
        if not self.d.has_event("EV_ABS", "ABS_MT_POSITION_X") or \
           not self.d.has_event("EV_ABS", "ABS_MT_POSITION_Y"):
               self.skipTest("No multitouch axes")

        smin = self.d.get_abs_minimum("ABS_X")
        mtmin = self.d.get_abs_minimum("ABS_MT_POSITION_X")
        self.assertEqual(smin, mtmin);
        smax = self.d.get_abs_maximum("ABS_X")
        mtmax = self.d.get_abs_maximum("ABS_MT_POSITION_X")
        self.assertEqual(smax, mtmax);
        smin = self.d.get_abs_minimum("ABS_Y")
        mtmin = self.d.get_abs_minimum("ABS_MT_POSITION_Y")
        self.assertEqual(smin, mtmin);
        smax = self.d.get_abs_maximum("ABS_Y")
        mtmax = self.d.get_abs_maximum("ABS_MT_POSITION_Y")
        self.assertEqual(smax, mtmax);

    def test_is_not_fake_multitouch_device(self):
        self.assertFalse(self.d.has_event("EV_ABS", 0x2e))

    def test_has_equal_resolutions_for_mt(self):
        res = self.d.get_abs_resolution("ABS_X")
        res_mt = self.d.get_abs_resolution("ABS_MT_POSITION_X")
        self.assertEqual(res, res_mt)

        res = self.d.get_abs_resolution("ABS_Y")
        res_mt = self.d.get_abs_resolution("ABS_MT_POSITION_Y")
        self.assertEqual(res, res_mt)

    def test_has_min_max_slots(self):
        smin = self.d.get_abs_minimum("ABS_MT_SLOT")
        smax = self.d.get_abs_maximum("ABS_MT_SLOT")
        self.assertEqual(smin, 0)
        self.assertGreaterEqual(smax, 1)

    def test_has_btn_tool_footap_for_each_slot(self):
        slots = self.d.get_abs_maximum("ABS_MT_SLOT")
        if slots >= 5:
            self.assertTrue(self.d.has_event("EV_KEY", "BTN_TOOL_QUINTTAP"))
        if slots >= 4:
            self.assertTrue(self.d.has_event("EV_KEY", "BTN_TOOL_QUADTAP"))
        if slots >= 3:
            self.assertTrue(self.d.has_event("EV_KEY", "BTN_TOOL_TRIPLETAP"))
        if slots >= 2:
            self.assertTrue(self.d.has_event("EV_KEY", "BTN_TOOL_DOUBLETAP"))
        if slots >= 1:
            self.assertTrue(self.d.has_event("EV_KEY", "BTN_TOUCH"))

    def test_has_resolution(self):
        axes = ["ABS_X", "ABS_Y", "ABS_MT_POSITION_X", "ABS_MT_POSITION_Y"]
        for a in axes:
            if self.d.has_event("EV_ABS", a):
                self.assertGreater(self.d.get_abs_resolution(a), 0)

class TestTouchpad(TestAbsoluteDevice):
    def setUp(self):
        super(TestTouchpad, self).setUp()

        if not self.d.has_event("EV_KEY", "BTN_TOOL_FINGER") or \
                self.d.has_event("EV_KEY", "BTN_TOOL_PEN"):
            raise unittest.SkipTest

    def test_is_clickpad(self):
        if self.d.has_event("EV_KEY", "BTN_LEFT") and \
                not self.d.has_event("EV_KEY", "BTN_RIGHT"):
            self.assertTrue(self.d.has_prop("INPUT_PROP_BUTTONPAD"))
        if self.d.has_prop("INPUT_PROP_BUTTONPAD"):
            self.assertTrue(self.d.has_event("EV_KEY", "BTN_LEFT") and \
                            not self.d.has_event("EV_KEY", "BTN_MIDDLE") and
                            not self.d.has_event("EV_KEY", "BTN_RIGHT"))

    def test_no_input_prop_direct(self):
        self.assertFalse(self.d.has_prop("INPUT_PROP_DIRECT"))

    def test_device_has_no_rel_axes(self):
        for i in range(0, evemu.event_get_value("EV_REL", "REL_MAX")):
            self.assertFalse(self.d.has_event("EV_REL", i))

class TestTablet(TestAbsoluteDevice):
    def setUp(self):
        super(TestTablet, self).setUp()

        if not self.d.has_event("EV_KEY", "BTN_TOOL_PEN"):
            raise unittest.SkipTest

    def test_has_input_prop_direct(self):
        self.assertTrue(self.d.has_prop("INPUT_PROP_DIRECT"))

    def test_has_btn_touch(self):
        self.assertTrue(self.d.has_event("EV_KEY", "BTN_TOUCH"))

    def test_has_stylus_button(self):
        self.assertTrue(self.d.has_event("EV_KEY", "BTN_STYLUS"))

    def test_has_stylus_button2(self):
        self.assertTrue(self.d.has_event("EV_KEY", "BTN_STYLUS2"))

    def test_events_btn_touch(self):
        count_touch_down = 0
        count_touch_up = 0
        for e in self.d.events():
            if e.matches("EV_KEY", "BTN_TOUCH"):
                self.assertGreaterEqual(e.value, 0)
                self.assertLessEqual(e.value, 1)
                if e.value == 0:
                    count_touch_up += 1
                else:
                    count_touch_down += 1
        self.assertGreater(count_touch_down, 0)
        self.assertGreater(count_touch_up, 0)

    def test_events_btn_touch_balanced(self):
        count_touch_down = 0
        count_touch_up = 0
        for e in self.d.events():
            if e.matches("EV_KEY", "BTN_TOUCH"):
                self.assertGreaterEqual(e.value, 0)
                self.assertLessEqual(e.value, 1)
                if e.value == 0:
                    count_touch_up += 1
                else:
                    count_touch_down += 1
        self.assertEqual(count_touch_down, count_touch_down)

    def test_events_btn_tool_pen(self):
        count_pen_down = 0
        count_pen_up = 0
        for e in self.d.events():
            if e.matches("EV_KEY", "BTN_TOOL_PEN"):
                self.assertGreaterEqual(e.value, 0)
                self.assertLessEqual(e.value, 1)
                if e.value == 0:
                    count_pen_up += 1
                else:
                    count_pen_down += 1
        self.assertGreater(count_pen_down, 0)
        self.assertGreater(count_pen_up, 0)

    def test_events_btn_tool_pen_balanced(self):
        count_pen_down = 0
        count_pen_up = 0
        for e in self.d.events():
            if e.matches("EV_KEY", "BTN_TOOL_PEN"):
                self.assertGreaterEqual(e.value, 0)
                self.assertLessEqual(e.value, 1)
                if e.value == 0:
                    count_pen_up += 1
                else:
                    count_pen_down += 1
        self.assertGreater(count_pen_down, 0)
        self.assertGreater(count_pen_up, 0)
        self.assertEqual(count_pen_down, count_pen_down)

    def test_events_btn_tool_pen_before_btn_tool_touch(self):
        pen_state = 0
        touch_state = 0
        for e in self.d.events():
            if e.matches("EV_KEY", "BTN_TOOL_PEN"):
                pen_state = e.value
            elif e.matches("EV_KEY", "BTN_TOUCH"):
                touch_state = e.value
            elif e.matches("EV_SYN", "SYN_REPORT"):
                self.assertGreaterEqual(pen_state, touch_state)

    def test_events_btn_tool_pen_before_btn_stylus(self):
        have_btn_stylus = False
        pen_state = 0
        stylus_state = 0
        stylus2_state = 0
        for e in self.d.events():
            if e.matches("EV_KEY", "BTN_TOOL_PEN"):
                pen_state = e.value
            elif e.matches("EV_KEY", "BTN_STYLUS"):
                stylus_state = e.value
                have_btn_stylus = True
            elif e.matches("EV_KEY", "BTN_STYLUS2"):
                stylus2_state = e.value
                have_btn_stylus = True
            elif e.matches("EV_SYN", "SYN_REPORT"):
                self.assertGreaterEqual(pen_state, stylus_state)
                self.assertGreaterEqual(pen_state, stylus2_state)
        if not have_btn_stylus:
            self.SkipTest("No BTN_STYLUS/BTN_STYLUS2 event found")

class TestRelativeDevice(TestEvdevDevice):
    def setUp(self):
        super(TestRelativeDevice, self).setUp()

        required = ["REL_X", "REL_Y"]
        is_rel = False

        for r in required:
            if self.d.has_event("EV_REL", r):
                is_rel = True
                break

        if not is_rel:
            raise unittest.SkipTest

    def test_no_touchpad_in_name(self):
        name = self.d.name
        self.assertEqual(name.lower().find("touchpad"), -1)

class TestMouse(TestRelativeDevice):
    def test_lmr_buttons(self):
        self.assertTrue(self.d.has_event("EV_KEY", "BTN_LEFT"))
        self.assertTrue(self.d.has_event("EV_KEY", "BTN_RIGHT"))
        self.assertTrue(self.d.has_event("EV_KEY", "BTN_MIDDLE"))

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("Usage: %s events.evemu" % os.path.basename(sys.argv[0]))
        sys.exit(1)

    evemu_path = sys.argv[1]
    del sys.argv[1]
    unittest.main()
