RANDOM_STATE = 42
COURSE_RELEASE = "2026.08"
KERNEL_NAME = "geo-embeddings-course"

# Study-area registry: bbox_4326 is (min_lon, min_lat, max_lon, max_lat);
# epsg is the single UTM zone each AOI is verified to sit entirely inside
# (02-RESEARCH.md "Region B Decision (settled)" — Seville's bbox was chosen
# specifically to avoid straddling a UTM zone boundary).
AREAS = {
    "bern": {"bbox_4326": (7.30, 46.85, 7.60, 47.05), "epsg": 32632},
    "seville": {"bbox_4326": (-5.99, 37.28, -5.69, 37.48), "epsg": 32630},
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
