from evaluator import evaluate_structure


BASE = {
    # ========================================================
    # GEOMETRY
    # ========================================================

    "geometry_mode": "planar",
    "width_um": 0.001,

    # Для этого теста experimental scaling нам вообще не важен
    "target_radius_um": 5.0,

    # ========================================================
    # SERIE 3 STRUCTURE
    # ========================================================

    "t_n_top_nm": 400.0,
    "t_n_ingaas_nm": 5.0,
    "t_i_ingaas_nm": 5.0,
    "t_p_nm": 4.0,
    "t_i_gaas_nm": 350.0,
    "t_n_bottom_nm": 1000.0,


    # ========================================================
    # DOPING
    # ========================================================

    "Nd_top": 5.0e18,
    "Nd_n_ingaas": 5.0e18,

    "Nd_i_ingaas": 1.0e14,

    # Serie 3 / Table 4
    "Na_p": 3.0e18,

    "Nd_i_gaas": 1.0e14,
    "Nd_bottom": 5.0e18,


    # ========================================================
    # MATERIAL
    # ========================================================

    "ga_fraction": 0.75,


    # ========================================================
    # PHYSICS
    # ========================================================

    "thermionic": False,
    "bgn_model": "OldSlotboom",


    # ========================================================
    # NORMAL IV
    # ========================================================

    "v_forward": 1.5,
    "v_reverse": -2.0,


    # ========================================================
    # FIXED VERY-FINE MESH FOR THIN BARRIER REGION
    # ========================================================

    "mesh_barrier_maxy_um": 0.000125,
    "mesh_barrier_miny_um": 0.000025,

    "mesh_p_maxy_um": 0.000100,
    "mesh_p_miny_um": 0.000025,
}


# ============================================================
# i-GaAs BREAKDOWN MESH CONVERGENCE
# ============================================================

cases = [
    {
        "name": "serie2_breakdown_mesh_5nm",
        "maxy": 0.005,
        "miny": 0.001,
    },
    {
        "name": "serie2_breakdown_mesh_2p5nm",
        "maxy": 0.0025,
        "miny": 0.0005,
    },
    {
        "name": "serie2_breakdown_mesh_1p25nm",
        "maxy": 0.00125,
        "miny": 0.00025,
    },
]


for case in cases:

    params = dict(BASE)

    params["mesh_igaas_maxy_um"] = case["maxy"]
    params["mesh_igaas_miny_um"] = case["miny"]

    params["physics_name"] = case["name"]

    print()
    print("=" * 72)
    print(case["name"])
    print("=" * 72)

    print(
        "i-GaAs mesh: "
        f"MaxY = {case['maxy'] * 1000:.3f} nm, "
        f"MinY = {case['miny'] * 1000:.3f} nm"
    )

    result = evaluate_structure(params)

    print()
    print("RESULT:")
    print(result)