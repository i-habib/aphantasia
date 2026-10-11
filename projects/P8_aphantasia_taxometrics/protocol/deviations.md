# P8 deviations log

Record every departure from the frozen `preregistration.md` here. Do not edit the plan itself after freezing.

| Date | Section | Change | Reason | Results seen before change? | Effect on conclusions |
|---|---|---|---|---|---|
| 2026-10-11 | §5, §9 | How the code runs, not what it computes. The independent analyses now run in parallel (R `parallel::mclapply`), in two batches: the detectability check and the profile-size check wait for the results they need. The run is on one Modal cloud machine (16 CPUs, Docker image `rocker/r-ver:4.6.1`, RTaxometrics 3.2.1) instead of the laptop. | Running one analysis at a time would take 8+ hours on one core. | No. A sequential local run was started and then stopped. Before it was stopped, the package wrote one graphics file (`Rplots.pdf`, 11 Oct 10:19, most likely the CCFI profile plot for the main sample) to the project folder. It was accidentally pushed to GitHub, then removed. We have not opened it, and it is kept unopened in `runs/stopped_local_run_2026-10-11/`. | None. Every analysis sets its own seeds, so the results are the same as running them in turn. |
