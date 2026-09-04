"""Shared AlphaEarth (Google Satellite Embedding) embedding-math helpers.

This is the ONE place the int8-to-unit-vector dequantization formula lives.
No other module in this project re-implements it — every consumer (live COG
readers, the extraction pipeline) imports `dequantize_aef` from here. See
02-RESEARCH.md "Extraction Mechanics, Verified End to End" step 3 and
PITFALLS.md Pitfall 1 for why: the quantization is non-linear, so averaging
raw int8 values (instead of dequantizing first) silently corrupts the data.

This module is also the ONE place the einsum cosine-similarity pattern
lives (`cosine_similarity_map`, below) — the two functions share a module
because both are "embedding math," not because they are related in any
other way.
"""

import numpy as np

NODATA = -128
N_BANDS = 64


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
    if raw.shape[0] != N_BANDS:
        raise ValueError(
            f"expected the band axis first with length {N_BANDS}, got shape "
            f"{raw.shape}. A frozen table's A00..A63 columns come out band-last "
            f"as (n_points, {N_BANDS}) — transpose before calling, or the "
            f"normalization runs across points instead of bands and silently "
            f"returns wrong vectors."
        )
    mask = np.any(raw == NODATA, axis=0, keepdims=True)
    v = raw.astype(np.float32)
    d = (v / 127.5) ** 2 * np.sign(v)
    norm = np.linalg.norm(d, axis=0, keepdims=True)
    unit = d / (norm + 1e-9)
    result = np.where(mask, np.nan, unit)
    return result.astype(np.float32)


def cosine_similarity_map(query: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    """Cosine similarity of `query` against every row of `matrix`.

    `query` has shape `(d,)`; `matrix` has shape `(n, d)` (band-last, the
    orientation a frozen table's `A00..A63` columns come out in via
    `course.schema.to_matrix` — the OPPOSITE orientation `dequantize_aef`
    above expects). Returns a `(n,)` float32 array.

    This function does NOT assume its inputs are already unit-norm: it
    always divides by the actual norms, so it stays correct even if a
    future embedding provider hands it un-normalized vectors. On this
    course's frozen AlphaEarth data the inputs happen to already be
    unit-norm, which is what lets the notebook demonstrate "dot product
    equals cosine similarity" as an observation about the data — not a
    shortcut baked into this helper.
    """
    if query.shape[-1] != matrix.shape[-1]:
        raise ValueError(
            f"query and matrix must share the embedding dimension: query "
            f"shape {query.shape}, matrix shape {matrix.shape}"
        )
    dot = np.einsum("d,nd->n", query, matrix)
    denom = np.linalg.norm(query) * np.linalg.norm(matrix, axis=1) + 1e-9
    return (dot / denom).astype(np.float32)


def change_score(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Paired, row-aligned change score: `1 - cosine_similarity` per row.

    `a` and `b` both have shape `(n, d)`, band-last (the same orientation
    `cosine_similarity_map`'s `matrix` argument uses). Row `i` of `a` is
    compared only against row `i` of `b` — this is the "same point, two
    years" counterpart to `cosine_similarity_map`'s query-vs-matrix
    broadcast, and is a distinct einsum contraction (do not build it by
    looping `cosine_similarity_map` per row).

    Like `cosine_similarity_map`, this does not assume its inputs are
    already unit-norm.

    IMPORTANT (teaching point): a large change score means the embedding
    representation moved between the two inputs. It is NOT, by itself,
    evidence of a semantic land-cover transition — the same score can be
    produced by phenology (seasonal vegetation change), a different
    observation mix feeding the embedding model, sensor/atmospheric
    artifacts, or genuine land-cover change. This function reports
    representation movement only; interpreting *why* it moved is the
    notebook's job, not this helper's.
    """
    if a.shape != b.shape:
        raise ValueError(
            f"change_score requires row-aligned matrices of identical shape: "
            f"a {a.shape}, b {b.shape}"
        )
    dot = np.einsum("nd,nd->n", a, b)
    denom = np.linalg.norm(a, axis=1) * np.linalg.norm(b, axis=1) + 1e-9
    return (1.0 - dot / denom).astype(np.float32)


def norm_diagnostics(matrix: np.ndarray) -> dict:
    """Report (never assert) vector-norm statistics for `matrix`.

    `matrix` has shape `(n, d)`, band-last. Returns a dict with keys
    `mean`, `std`, `min`, `max` (plain Python `float`) and `n` (plain
    Python `int`, so the result JSON-serializes cleanly for a
    provenance/diagnostics cell without a custom encoder).

    This function never raises and never assumes or enforces unit norm.
    AlphaEarth's dequantized vectors happen to be unit-norm; TESSERA's
    128-D vectors' unit-norm property is undocumented upstream, and
    Clay's differs again — each provider must be *checked*, not assumed.
    Callers decide their own `assert abs(diagnostics["mean"] - 1.0) <
    atol` with a provider-appropriate tolerance in the notebook itself;
    this helper only reports.
    """
    norms = np.linalg.norm(matrix, axis=1)
    return {
        "mean": float(norms.mean()),
        "std": float(norms.std()),
        "min": float(norms.min()),
        "max": float(norms.max()),
        "n": int(matrix.shape[0]),
    }
