from pathlib import Path
import subprocess
import shutil
import re


VM = "sentaurus-vm"

REMOTE_PROJECT = (
    "/home/student/sentaurus/"
    "diod_heterostructure_1"
)

REMOTE_RUNS = f"{REMOTE_PROJECT}/auto_runs"


# ============================================================
# BASIC PROCESS
# ============================================================

def run_process(args, timeout=None):
    result = subprocess.run(
        args,
        capture_output=True,
        text=True,
        timeout=timeout,
        encoding="utf-8",
        errors="replace"
    )

    return result


def run_remote(remote_dir, command, timeout=None):
    """
    Выполнить команду внутри конкретной папки VM.
    """

    full_command = (
        f"cd {remote_dir} && {command}"
    )

    result = run_process(
        ["ssh", VM, full_command],
        timeout=timeout
    )

    return result


# ============================================================
# RUN FOLDERS
# ============================================================

def get_next_run_id():
    """
    Находит следующий свободный глобальный run ID
    по папкам на VM.

    run_0001
    run_0002
    ...
    """

    result = run_process([
        "ssh",
        VM,
        f"mkdir -p {REMOTE_RUNS} && ls -1 {REMOTE_RUNS}"
    ])

    if result.returncode != 0:
        raise RuntimeError(
            "Cannot read remote runs:\n"
            + result.stderr
        )

    run_ids = []

    for name in result.stdout.splitlines():

        match = re.fullmatch(
            r"run_(\d+)",
            name.strip()
        )

        if match:
            run_ids.append(
                int(match.group(1))
            )

    if not run_ids:
        return 1

    return max(run_ids) + 1

def create_remote_run(run_name):
    """
    Создаёт отдельную папку расчёта на VM.

    Важно:
    если папка уже существует, функция выдаст ошибку,
    чтобы случайно не затереть старый расчёт.
    """

    remote_dir = f"{REMOTE_RUNS}/{run_name}"

    result = run_process([
        "ssh",
        VM,
        f"mkdir {remote_dir}"
    ])

    if result.returncode != 0:
        raise RuntimeError(
            f"Cannot create remote run folder:\n"
            f"{remote_dir}\n\n"
            f"STDERR:\n{result.stderr}"
        )

    return remote_dir


# ============================================================
# FILE TRANSFER
# ============================================================

def upload_file(
    local_path,
    remote_dir,
    remote_name=None
):
    local_path = Path(local_path)

    if remote_name is None:
        remote_name = local_path.name

    destination = (
        f"{VM}:{remote_dir}/{remote_name}"
    )

    result = run_process([
        "scp",
        str(local_path),
        destination
    ])

    if result.returncode != 0:
        raise RuntimeError(
            "SCP upload failed:\n"
            + result.stderr
        )


def download_file(
    remote_dir,
    remote_name,
    local_path
):
    local_path = Path(local_path)

    local_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    source = (
        f"{VM}:{remote_dir}/{remote_name}"
    )

    result = run_process([
        "scp",
        source,
        str(local_path)
    ])

    if result.returncode != 0:
        raise RuntimeError(
            "SCP download failed:\n"
            + result.stderr
        )


# ============================================================
# SENTAURUS
# ============================================================

def run_sde(remote_dir):
    print("Running SDE...")

    result = run_remote(
        remote_dir,
        "sde -e -l model_sde.cmd",
        timeout=1800
    )

    if result.returncode != 0:
        raise RuntimeError(
            "SDE failed.\n\n"
            "STDOUT:\n"
            + result.stdout
            + "\nSTDERR:\n"
            + result.stderr
        )

    print("SDE finished.")

    return result


def run_sdevice(remote_dir):
    print("Running SDevice...")

    result = run_remote(
        remote_dir,
        "sdevice model_des.cmd",
        timeout=7200
    )

    if result.returncode != 0:
        raise RuntimeError(
            "SDevice failed.\n\n"
            "STDOUT:\n"
            + result.stdout
            + "\nSTDERR:\n"
            + result.stderr
        )

    print("SDevice finished.")

    return result


# ============================================================
# INSPECT
# ============================================================

def run_inspect(remote_dir):
    print("Running Inspect...")

    result = run_remote(
        remote_dir,
        "DISPLAY=:0.0 inspect -f extract_iv.cmd",
        timeout=300
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

    return result


# ============================================================
# COMPLETE SENTARUS RUN
# ============================================================

def run_sentaurus(
    run_name,
    local_run_folder,
    sde_file,
    sdevice_file,
    inspect_file
):
    """
    Полный автоматический цикл одного расчёта:

    Windows
        ->
    отдельная папка на VM
        ->
    SDE
        ->
    SDevice
        ->
    Inspect
        ->
    скачивание результатов обратно на Windows

    Каждый run работает в собственной папке.
    """

    local_run_folder = Path(
        local_run_folder
    )

    local_run_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    # ========================================================
    # 1. CREATE REMOTE RUN FOLDER
    # ========================================================

    remote_dir = create_remote_run(
        run_name
    )

    print(
        "Remote run folder:",
        remote_dir
    )

    # ========================================================
    # 2. UPLOAD INPUT FILES
    # ========================================================

    print("Uploading input files...")

    upload_file(
        sde_file,
        remote_dir,
        "model_sde.cmd"
    )

    upload_file(
        sdevice_file,
        remote_dir,
        "model_des.cmd"
    )

    upload_file(
        inspect_file,
        remote_dir,
        "extract_iv.cmd"
    )

    print("Input files uploaded.")

    # ========================================================
    # 3. RUN SDE
    # ========================================================

    sde_result = run_sde(
        remote_dir
    )

    # Сохраняем консольный вывод SDE на Windows
    sde_console_file = (
        local_run_folder
        / "sde_console.txt"
    )

    sde_console_file.write_text(
        sde_result.stdout
        + "\n"
        + sde_result.stderr,
        encoding="utf-8"
    )

    # ========================================================
    # 4. RUN SDEVICE
    # ========================================================

    sdevice_result = run_sdevice(
        remote_dir
    )

    # Сохраняем консольный вывод SDevice на Windows
    sdevice_console_file = (
        local_run_folder
        / "sdevice_console.txt"
    )

    sdevice_console_file.write_text(
        sdevice_result.stdout
        + "\n"
        + sdevice_result.stderr,
        encoding="utf-8"
    )

    # ========================================================
    # 5. RUN INSPECT
    # ========================================================

    inspect_result = run_inspect(
        remote_dir
    )

    inspect_console_file = (
        local_run_folder
        / "inspect_console.txt"
    )

    inspect_console_file.write_text(
        inspect_result.stdout
        + "\n"
        + inspect_result.stderr,
        encoding="utf-8"
    )

    # ========================================================
    # 6. DOWNLOAD REQUIRED IV FILES
    # ========================================================

    print("Downloading IV files...")

    forward_local = (
        local_run_folder
        / "model_forward.txt"
    )

    reverse_local = (
        local_run_folder
        / "model_reverse.txt"
    )

    # Эти два файла обязательны.
    # Если хотя бы одного нет — run действительно плохой.
    download_file(
        remote_dir,
        "model_forward.txt",
        forward_local
    )

    download_file(
        remote_dir,
        "model_reverse.txt",
        reverse_local
    )

    print("IV files downloaded.")

    # ========================================================
    # 7. DOWNLOAD SDEVICE LOG
    # ========================================================

    # У старого Sentaurus имя лога может отличаться.
    # Поэтому проверяем несколько возможных имён.
    #
    # Лог полезен, но отсутствие лога НЕ должно
    # убивать уже успешно рассчитанный run.

    print("Looking for SDevice log...")

    log_candidates = [
        "model_iv.log",
        "model_iv_des.log",
    ]

    downloaded_log = None

    for log_name in log_candidates:

        check = run_remote(
            remote_dir,
            f"test -f {log_name}"
        )

        if check.returncode == 0:

            local_log = (
                local_run_folder
                / log_name
            )

            download_file(
                remote_dir,
                log_name,
                local_log
            )

            downloaded_log = local_log

            print(
                "SDevice log downloaded:",
                log_name
            )

            break

    if downloaded_log is None:
        print(
            "WARNING: SDevice log was not found."
        )

    # ========================================================
    # 8. FINISH
    # ========================================================

    print()
    print("=" * 60)
    print("SENTAURUS RUN COMPLETED")
    print("=" * 60)

    print(
        "Remote folder:",
        remote_dir
    )

    print(
        "Local folder:",
        local_run_folder
    )

    # Возвращаем main.py пути к нужным файлам
    return {
        "remote_dir": remote_dir,
        "forward_file": forward_local,
        "reverse_file": reverse_local,
        "log_file": downloaded_log,
    }

