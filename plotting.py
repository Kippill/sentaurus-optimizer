from pathlib import Path
import matplotlib.pyplot as plt


def plot_branch(
    result,
    title,
    output_path
):
    output_path = Path(output_path)

    plt.figure(figsize=(8, 6))

    plt.plot(
        result["voltage"],
        result["experiment"],
        "o-",
        label="Experiment"
    )

    plt.plot(
        result["voltage"],
        result["model"],
        "-",
        label="TCAD raw"
    )

    plt.xlabel("Voltage, V")
    plt.ylabel("Current, A")

    plt.title(
        f"{title}\n"
        f"Pearson = {result['pearson']:.6f}, "
        f"K = {result['K']:.4g}"
    )

    plt.grid(True)
    plt.legend()
    plt.tight_layout()

    plt.savefig(
        output_path,
        dpi=200
    )

    plt.close()


def plot_branch_scaled(
    result,
    title,
    output_path
):
    output_path = Path(output_path)

    plt.figure(figsize=(8, 6))

    plt.plot(
        result["voltage"],
        result["experiment"],
        "o-",
        label="Experiment"
    )

    plt.plot(
        result["voltage"],
        result["model_scaled"],
        "-",
        label="TCAD / K"
    )

    plt.xlabel("Voltage, V")
    plt.ylabel("Current, A")

    plt.title(
        f"{title} — scaled\n"
        f"Pearson = {result['pearson']:.6f}, "
        f"R² scaled = "
        f"{result['r2_scaled']:.6f}, "
        f"K = {result['K']:.4g}"
    )

    plt.grid(True)
    plt.legend()
    plt.tight_layout()

    plt.savefig(
        output_path,
        dpi=200
    )

    plt.close()