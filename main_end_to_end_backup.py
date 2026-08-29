from pathlib import Path
from datetime import datetime
import json

from template_manager import (
    save_rendered_template
)

from sentaurus_runner import (
    run_sentaurus
)

from iv_reader import (
    read_iv,
    read_experimental_iv
)

from metrics import compare_branch

from plotting import (
    plot_branch,
    plot_branch_scaled
)

import numpy as np


# ============================================================
# RUN
# ============================================================

RUN_ID = 1
RUN_NAME = f"run_{RUN_ID:04d}"

today = datetime.now().strftime(
    "%Y-%m-%d"
)

run_folder = (
    Path("results")
    / today
    / RUN_NAME
)

run_folder.mkdir(
    parents=True,
    exist_ok=True
)


print("=" * 60)
print("AUTOMATIC SENTAURUS RUN")
print("=" * 60)
print("Run:", RUN_NAME)


# ============================================================
# PHYSICAL PARAMETERS
#
# Thicknesses below are in nm.
# ============================================================

params = {

    "width_um": 1.0,

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

    "v_forward": 1.5,
    "v_reverse": -1.5,
}


# ============================================================
# SAVE HUMAN PARAMETERS
# ============================================================

with open(
    run_folder / "parameters.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        params,
        f,
        indent=4,
        ensure_ascii=False
    )


# ============================================================
# TEMPLATE REPLACEMENTS
# ============================================================

sde_replacements = {

    "WIDTH_UM":
        params["width_um"],

    "T_NTOP_UM":
        params["t_n_top_nm"] / 1000,

    "T_NINGAAS_UM":
        params["t_n_ingaas_nm"] / 1000,

    "T_IINGAAS_UM":
        params["t_i_ingaas_nm"] / 1000,

    "T_P_UM":
        params["t_p_nm"] / 1000,

    "T_IGAAS_UM":
        params["t_i_gaas_nm"] / 1000,

    "T_NBOTTOM_UM":
        params["t_n_bottom_nm"] / 1000,

    "ND_TOP":
        params["Nd_top"],

    "ND_NINGAAS":
        params["Nd_n_ingaas"],

    "ND_IINGAAS":
        params["Nd_i_ingaas"],

    "NA_P":
        params["Na_p"],

    "ND_IGAAS":
        params["Nd_i_gaas"],

    "ND_BOTTOM":
        params["Nd_bottom"],
}


sdevice_replacements = {

    "GA_FRACTION":
        params["ga_fraction"],

    "V_FORWARD":
        params["v_forward"],

    "V_REVERSE":
        params["v_reverse"],
}


# ============================================================
# RENDER REAL CMD FILES
# ============================================================

generated_sde = (
    run_folder
    / "input_sde.cmd"
)

generated_sdevice = (
    run_folder
    / "input_sdevice.cmd"
)


save_rendered_template(
    "hetero_sde_template.cmd",
    generated_sde,
    sde_replacements
)


save_rendered_template(
    "hetero_des_template.cmd",
    generated_sdevice,
    sdevice_replacements
)


print("Templates rendered.")


# ============================================================
# RUN SENTAURUS
# ============================================================

result = run_sentaurus(

    run_name=RUN_NAME,

    local_run_folder=run_folder,

    sde_file=generated_sde,

    sdevice_file=generated_sdevice,

    inspect_file=(
        Path("templates")
        / "extract_iv.cmd"
    )
)


# ============================================================
# READ RESULT
# ============================================================

V_forward, I_forward = read_iv(
    result["forward_file"]
)

V_reverse, I_reverse = read_iv(
    result["reverse_file"]
)


print()
print("=" * 60)
print("RESULT")
print("=" * 60)

print()
print("FORWARD")
print("points =", len(V_forward))
print("V =", V_forward.min(), "→", V_forward.max())
print("I =", I_forward.min(), "→", I_forward.max())

print()
print("REVERSE")
print("points =", len(V_reverse))
print("V =", V_reverse.min(), "→", V_reverse.max())
print("I =", I_reverse.min(), "→", I_reverse.max())

print()
print("Run folder:")
print(run_folder)

# ============================================================
# READ EXPERIMENT
# ============================================================

print()
print("Reading experimental IV...")

V_exp, I_exp = read_experimental_iv(
    "data/experimental_iv.csv"
)


# ============================================================
# SPLIT EXPERIMENT
# ============================================================

forward_mask = V_exp > 0
reverse_mask = V_exp < 0

V_exp_forward = V_exp[forward_mask]
I_exp_forward = I_exp[forward_mask]

V_exp_reverse = V_exp[reverse_mask]
I_exp_reverse = I_exp[reverse_mask]


# ============================================================
# COMPARE WITH EXPERIMENT
# ============================================================

forward_metrics = compare_branch(
    V_forward,
    I_forward,
    V_exp_forward,
    I_exp_forward
)

reverse_metrics = compare_branch(
    V_reverse,
    I_reverse,
    V_exp_reverse,
    I_exp_reverse
)


k_ratio = abs(
    reverse_metrics["K"]
    / forward_metrics["K"]
)


# ============================================================
# SAVE METRICS
# ============================================================

metrics_summary = {

    "forward": {
        "pearson":
            forward_metrics["pearson"],

        "K":
            forward_metrics["K"],

        "r2_scaled":
            forward_metrics["r2_scaled"],

        "origin_slope":
            forward_metrics["origin_slope"],

        "origin_intercept":
            forward_metrics["origin_intercept"],

        "origin_r2":
            forward_metrics["origin_r2"],
    },

    "reverse": {
        "pearson":
            reverse_metrics["pearson"],

        "K":
            reverse_metrics["K"],

        "r2_scaled":
            reverse_metrics["r2_scaled"],

        "origin_slope":
            reverse_metrics["origin_slope"],

        "origin_intercept":
            reverse_metrics["origin_intercept"],

        "origin_r2":
            reverse_metrics["origin_r2"],
    },

    "K_reverse_over_forward":
        float(k_ratio),
}


with open(
    run_folder / "metrics.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        metrics_summary,
        f,
        indent=4,
        ensure_ascii=False
    )


# ============================================================
# PLOTS
# ============================================================

plot_branch(
    forward_metrics,
    "Forward branch",
    run_folder / "forward_raw.png"
)

plot_branch_scaled(
    forward_metrics,
    "Forward branch",
    run_folder / "forward_scaled.png"
)

plot_branch(
    reverse_metrics,
    "Reverse branch",
    run_folder / "reverse_raw.png"
)

plot_branch_scaled(
    reverse_metrics,
    "Reverse branch",
    run_folder / "reverse_scaled.png"
)


# ============================================================
# PRINT CALIBRATION RESULTS
# ============================================================

print()
print("=" * 60)
print("AUTOMATIC CALIBRATION")
print("=" * 60)

print()
print("FORWARD")
print(
    f"Pearson      = "
    f"{forward_metrics['pearson']:.6f}"
)
print(
    f"K            = "
    f"{forward_metrics['K']:.6g}"
)
print(
    f"Origin slope = "
    f"{forward_metrics['origin_slope']:.6g}"
)
print(
    f"Scaled R2    = "
    f"{forward_metrics['r2_scaled']:.6f}"
)

print()
print("REVERSE")
print(
    f"Pearson      = "
    f"{reverse_metrics['pearson']:.6f}"
)
print(
    f"K            = "
    f"{reverse_metrics['K']:.6g}"
)
print(
    f"Origin slope = "
    f"{reverse_metrics['origin_slope']:.6g}"
)
print(
    f"Scaled R2    = "
    f"{reverse_metrics['r2_scaled']:.6f}"
)

print()
print(
    "K reverse / forward =",
    k_ratio
)