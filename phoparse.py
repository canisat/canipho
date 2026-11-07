import struct

# consts
MAGIC = b"CPSS_IMAGE"
KEY_OFFSET = 0x90 # 4-byte XOR key
DATA_OFFSET = 0x200 # JPEG data starts here (512-byte header)
ENC_LEN_OFFSET = 0xC8 # length of ciphered prefix
SIZE_OFFSET = 0x10C # declared JPEG size
DEFAULT_ENC_LEN = 160 # observed value in known samples

def parse_pho(data, filename):
    if len(data) < DATA_OFFSET:
        print("file too small (%d bytes) to be an overlay photo" % len(data))
        return
    if data[:10] != MAGIC:
        print("bad magic %r (expected %r)" % (data[:10], MAGIC))
        return

    # jpg size
    actual_size = len(data) - DATA_OFFSET

    # photo data
    info = {
        "filename": filename,
        "file_size": len(data),
        "name": data[0x10:0x90].split(b"\x00")[0].decode("ascii", "replace"),
        "key": data[KEY_OFFSET:KEY_OFFSET + 4],
        # signed 32-bit int, degrees x 1e-7 ("micro-degrees")
        "lat_n": struct.unpack_from("<i", data, 0x94)[0] / 1e7,
        "lon_e": struct.unpack_from("<i", data, 0x98)[0] / 1e7,
        "lat_s": struct.unpack_from("<i", data, 0x9C)[0] / 1e7,
        "field_0xA0": struct.unpack_from("<I", data, 0xA0)[0],
        "field_0xA4": struct.unpack_from("<I", data, 0xA4)[0],
        "field_0xA8": struct.unpack_from("<I", data, 0xA8)[0],
        "enc_len": struct.unpack_from("<I", data, ENC_LEN_OFFSET)[0],
        "version": struct.unpack_from("<I", data, 0x100)[0],
        "height": struct.unpack_from("<H", data, 0x104)[0],
        "width": struct.unpack_from("<H", data, 0x106)[0],
        "field_0x108": struct.unpack_from("<I", data, 0x108)[0],
        "jpeg_size": struct.unpack_from("<I", data, SIZE_OFFSET)[0],
    }

    # sanity checks
    warnings = []
    if info["jpeg_size"] != actual_size:
        warnings.append("declared JPEG size %d != actual %d"
                        % (info["jpeg_size"], actual_size))
    if info["lat_n"] == 0 and info["lat_s"] == 0 and info["lon_e"] == 0:
        warnings.append("no georeferencing coordinates stored (all zero)")
    elif not (info["lat_s"] < info["lat_n"]):
        warnings.append("latitude pair looks inverted (N=%.7f S=%.7f)"
                        % (info["lat_n"], info["lat_s"]))

    # unscamble JPEG prefix
    # use the value observed in known samples if enc_len missing/corrupt
    # 160 = SOI + APP0 + DQT*2 + FF C0
    enc_len = info["enc_len"]
    if not (0 < enc_len < actual_size):
        warnings.append("bogus enc_len %d, using default %d"
                        % (enc_len, DEFAULT_ENC_LEN))
        enc_len = DEFAULT_ENC_LEN
    info["enc_len_used"] = enc_len

    key = info["key"]
    prefix = bytes(b ^ key[i % 4]
                   for i, b in enumerate(data[DATA_OFFSET:DATA_OFFSET + enc_len]))
    if prefix[:2] != b"\xff\xd8":
        print("decrypted JPEG prefix does not start with SOI (FF D8); "
                       "key or length is wrong (key=%s)" % key.hex())
        return

    jpeg = prefix + data[DATA_OFFSET + enc_len:]
    if jpeg[-2:] != b"\xff\xd9":
        warnings.append("JPEG does not end with EOI (FF D9)")

    # Cross-check dimensions in SOF vs header fields
    sof = jpeg.find(b"\xff\xc0")
    if sof != -1:
        jh, jw = struct.unpack_from(">HH", jpeg, sof + 5)
        if (jh, jw) != (info["height"], info["width"]):
            warnings.append("header dims %dx%d != JPEG dims %dx%d"
                            % (info["width"], info["height"], jw, jh))

    info["jpeg"] = jpeg
    info["warnings"] = warnings
    return info
