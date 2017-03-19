#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys, os
import argparse
from PIL import Image, ImageEnhance
import numpy as np
import numba
from numba import cuda

@numba.jit
def dither(num, thresh = 127):
    derr = np.zeros(num.shape, dtype=int)

    div = 8
    for y in xrange(num.shape[0]):
        for x in xrange(num.shape[1]):
            newval = derr[y,x] + num[y,x]
            if newval >= thresh:
                errval = newval - 255
                num[y,x] = 1.
            else:
                errval = newval
                num[y,x] = 0.
            if x + 1 < num.shape[1]:
                derr[y, x + 1] += errval / div
                if x + 2 < num.shape[1]:
                    derr[y, x + 2] += errval / div
            if y + 1 < num.shape[0]:
                derr[y + 1, x - 1] += errval / div
                derr[y + 1, x] += errval / div
                if y + 2< num.shape[0]:
                    derr[y + 2, x] += errval / div
                if x + 1 < num.shape[1]:
                    derr[y + 1, x + 1] += errval / div
    return num[::-1,:] * 255

def main(argv = None):
    if argv is None:
        argv = sys.argv
    programName = os.path.basename(argv[0])

    parser = argparse.ArgumentParser(
        description="Dither image an image using Atkinson 'hyperdither'.")
    parser.add_argument('filename')
    parser.add_argument('-1', '--mono', dest = 'mono', action='store_true',
        default = False, help = '1-bit black and white file')
    parser.add_argument('-t', '--threshold', dest = 'threshold', type = int,
        action='store', default = 127, help = 'black/white threshold')
    parser.add_argument('-d', '--dpi', dest = 'dpi', type = int,
        action='store', default = 72, help = 'dpi out output file')
    parser.add_argument('-e', '--ext', dest = 'ext', action='store',
        default = 'png', help = 'output filetype')
    parser.add_argument('-b', '--bottom', dest = 'bottom',
        action='store_true', default = False, 
        help = "start at bottom left instead of top left")
    parser.add_argument('-c', '--contrast', dest = 'contrast',
        action='store', default = 0, type = float,
        help = "boost contrast by specified factor (default 1)")
    parser.add_argument('-s', '--sharpness', dest = 'sharpness',
        action='store', default = 0, type = float,
        help = "boost sharpness by specified factor (default 1)")
    parser.add_argument('-r', '--resize', dest = 'resize', action='store',
        default = None, type = int,
        help = """resize pre-dither image on longest dimension""")
    parser.add_argument('-2', '--double', dest = 'double',
        action='store_true', default = False,
        help = "double post-dither image using nearest neighbors")

    args = parser.parse_args()

    if not os.path.isfile(args.filename):
        print("Must supply a valid file.")
        sys.exit(1)
    img = Image.open(os.path.expanduser(args.filename)).convert('L')
    if args.contrast:
        # img = ImageEnhance.Contrast(img).enhance(1 + args.contrast/100)
        img = ImageEnhance.Contrast(img).enhance(args.contrast)
    if args.resize:
        img.thumbnail((args.resize,) * 2, 3)
    if args.sharpness:
        # img = ImageEnhance.Sharpness(img).enhance(1 + args.sharpness/100)
        img = ImageEnhance.Sharpness(img).enhance(args.sharpness)

    if args.bottom:
        m = np.array(img)[::-1,:]
        m2 = dither(m, thresh = args.threshold)
        out = Image.fromarray(m2[:,:])
    else:
        m = np.array(img)[:,:]
        m2 = dither(m, thresh = args.threshold)
        out = Image.fromarray(m2[::-1,:])
    basename, ext = os.path.splitext(args.filename)
    outfn = basename + '_out.' + args.ext

    if args.double:
        out = out.resize((out.width *2, out.height*2))
    if args.mono:
        out.convert('1').save(outfn, dpi=(args.dpi,)*2)
    else:
        out.save(outfn, dpi=(args.dpi,)*2)

if __name__ == "__main__":
    sys.exit(main())
