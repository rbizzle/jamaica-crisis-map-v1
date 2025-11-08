"""
Extract NOAA Tile URLs for Hurricane Melissa

MANUAL STEPS (Most Reliable):
==============================

1. Open this URL in your browser:
   https://storms.ngs.noaa.gov/storms/melissa/index.html#9/18.18/-77.39

2. Open Developer Tools (F12)

3. Go to Network tab

4. Filter by "Img" or type "png" in the filter box

5. Clear the network log

6. Navigate/zoom the map over Jamaica

7. You'll see tile requests like:
   https://storms.ngs.noaa.gov/storms/melissa/YYYYMMDD_oblique/tiles/ZZ/XXXXX/YYYYY.png

8. Right-click on a tile request → Copy → Copy URL

9. Use those URLs below


COMMON MELISSA TILE URL PATTERNS:
==================================
"""

import math

def get_tile_coords_for_jamaica():
    """
    Generate tile coordinates for Jamaica area.
    Jamaica center: approximately 18.18° N, -77.39° W
    """
    
    def latlon_to_tile(lat, lon, zoom):
        """Convert lat/lon to tile coordinates."""
        lat_rad = math.radians(lat)
        n = 2.0 ** zoom
        x = int((lon + 180.0) / 360.0 * n)
        y = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
        return x, y
    
    def tile_to_bounds(x, y, zoom):
        """Convert tile coordinates back to lat/lon bounds."""
        n = 2.0 ** zoom
        west = x / n * 360.0 - 180.0
        east = (x + 1) / n * 360.0 - 180.0
        
        lat_rad_north = math.atan(math.sinh(math.pi * (1 - 2 * y / n)))
        north = math.degrees(lat_rad_north)
        
        lat_rad_south = math.atan(math.sinh(math.pi * (1 - 2 * (y + 1) / n)))
        south = math.degrees(lat_rad_south)
        
        return {"west": west, "south": south, "east": east, "north": north}
    
    # Jamaica coordinates
    jamaica_center = (18.18, -77.39)
    
    # Typical zoom levels for NOAA imagery
    zoom_levels = [18, 19, 20]
    
    print("Potential tile coordinates for Jamaica:")
    print("="*60)
    
    for zoom in zoom_levels:
        x, y = latlon_to_tile(jamaica_center[0], jamaica_center[1], zoom)
        bounds = tile_to_bounds(x, y, zoom)
        
        print(f"\nZoom {zoom}:")
        print(f"  Center tile: {x}/{y}")
        print(f"  Bounds: {bounds}")
        print(f"  URL pattern: https://storms.ngs.noaa.gov/storms/melissa/YYYYMMDD_oblique/tiles/{zoom}/{x}/{y}.png")
        
        # Generate URLs for surrounding tiles
        print(f"\n  Surrounding tiles:")
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                tile_x = x + dx
                tile_y = y + dy
                b = tile_to_bounds(tile_x, tile_y, zoom)
                print(f"    tiles/{zoom}/{tile_x}/{tile_y}.png")
                print(f"      Bounds: W:{b['west']:.4f}, S:{b['south']:.4f}, E:{b['east']:.4f}, N:{b['north']:.4f}")

if __name__ == "__main__":
    get_tile_coords_for_jamaica()
    
    print("\n" + "="*60)
    print("NEXT STEPS:")
    print("="*60)
    print("1. Visit: https://storms.ngs.noaa.gov/storms/melissa/")
    print("2. Use F12 → Network → look for date folders like '20241102_oblique'")
    print("3. Replace YYYYMMDD in the URLs above with the actual date")
    print("4. Test URLs with: python test_melissa_tiles.py")
