import os
from xml.sax.saxutils import escape

def geo_bbox(info):
    # Fetch coords
    n, s, e = info["lat_n"], info["lat_s"], info["lon_e"]
    # Return implied boundbox (W is E-(N-S))
    return n, s, e, e - (n - s)

def write_jgw(info, jpg_path):
    # Get bounds
    n, s, e, w = geo_bbox(info)

    base = os.path.splitext(jpg_path)[0]

    dx = (e - w) / info["width"]
    dy = (n - s) / info["height"]

    # ESRI
    with open(base + ".jgw", "w") as f:
        # pixel size, rotations, center of top-left
        f.write("%.10f\n0\n0\n%.10f\n%.10f\n%.10f\n"
                % (dx, -dy, w + dx / 2.0, n - dy / 2.0))

    # WGS84
    with open(base + ".prj", "w") as f:
        f.write('GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",'
                'SPHEROID["WGS_1984",6378137.0,298.257223563]],'
                'PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]]')

    # write
    return base + ".jgw", base + ".prj"

def write_kml(info, jpg_path):
    # Get bounds
    n, s, e, w = geo_bbox(info)

    kml_path = os.path.splitext(jpg_path)[0] + ".kml"
    with open(kml_path, "w", encoding="utf-8") as f:
        # format coords for keyhole
        f.write(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<kml xmlns="http://www.opengis.net/kml/2.2">\n'
            '<Document>\n'
            '  <name>%s</name>\n'
            '  <GroundOverlay>\n'
            '    <name>%s</name>\n'
            '    <Icon><href>%s</href></Icon>\n'
            '    <LatLonBox>\n'
            '      <north>%.7f</north>\n'
            '      <south>%.7f</south>\n'
            '      <east>%.7f</east>\n'
            '      <west>%.7f</west>\n'
            '      <rotation>0</rotation>\n'
            '    </LatLonBox>\n'
            '  </GroundOverlay>\n'
            '</Document>\n</kml>\n'
            % (escape(info["name"]), escape(info["name"]),
               escape(os.path.basename(jpg_path)), n, s, e, w))
    return kml_path
