"""Notebook-level provenance summary builder.

`build_provenance` reshapes a mapping of already-loaded region/year tables
(each carrying `gdf.attrs["course_provenance"]`, populated by
`course.data.load`) into one notebook-level summary dict. Every field is
read directly from that carried metadata -- never hand-typed here -- so a
future dataset-version bump is reflected automatically instead of silently
going undetected in the notebook's own provenance file.
"""

import json
from datetime import UTC, datetime
from pathlib import Path

_FIELDS = [
    "region",
    "year",
    "embedding_product",
    "dataset_version",
    "crs",
    "label_source",
    "validation_source",
]


def build_provenance(loaded: dict, created_by: str) -> dict:
    """Build a notebook-level provenance summary from already-loaded tables.

    `loaded` maps an arbitrary label (e.g. "bern_2021") to an already-loaded
    GeoDataFrame (or any object exposing `.attrs`) carrying
    `attrs["course_provenance"]`. Raises KeyError, naming the offending
    entry, if any table lacks that metadata -- a loud failure rather than a
    silently incomplete provenance file.
    """
    tables = []
    for key, gdf in loaded.items():
        prov = gdf.attrs.get("course_provenance")
        if prov is None:
            raise KeyError(
                f"loaded[{key!r}] has no 'course_provenance' in its .attrs; "
                "cannot build provenance for this table."
            )
        entry = {field: prov[field] for field in _FIELDS}
        entry["license"] = prov["license_alphaearth"]
        entry["attribution"] = prov["attribution_alphaearth"]
        tables.append(entry)

    return {
        "created_by": created_by,
        "generated_at": datetime.now(UTC).isoformat(),
        "tables": tables,
    }


def write_provenance(provenance: dict, path: Path) -> None:
    """Write `provenance` as indented JSON to `path`, creating parents."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(provenance, indent=2))
