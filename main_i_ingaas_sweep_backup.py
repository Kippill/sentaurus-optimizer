from evaluator import evaluate_structure
from iv_reader import read_iv

import csv
import json
from pathlib import Path
from datetime import datetime

import numpy as np
import matplotlib.pyplot as plt


# ============================================================
# SWEEP SETTINGS
# ============================================================

THICKNESSES_NM = [
    3.0,
    4.0,
    5.0,
    6.0,
    7.0,
    8.0,
    10.0,
]

BASELINE_THICKNESS_NM = 5.0

FORWARD_CHECK_V = 1.0
REVERSE_CHECK_V = -1.0


# ============================================================
# BASE STRUCTURE
# ============================================================

BASE_PARAMS = {

    # --------------------------------------------------------
    # GEOMETRY
    # --------------------------------------------------------

    "geometry_mode": "cylindrical",

    # simulated radius
    "width_um": 5.0,

    # real device radius
    "target_radius_um": 50.0,


    # --------------------------------------------------------
    # STRUCTURE
    # --------------------------------------------------------

    "t_n_top_nm": 400.0,
    "t_n_ingaas_nm": 5.0,

    # THIS PARAMETER WILL BE VARIED
    "t_i_ingaas_nm": BASELINE_THICKNESS_NM,

    "t_p_nm": 4.0,
    "t_i_gaas_nm": 350.0,
    "t_n_bottom_nm": 1000.0,


    # --------------------------------------------------------
    # DOPING
    # --------------------------------------------------------

    "Nd_top": 5.0e18,
    "Nd_n_ingaas": 5.0e18,
    "Nd_i_ingaas": 1.0e14,
    "Na_p": 3.0e18,
    "Nd_i_gaas": 1.0e14,
    "Nd_bottom": 5.0e18,


    # --------------------------------------------------------
    # MATERIAL
    # --------------------------------------------------------

    "ga_fraction": 0.75,


    # --------------------------------------------------------
    # PHYSICS
    # --------------------------------------------------------

    "thermionic": False,
    "bgn_model": "OldSlotboom",


    # --------------------------------------------------------
    # IV
    # --------------------------------------------------------

    "v_forward": 1.5,
    "v_reverse": -1.5,
}


# ============================================================
# RUN SWEEP
# ============================================================

results = []


for thickness_nm in THICKNESSES_NM:

    print()
    print("#" * 72)
    print(
        f"i-InGaAs thickness: "
        f"{thickness_nm:.1f} nm"
    )
    print("#" * 72)

    params = BASE_PARAMS.copy()

    params["t_i_ingaas_nm"] = thickness_nm

    params["physics_name"] = (
        f"iInGaAs_{thickness_nm:.1f}nm"
    )

    try:

        run_result = evaluate_structure(
            params
        )

        run_folder = Path(
            run_result["run_folder"]
        )

        # ----------------------------------------------------
        # READ RAW CYLINDRICAL IV
        # ----------------------------------------------------

        V_forward, I_forward = read_iv(
            run_folder / "model_forward.txt"
        )

        V_reverse, I_reverse = read_iv(
            run_folder / "model_reverse.txt"
        )

        # ----------------------------------------------------
        # CURRENT AT FIXED VOLTAGES
        # ----------------------------------------------------

        I_plus_1V = float(
            np.interp(
                FORWARD_CHECK_V,
                V_forward,
                I_forward
            )
        )

        # reverse voltage array may not be sorted ascending
        reverse_order = np.argsort(
            V_reverse
        )

        V_reverse_sorted = (
            V_reverse[reverse_order]
        )

        I_reverse_sorted = (
            I_reverse[reverse_order]
        )

        I_minus_1V = float(
            np.interp(
                REVERSE_CHECK_V,
                V_reverse_sorted,
                I_reverse_sorted
            )
        )

        result = {
            "status": "OK",

            "run_id":
                run_result["run_id"],

            "run_name":
                run_result["run_name"],

            "run_folder":
                str(run_folder),

            "t_i_ingaas_nm":
                thickness_nm,

            "I_plus_1V_A":
                I_plus_1V,

            "I_minus_1V_A":
                I_minus_1V,
        }

        results.append(
            result
        )

    except Exception as error:

        print()
        print("!!! RUN FAILED !!!")
        print(
            f"Thickness = {thickness_nm} nm"
        )
        print("Error:", error)

        results.append({
            "status": "FAILED",
            "t_i_ingaas_nm": thickness_nm,
            "error": str(error),
        })


# ============================================================
# FIND 5 nm BASELINE
# ============================================================

baseline = None

for result in results:

    if (
        result["status"] == "OK"
        and
        result["t_i_ingaas_nm"]
        == BASELINE_THICKNESS_NM
    ):

        baseline = result
        break


if baseline is None:

    raise RuntimeError(
        "5 nm baseline run was not completed."
    )


baseline_forward = (
    baseline["I_plus_1V_A"]
)

baseline_reverse = (
    baseline["I_minus_1V_A"]
)


# ============================================================
# NORMALIZATION TO 5 nm
# ============================================================

for result in results:

    if result["status"] != "OK":
        continue

    result["I_plus_1V_ratio"] = (
        result["I_plus_1V_A"]
        / baseline_forward
    )

    # use absolute reverse current
    result["I_minus_1V_ratio"] = (
        abs(result["I_minus_1V_A"])
        / abs(baseline_reverse)
    )


# ============================================================
# OUTPUT FOLDER
# ============================================================

today = datetime.now().strftime(
    "%Y-%m-%d"
)

summary_folder = (
    Path("results")
    / today
    / "i_ingaas_thickness_sweep"
)

summary_folder.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# CSV
# ============================================================

csv_path = (
    summary_folder
    / "i_ingaas_sweep_summary.csv"
)

fieldnames = [
    "status",
    "run_id",
    "run_name",
    "t_i_ingaas_nm",

    "I_plus_1V_A",
    "I_plus_1V_ratio",

    "I_minus_1V_A",
    "I_minus_1V_ratio",
]


with open(
    csv_path,
    "w",
    newline="",
    encoding="utf-8"
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=fieldnames,
        extrasaction="ignore"
    )

    writer.writeheader()

    for result in results:
        writer.writerow(result)


# ============================================================
# JSON
# ============================================================

json_path = (
    summary_folder
    / "i_ingaas_sweep_summary.json"
)

with open(
    json_path,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        results,
        f,
        indent=4,
        ensure_ascii=False
    )


# ============================================================
# FORWARD IV OVERLAY
# ============================================================

plt.figure(
    figsize=(10, 7)
)

for result in results:

    if result["status"] != "OK":
        continue

    run_folder = Path(
        result["run_folder"]
    )

    V, I = read_iv(
        run_folder
        / "model_forward.txt"
    )

    plt.plot(
        V,
        I,
        label=(
            f"{result['t_i_ingaas_nm']:.0f} nm"
        )
    )


plt.xlabel("Voltage, V")
plt.ylabel("Current, A")

plt.title(
    "Forward IV vs i-InGaAs thickness\n"
    "Cylindrical R = 5 um"
)

plt.grid(True)
plt.legend()
plt.tight_layout()

forward_plot = (
    summary_folder
    / "forward_i_ingaas_sweep.png"
)

plt.savefig(
    forward_plot,
    dpi=200
)

plt.close()


# ============================================================
# REVERSE IV OVERLAY
# ============================================================

plt.figure(
    figsize=(10, 7)
)

for result in results:

    if result["status"] != "OK":
        continue

    run_folder = Path(
        result["run_folder"]
    )

    V, I = read_iv(
        run_folder
        / "model_reverse.txt"
    )

    plt.plot(
        V,
        I,
        label=(
            f"{result['t_i_ingaas_nm']:.0f} nm"
        )
    )


plt.xlabel("Voltage, V")
plt.ylabel("Current, A")

plt.title(
    "Reverse IV vs i-InGaAs thickness\n"
    "Cylindrical R = 5 um"
)

plt.grid(True)
plt.legend()
plt.tight_layout()

reverse_plot = (
    summary_folder
    / "reverse_i_ingaas_sweep.png"
)

plt.savefig(
    reverse_plot,
    dpi=200
)

plt.close()


# ============================================================
# FINAL TABLE
# ============================================================

print()
print("=" * 88)
print("i-InGaAs THICKNESS SWEEP")
print("=" * 88)

header = (
    f"{'t, nm':>8}"
    f"{'I(+1V), A':>18}"
    f"{'/5nm':>12}"
    f"{'I(-1V), A':>18}"
    f"{'/5nm':>12}"
)

print(header)
print("-" * 88)


for result in results:

    if result["status"] != "OK":

        print(
            f"{result['t_i_ingaas_nm']:>8.1f}"
            f"{'FAILED':>18}"
        )

        continue

    print(
        f"{result['t_i_ingaas_nm']:>8.1f}"
        f"{result['I_plus_1V_A']:>18.6e}"
        f"{result['I_plus_1V_ratio']:>12.3f}"
        f"{result['I_minus_1V_A']:>18.6e}"
        f"{result['I_minus_1V_ratio']:>12.3f}"
    )


print()
print("Summary:")
print(csv_path)

print()
print("Forward plot:")
print(forward_plot)

print()
print("Reverse plot:")
print(reverse_plot)