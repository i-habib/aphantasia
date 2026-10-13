"""Run the registered P8 analysis (fast profile) in a free Kaggle notebook session.

Same code, data and seeds as the Modal fast run; only the machine differs. Analyses that the
Modal fast run already finished are reused from its saved checkpoints, and anything this session
finishes is saved to /kaggle/working/checkpoints_fast, so a later session can carry on from there.

Kaggle runs this file as a private script. It needs the private dataset `p8-aphantasia-bundle`
(code, plan, data files and Modal checkpoints in one archive) and internet access to install R.

    kaggle kernels status ivanhabib/p8-aphantasia-taxometrics
    kaggle kernels output ivanhabib/p8-aphantasia-taxometrics -p runs/latest/P8_kaggle   # after it finishes

To split the work, push copies with SHARD set (scripts/p8_kaggle_push.py does this), then one session with
SHARD = "" whose kernel_sources list the earlier sessions, so it starts with all their saved pieces.

The log printed here never contains results; R's own output goes to files in /kaggle/working.
"""
from __future__ import annotations

import base64
import hashlib
import os
import shutil
import signal
import subprocess
import tarfile
import threading
import time
from pathlib import Path

REGISTRATION = "https://osf.io/w8xj9"
R_VERSION = "4.6.1"
RTAXOMETRICS = "3.2.1"
# Stop R this long after the session starts (a Kaggle CPU session is cut off at 12 hours), so the session ends
# normally and its saved files are kept.
BUDGET_HOURS = float(os.environ.get("P8_BUDGET_HOURS", "11.3"))
PROBE = False  # True: install R, run the self-test and a short speed test on simulated data, then stop.
# Non-empty: compute only this share of the profile pieces ("i/n" or "profile_size"; see run_shard in the R script).
# Several sessions can then work at once; a final session with all their outputs as inputs assembles the results.
SHARD = ""
# Non-empty: base64 of scripts/p8_taxometrics.R, written over the bundle's copy (the bundle predates the shard mode;
# the dataset holds participant data, so only the user uploads new versions of it). p8_kaggle_push.py fills it in.
R_SCRIPT_B64 = ""

START = time.time()
INPUT = Path("/kaggle/input")
WORK = Path("/kaggle/working")
ROOT = Path("/tmp/aphantasia")
OUT = Path("/tmp/p8_out")
CHECKPOINTS = WORK / "checkpoints_fast"


def say(message: str) -> None:
    print(f"[{(time.time() - START) / 60:6.1f} min] {message}", flush=True)


def sh(command: str, **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(command, shell=True, text=True, capture_output=True, **kwargs)


def machine() -> None:
    release = dict(line.strip().split("=", 1) for line in Path("/etc/os-release").read_text().splitlines() if "=" in line)
    memory_gb = int(Path("/proc/meminfo").read_text().split()[1]) / 1e6
    say(f"machine: {os.cpu_count()} CPUs, {memory_gb:.0f} GB, {release.get('PRETTY_NAME', '?')}")


def unpack() -> None:
    """Put the project at ROOT with the same layout as the checkout."""
    archives = list(INPUT.rglob("p8_bundle.tar.gz"))
    if archives:
        ROOT.mkdir(parents=True, exist_ok=True)
        with tarfile.open(archives[0]) as tar:
            tar.extractall(ROOT)
    else:  # Kaggle unpacked the archive itself
        scripts = list(INPUT.rglob("scripts/p8_taxometrics.R"))
        if not scripts:
            raise SystemExit("bundle not found under /kaggle/input")
        shutil.copytree(scripts[0].parents[1], ROOT, dirs_exist_ok=True)
    # The survey archive is stored under another name so nothing unpacks it on the way; R checks its SHA-256.
    kept = ROOT / "2bdn6-osfstorage-archive.zip.keep"
    if kept.exists():
        kept.rename(ROOT / "2bdn6-osfstorage-archive.zip")
    if R_SCRIPT_B64:
        script = base64.b64decode(R_SCRIPT_B64)
        (ROOT / "scripts" / "p8_taxometrics.R").write_bytes(script)
        say(f"R script replaced from this kernel's code, SHA-256 {hashlib.sha256(script).hexdigest()}")
    say("project unpacked")


def install_r() -> None:
    release = dict(line.strip().split("=", 1) for line in Path("/etc/os-release").read_text().splitlines() if "=" in line)
    distro = release["ID"].strip('"')
    version = release["VERSION_ID"].strip('"')
    codename = release.get("VERSION_CODENAME", "").strip('"')
    platform = f"ubuntu-{version.replace('.', '')}" if distro == "ubuntu" else f"debian-{version.split('.')[0]}"
    deb = f"https://cdn.posit.co/r/{platform}/pkgs/r-{R_VERSION}_1_amd64.deb"
    done = sh(f"cd /tmp && curl -fsSLO {deb} && apt-get update -qq && "
              f"DEBIAN_FRONTEND=noninteractive apt-get install -y -qq ./r-{R_VERSION}_1_amd64.deb")
    if done.returncode != 0:
        raise SystemExit(f"R install failed ({deb}):\n{done.stderr[-3000:]}")
    os.environ["PATH"] = f"/opt/R/{R_VERSION}/bin:" + os.environ["PATH"]
    repo = f"https://packagemanager.posit.co/cran/__linux__/{codename}/latest"
    script = (
        'options(HTTPUserAgent = sprintf("R/%s R (%s)", getRversion(), paste(getRversion(), R.version["platform"], '
        'R.version["arch"], R.version["os"])));'
        f'install.packages(c("jsonlite", "remotes"), repos = "{repo}");'
        f'remotes::install_version("RTaxometrics", "{RTAXOMETRICS}", repos = "{repo}", upgrade = "never");'
        f'stopifnot(as.character(packageVersion("RTaxometrics")) == "{RTAXOMETRICS}", requireNamespace("foreign"));'
        'cat(R.version.string, as.character(packageVersion("RTaxometrics")), "\\n")'
    )
    done = sh(f"Rscript -e '{script}'")
    if done.returncode != 0:
        raise SystemExit(f"R package install failed:\n{done.stderr[-3000:]}")
    say("R ready: " + done.stdout.strip().splitlines()[-1])


def restore_checkpoints() -> None:
    """Copy every saved analysis we can find (the bundle's, or an earlier session's output) into this session."""
    CHECKPOINTS.mkdir(parents=True, exist_ok=True)
    sources = list((ROOT / "checkpoints_fast").glob("*.rds")) + [p for p in INPUT.rglob("*.rds") if p.parent.name == "checkpoints_fast"]
    for source in sources:
        if not (CHECKPOINTS / source.name).exists():
            shutil.copy(source, CHECKPOINTS / source.name)
    say(f"saved analyses available at start: {len(list(CHECKPOINTS.glob('*.rds')))}")


def selftest() -> None:
    done = sh(f"Rscript {ROOT}/scripts/p8_taxometrics.R --selftest")
    if done.returncode != 0 or "false" in done.stdout.lower():
        raise SystemExit(f"self-test failed:\n{done.stdout[-2000:]}\n{done.stderr[-2000:]}")
    say("self-test on simulated data passed")


def speed_test() -> None:
    """Time one small taxometric run on simulated data, to compare this machine's cores with others."""
    script = ('suppressMessages(library(RTaxometrics)); options(device = function(...) pdf(NULL));'
              'x <- CreateData("dim", n = 8000, k = 4, seed = 7)[, 1:4]; g <- ClassifyCases(x, p = 0.1);'
              'cat(system.time(RunTaxometrics(g, seed = 1, n.samples = 10, graph = 0))[["elapsed"]])')
    done = sh(f"Rscript -e '{script}'")
    say("speed test seconds: " + (done.stdout.strip().splitlines()[-1] if done.returncode == 0 else done.stderr[-500:]))


def heartbeat(stop: threading.Event) -> None:
    while not stop.wait(600):
        say(f"running; saved analyses: {len(list(CHECKPOINTS.glob('*.rds')))}")


def run() -> None:
    env = {**os.environ, "P8_FAST_PROFILE": "1", "P8_CHECKPOINT_DIR": str(CHECKPOINTS), "P8_SHARD": SHARD}
    command = ["python3", f"{ROOT}/scripts/run_available.py", "--root", str(ROOT), "--output", str(OUT), "--project", "P8",
               "--preregistration-url", REGISTRATION]
    stop = threading.Event()
    threading.Thread(target=heartbeat, args=(stop,), daemon=True).start()
    with open(WORK / "r_stdout.txt", "w") as out, open(WORK / "r_stderr.txt", "w") as err:
        process = subprocess.Popen(command, stdout=out, stderr=err, env=env, start_new_session=True)
        try:
            code = process.wait(timeout=max(60, BUDGET_HOURS * 3600 - (time.time() - START)))
            status = "finished" if code == 0 else f"stopped with return code {code}"
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)  # R's parallel workers are in the same process group
            status = "out of time; rerun to continue from the saved analyses"
    stop.set()
    saved = WORK / "latest_fast"
    if (OUT / "P8").exists():
        shutil.copytree(OUT / "P8", saved, dirs_exist_ok=True)
    (WORK / "run_status.txt").write_text(status + "\n")
    say(f"{status}; saved analyses: {len(list(CHECKPOINTS.glob('*.rds')))}; "
        f"results file written: {(saved / 'p8_results.json').exists()}")


if __name__ == "__main__":
    machine()
    unpack()
    install_r()
    selftest()
    if PROBE:
        speed_test()
    else:
        restore_checkpoints()
        run()
