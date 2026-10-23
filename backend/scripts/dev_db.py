"""A throwaway local Postgres for development and tests, kept inside backend/.pgdata.

    python scripts/dev_db.py start     create it the first time, then start it on port 5544
    python scripts/dev_db.py stop
    python scripts/dev_db.py status

It never touches any other Postgres on your machine. It needs the Postgres command line tools:
put their folder on PATH, or set PG_BIN to it (for example C:\\Program Files\\PostgreSQL\\18\\bin).
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

PORT = "5544"
USER = "lopper"
DATABASES = ("lopper", "lopper_test")
DATA_DIR = Path(__file__).resolve().parent.parent / ".pgdata"


def tool(name: str) -> str:
    folder = os.environ.get("PG_BIN")
    found = shutil.which(name, path=folder) if folder else shutil.which(name)
    if not found:
        sys.exit(f"Couldn't find {name}. Put the Postgres bin folder on PATH or set PG_BIN.")
    return found


def run(*command: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(command, check=check, capture_output=True, text=True)


def is_up() -> bool:
    return run(tool("pg_isready"), "-h", "localhost", "-p", PORT, check=False).returncode == 0


def start() -> None:
    if not (DATA_DIR / "PG_VERSION").exists():
        print("Creating the dev database cluster...")
        run(tool("initdb"), "-D", str(DATA_DIR), "-U", USER, "--auth=trust", "-E", "UTF8")
    if not is_up():
        print(f"Starting Postgres on port {PORT}...")
        # Popen so this script doesn't wait on the server's output.
        subprocess.Popen(
            [tool("pg_ctl"), "-D", str(DATA_DIR), "-o", f"-p {PORT}", "-l", str(DATA_DIR / "server.log"), "-w", "start"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL,
        ).wait()
    if not is_up():
        sys.exit(f"Postgres didn't start. See {DATA_DIR / 'server.log'}.")
    psql = tool("psql")
    for database in DATABASES:
        exists = run(psql, "-h", "localhost", "-p", PORT, "-U", USER, "-d", "postgres", "-tAc",
                     f"SELECT 1 FROM pg_database WHERE datname = '{database}'").stdout.strip()
        if not exists:
            run(psql, "-h", "localhost", "-p", PORT, "-U", USER, "-d", "postgres", "-c", f"CREATE DATABASE {database}")
    print(f"Ready: postgresql://{USER}@localhost:{PORT}/lopper (and lopper_test for the tests)")


def stop() -> None:
    if is_up():
        run(tool("pg_ctl"), "-D", str(DATA_DIR), "-m", "fast", "stop")
        print("Stopped.")
    else:
        print("It wasn't running.")


def main() -> None:
    action = sys.argv[1] if len(sys.argv) > 1 else "status"
    if action == "start":
        start()
    elif action == "stop":
        stop()
    elif action == "status":
        print("running" if is_up() else "stopped")
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
