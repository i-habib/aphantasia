"""Run the registered P8 analysis on one Modal machine with many CPUs.

No longer used: since 2026-10-13 P8 runs in free Kaggle sessions (scripts/p8_kaggle.py, p8_kaggle_push.py).
Kept because the 11 Oct Modal runs and their saved pieces are part of the record.

Same code and data as a local run (the R script checks the plan and data
fingerprints itself); only the machine differs. Results are copied back to
runs/latest/P8/.

    modal run --detach scripts/p8_modal.py --preregistration-url https://osf.io/w8xj9
    modal volume get aphantasia-p8-results latest runs/latest/P8_modal   # after it finishes, if detached

    modal run --detach scripts/p8_modal.py --fast --preregistration-url https://osf.io/w8xj9   # starts run_fast and returns
    modal volume get aphantasia-p8-results latest_fast runs/latest/P8_modal_fast               # after it finishes
"""
from __future__ import annotations

from pathlib import Path

import modal

ROOT = Path(__file__).resolve().parents[1]
REMOTE = "/root/aphantasia"
P8 = "projects/P8_aphantasia_taxometrics"

image = (
    modal.Image.from_registry("rocker/r-ver:4.6.1", add_python="3.12")
    .run_commands(
        "Rscript -e 'install.packages(c(\"RTaxometrics\", \"jsonlite\"), repos = \"https://cloud.r-project.org\")'",
        "Rscript -e 'stopifnot(as.character(packageVersion(\"RTaxometrics\")) == \"3.2.1\")'",
    )
    .pip_install("numpy", "pandas", "scipy")
    .add_local_dir(ROOT / "src", f"{REMOTE}/src")
    .add_local_dir(ROOT / "scripts", f"{REMOTE}/scripts")
    .add_local_dir(ROOT / P8 / "protocol", f"{REMOTE}/{P8}/protocol")
    .add_local_dir(ROOT / P8 / "data_raw", f"{REMOTE}/{P8}/data_raw")
    .add_local_file(ROOT / "2bdn6-osfstorage-archive.zip", f"{REMOTE}/2bdn6-osfstorage-archive.zip")
)

app = modal.App("aphantasia-p8", image=image)
results = modal.Volume.from_name("aphantasia-p8-results", create_if_missing=True)


@app.function(cpu=16, memory=32768, timeout=24 * 60 * 60, volumes={"/results": results})
def run(preregistration_url: str) -> dict[str, bytes | str]:
    import os
    import shutil
    import subprocess

    out = Path("/tmp/P8")
    # Finished analyses are saved here, so a restart skips them (Modal commits volume writes in the background).
    os.makedirs("/results/checkpoints", exist_ok=True)
    os.environ["P8_CHECKPOINT_DIR"] = "/results/checkpoints"
    completed = subprocess.run(
        ["python3", f"{REMOTE}/scripts/run_available.py", "--root", REMOTE, "--output", "/tmp", "--project", "P8",
         "--preregistration-url", preregistration_url],
        capture_output=True, text=True,
    )
    files: dict[str, bytes | str] = {"_stdout": completed.stdout, "_stderr": completed.stderr[-20000:],
                                     "_returncode": str(completed.returncode)}
    if out.exists():
        for path in out.iterdir():
            files[path.name] = path.read_bytes()
    # Also keep a copy in the volume, so results survive if the local client disconnects (run with --detach).
    saved = Path("/results/latest")
    if saved.exists():
        shutil.rmtree(saved)
    saved.mkdir(parents=True)
    for name, content in files.items():
        (saved / (f"modal{name}.txt" if name.startswith("_") else name)).write_bytes(
            content if isinstance(content, bytes) else str(content).encode())
    results.commit()
    return files


@app.function(cpu=64, memory=131072, timeout=24 * 60 * 60, volumes={"/results": results})
def run_fast(preregistration_url: str) -> str:
    """Same analyses with each CCFI profile split by taxon size across cores (deviation logged). Saves to /results/latest_fast."""
    import os
    import shutil
    import subprocess

    os.makedirs("/results/checkpoints_fast", exist_ok=True)
    env = {**os.environ, "P8_FAST_PROFILE": "1", "P8_CHECKPOINT_DIR": "/results/checkpoints_fast"}
    done = subprocess.run(["python3", f"{REMOTE}/scripts/run_available.py", "--root", REMOTE, "--output", "/tmp", "--project", "P8",
                           "--preregistration-url", preregistration_url], capture_output=True, text=True, env=env)
    saved = Path("/results/latest_fast")
    if saved.exists():
        shutil.rmtree(saved)
    saved.mkdir(parents=True)
    (saved / "modal_stdout.txt").write_text(done.stdout)
    (saved / "modal_stderr.txt").write_text(done.stderr[-20000:])
    (saved / "modal_returncode.txt").write_text(str(done.returncode))
    out = Path("/tmp/P8")
    if out.exists():
        for path in out.iterdir():
            shutil.copy(path, saved / path.name)
    results.commit()
    return done.stdout[-2000:]


@app.function(cpu=32, memory=65536, timeout=3600)
def selftest_pipeline(extra: list[str]) -> str:
    """Self-tests on simulated data; reads no real data."""
    import subprocess

    done = subprocess.run(["Rscript", f"{REMOTE}/scripts/p8_taxometrics.R", "--selftest", *extra], capture_output=True, text=True)
    return done.stdout.strip().splitlines()[-1] if done.stdout.strip() else done.stderr[-3000:]


@app.function(cpu=2, timeout=600)
def check() -> str:
    """Report the R and package versions in the image; reads no data."""
    import subprocess

    return subprocess.run(["Rscript", "-e", "cat(R.version.string, as.character(packageVersion('RTaxometrics')), parallel::detectCores(), '\\n')"],
                          capture_output=True, text=True).stdout


@app.local_entrypoint()
def main(preregistration_url: str = "", check_only: bool = False, selftest: bool = False, fast: bool = False) -> None:
    if check_only:
        print(check.remote())
        return
    if selftest:
        calls = [selftest_pipeline.spawn(["--agreement"]), selftest_pipeline.spawn(["--pipeline", "--fast"])]
        for call in calls:
            print(call.get())
        return
    if fast:
        # Start it and return. Waiting here ties the run to this machine: on 2026-10-11 it was cancelled when the laptop slept.
        call = run_fast.spawn(preregistration_url)
        print("started run_fast", call.object_id)
        return
    files = run.remote(preregistration_url)
    target = ROOT / "runs" / "latest" / "P8"
    target.mkdir(parents=True, exist_ok=True)
    for name, content in files.items():
        if name.startswith("_"):
            (target / f"modal{name}.txt").write_text(str(content))
        else:
            (target / name).write_bytes(content if isinstance(content, bytes) else content.encode())
    print(files["_stdout"][-2000:])
    print("return code", files["_returncode"])
