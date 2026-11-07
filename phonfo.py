import math
import struct

DATA_OFFSET = 0x200 # JPEG data starts here (512-byte header)

# JPEG marker name lookup
MARKER_NAMES = {
    0xC0: "SOF0 (baseline DCT)",
    0xC1: "SOF1 (extended DCT)",
    0xC2: "SOF2 (progressive DCT)",
    0xC4: "DHT (Huffman table)",
    0xD8: "SOI (start of image)",
    0xD9: "EOI (end of image)",
    0xDA: "SOS (start of scan)",
    0xDB: "DQT (quantization table)",
    0xDD: "DRI (restart interval)",
    0xE0: "APP0 (JFIF)",
    0xE1: "APP1 (EXIF/XMP)",
    0xEE: "APP14 (Adobe)",
    0xFE: "COM (comment)",
}

def dump_info(info):
    print("=" * 72)
    print("File         : %s  (%d bytes)" % (info["filename"], info["file_size"]))
    print("Name         : %r" % info["name"])
    print("XOR key      : %s" % info["key"].hex(" "))
    n, s, e = info["lat_n"], info["lat_s"], info["lon_e"]
    w = e - (n - s)   # implied west edge, square in degrees
    print("Coordinates  : N %.7f  S %.7f  E %.7f   (int32 x 1e-7 @ 0x94/0x98/0x9C)"
          % (n, s, e))
    print("Derived bbox : W %.7f .. E %.7f,  N %.7f .. S %.7f   (W assumed)"
          % (w, e, n, s))
    if info["height"] and n != s:
        span_m = (n - s) * 111320.0
        print("             : ~%.0f m x %.0f m  ->  ~%.2f m/pixel"
              % (span_m, span_m * math.cos(math.radians((n + s) / 2.0)),
                 span_m / info["height"]))
    print("Field A0     : %d (0x%X)" % (info["field_0xA0"], info["field_0xA0"]))
    print("Field A4     : %d" % info["field_0xA4"])
    print("Field A8     : %d" % info["field_0xA8"])
    print("Cipher len   : %d bytes of JPEG prefix"
          % info["enc_len"])
    print("Version?     : %d" % info["version"])
    print("Type-flag?   : 0x100=%d, 0xA4=%d, 0xA8=%d, 0x108=%d "
          "(aerial photos are 1,0,0,0)"
          % (info["version"], info["field_0xA4"], info["field_0xA8"],
             info["field_0x108"]))
    print("Dimensions   : %d x %d" % (info["width"], info["height"]))
    print("Field 108    : %d" % info["field_0x108"])
    print("JPEG size    : %d (actual %d)" % (info["jpeg_size"],
                                             info["file_size"] - DATA_OFFSET))
    print("JPEG stream  : starts at %X; first %d bytes ciphered"
          % (DATA_OFFSET, info["enc_len_used"]))
    for x in info["warnings"]:
        print("WARNING      : %s" % x)

    # jpg debugs
    jpeg = info["jpeg"]
    print("-" * 72)
    print("JPEG marker structure:")
    i = 0
    while i < len(jpeg) - 1:
        if jpeg[i] != 0xFF:
            i += 1
            continue
        m = jpeg[i + 1]
        if m in (0x00, 0xFF) or 0xD0 <= m <= 0xD7:   # stuffing / RST markers
            i += 1
            continue
        if m == 0xD8:
            print("  %08X  FF D8  SOI (start of image)" % i)
            i += 2
        elif m == 0xD9:
            print("  %08X  FF D9  EOI (end of image)" % i)
            i += 2
        else:
            seglen = struct.unpack_from(">H", jpeg, i + 2)[0]
            print("  %08X  FF %02X  %-24s len=%d"
                  % (i, m, MARKER_NAMES.get(m, "?"), seglen))
            if m == 0xDA:
                eoi = jpeg.find(b"\xff\xd9", i)
                print("             ... entropy-coded scan: %d bytes ..."
                      % ((eoi if eoi != -1 else len(jpeg)) - (i + 2 + seglen)))
                i = (eoi if eoi != -1 else len(jpeg))
            else:
                i += 2 + seglen
    print("=" * 72)
