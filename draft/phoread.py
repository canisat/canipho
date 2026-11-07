import sys
import struct

FILEKIND = b"CPSS_IMAGE"

# Point where the JPEG info starts
JPEG_OFFSET = 0x200

def readpho(data):
    # File magic check
    if data[:10] != FILEKIND:
        print('File is not a Bushnell overlay photo')
        return
    print("Bushnell Photo Info")
    print(f"Name: {data[0x10:0x90].split(b"\x00")[0].decode("ascii", "replace")}")
    # Not sure if height x width, or width x height
    print(
        f"Photo resolution: "
        f"{struct.unpack_from("<H", data, 0x106)[0]}px"
        f" x "
        f"{struct.unpack_from("<H", data, 0x104)[0]}px"
    )
    print(f"Photo filesize: {struct.unpack_from("<I", data, 0x10c)[0]/1024:.2f}KB")
    
    # print(f"Header cipher: {data[0x90:0x94].hex(" ")}") # XOR key
    print(
        f"Coordinates: "
        f"N {struct.unpack_from("<i", data, 0x94)[0] / 1e7} "
        f"E {struct.unpack_from("<i", data, 0x98)[0] / 1e7} "
        f"S {struct.unpack_from("<i", data, 0x9c)[0] / 1e7}"
    )

def main():
    if len(sys.argv) == 2:
        # Open file
        with open(sys.argv[1], "rb") as file:
            data = file.read()
        readpho(data)
    else:
        print("usage: phoread.py file.pho")

if __name__ == "__main__":
    main()
