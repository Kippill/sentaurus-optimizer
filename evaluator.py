from pathlib import Path
from datetime import datetime
import json
import numpy as np

from template_manager import save_rendered_template

from sentaurus_runner import (
    get_next_run_id,
    run_sentaurus,
)

from iv_reader import (
    read_iv,
    read_experimental_iv,
)

from metrics import compare_branch

from plotting import (
    plot_branch,
    plot_branch_scaled,
)


def _short_metrics(result):
    """
    Оставляет только численные метрики,
    без массивов V/I.
    """

    return {
        "points": result["points"],
        "pearson": result["pearson"],
        "K": result["K"],
        "r2_scaled": result["r2_scaled"],
        "origin_slope": result["origin_slope"],
        "origin_intercept": result["origin_intercept"],
        "origin_r2": result["origin_r2"],
    }


def evaluate_structure(
    params,
    experiment_file="data/experimental_iv.csv"
):
    """
    Полный цикл одного расчёта:

    params
        ->
    SDE/SDevice templates
        ->
    Sentaurus
        ->
    Inspect
        ->
    IV
        ->
    comparison with experiment
        ->
    metrics + plots
        ->
    result dictionary
    """

    # ========================================================
    # 1. AUTOMATIC RUN ID
    # ========================================================

    run_id = get_next_run_id()

    run_name = (
        f"run_{run_id:04d}"
    )

    today = datetime.now().strftime(
        "%Y-%m-%d"
    )

    run_folder = (
        Path("results")
        / today
        / run_name
    )

    run_folder.mkdir(
        parents=True,
        exist_ok=False
    )

    print()
    print("=" * 60)
    print("EVALUATE STRUCTURE")
    print("=" * 60)
    print("Run:", run_name)

    # ========================================================
    # 2. SAVE PARAMETERS
    # ========================================================

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

    # ========================================================
    # 3. SDE REPLACEMENTS
    # ========================================================

    sde_replacements = {

        "MESH_IGAAS_MAXY": 
            params.get(
                "mesh_igaas_maxy_um",
                0.010,
            ),

        "MESH_IGAAS_MINY": 
            params.get(
                "mesh_igaas_miny_um",
                0.001,
            ),

        "MESH_BARRIER_MAXY":
            params.get(
                "mesh_barrier_maxy_um",
                0.00050
            ),

        "MESH_BARRIER_MINY":
            params.get(
                "mesh_barrier_miny_um",
                0.00010
            ),

        "MESH_P_MAXY":
            params.get(
                "mesh_p_maxy_um",
                0.00040
            ),

        "MESH_P_MINY":
            params.get(
                "mesh_p_miny_um",
                0.00010
            ),

        "WIDTH_UM":
            params["width_um"],

        "T_NTOP_UM":
            params["t_n_top_nm"] / 1000.0,

        "T_NINGAAS_UM":
            params["t_n_ingaas_nm"] / 1000.0,

        "T_IINGAAS_UM":
            params["t_i_ingaas_nm"] / 1000.0,

        "T_P_UM":
            params["t_p_nm"] / 1000.0,

        "T_IGAAS_UM":
            params["t_i_gaas_nm"] / 1000.0,

        "T_NBOTTOM_UM":
            params["t_n_bottom_nm"] / 1000.0,

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

    # ========================================================
    # 4. SDEVICE REPLACEMENTS
    # ========================================================

    geometry_mode = params.get(
        "geometry_mode",
        "planar_fast"
    )

    sdevice_replacements = {

        "GA_FRACTION":
            params["ga_fraction"],

        "V_FORWARD":
            params["v_forward"],

        "V_REVERSE":
            params["v_reverse"],

        "THERMIONIC":
            (
                "Thermionic"
                if params.get("thermionic", False)
                else ""
            ),

        "BGN_MODEL":
            params.get(
                "bgn_model",
                "OldSlotboom"
            ),
        "GEOMETRY_OPTION":
            (
                "Cylindrical"
                if geometry_mode == "cylindrical"
                else ""
            ),
    }

    # ========================================================
    # 5. RENDER CMD FILES
    # ========================================================

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

    # ========================================================
    # 6. RUN SENTAURUS
    # ========================================================

    sentaurus_result = run_sentaurus(

        run_name=run_name,

        local_run_folder=run_folder,

        sde_file=generated_sde,

        sdevice_file=generated_sdevice,

        inspect_file=(
            Path("templates")
            / "extract_iv.cmd"
        )
    )

    # ========================================================
    # 7. READ RAW TCAD IV
    # ========================================================

    V_forward, I_forward_raw = read_iv(
        sentaurus_result["forward_file"]
    )

    V_reverse, I_reverse_raw = read_iv(
        sentaurus_result["reverse_file"]
    )

    # ========================================================
    # 8. GEOMETRY SCALING
    # ========================================================
    #
    # planar_fast:
    #
    # Sentaurus 2D planar current corresponds approximately
    # to width_um x 1 um.
    #
    # We convert it to the current of the target circular
    # device with radius target_radius_um.
    #
    # cylindrical:
    #
    # Current already corresponds to the full device,
    # therefore scale = 1.
    # ========================================================

# ============================================================
# GEOMETRY CURRENT SCALING
# ============================================================

    geometry_mode = params.get(
        "geometry_mode",
        "planar_fast"
    )

    target_radius_um = params[
        "target_radius_um"
    ]


    if geometry_mode == "planar_fast":

        # Standard 2D planar model:
        # width_um x 1 um effective depth

        simulation_area_um2 = (
            params["width_um"] * 1.0
        )

        target_area_um2 = (
            np.pi * target_radius_um ** 2
        )

        area_scale = (
            target_area_um2
            / simulation_area_um2
        )


    elif geometry_mode == "cylindrical":

        # In cylindrical mode:
        # x = 0 ... R
        # width_um is the simulated radius

        simulation_radius_um = params[
            "width_um"
        ]

        simulation_area_um2 = (
            np.pi
            * simulation_radius_um ** 2
        )

        target_area_um2 = (
            np.pi
            * target_radius_um ** 2
        )

        area_scale = (
            target_area_um2
            / simulation_area_um2
        )


    else:

        raise ValueError(
            "Unknown geometry_mode: "
            + str(geometry_mode)
        )


    print(
        "Geometry current scale =",
        area_scale
    )


    # Scale simulated terminal current
    # to the target physical device area

    I_forward_device = (
        I_forward_raw * area_scale
    )

    I_reverse_device = (
        I_reverse_raw * area_scale
    )


    # ============================================================
    # EXPERIMENT
    # ============================================================

    print(
        "Reading experimental IV..."
    )

    V_exp, I_exp = read_experimental_iv(
        experiment_file
    )

    forward_mask = V_exp > 0
    reverse_mask = V_exp < 0

    V_exp_forward = (
        V_exp[forward_mask]
    )

    I_exp_forward = (
        I_exp[forward_mask]
    )

    V_exp_reverse = (
        V_exp[reverse_mask]
    )

    I_exp_reverse = (
        I_exp[reverse_mask]
    )

    # ========================================================
    # 10. RAW PLANAR METRICS
    # ========================================================

    raw_forward = compare_branch(
        V_forward,
        I_forward_raw,
        V_exp_forward,
        I_exp_forward
    )

    raw_reverse = compare_branch(
        V_reverse,
        I_reverse_raw,
        V_exp_reverse,
        I_exp_reverse
    )

    # ========================================================
    # 11. DEVICE-SCALED METRICS
    # ========================================================

    forward = compare_branch(
        V_forward,
        I_forward_device,
        V_exp_forward,
        I_exp_forward
    )

    reverse = compare_branch(
        V_reverse,
        I_reverse_device,
        V_exp_reverse,
        I_exp_reverse
    )

    k_ratio = abs(
        reverse["K"]
        / forward["K"]
    )

    # ========================================================
    # 12. SAVE METRICS
    # ========================================================

    metrics_summary = {

        "run_id": run_id,

        "run_name": run_name,

        "geometry": {
            "mode": geometry_mode,
            "simulation_width_um":
                params["width_um"],
            "target_radius_um":
                params.get(
                    "target_radius_um"
                ),
            "current_area_scale":
                float(area_scale),
        },

        "raw_model": {
            "forward":
                _short_metrics(
                    raw_forward
                ),
            "reverse":
                _short_metrics(
                    raw_reverse
                ),
        },

        "device_scaled": {
            "forward":
                _short_metrics(
                    forward
                ),
            "reverse":
                _short_metrics(
                    reverse
                ),
            "K_reverse_over_forward":
                float(k_ratio),
        },
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

    # ========================================================
    # 13. PLOTS
    # ========================================================

    plot_branch(
        forward,
        "Forward branch — device area",
        run_folder
        / "forward_raw.png"
    )

    plot_branch_scaled(
        forward,
        "Forward branch — device area",
        run_folder
        / "forward_scaled.png"
    )

    plot_branch(
        reverse,
        "Reverse branch — device area",
        run_folder
        / "reverse_raw.png"
    )

    plot_branch_scaled(
        reverse,
        "Reverse branch — device area",
        run_folder
        / "reverse_scaled.png"
    )

    # ========================================================
    # 14. PRINT RESULT
    # ========================================================

    print()
    print("=" * 60)
    print("EVALUATION RESULTS")
    print("=" * 60)

    print()
    print("RAW SIMULATION")

    print(
        "K forward =",
        raw_forward["K"]
    )

    print(
        "K reverse =",
        raw_reverse["K"]
    )

    print()
    print("SCALED TO TARGET DEVICE")

    print(
        "Pearson forward =",
        forward["pearson"]
    )

    print(
        "K forward       =",
        forward["K"]
    )

    print(
        "Pearson reverse =",
        reverse["pearson"]
    )

    print(
        "K reverse       =",
        reverse["K"]
    )

    print(
        "K reverse / forward =",
        k_ratio
    )

    print()
    print(
        "Results:",
        run_folder
    )

    # ========================================================
    # 15. RETURN API RESULT
    # ========================================================

    return {
        "run_id": run_id,
        "run_name": run_name,
        "run_folder": str(run_folder),

        "area_scale":
            float(area_scale),

        "pearson_forward":
            forward["pearson"],

        "pearson_reverse":
            reverse["pearson"],

        "K_forward":
            forward["K"],

        "K_reverse":
            reverse["K"],

        "K_ratio":
            float(k_ratio),

        "r2_forward":
            forward["r2_scaled"],

        "r2_reverse":
            reverse["r2_scaled"],
    }