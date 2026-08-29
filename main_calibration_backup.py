from pathlib import Path
from datetime import datetime
import json
import numpy as np

from sentaurus_runner import extract_iv
from iv_reader import (
    read_iv,
    read_experimental_iv
)
from metrics import compare_branch
from plotting import (
    plot_branch,
    plot_branch_scaled
)


print("=" * 60)
print("SENTAURUS BASELINE CALIBRATION")
print("=" * 60)


# ============================================================
# OUTPUT FOLDER
# ============================================================

today = datetime.now().strftime(
    "%Y-%m-%d"
)

output_folder = (
    Path("results")
    / today
    / "baseline_calibration"
)

output_folder.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# READ TCAD
# ============================================================

print("\nExtracting TCAD IV...")

forward_file, reverse_file = extract_iv(
    output_folder
)

V_forward, I_forward = read_iv(
    forward_file
)

V_reverse, I_reverse = read_iv(
    reverse_file
)


# ============================================================
# READ EXPERIMENT
# ============================================================

print("Reading experiment...")

V_exp, I_exp = read_experimental_iv(
    "data/experimental_iv.csv"
)


# ============================================================
# SPLIT EXPERIMENT
# ============================================================

forward_mask = V_exp > 0
reverse_mask = V_exp < 0


V_exp_forward = V_exp[
    forward_mask
]

I_exp_forward = I_exp[
    forward_mask
]


V_exp_reverse = V_exp[
    reverse_mask
]

I_exp_reverse = I_exp[
    reverse_mask
]


# ============================================================
# COMPARE
# ============================================================

print("Comparing forward branch...")

forward = compare_branch(
    V_forward,
    I_forward,
    V_exp_forward,
    I_exp_forward
)


print("Comparing reverse branch...")

reverse = compare_branch(
    V_reverse,
    I_reverse,
    V_exp_reverse,
    I_exp_reverse
)


# ============================================================
# SUMMARY
# ============================================================

k_ratio = (
    abs(reverse["K"] / forward["K"])
    if forward["K"] != 0
    else np.nan
)


summary = {

    "forward": {
        "points": forward["points"],
        "pearson": forward["pearson"],
        "K": forward["K"],
        "r2_scaled": forward["r2_scaled"],
        "origin_slope":
            forward["origin_slope"],
        "origin_intercept":
            forward["origin_intercept"],
        "origin_r2":
            forward["origin_r2"],
    },

    "reverse": {
        "points": reverse["points"],
        "pearson": reverse["pearson"],
        "K": reverse["K"],
        "r2_scaled": reverse["r2_scaled"],
        "origin_slope":
            reverse["origin_slope"],
        "origin_intercept":
            reverse["origin_intercept"],
        "origin_r2":
            reverse["origin_r2"],
    },

    "K_reverse_over_forward":
        float(k_ratio)
}


# ============================================================
# SAVE JSON
# ============================================================

with open(
    output_folder / "metrics.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        summary,
        f,
        indent=4,
        ensure_ascii=False
    )


# ============================================================
# PLOTS
# ============================================================

plot_branch(
    forward,
    "Forward branch",
    output_folder / "forward_raw.png"
)

plot_branch_scaled(
    forward,
    "Forward branch",
    output_folder / "forward_scaled.png"
)

plot_branch(
    reverse,
    "Reverse branch",
    output_folder / "reverse_raw.png"
)

plot_branch_scaled(
    reverse,
    "Reverse branch",
    output_folder / "reverse_scaled.png"
)


# ============================================================
# PRINT
# ============================================================

print()
print("=" * 60)
print("CALIBRATION RESULTS")
print("=" * 60)

print("\nFORWARD")
print(
    f"Pearson       = "
    f"{forward['pearson']:.6f}"
)
print(
    f"K             = "
    f"{forward['K']:.6g}"
)
print(
    f"Scaled R²     = "
    f"{forward['r2_scaled']:.6f}"
)
print(
    f"Origin slope  = "
    f"{forward['origin_slope']:.6g}"
)
print(
    f"Origin R²     = "
    f"{forward['origin_r2']:.6f}"
)


print("\nREVERSE")
print(
    f"Pearson       = "
    f"{reverse['pearson']:.6f}"
)
print(
    f"K             = "
    f"{reverse['K']:.6g}"
)
print(
    f"Scaled R²     = "
    f"{reverse['r2_scaled']:.6f}"
)
print(
    f"Origin slope  = "
    f"{reverse['origin_slope']:.6g}"
)
print(
    f"Origin R²     = "
    f"{reverse['origin_r2']:.6f}"
)


print(
    "\nK reverse / forward = "
    f"{k_ratio:.6g}"
)

print(
    "\nResults saved to:"
)

print(output_folder)