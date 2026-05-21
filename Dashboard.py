import sys
import time
import argparse
import datetime
import urllib.request
import urllib.error
import json
import os
import shutil

DASHBOARD_URL = "http://127.0.0.1:8000/dashboard"

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
FG_WHITE = "\033[97m"
FG_CYAN = "\033[96m"
FG_GREEN = "\033[92m"
FG_GRAY = "\033[90m"
FG_YELLOW = "\033[93m"
FG_RED = "\033[91m"
FG_MAGENTA = "\033[95m"

COLUMNS = [
    ("#", "#", 4),
    ("job_id", "JOB ID", 10),
    ("status", "STATUS", 12),
    ("GPU", "GPU", 6),
    ("RAM", "RAM", 8),
    ("CPU", "CPU", 6),
    ("Storage", "STORAGE", 10),
    ("memory_peak", "MEM PEAK", 10),
    ("WallTime", "WALL TIME", 12),
    ("ProcessType", "P.TYPE", 7),
    ("Query", "QUERY", 50),
]


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def terminal_width() -> int:
    return shutil.get_terminal_size((130, 40)).columns


def c(text: str, *colors: str) -> str:
    return "".join(colors) + str(text) + RESET


def fit(value, width: int) -> str:
    s = str(value) if value is not None else "—"
    if len(s) >= width:
        return s[:width - 1] + "…"
    return s.ljust(width)


def fetch_dashboard():
    try:
        with urllib.request.urlopen(DASHBOARD_URL, timeout=4) as resp:
            raw = resp.read().decode()
            data = json.loads(raw)

            jobs = []
            jobs.extend(data.get("pending_jobs", []))
            jobs.extend(data.get("running_jobs", []))
            jobs.extend(data.get("completed_jobs", []))

            return jobs, raw, None

    except urllib.error.URLError as e:
        return None, "", f"URLError: {e.reason}"
    except json.JSONDecodeError as e:
        return None, "", f"JSON inválido: {e}"
    except Exception as e:
        return None, "", f"Error inesperado: {e}"


def render(jobs: list, interval: int):
    w = terminal_width()
    ts = datetime.datetime.now().strftime("%Y-%m-%d  %H:%M:%S")

    pending = sum(1 for job in jobs if job.get("status") in ["QUEUED", "WAITING"])
    running = sum(1 for job in jobs if job.get("status") == "RUNNING")
    completed = sum(1 for job in jobs if job.get("status") == "COMPLETED")

    title = " MOAB-Torque · Dashboard de Jobs "
    pad = max((w - len(title)) // 2, 0)

    print(c("═" * w, FG_GRAY))
    print(c(" " * pad + title, BOLD, FG_WHITE))
    print(c(f"  {DASHBOARD_URL}   │   {ts}   │   refresco: {interval}s", DIM))
    print(c("─" * w, FG_GRAY))

    print(
        c(
            f"  Total jobs: {len(jobs)}  |  "
            f"Pendientes: {pending}  |  "
            f"En ejecución: {running}  |  "
            f"Completados: {completed}",
            BOLD,
            FG_GREEN
        )
    )

    print(c("─" * w, FG_GRAY))

    if not jobs:
        print(c("\n  No hay jobs registrados.\n", DIM))
        print(c("─" * w, FG_GRAY))
        print(c(f"  Próxima actualización en {interval}s  │  Ctrl+C para salir", DIM))
        return

    header = "  ".join(
        c(fit(hdr, width), BOLD, FG_CYAN)
        for _, hdr, width in COLUMNS
    )

    print("  " + header)
    print(c("─" * w, FG_GRAY))

    for idx, job in enumerate(jobs, start=1):
        row = []

        for key, _hdr, width in COLUMNS:
            if key == "#":
                row.append(c(fit(idx, width), FG_GRAY))

            elif key == "status":
                status = job.get(key, "—")

                if status in ["QUEUED", "WAITING"]:
                    row.append(c(fit(status, width), FG_YELLOW))
                elif status == "RUNNING":
                    row.append(c(fit(status, width), FG_MAGENTA))
                elif status == "COMPLETED":
                    row.append(c(fit(status, width), FG_GREEN))
                else:
                    row.append(c(fit(status, width), FG_WHITE))

            elif key == "Query":
                row.append(c(fit(job.get(key, "—"), width), FG_YELLOW))

            elif key == "ProcessType":
                row.append(c(fit(job.get(key, "—"), width), FG_MAGENTA))

            elif key in ("GPU", "CPU"):
                row.append(c(fit(job.get(key, "—"), width), FG_GREEN))

            elif key in ("RAM", "Storage", "memory_peak"):
                row.append(c(fit(job.get(key, "—"), width), FG_CYAN))

            elif key == "WallTime":
                row.append(c(fit(job.get(key, "—"), width), FG_WHITE))

            else:
                row.append(c(fit(job.get(key, "—"), width), FG_WHITE))

        print("  " + "  ".join(row))

    print(c("═" * w, FG_GRAY))
    print(c(f"  Próxima actualización en {interval}s  │  Ctrl+C para salir", DIM))


def main():
    parser = argparse.ArgumentParser(
        description="Dashboard dinámico MOAB-Torque"
    )

    parser.add_argument(
        "--interval",
        "-n",
        type=int,
        default=2,
        help="Segundos entre actualizaciones"
    )

    args = parser.parse_args()

    print(c(f"Conectando a {DASHBOARD_URL} ...", FG_CYAN))
    time.sleep(1)

    error_count = 0

    try:
        while True:
            jobs, raw, err = fetch_dashboard()
            clear_screen()

            if err:
                error_count += 1
                print(c(f"\n  Error #{error_count}: {err}", FG_RED))
                print(c(f"  URL: {DASHBOARD_URL}", DIM))

                if raw:
                    print(c(f"\n  Respuesta cruda:\n  {raw[:300]}", DIM))

                print(c("\n  Revisa que FastAPI esté corriendo en puerto 8000.\n", FG_YELLOW))

            else:
                error_count = 0
                render(jobs, args.interval)

            time.sleep(args.interval)

    except KeyboardInterrupt:
        print(c("\n\n  Monitor detenido.\n", DIM))
        sys.exit(0)


if __name__ == "__main__":
    main()