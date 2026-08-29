from pathlib import Path
import subprocess

from config import VM, REMOTE_PROJECT


def _run_process(args, timeout=None):
    """
    Запускает локальный процесс Windows:
    ssh, scp и т.п.
    """

    return subprocess.run(
        args,
        capture_output=True,
        text=True,
        timeout=timeout,
        encoding="utf-8",
        errors="replace"
    )


def remote(command, timeout=None):
    """
    Выполняет команду внутри Linux VM
    в папке Sentaurus-проекта.
    """

    full_command = (
        f"cd {REMOTE_PROJECT} && {command}"
    )

    return _run_process(
        [
            "ssh",
            VM,
            full_command
        ],
        timeout=timeout
    )


def upload_file(local_path, remote_name=None):
    """
    Копирует локальный файл Windows -> VM.
    """

    local_path = Path(local_path)

    if remote_name is None:
        remote_name = local_path.name

    destination = (
        f"{VM}:{REMOTE_PROJECT}/{remote_name}"
    )

    result = _run_process(
        [
            "scp",
            str(local_path),
            destination
        ]
    )

    if result.returncode != 0:
        raise RuntimeError(
            "SCP upload failed:\n"
            + result.stderr
        )


def download_file(remote_name, local_path):
    """
    Копирует файл VM -> Windows.
    """

    local_path = Path(local_path)

    local_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    source = (
        f"{VM}:{REMOTE_PROJECT}/{remote_name}"
    )

    result = _run_process(
        [
            "scp",
            source,
            str(local_path)
        ]
    )

    if result.returncode != 0:
        raise RuntimeError(
            "SCP download failed:\n"
            + result.stderr
        )


def extract_iv(output_folder):
    """
    Извлекает уже рассчитанную ВАХ
    из pos/neg .plt через Sentaurus Inspect.
    """

    output_folder = Path(output_folder)

    output_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    # Отправляем Inspect-скрипт
    upload_file(
        "templates/extract_iv.cmd",
        "extract_iv.cmd"
    )

    print("Running Inspect...")

    result = remote(
        "DISPLAY=:0.0 inspect -f extract_iv.cmd",
        timeout=120
    )   

    if result.returncode != 0:
        raise RuntimeError(
            "Inspect failed.\n\n"
            "STDOUT:\n"
            + result.stdout
            + "\nSTDERR:\n"
            + result.stderr
        )

    print("Inspect finished.")

    forward_local = (
        output_folder / "model_forward.txt"
    )

    reverse_local = (
        output_folder / "model_reverse.txt"
    )

    download_file(
        "model_forward.txt",
        forward_local
    )

    download_file(
        "model_reverse.txt",
        reverse_local
    )

    return forward_local, reverse_local