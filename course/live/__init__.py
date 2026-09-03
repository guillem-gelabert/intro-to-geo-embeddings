class LiveSourceUnavailable(RuntimeError):
    """Raised by any live-source adapter (AlphaEarth COG, WorldCover, HRL,
    Sentinel-2 STAC, ...) when it cannot fetch data from its upstream source.

    Every adapter in this package raises this on a source failure so callers
    can catch one exception type and fall back to the frozen (Path B) data
    instead of a source-specific error (network timeout, HTTP status, GDAL
    error, ...).
    """
