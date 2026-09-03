"""Spatial-block construction and grouped cross-validation reporting.

This is the ONE place spatial blocks get built and grouped-CV scoring gets
computed for the course. See PITFALLS.md Pitfall 3 ("Building spatial
blocks wrongly"): computing blocks in a geographic (degree-based) CRS
produces nonsense metre sizes, so `make_blocks` refuses geographic input
outright rather than silently misbehaving.

`spatial_cv_report` is deliberately generic: it accepts any scikit-learn
splitter (a `GroupKFold` instance for in-region block CV, or a
`LeaveOneGroupOut` instance for leave-region-out) and does not construct
either itself, so the identical code path serves both. On this course's
measured data (logistic regression, four classes, Bern vs Seville, 2021),
leave-region-out costs roughly 17-19 accuracy points relative to random or
spatial-block splits, while the in-region block gap is close to zero —
this module must not assume spatial blocking always lowers the score.
"""

import numpy as np
from sklearn.model_selection import cross_validate


def make_blocks(gdf_projected, block_size_m: float) -> np.ndarray:
    """Assign each row of `gdf_projected` a spatial-block id.

    `gdf_projected` must already be in a projected (metre-based) CRS -- e.g.
    EPSG:2056 -- reprojected by the caller as a deliberate, visible teaching
    step. This function does not reproject for the caller: it raises
    ValueError if handed a geographic CRS, since block sizes computed in
    degrees are meaningless (PITFALLS.md Pitfall 3).
    """
    crs = gdf_projected.crs
    if crs is None or crs.is_geographic:
        raise ValueError(
            "make_blocks requires a projected CRS in metres; got "
            f"{crs!r} which is geographic (or missing). Reproject to a "
            "projected CRS (e.g. EPSG:2056) before calling make_blocks."
        )
    x = gdf_projected.geometry.x.to_numpy()
    y = gdf_projected.geometry.y.to_numpy()
    block_x = np.floor(x / block_size_m).astype(int)
    block_y = np.floor(y / block_size_m).astype(int)
    return np.array([f"{bx}_{by}" for bx, by in zip(block_x, block_y)])


def spatial_cv_report(
    estimator,
    X: np.ndarray,
    y: np.ndarray,
    groups: np.ndarray,
    cv,
    scoring: tuple[str, ...] = ("balanced_accuracy", "f1_macro"),
) -> dict:
    """Thin, generic wrapper around `sklearn.model_selection.cross_validate`.

    `cv` is caller-supplied: pass a `GroupKFold(...)` instance for in-region
    block cross-validation, or a `LeaveOneGroupOut()` instance for
    leave-region-out. This function never constructs a splitter itself, so
    both use cases run through the identical code path.

    Returns a dict with the raw `test_<metric>` fold-score arrays from
    `cross_validate`, plus `mean_<metric>`/`std_<metric>` per requested
    metric, `n_groups`, and `n_splits`.
    """
    scoring_list = list(scoring)
    raw = cross_validate(
        estimator, X, y, groups=groups, cv=cv, scoring=scoring_list
    )
    result: dict = {}
    for metric in scoring_list:
        key = f"test_{metric}"
        result[key] = raw[key]
        result[f"mean_{metric}"] = float(np.mean(raw[key]))
        result[f"std_{metric}"] = float(np.std(raw[key]))
    result["n_groups"] = len(np.unique(groups))
    result["n_splits"] = cv.get_n_splits(groups=groups)
    return result
