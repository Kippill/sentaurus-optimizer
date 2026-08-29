from pathlib import Path

import numpy as np
import pandas as pd

from iv_reader import read_iv


# ============================================================
# SETTINGS
# ============================================================

RESULTS_ROOT = Path(
    "results/2026-08-28"
)

SWEEP_CSV = (
    RESULTS_ROOT
    / "night_2d_i_layers"
    / "night_2d_sweep.csv"
)

OUTPUT_CSV = (
    RESULTS_ROOT
    / "rs_vs_i_gaas.csv"
)


# We want the original structure
FIXED_I_INGAAS_NM = 5.0

# Only inspect the upper part of forward IV
MIN_VOLTAGE_FRACTION = 0.55

# Minimum number of points in fitted linear region
MIN_POINTS = 12

# Criterion that the region is sufficiently linear
MIN_R2 = 0.9995


# ============================================================
# LINEAR FIT
# ============================================================

def linear_fit(x, y):

    p = np.polyfit(
        x,
        y,
        1
    )

    slope = p[0]
    intercept = p[1]

    y_fit = (
        slope * x
        + intercept
    )

    ss_res = np.sum(
        (y - y_fit) ** 2
    )

    ss_tot = np.sum(
        (y - np.mean(y)) ** 2
    )

    if ss_tot == 0:
        r2 = 1.0
    else:
        r2 = (
            1.0
            - ss_res / ss_tot
        )

    return (
        slope,
        intercept,
        r2
    )


# ============================================================
# FIND SERIES-RESISTANCE REGION
# ============================================================

def extract_rs(
    voltage,
    current
):

    voltage = np.asarray(
        voltage,
        dtype=float
    )

    current = np.asarray(
        current,
        dtype=float
    )

    # sort by voltage
    order = np.argsort(
        voltage
    )

    voltage = voltage[order]
    current = current[order]

    # forward branch only
    mask = (
        voltage > 0
    )

    voltage = voltage[mask]
    current = current[mask]

    if len(voltage) < MIN_POINTS:

        raise RuntimeError(
            "Too few forward IV points."
        )

    vmax = np.max(
        voltage
    )

    vmin_search = (
        MIN_VOLTAGE_FRACTION
        * vmax
    )

    start_candidates = np.where(
        voltage >= vmin_search
    )[0]

    valid_fits = []

    # --------------------------------------------------------
    # Every candidate is a TAIL:
    #
    # start -> maximum voltage
    #
    # The diode should already be fully open there.
    # --------------------------------------------------------

    for start in start_candidates:

        V = voltage[start:]
        I = current[start:]

        if len(V) < MIN_POINTS:
            continue

        # Fit:
        #
        # V = Rs * I + V0
        #
        Rs, V0, r2 = linear_fit(
            I,
            V
        )

        if Rs <= 0:
            continue

        valid_fits.append({

            "start":
                start,

            "n_points":
                len(V),

            "Rs":
                Rs,

            "V0":
                V0,

            "r2":
                r2,

            "V_min":
                V[0],

            "V_max":
                V[-1],

            "I_min":
                I[0],

            "I_max":
                I[-1],
        })


    if not valid_fits:

        raise RuntimeError(
            "Could not fit high-current region."
        )


    # --------------------------------------------------------
    # Prefer the LONGEST region satisfying R2 requirement
    # --------------------------------------------------------

    good = [
        fit
        for fit in valid_fits
        if fit["r2"] >= MIN_R2
    ]


    if good:

        best = max(
            good,
            key=lambda x:
                x["n_points"]
        )

        best["fit_status"] = (
            "LINEAR"
        )

    else:

        # No region passed threshold.
        # Return the best available fit,
        # but mark it.
        best = max(
            valid_fits,
            key=lambda x:
                x["r2"]
        )

        best["fit_status"] = (
            "WARNING_LOW_R2"
        )


    return best


# ============================================================
# READ SWEEP
# ============================================================

df = pd.read_csv(
    SWEEP_CSV
)


# Only i-InGaAs = 5 nm
df = df[
    (
        df["status"] == "OK"
    )
    &
    (
        np.isclose(
            df["t_i_ingaas_nm"],
            FIXED_I_INGAAS_NM
        )
    )
].copy()


df = df.sort_values(
    "t_i_gaas_nm"
)


# ============================================================
# CALCULATE Rs
# ============================================================

results = []


for _, row in df.iterrows():

    thickness = float(
        row["t_i_gaas_nm"]
    )

    run_name = str(
        row["run_name"]
    )

    run_folder = (
        RESULTS_ROOT
        / run_name
    )

    forward_file = (
        run_folder
        / "model_forward.txt"
    )


    print()
    print("=" * 70)

    print(
        f"i-GaAs = "
        f"{thickness:.1f} nm"
    )

    print(
        f"Run = {run_name}"
    )


    V, I = read_iv(
        forward_file
    )


    fit = extract_rs(
        V,
        I
    )


    # --------------------------------------------------------
    # Raw cylindrical simulation has R = 5 um.
    #
    # Going from R=5 to R=50:
    #
    # area x100
    # current x100
    # resistance /100
    # --------------------------------------------------------

    Rs_R5 = (
        fit["Rs"]
    )

    Rs_R50 = (
        Rs_R5 / 100.0
    )


    result = {

        "t_i_gaas_nm":
            thickness,

        "run_name":
            run_name,

        "fit_status":
            fit["fit_status"],

        "Rs_R5_ohm":
            Rs_R5,

        "Rs_R50_ohm":
            Rs_R50,

        "V0_fit_V":
            fit["V0"],

        "fit_R2":
            fit["r2"],

        "V_fit_min":
            fit["V_min"],

        "V_fit_max":
            fit["V_max"],

        "I_fit_min_A":
            fit["I_min"],

        "I_fit_max_A":
            fit["I_max"],

        "n_fit_points":
            fit["n_points"],
    }


    results.append(
        result
    )


    print(
        f"Rs (R=5 um)  = "
        f"{Rs_R5:.6e} Ohm"
    )

    print(
        f"Rs (R=50 um) = "
        f"{Rs_R50:.6e} Ohm"
    )

    print(
        f"Linear range = "
        f"{fit['V_min']:.3f} ... "
        f"{fit['V_max']:.3f} V"
    )

    print(
        f"R2 = "
        f"{fit['r2']:.8f}"
    )


# ============================================================
# DATAFRAME
# ============================================================

result_df = pd.DataFrame(
    results
)


# ============================================================
# NORMALIZE TO 350 nm
# ============================================================

baseline_rows = result_df[
    np.isclose(
        result_df[
            "t_i_gaas_nm"
        ],
        350.0
    )
]


if len(baseline_rows) == 1:

    baseline_rs = float(
        baseline_rows.iloc[0][
            "Rs_R5_ohm"
        ]
    )

    result_df[
        "Rs_over_Rs350"
    ] = (
        result_df[
            "Rs_R5_ohm"
        ]
        / baseline_rs
    )


# ============================================================
# SAVE
# ============================================================

result_df.to_csv(
    OUTPUT_CSV,
    index=False
)


# ============================================================
# PRINT
# ============================================================

print()
print("=" * 100)
print("SERIES RESISTANCE vs i-GaAs THICKNESS")
print("=" * 100)

columns = [
    "t_i_gaas_nm",
    "Rs_R5_ohm",
    "Rs_R50_ohm",
    "Rs_over_Rs350",
    "fit_R2",
    "V_fit_min",
    "V_fit_max",
    "fit_status",
]

print(
    result_df[
        columns
    ].to_string(
        index=False
    )
)

print()
print(
    "Saved:",
    OUTPUT_CSV
)