RANDOM_STATE = 42
COURSE_RELEASE = "2026.08"
KERNEL_NAME = "geo-embeddings-course"

# Study-area registry: bbox_4326 is (min_lon, min_lat, max_lon, max_lat);
# epsg is the single UTM zone each AOI is verified to sit entirely inside
# (02-RESEARCH.md "Region B Decision (settled)" — Seville's bbox was chosen
# specifically to avoid straddling a UTM zone boundary).
# An AOI must fit inside a SINGLE AlphaEarth tile, not merely inside one UTM
# zone. The pipeline reads one tile per (area, year); anything past that tile's
# edge comes back as -128 nodata and dequantizes to NaN.
#
# Seville was originally (-5.99, 37.28, -5.69, 37.48). Two tiles cover that
# span -- one ending at lon -5.7610, the next starting at -5.7882 -- so 448 of
# 2050 points (21.9%) landed outside the tile actually read and every embedding
# for them was NaN, identically in all three years.
#
# The east edge then went to -5.77 on the strength of the index's stated tile
# bounds, and 49 rows (2.4%) at lon -5.7775..-5.7704 were STILL NaN. The index
# publishes each tile's WGS84 *bounding box*, but the tile is a UTM square, so
# its true eastern data edge bows west of that box at some latitudes. Trust
# measured coverage over the advertised bbox: -5.79 clears the observed NaN
# band by roughly 1.3 km. The west edge is -5.98 rather than -5.99 to keep
# matching margin off the tile's other side.
AREAS = {
    "bern": {"bbox_4326": (7.30, 46.85, 7.60, 47.05), "epsg": 32632},
    "seville": {"bbox_4326": (-5.98, 37.28, -5.79, 37.48), "epsg": 32630},
}

# AlphaEarth tiles confirmed to exist for both regions at these years
# (02-RESEARCH.md "Anchor Years").
ANCHOR_YEARS = [2018, 2021, 2024]

# 1.5 km, inside the settled 1-2 km recommendation (02-RESEARCH.md
# "Sampling and Block Design" -> "Block size").
BLOCK_SIZE_M = 1500

DATA_DIR = "data"

# Placeholders — Plan 02-11 confirms and may overwrite these with a
# checkpoint before anything is actually published.
RELEASE_ORG = "guillem-gelabert"
RELEASE_REPO = "intro-to-geo-embeddings"
RELEASE_TAG = f"v{COURSE_RELEASE}"
