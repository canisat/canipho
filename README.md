# CaniPho

**GPS Overlay Photo Inspector**

Utility for inspecting and decoding overlay photos (`.pho` container format) used by GPS devices from Bushnell Outdoor Products.

## About

Bushnell's ONIX devices uses a custom JPEG container (`CPSS_IMAGE`) which encodes geolocation data alongside the photo to be overlayed.

A 512-byte header lists the name of the overlay, N/E/S tile edges encoded as georeference information for display on the device (signed 32-bit interger, roughly 1e-7 degrees), and a 4-byte check key (at `0x90`) to decode the first 160 bytes of the photo information.

As the ONIX 400 model specifically is capable of utilizing SiriusXM's satellite services in addition to standard handheld navigator functions, and support for this image format, it is included in the scope of the CaniSat project.

## Usage

`pho2jpg.py` can dump and inspect the overlay photos.

```
python pho2jpg.py file.pho            # -> file.jpg
python pho2jpg.py --info file.pho     # header + geo + JPEG marker dump
python pho2jpg.py --kml file.pho      # -> file.jpg + file.kml (Google Earth)
python pho2jpg.py --jgw file.pho      # -> file.jpg + file.jgw/.prj (ESRI)
```

## Header structure

This information is based off two surviving examples as the service which encodes overlay photos for the navigation devices no longer exists.

| Offset | Size | Field | Notes |
|--------|------|-------|-------|
| `0x000` | 10 | Kind | ASCII `"CPSS_IMAGE"` |
| `0x00A` | 6 | Padding | Zero |
| `0x010` | 128 | Overlay name | Null-padded ASCII |
| `0x090` | 4 | **XOR key** | Repeating 4-byte mask applied to the first 160 bytes of the JPEG |
| `0x094` | 4 | **North edge latitude** | signed 32-bit int, degrees x 1e-7 |
| `0x098` | 4 | **East edge longitude** | signed 32-bit int, degrees x 1e-7 |
| `0x09C` | 4 | **South edge latitude** | signed 32-bit int, degrees x 1e-7 |
| `0x0A0` | 4 | `200` (`0xC8`) | Offset pointing at `0xC8` (enc-length field)? |
| `0x0A4` | 4 | `0` | |
| `0x0A8` | 4 | `0` | |
| `0x0AC`–`0x0C7` | 28 | Padding | Zero |
| `0x0C8` | 4 | `160` (`0xA0`) | **Length of encoded JPEG prefix?** |
| `0x0CC`–`0x0FF` | 52 | Padding | Zero |
| `0x100` | 4 | `1` | Format version? |
| `0x104` | 2 | `600` | Photo height (unsigned 16-bit EL) |
| `0x106` | 2 | `600` | Photo width (unsigned 16-bit EL) |
| `0x108` | 4 | `0` | Unknown |
| `0x10C` | 4 | JPEG size | Photo file size (Minus the 512-byte header) |
| `0x110`–`0x1FF` | 240 | Padding | Zero |
| `0x200` | … | JPEG | Photo contents (First bytes XOR'd') |

## XOR Check Key

```python
key = pho[0x90:0x94] # 4 bytes, different per file
enc_len = int.from_bytes(pho[0xC8:0xCC], "little") # 160 in both samples
plain = bytes(b ^ key[i % 4] for i, b in enumerate(pho[0x200:0x200 + enc_len]))
jpeg = plain + pho[0x200 + enc_len:]
```

Overlay photos are ciphered to make them function only in the navigator software. The 4-byte key, however, can be trivially recovered anyway regardless of the proprietary header, as every JPEG begins with the known `FF D8 FF E0 00 10 "JFIF"` plaintext.

In the two samples that were analyzed, the chroma quantization table is set to all `0x32` (50), resulting in a repeating 4-byte pattern (`97 9D 60 FE` = `"22 22 22 22"` XOR'd).

The ciphered region covers the JPEG's leading structure:

`FF D8` (SOI) → APP0/JFIF → DQT x2 → `FF C0` (SOF0)

Everything from the SOF0 *length field* onward - SOF0 payload, 4x DHT, SOS, entropy-coded scan, `FF D9` (EOI) - is stored in the clear.

## Georeferencing

`0x94`, `0x98` and `0x9C` are signed 32-bit integers storing tile edges in degrees x 1e-7 ("micro-degrees", GPS integer encoding).

The west edge is not stored, instead implied by the tile being roughly square in degrees (lon span = lat span ≈ 0.0106–0.0108°, i.e. ~1.2 km, which at 600 px gives ~2 m/pixel - standard aerial-photo resolution).

## Unknowns

* **Image type flag (Aerial photo or topo/elevation map)**: The software also has topographic overlay images, to which no surviving samples exist. Candidates for the type discriminator are identical in both aerial samples: `0x100` = 1, `0xA4` = 0, `0xA8` = 0, `0x108` = 0. This might require examining the software.
* **Exact coordinate anchor semantics**: The evidence supports N/E/S edges respectively, with a square-in-degrees tile, but with only two samples, alternatives like a NE-corner anchor with a different rule for the implied west edge cannot be fully excluded. Info printouts list the derived boundary box under the square-degree assumption.
* **Key derivation**: How the per-file XOR key at `0x90` is generated is not known. It is not some CRC checksum of the image or a XOR of header words. In both samples, `key[3]` coincides with the top byte of the east longitude. Maybe metadata??
* **Meaning of `0xA0` (= 0xC8) and `0xC8` (= 0xA0)**: These two point at each other's offsets. These have been noted as "pointer to encoded length" and "encoded length", but could be struct coincidence.
* **Width x Height, or Height x Width**: Whether `0x104` is height and `0x106` width, or vice versa. Both are 600 in the samples so the order cannot be distinguished.
* **Are all photos encoded at the first 160 bytes?**: Whether it's always the first 160 bytes ciphered. May require checking the software. Attempts to read from `0xC8` and falls back to 160 if the value seems corrupt, then validates that the decrypted prefix starts with `FF D8`.

## AI Disclosure

Please see [AI_DISCLOSURE.md](AI_DISCLOSURE.md).

## Notice

This utility is not affiliated with either Revelyst, Inc. (formerly Vista Outdoor Inc.), Bushnell, LLC or Bushnell Holdings, Inc. Bushnell is the trademark or registered trademark of Bushnell, LLC.

CaniSat, a non-profit initiative, is not affiliated with either Sirius XM Holdings Inc, Sirius XM Radio LLC, Sirius XM Canada Inc, or any of their products, partners, or subsidiaries. Sirius, XM, SiriusXM, XMWX, and all related indicia are registered trademarks of Sirius XM Radio LLC.

The data products distributed in the service(s) are intended to be supplemental and advisory per the provider. It is not recommended for use in circumstances that require immediate urgency to fulfill safety-critical work. Both CaniSat and the service provider are not responsible for errors and inaccuracies encountered when utilizing the service data products.

CaniSat does not condone or encourage the use of its affiliated projects for unauthorized copying, duplication, or distribution of copyrighted materials received through the supported services. The end user is solely responsible for ensuring their activities comply with applicable copyright laws and service terms. Don't steal music.
