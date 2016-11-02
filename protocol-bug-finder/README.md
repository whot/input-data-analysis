Checks a protocol stream for a couple of general possible bugs

Input data is an evemu recording:

        $ sudo evemu-record > touchpad.evemu
        # select your device in the list

This tool is based on python's unittest framework and takes all the
arguments that package takes. The first argument must be the evemu recording
name, the rest is passed straight through.

        $ ./protocol-bug-finger.py touchpad.evemu --verbose
        test_abs_does_not_exceed_axis_ranges (__main__.TestAbsoluteDevice) ... ok
        test_abs_has_both_abs_x_and_y (__main__.TestAbsoluteDevice) ... ok
        test_abs_has_resolution (__main__.TestAbsoluteDevice) ... ok
        test_abs_has_single_emulation (__main__.TestAbsoluteDevice) ... ok
        test_evdev_no_SYN_DROPPED (__main__.TestAbsoluteDevice) ... ok
        test_abs_does_not_exceed_axis_ranges (__main__.TestAbsoluteMultitouchDevice) ... ok
        test_abs_has_both_abs_x_and_y (__main__.TestAbsoluteMultitouchDevice) ... ok
        test_abs_has_resolution (__main__.TestAbsoluteMultitouchDevice) ... ok
        ....

All tests matching the given device will run, there will always be a set of
tests skipped. For example, if the recording is from a touchpad, all tests
analyzing mice and relative-devices will be skipped.

If a test fails, it's not always an immediate signal that the device is
buggy, it just warrants closer inspection. For example, a test to check for
the PROP_INPUT_DIRECT property will always fail on an external tablet.
