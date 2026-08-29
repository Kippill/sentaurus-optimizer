from evaluator import evaluate_structure

import csv
import json
from pathlib import Path
from datetime import datetime

import matplotlib.pyplot as plt

from iv_reader import read_iv


# ============================================================
# SETTINGS
# ============================================================

BASE_I_GAAS_NM = 350.0

THICKNESS_CHANGE_PCT = [
    -70,
    -50,
    -30,
    -10,
    0,
    10,
    30,
    50,
    70,
    90,
    100,
]


# ============================================================
# BASE STRUCTURE
# ============================================================

BASE_PARAMS = {

    # --------------------------------------------------------
    # GEOMETRY
    # --------------------------------------------------------

    "geometry_mode": "cylindrical",

    # Cylindrical radius
    "width_um": 5.0,

    # Experimental device radius
    "target_radius_um": 50.0,


    # --------------------------------------------------------
    # STRUCTURE
    # --------------------------------------------------------

    "t_n_top_nm": 400.0,
    "t_n_ingaas_nm": 5.0,
    "t_i_ingaas_nm": 5.0,
    "t_p_nm": 4.0,

    # THIS PARAMETER WILL BE VARIED
    "t_i_gaas_nm": BASE_I_GAAS_NM,

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


for change_pct in THICKNESS_CHANGE_PCT:

    thickness_nm = (
        BASE_I_GAAS_NM
        * (1.0 + change_pct / 100.0)
    )

    print()
    print("#" * 72)
    print(
        f"i-GaAs thickness: "
        f"{thickness_nm:.1f} nm "
        f"({change_pct:+.0f} %)"
    )
    print("#" * 72)

    params = BASE_PARAMS.copy()

    params["t_i_gaas_nm"] = thickness_nm

    params["physics_name"] = (
        f"iGaAs_{thickness_nm:.0f}nm"
    )

    try:

        result = evaluate_structure(
            params
        )

        result["status"] = "OK"
        result["change_pct"] = change_pct
        result["t_i_gaas_nm"] = thickness_nm

        results.append(result)

    except Exception as error:

        print()
        print("!!! RUN FAILED !!!")
        print(
            f"Thickness = {thickness_nm:.1f} nm"
        )
        print("Error:", error)

        results.append({

            "status": "FAILED",
            "change_pct": change_pct,
            "t_i_gaas_nm": thickness_nm,
            "error": str(error),

        })


# ============================================================
# OUTPUT FOLDER
# ============================================================

today = datetime.now().strftime(
    "%Y-%m-%d"
)

summary_folder = (
    Path("results")
    / today
    / "i_gaas_thickness_sweep"
)

summary_folder.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# SAVE JSON
# ============================================================

json_path = (
    summary_folder
    / "thickness_sweep_summary.json"
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
# SAVE CSV
# ============================================================

csv_path = (
    summary_folder
    / "thickness_sweep_summary.csv"
)

fieldnames = [

    "status",

    "change_pct",
    "t_i_gaas_nm",

    "run_id",
    "run_name",

    "K_forward",
    "K_reverse",
    "K_ratio",

    "r2_forward",
    "r2_reverse",

    "pearson_forward",
    "pearson_reverse",
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
        run_folder / "model_forward.txt"
    )

    plt.plot(
        V,
        I,
        label=(
            f"{result['t_i_gaas_nm']:.0f} nm"
        )
    )


plt.xlabel("Voltage, V")
plt.ylabel("Current, A")

plt.title(
    "Forward IV vs i-GaAs thickness\n"
    "Cylindrical R = 5 um"
)

plt.grid(True)

plt.legend(
    fontsize=8,
    ncol=2
)

plt.tight_layout()

forward_plot = (
    summary_folder
    / "forward_thickness_sweep.png"
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
        run_folder / "model_reverse.txt"
    )

    plt.plot(
        V,
        I,
        label=(
            f"{result['t_i_gaas_nm']:.0f} nm"
        )
    )


plt.xlabel("Voltage, V")
plt.ylabel("Current, A")

plt.title(
    "Reverse IV vs i-GaAs thickness\n"
    "Cylindrical R = 5 um"
)

plt.grid(True)

plt.legend(
    fontsize=8,
    ncol=2
)

plt.tight_layout()

reverse_plot = (
    summary_folder
    / "reverse_thickness_sweep.png"
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
print("i-GaAs THICKNESS SWEEP SUMMARY")
print("=" * 88)

header = (
    f"{'Change':>9}"
    f"{'t_i, nm':>12}"
    f"{'K+':>14}"
    f"{'K-':>14}"
    f"{'K-/K+':>12}"
    f"{'R2+':>12}"
    f"{'R2-':>12}"
)

print(header)

print("-" * 88)


for result in results:

    if result["status"] != "OK":

        print(
            f"{result['change_pct']:>+8.0f}%"
            f"{result['t_i_gaas_nm']:>12.1f}"
            f"{'FAILED':>14}"
        )

        continue

    print(
        f"{result['change_pct']:>+8.0f}%"
        f"{result['t_i_gaas_nm']:>12.1f}"
        f"{result['K_forward']:>14.3f}"
        f"{result['K_reverse']:>14.3f}"
        f"{result['K_ratio']:>12.3f}"
        f"{result['r2_forward']:>12.6f}"
        f"{result['r2_reverse']:>12.6f}"
    )


print()
print("Summary:")
print(csv_path)

print()
print("Forward IV plot:")
print(forward_plot)

print()
print("Reverse IV plot:")
print(reverse_plot)