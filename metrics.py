import numpy as np
from scipy.stats import pearsonr


def interpolate_model(v_model, i_model, v_exp):
    """
    Интерполирует TCAD-ток на напряжения экспериментальных точек.
    Используются только точки внутри диапазона TCAD.
    """

    order = np.argsort(v_model)

    v_model = np.asarray(v_model)[order]
    i_model = np.asarray(i_model)[order]
    v_exp = np.asarray(v_exp)

    mask = (
        (v_exp >= v_model.min()) &
        (v_exp <= v_model.max())
    )

    v_common = v_exp[mask]

    i_interp = np.interp(
        v_common,
        v_model,
        i_model
    )

    return mask, v_common, i_interp


def zero_offset_scale(i_model, i_exp):
    """
    K в определении:

        I_TCAD ≈ K * I_EXP

    Идеальный результат: K = 1.
    """

    denominator = np.dot(i_exp, i_exp)

    if denominator == 0:
        return np.nan

    return np.dot(i_exp, i_model) / denominator


def affine_fit(i_model, i_exp):
    """
    Подгонка:
        I_TCAD = intercept + slope * I_EXP

    Это аналог линейной регрессии в Origin.
    """

    slope, intercept = np.polyfit(
        i_exp,
        i_model,
        1
    )

    return slope, intercept


def r_squared(y_true, y_pred):
    ss_res = np.sum(
        (y_true - y_pred) ** 2
    )

    ss_tot = np.sum(
        (y_true - np.mean(y_true)) ** 2
    )

    if ss_tot == 0:
        return np.nan

    return 1.0 - ss_res / ss_tot


def compare_branch(
    v_model,
    i_model,
    v_exp,
    i_exp
):
    """
    Сравнение одной ветви TCAD и эксперимента.
    """

    mask, v_common, i_model_interp = interpolate_model(
        v_model,
        i_model,
        v_exp
    )

    i_exp_common = np.asarray(i_exp)[mask]

    if len(v_common) < 3:
        raise ValueError(
            "Недостаточно общих точек "
            "TCAD и эксперимента."
        )

    # Pearson
    pearson, _ = pearsonr(
        i_model_interp,
        i_exp_common
    )

    # Физически понятный коэффициент:
    # I_TCAD ≈ K * I_EXP
    k = zero_offset_scale(
        i_model_interp,
        i_exp_common
    )

    # TCAD, приведённый к масштабу эксперимента
    if np.isfinite(k) and k != 0:
        i_model_scaled = (
            i_model_interp / k
        )
    else:
        i_model_scaled = (
            i_model_interp.copy()
        )

    r2_scaled = r_squared(
        i_exp_common,
        i_model_scaled
    )

    # Аналог Origin:
    slope, intercept = affine_fit(
        i_model_interp,
        i_exp_common
    )

    i_affine = (
        intercept +
        slope * i_exp_common
    )

    r2_affine = r_squared(
        i_model_interp,
        i_affine
    )

    return {
        "voltage": v_common,
        "experiment": i_exp_common,
        "model": i_model_interp,
        "model_scaled": i_model_scaled,

        "pearson": float(pearson),

        "K": float(k),

        "r2_scaled": float(r2_scaled),

        "origin_slope": float(slope),
        "origin_intercept": float(intercept),
        "origin_r2": float(r2_affine),

        "points": int(len(v_common)),
    }