"""
Guide: How to Extract Real NOAA Tile URLs
==========================================

Since Hurricane Melissa may not exist yet (as of Nov 2025), you'll need to use
an actual NOAA emergency response imagery dataset. Here's how:

METHOD 1: Use Browser Developer Tools (Recommended)
----------------------------------------------------

1. Visit NOAA Emergency Response Imagery:
   https://storms.ngs.noaa.gov/storms/

2. Select a real storm (e.g., Hurricane Ian, Hurricane Fiona, etc.)

3. Open the interactive map viewer

4. Open Browser Developer Tools:
   - Press F12
   - Click on "Network" tab
   - Filter by "Img" or "PNG"

5. Navigate around the map - you'll see tile requests like:
   https://storms.ngs.noaa.gov/storms/STORMNAME/YYYYMMDD_oblique/tiles/19/123456/789012.png

6. Copy several of these URLs


METHOD 2: Use Known NOAA Tile URL Pattern
------------------------------------------

NOAA uses standard Slippy Map tile format:
https://storms.ngs.noaa.gov/storms/{storm_name}/{date}_oblique/tiles/{z}/{x}/{y}.png

Where:
- storm_name: e.g., "ian", "fiona", "idalia"
- date: YYYYMMDD format
- z: zoom level (typically 18-20 for high resolution)
- x, y: tile coordinates

Example real URLs from Hurricane Ian (2022):
https://storms.ngs.noaa.gov/storms/ian/20220929_oblique/tiles/19/165234/234567.png


METHOD 3: Use NOAA's Public Dataset
------------------------------------

1. Visit: https://www.ngs.noaa.gov/storms_aerialimagery/

2. Look for recent disasters with published imagery

3. Common recent events:
   - Hurricane Ian (2022)
   - Hurricane Fiona (2022)
   - Hurricane Idalia (2023)
   - California Fires
   - Flooding events


EXAMPLE CODE: Once You Have Real URLs
--------------------------------------
"""

# Example with Hurricane Ian imagery
REAL_NOAA_TILES = [
    {
        "image_id": "ian_florida_001",
        "tile_url": "https://storms.ngs.noaa.gov/storms/ian/20220929_oblique/tiles/19/165234/234567.png",
        "bounds": {
            "west": -82.5,
            "south": 26.5,
            "east": -82.4,
            "north": 26.6
        },
        "timestamp": "2022-09-29T14:30:00Z",
        "metadata": {
            "mission": "ian",
            "disaster_type": "hurricane",
            "location": "Florida"
        }
    },
    {
        "image_id": "ian_florida_002",
        "tile_url": "https://storms.ngs.noaa.gov/storms/ian/20220929_oblique/tiles/19/165235/234568.png",
        "bounds": {
            "west": -82.4,
            "south": 26.6,
            "east": -82.3,
            "north": 26.7
        },
        "timestamp": "2022-09-29T14:35:00Z",
        "metadata": {
            "mission": "ian",
            "disaster_type": "hurricane",
            "location": "Florida"
        }
    }
]

"""
CALCULATING BOUNDS FROM TILE COORDINATES
-----------------------------------------

If you have tile coordinates (z, x, y), you can calculate bounds:
"""

import math

def tile_to_bounds(z, x, y):
    """Convert tile coordinates to lat/lon bounds."""
    def tile_to_lon(x, z):
        return x / (2 ** z) * 360 - 180
    
    def tile_to_lat(y, z):
        n = math.pi - 2 * math.pi * y / (2 ** z)
        return math.degrees(math.atan(math.sinh(n)))
    
    west = tile_to_lon(x, z)
    east = tile_to_lon(x + 1, z)
    north = tile_to_lat(y, z)
    south = tile_to_lat(y + 1, z)
    
    return {
        "west": west,
        "south": south,
        "east": east,
        "north": north
    }

# Example usage:
# bounds = tile_to_bounds(z=19, x=165234, y=234567)
# print(bounds)


"""
QUICK START FOR JAMAICA CRISIS MAP
-----------------------------------

If you can't find Melissa imagery, use imagery from a similar Caribbean event:

1. Hurricane Fiona (2022) - Puerto Rico
2. Hurricane Maria (2017) - Puerto Rico/Caribbean
3. Hurricane Dorian (2019) - Bahamas

These will have similar coastal/island disaster imagery that you can use
to demonstrate your Jamaica crisis map functionality.
"""
