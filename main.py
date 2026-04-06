from pathlib import Path
import subprocess
import sys
import time


ROOT_DIR = Path(__file__).resolve().parent
MAIN_FILE = Path(__file__).resolve()


def find_target_scripts() -> list[Path]:
    scripts = []
    for path in ROOT_DIR.rglob("*.py"):
        if path.resolve() == MAIN_FILE:
            continue
        scripts.append(path.resolve())
    return sorted(scripts)


def launch_script(script_path: Path) -> subprocess.Popen:
    return subprocess.Popen(
        [sys.executable, script_path.name],
        cwd=str(script_path.parent),
    )


def wait_for_processes(process_map: dict[Path, subprocess.Popen]) -> None:
    remaining = dict(process_map)
    while remaining:
        finished = []
        for script_path, process in remaining.items():
            exit_code = process.poll()
            if exit_code is None:
                continue
            print(f"[EXIT] {script_path.relative_to(ROOT_DIR)} (code={exit_code})")
            finished.append(script_path)

        for script_path in finished:
            remaining.pop(script_path, None)

        if remaining:
            time.sleep(0.5)


def terminate_processes(process_map: dict[Path, subprocess.Popen]) -> None:
    for process in process_map.values():
        if process.poll() is None:
            process.terminate()


def main() -> int:
    scripts = find_target_scripts()
    if not scripts:
        print("No Python scripts found to run.")
        return 1

    print("Starting scripts:")
    for script in scripts:
        print(f" - {script.relative_to(ROOT_DIR)}")

    processes: dict[Path, subprocess.Popen] = {}
    try:
        for script in scripts:
            process = launch_script(script)
            processes[script] = process
            print(f"[START] {script.relative_to(ROOT_DIR)} (pid={process.pid})")

        wait_for_processes(processes)
        return 0
    except KeyboardInterrupt:
        print("\nStopping child processes...")
        terminate_processes(processes)
        wait_for_processes(processes)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
