from evaluator import evaluate_structure

import csv
import json
from pathlib import Path
from datetime import datetime


# ============================================================
# BASE STRUCTURE
# ============================================================

BASE_PARAMS = {

    # --------------------------------------------------------
    # GEOMETRY
    # --------------------------------------------------------

    "geometry_mode": "cylindrical",

    # In Cylindrical mode width_um = RADIUS
    "width_um": 5.0,

    # Experimental diode:
    # diameter = 100 um -> radius = 50 um
    "target_radius_um": 50.0,


    # --------------------------------------------------------
    # STRUCTURE
    # --------------------------------------------------------

    "t_n_top_nm": 400.0,
    "t_n_ingaas_nm": 5.0,
    "t_i_ingaas_nm": 5.0,
    "t_p_nm": 4.0,
    "t_i_gaas_nm": 350.0,
    "t_n_bottom_nm": 1000.0,

    "Nd_top": 5.0e18,
    "Nd_n_ingaas": 5.0e18,
    "Nd_i_ingaas": 1.0e14,
    "Na_p": 3.0e18,
    "Nd_i_gaas": 1.0e14,
    "Nd_bottom": 5.0e18,

    "ga_fraction": 0.75,


    # --------------------------------------------------------
    # IV
    # --------------------------------------------------------

    "v_forward": 1.5,
    "v_reverse": -1.5,
}


# ============================================================
# PHYSICS VARIANTS
# ============================================================

PHYSICS_VARIANTS = {

    "baseline": {
        "thermionic": False,
        "bgn_model": "OldSlotboom",
    },

    "thermionic": {
        "thermionic": True,
        "bgn_model": "OldSlotboom",
    },

    "no_bgn": {
        "thermionic": False,
        "bgn_model": "Nobandgapnarrowing",
    },

    "thermionic_no_bgn": {
        "thermionic": True,
        "bgn_model": "Nobandgapnarrowing",
    },
}


# ============================================================
# RUN
# ============================================================

results = []


for physics_name, physics_params in PHYSICS_VARIANTS.items():

    print()
    print("#" * 70)
    print(
        "CYLINDRICAL R=5 um | PHYSICS:",
        physics_name
    )
    print("#" * 70)

    params = BASE_PARAMS.copy()
    params.update(physics_params)

    params["physics_name"] = (
        physics_name + "_cyl_R5"
    )

    try:

        result = evaluate_structure(
            params
        )

        result["physics_name"] = physics_name
        result["status"] = "OK"

        results.append(result)

    except Exception as error:

        print()
        print("!!! RUN FAILED !!!")
        print("Physics:", physics_name)
        print("Error:", error)

        results.append({
            "physics_name": physics_name,
            "status": "FAILED",
            "error": str(error),
        })


# ============================================================
# SAVE SUMMARY
# ============================================================

today = datetime.now().strftime(
    "%Y-%m-%d"
)

summary_folder = (
    Path("results")
    / today
)

summary_folder.mkdir(
    parents=True,
    exist_ok=True
)


json_path = (
    summary_folder
    / "cyl_R5_physics_summary.json"
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


csv_path = (
    summary_folder
    / "cyl_R5_physics_summary.csv"
)

fieldnames = [
    "physics_name",
    "status",
    "run_id",
    "run_name",
    "area_scale",
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
# FINAL TABLE
# ============================================================

print()
print("=" * 82)
print("CYLINDRICAL R=5 um PHYSICS SUMMARY")
print("=" * 82)

header = (
    f"{'Physics':<24}"
    f"{'K+':>12}"
    f"{'K-':>12}"
    f"{'K-/K+':>12}"
    f"{'R2+':>11}"
    f"{'R2-':>11}"
)

print(header)
print("-" * 82)


for result in results:

    if result["status"] != "OK":

        print(
            f"{result['physics_name']:<24}"
            f"{'FAILED':>12}"
        )

        continue

    print(
        f"{result['physics_name']:<24}"
        f"{result['K_forward']:>12.3f}"
        f"{result['K_reverse']:>12.3f}"
        f"{result['K_ratio']:>12.3f}"
        f"{result['r2_forward']:>11.6f}"
        f"{result['r2_reverse']:>11.6f}"
    )


print()
print("Summary JSON:")
print(json_path)

print()
print("Summary CSV:")
print(csv_path)