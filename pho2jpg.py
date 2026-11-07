#!/usr/bin/env python3

import argparse
import os
import sys

import phoparse
import phonfo
import phoconv

def main(argv=None):
    # argparse
    ap = argparse.ArgumentParser(
        description="Convert PHO overlays into JPEG.")
    ap.add_argument("files", nargs="+", metavar="file.pho",
                    help=".pho file(s) to process")
    ap.add_argument("-i", "--info", action="store_true",
                    help="print a detailed file inspection instead of converting")
    ap.add_argument("-o", "--output", metavar="PATH",
                    help="output .jpg path (single input only; default: input + .jpg)")
    ap.add_argument("--jgw", action="store_true",
                    help="write an ESRI world file (.jgw + .prj) beside the .jpg")
    ap.add_argument("--kml", action="store_true",
                    help="write a Google Earth GroundOverlay KML beside the .jpg")
    args = ap.parse_args(argv)

    # handling
    if args.output and (len(args.files) > 1 or args.info):
        ap.error("--output works with a single input and no --info")

    for path in args.files:
        try:
            # open PHO
            with open(path, "rb") as f:
                data = f.read()

            info = phoparse.parse_pho(data, path)

            if args.info:
                phonfo.dump_info(info)
            else:
                # out filename
                out = args.output or (os.path.splitext(info["filename"])[0] + ".jpg")
                # save jpg
                with open(out, "wb") as jpgout:
                    jpgout.write(info["jpeg"])
                print("%s -> %s  (%d x %d, %d bytes)"
                      % (path, out, info["width"], info["height"],
                         len(info["jpeg"])))
                
                # conversions
                if args.jgw:
                    jgw, prj = phoconv.write_jgw(info, out)
                    print("  georef    -> %s, %s" % (jgw, prj))
                if args.kml:
                    print("  overlay   -> %s" % phoconv.write_kml(info, out))

                # warning
                for x in info["warnings"]:
                    print("  WARNING: %s" % x)
        except (OSError) as e:
            print("ERROR: %s: %s" % (path, e), file=sys.stderr)

if __name__ == "__main__":
    main()
