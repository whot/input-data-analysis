#!/usr/bin/python

from __future__ import print_function

import evemu
import os
import sys

UP = 0
DOWN = 1
IS_DOWN = 2
NONE = 3

def main(argv):
    d = evemu.Device(argv[1], create=False)
    offsets = {}
    offset = 2

    #     timestamp  count  star   separator
    print('Legend:')
    print('  time, count of keys down, * to mark <3ms timestamp')
    print('  + .... key down, | .... key is down, ^ .... key up')
    print(' ' * 12 + '   ' + ' ' +  ' |', end='')
    for c in range(ord('a'), ord('z') + 1):
        print('{}'.format(chr(c)), end='')
        offsets[offset] = chr(c)
        offset += 1

    for c in range(ord('0'), ord('9') + 1):
        print('{}'.format(chr(c)), end='')
        offsets[offset] = chr(c)
        offset += 1

    offset += 1
    print(' Spc Bksp Del Ret LShf RShf', end='')
    offsets[offset + 2] = 'space'
    offset += 4
    offsets[offset + 2] = 'backspace'
    offset += 5
    offsets[offset + 1] = 'delete'
    offset += 4
    offsets[offset + 1] = 'enter'
    offset += 4
    offsets[offset + 2] = 'leftshift'
    offset += 5
    offsets[offset + 2] = 'rightshift'
    offset += 5
    print('')

    max_offset = offset

    char = ['^', '+', '|', ' ']

    down = {}
    last_down = {}
    bounce = False
    for e in d.events():
        if e.matches('EV_SYN', 'SYN_REPORT'):
            line = []
            line.append('{:06d}.{:06d}'.format(e.sec, e.usec))
            line.append(' {} '.format(len(down)))

            time = e.sec * 1000000 + e.usec
            if bounce:
                line.append('*')
                bounce = False
            else:
                line.append(' ')

            line.append('|')
            for i in range(2, max_offset):
                try:
                    line.append(char[down[offsets[i]]])
                except KeyError:
                    line.append(' ')
            print(''.join(line))

            for key in down:
                if down[key] == DOWN:
                    down[key] = IS_DOWN
                elif down[key] == UP:
                    down[key] = NONE

            d2 = {}
            for key in down.keys():
                value = down[key]
                if value != NONE:
                    d2[key] = value
            down = d2

        if not e.matches('EV_KEY'):
            continue

        key = evemu.event_get_name(e.type, e.code)
        key = key[4:].lower()  # remove KEY_ prefix
        down[key] = e.value
        
        if e.value:
            time = e.sec * 1000000 + e.usec
            if (key in last_down) and (time - last_down[key] < 70000):  # 70 ms
                bounce = True
            else:
                last_down[key] = time


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("Usage: %s events.evemu" % os.path.basename(sys.argv[0]))
        sys.exit(1)
    main(sys.argv)
