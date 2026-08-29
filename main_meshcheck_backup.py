from evaluator import evaluate_structure
from iv_reader import read_iv

from pathlib import Path
import numpy as np


# ============================================================
# EXISTING STANDARD-MESH RUNS
# ============================================================

STANDARD_RUNS = {

    5.0:
        Path(
            "results/2026-08-28/run_0033"
        ),

    8.0:
        Path(
            "results/2026-08-28/run_0034"
        ),
}


# ============================================================
# COMMON STRUCTURE
# ============================================================

BASE_PARAMS = {

    # geometry
    "geometry_mode": "cylindrical",
    "width_um": 5.0,
    "target_radius_um": 50.0,

    # structure
    "t_n_top_nm": 400.0,
    "t_n_ingaas_nm": 5.0,
    "t_i_ingaas_nm": 5.0,
    "t_p_nm": 4.0,
    "t_i_gaas_nm": 350.0,
    "t_n_bottom_nm": 1000.0,

    # doping
    "Nd_top": 5.0e18,
    "Nd_n_ingaas": 5.0e18,
    "Nd_i_ingaas": 1.0e14,
    "Na_p": 3.0e18,
    "Nd_i_gaas": 1.0e14,
    "Nd_bottom": 5.0e18,

    # material
    "ga_fraction": 0.75,

    # physics
    "thermionic": False,
    "bgn_model": "OldSlotboom",

    # IV
    "v_forward": 1.5,
    "v_reverse": -1.5,

    # ========================================================
    # FINE MESH
    # ========================================================

    "mesh_barrier_maxy_um": 0.000125,
    "mesh_barrier_miny_um": 0.000025,

    "mesh_p_maxy_um": 0.000100,
    "mesh_p_miny_um": 0.000025,
}


# ============================================================
# HELPER
# ============================================================

def current_at_voltage(
    file_path,
    voltage
):

    V, I = read_iv(
        file_path
    )

    order = np.argsort(V)

    return float(
        np.interp(
            voltage,
            V[order],
            I[order]
        )
    )


# ============================================================
# RUN 5 nm AND 8 nm
# ============================================================

results = []


for thickness_nm in [5.0, 8.0]:

    print()
    print("#" * 70)
    print(
        f"FINE MESH CHECK | "
        f"i-InGaAs = {thickness_nm:.1f} nm"
    )
    print("#" * 70)

    params = BASE_PARAMS.copy()

    params[
        "t_i_ingaas_nm"
    ] = thickness_nm

    params[
        "physics_name"
    ] = (
        f"meshcheck_"
        f"iInGaAs_{thickness_nm:.0f}nm"
    )

    # --------------------------------------------------------
    # NEW FINE-MESH RUN
    # --------------------------------------------------------

    fine_result = evaluate_structure(
        params
    )

    fine_folder = Path(
        fine_result["run_folder"]
    )

    # --------------------------------------------------------
    # EXISTING STANDARD-MESH RUN
    # --------------------------------------------------------

    standard_folder = (
        STANDARD_RUNS[
            thickness_nm
        ]
    )

    # --------------------------------------------------------
    # +1 V
    # --------------------------------------------------------

    I_std_forward = (
        current_at_voltage(
            standard_folder
            / "model_forward.txt",
            1.0
        )
    )

    I_fine_forward = (
        current_at_voltage(
            fine_folder
            / "model_forward.txt",
            1.0
        )
    )

    forward_error_pct = (
        100.0
        * (
            I_fine_forward
            - I_std_forward
        )
        / I_std_forward
    )

    # --------------------------------------------------------
    # -1 V
    # --------------------------------------------------------

    I_std_reverse = (
        current_at_voltage(
            standard_folder
            / "model_reverse.txt",
            -1.0
        )
    )

    I_fine_reverse = (
        current_at_voltage(
            fine_folder
            / "model_reverse.txt",
            -1.0
        )
    )

    reverse_error_pct = (
        100.0
        * (
            abs(I_fine_reverse)
            - abs(I_std_reverse)
        )
        / abs(I_std_reverse)
    )

    results.append({

        "thickness_nm":
            thickness_nm,

        "I_std_forward":
            I_std_forward,

        "I_fine_forward":
            I_fine_forward,

        "forward_error_pct":
            forward_error_pct,

        "I_std_reverse":
            I_std_reverse,

        "I_fine_reverse":
            I_fine_reverse,

        "reverse_error_pct":
            reverse_error_pct,

        "run_name":
            fine_result["run_name"],
    })


# ============================================================
# SUMMARY
# ============================================================

print()
print("=" * 100)
print("MESH CONVERGENCE CHECK")
print("=" * 100)

print(
    f"{'t, nm':>8}"
    f"{'I+ std':>16}"
    f"{'I+ fine':>16}"
    f"{'dI+ %':>12}"
    f"{'I- std':>16}"
    f"{'I- fine':>16}"
    f"{'dI- %':>12}"
)

print("-" * 100)


for r in results:

    print(
        f"{r['thickness_nm']:>8.1f}"
        f"{r['I_std_forward']:>16.6e}"
        f"{r['I_fine_forward']:>16.6e}"
        f"{r['forward_error_pct']:>12.3f}"
        f"{r['I_std_reverse']:>16.6e}"
        f"{r['I_fine_reverse']:>16.6e}"
        f"{r['reverse_error_pct']:>12.3f}"
    )