from pathlib import Path
from datetime import datetime
import json


RESULTS_DIR = Path("results")


def create_run_folder(run_id, params):
    """
    Создаёт отдельную папку для одного расчёта.
    """

    date_string = datetime.now().strftime("%Y-%m-%d")

    day_folder = RESULTS_DIR / date_string
    day_folder.mkdir(parents=True, exist_ok=True)

    folder_name = (
        f"run_{run_id:04d}"
        f"_tp{params['t_p_nm']:.2f}"
        f"_Na{params['Na_p']:.2e}"
        f"_ti{params['t_i_ingaas_nm']:.2f}"
        f"_tn{params['t_n_ingaas_nm']:.2f}"
    )

    run_folder = day_folder / folder_name

    run_folder.mkdir(
        parents=True,
        exist_ok=False
    )

    return run_folder


def save_parameters(run_folder, params):
    """
    Сохраняет параметры одновременно в JSON и TXT.
    """

    # Машиночитаемый вариант
    json_path = run_folder / "parameters.json"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(
            params,
            f,
            indent=4,
            ensure_ascii=False
        )

    # Удобный человеку вариант
    txt_path = run_folder / "parameters.txt"

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("SENTAURUS STRUCTURE PARAMETERS\n")
        f.write("=" * 50 + "\n\n")

        for key, value in params.items():
            f.write(f"{key} = {value}\n")


def save_metadata(run_folder, metadata):
    """
    Сохраняет служебную информацию о расчёте.
    """

    metadata = metadata.copy()

    metadata["created"] = datetime.now().isoformat(
        timespec="seconds"
    )

    path = run_folder / "metadata.json"

    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            metadata,
            f,
            indent=4,
            ensure_ascii=False
        )