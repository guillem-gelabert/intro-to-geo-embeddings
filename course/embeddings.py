"""Shared AlphaEarth (Google Satellite Embedding) dequantization helper.

This is the ONE place the int8-to-unit-vector dequantization formula lives.
No other module in this project re-implements it — every consumer (live COG
readers, the extraction pipeline) imports `dequantize_aef` from here. See
02-RESEARCH.md "Extraction Mechanics, Verified End to End" step 3 and
PITFALLS.md Pitfall 1 for why: the quantization is non-linear, so averaging
raw int8 values (instead of dequantizing first) silently corrupts the data.
"""

import numpy as np

NODATA = -128


def dequantize_aef(raw: np.ndarray) -> np.ndarray:
    """Dequantize a raw int8 AlphaEarth array into a float32 unit-norm array.

    `raw` has the band axis first (axis 0, length 64): shape `(64,)` for a
    single vector, `(64, H, W)` for a window, or `(64, N)` for N sampled
    points.

    A NODATA (-128) value in ANY band at a given spatial/point position marks
    that whole position as nodata: the output at that position is NaN across
    all 64 bands.

    Valid positions: `d = (v / 127.5) ** 2 * sign(v)` element-wise on the
    int8-as-float32 array, then L2-renormalized along axis 0. Renormalization
    is required, not optional — population statistics show the pre-renorm
    norm deviates from 1.0 by up to ~0.9% per pixel (02-RESEARCH.md).
    """
    mask = np.any(raw == NODATA, axis=0, keepdims=True)
    v = raw.astype(np.float32)
    d = (v / 127.5) ** 2 * np.sign(v)
    norm = np.linalg.norm(d, axis=0, keepdims=True)
    unit = d / (norm + 1e-9)
    result = np.where(mask, np.nan, unit)
    return result.astype(np.float32)
