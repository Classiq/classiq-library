import functools
import time
from functools import wraps
from pathlib import Path
from typing import (
    Callable,
    Optional,
    ParamSpec,
    Tuple,
    TypeVar,
)

import numpy as np
from statsmodels.stats.proportion import proportion_confint

# Type variables for preserving the signature
P = ParamSpec("P")  # For parameters
R = TypeVar("R")  # For return type


def timeit(func: Callable[P, R]) -> Callable[P, R]:
    @wraps(func)
    def wrap(*args: P.args, **kwargs: P.kwargs) -> R:
        if args[0]._benchmarking:
            start = time.time()
            res = func(*args, **kwargs)
            elapsed = time.time() - start
            print(f"Elapsed time for function '{func.__name__}': {elapsed:.2e} s")
        else:
            res = func(*args, **kwargs)
        return res

    return wrap


def get_pfail(
    shots: int | np.ndarray,
    fails: int | np.ndarray,
    alpha: float = 0.01,
    confint_method: str = "wilson",
) -> Tuple[float | np.ndarray, float | np.ndarray]:
    """
    Calculate the failure probability and confidence interval.

    This function computes the estimated failure probability and the half-width
    of its confidence interval based on the number of shots and failures.

    Parameters
    ----------
    shots : int or array-like
        Total number of experimental shots.
    fails : int or array-like
        Number of failures observed.
    alpha : float, default 0.01
        Significance level for the confidence interval (e.g., 0.01 for 99%
        confidence).
    confint_method : str, default "wilson"
        Method to calculate confidence intervals. See
        statsmodels.stats.proportion.proportion_confint for available options.

    Returns
    -------
    pfail : float or array-like
        Estimated failure probability (midpoint of confidence interval).
    delta_pfail : float or array-like
        Half-width of the confidence interval.
    """
    pfail_low, pfail_high = proportion_confint(
        fails, shots, alpha=alpha, method=confint_method
    )
    pfail = (pfail_low + pfail_high) / 2
    delta_pfail = pfail_high - pfail

    return pfail, delta_pfail


def get_project_folder() -> Path:
    project_folder = Path(__file__).resolve().parents[2]
    return project_folder


def _get_final_predictions(
    weights: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, Optional[np.ndarray]]:
    """
    Finds the best logical class and color index that minimizes the weight
    for each sample from a 3D weights array, and calculates the gap between
    the best and second-best logical class minimum weights.

    Parameters
    ----------
    weights : np.ndarray
        A 3D float array with shape (num_logical_classes, num_colors, num_samples).
        `weights[i, c, j]` is the weight for the j-th sample, i-th logical
        class, and c-th color index.

    Returns
    -------
    best_logical_classes : np.ndarray
        1D int array. The index of the best logical class for each sample.
    best_color_indices : np.ndarray
        1D int array. The index of the best color for each sample.
    weights_final : np.ndarray
        1D float array. The minimum weight found for each sample.
    logical_gap : Optional[np.ndarray]
        1D float array or None. The difference between the second smallest and
        smallest minimum weight across logical classes for each sample.
        Calculated only if `num_logical_classes > 1`.
    """
    if weights.ndim != 3 or weights.size == 0:
        raise ValueError(f"Invalid input shape: {weights.shape}")

    num_logical_classes, num_colors, num_samples = weights.shape

    # 1. Find the overall minimum weight and its index for each sample
    # Reshape to (logical_class * color, sample) to find the flat index of the min
    reshaped_weights = weights.reshape(num_logical_classes * num_colors, num_samples)

    flat_min_indices = np.argmin(reshaped_weights, axis=0)
    weights_final = np.min(
        reshaped_weights, axis=0
    )  # Or: reshaped_weights[flat_min_indices, np.arange(num_samples)]

    # 2. Decode the flat index back into logical class and color index
    best_logical_classes = flat_min_indices // num_colors
    best_color_indices = flat_min_indices % num_colors

    # 3. Calculate logical_gap if needed
    logical_gap: Optional[np.ndarray] = None
    if num_logical_classes > 1:
        # Find the minimum weight per logical class for each sample
        # Shape: (num_logical_classes, num_samples)
        min_weights_per_class = np.min(weights, axis=1)  # Min across color axis

        # Sort along the logical class axis to find the smallest two
        # Shape: (num_logical_classes, num_samples)
        sorted_min_weights = np.sort(min_weights_per_class, axis=0)

        # Calculate the gap between the second smallest and the smallest
        # Shape: (num_samples,)
        logical_gap = sorted_min_weights[1] - sorted_min_weights[0]

    # Return best_color_indices directly instead of mapped string colors
    return best_logical_classes, best_color_indices, weights_final, logical_gap
