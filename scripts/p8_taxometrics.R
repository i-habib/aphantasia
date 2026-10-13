# P8: taxometric analysis of visual and multisensory imagery.
#
# Implements projects/P8_aphantasia_taxometrics/protocol/preregistration.md.
# Run through the gate, which checks the registration first:
#   python3 scripts/run_available.py --project P8 --preregistration-url <URL>
# Self-test on simulated data only (no real data are read):
#   Rscript scripts/p8_taxometrics.R --selftest          # helpers only, seconds
#   Rscript scripts/p8_taxometrics.R --selftest --full   # also taxometric runs, about 6 minutes
#   Rscript scripts/p8_taxometrics.R --selftest --pipeline  # whole pipeline, small settings, parallel
#
# Writes summary results and graphs only, never individual rows.

suppressMessages({
  library(RTaxometrics)
  library(jsonlite)
})

SEED <- 20261011
PROFILE_MAX_N <- 5000
MIN_TAXON_N <- 30
CCFI_TAXONIC <- 0.55
CCFI_DIMENSIONAL <- 0.45
WIDE_TAXONIC <- 0.60
WIDE_DIMENSIONAL <- 0.40
GOOD_VALIDITY_D <- 1.25
GOOD_WITHIN_R <- 0.30
PLAN <- "projects/P8_aphantasia_taxometrics/protocol/preregistration.md"
FREEZE <- "projects/P8_aphantasia_taxometrics/protocol/preregistration.sha256"
DATA <- "projects/P8_aphantasia_taxometrics/data_raw"
FILES <- list(
  monzel = list(path = file.path(DATA, "monzel2026_total_data_set.Rdata"),
                sha256 = "2f601bff1328d7ae87832d67e689588c31fa4380177ec6f7c260b243dee5a5e6"),
  dance = list(path = file.path(DATA, "dance2021_prevalence.sav"),
               sha256 = "43512d3962d933ceadefd660c3be92dfe62be5528bb11fb35d8777c006ad9633"),
  new = list(path = "2bdn6-osfstorage-archive.zip",
             sha256 = "6abd7a36b3e89c20936c295f5a8569aea545b49562f8ef388a057a5e75462bdd")
)
SCENES <- list(friend = 1:4, sun = 5:8, shop = 9:12, country = 13:16)
NEW_SENSES <- c("image", "sound", "touch", "motor", "taste", "smell", "emotion", "voice")

stop_with <- function(code, message) {
  cat(toJSON(list(status = "blocked", code = code, message = message), auto_unbox = TRUE), "\n")
  quit(status = 2)
}

verify_registration <- function(root, url) {
  if (is.null(url) || !startsWith(url, "https://")) {
    stop_with("awaiting_preregistration", "Pass --registration with the https:// registration link.")
  }
  freeze <- file.path(root, FREEZE)
  if (!file.exists(freeze)) stop_with("plan_not_frozen", "Run scripts/freeze_preregistration.py --project P8 first.")
  recorded <- strsplit(readLines(freeze, n = 1), " +")[[1]][1]
  current <- unname(tools::sha256sum(file.path(root, PLAN)))
  if (!identical(recorded, current)) stop_with("plan_changed_after_freeze", "The plan no longer matches its frozen SHA-256.")
  current
}

verify_data <- function(root) {
  for (name in names(FILES)) {
    observed <- unname(tools::sha256sum(file.path(root, FILES[[name]]$path)))
    if (!identical(observed, FILES[[name]]$sha256)) stop_with("data_changed", sprintf("%s does not match its SHA-256.", FILES[[name]]$path))
  }
}

# ---- loading (each returns item or sense scores, one row per person) ----

check_range <- function(x, low, high, label) {
  values <- unlist(x)
  if (any(values < low | values > high)) stop(sprintf("%s has answers outside %d-%d", label, low, high))
  x
}

require_columns <- function(df, columns, label) {
  missing <- setdiff(columns, names(df))
  if (length(missing)) stop(sprintf("%s is missing columns: %s", label, paste(missing, collapse = ", ")))
}

load_monzel <- function(root) {
  env <- new.env()
  load(file.path(root, FILES$monzel$path), envir = env)
  df <- as.data.frame(env$df)
  items <- sprintf("VVIQ_%02d", 1:16)
  require_columns(df, c(items, "subject_id"), "Monzel data")
  flow <- list(rows = nrow(df))
  df <- df[complete.cases(df[, items]), , drop = FALSE]
  flow$complete_items <- nrow(df)
  df <- df[!duplicated(df$subject_id), , drop = FALSE]
  flow$after_removing_repeats <- nrow(df)
  out <- check_range(as.matrix(df[, items]), 1, 5, "Monzel VVIQ")
  list(items = out, flow = flow)
}

load_dance <- function(root) {
  df <- suppressWarnings(foreign::read.spss(file.path(root, FILES$dance$path), to.data.frame = TRUE, use.value.labels = FALSE))
  items <- sprintf("vviq_%d", 1:16)
  require_columns(df, items, "Dance data")
  flow <- list(rows = nrow(df))
  df <- df[complete.cases(df[, items]), , drop = FALSE]
  flow$complete_items <- nrow(df)
  out <- check_range(as.matrix(df[, items]), 1, 5, "Dance VVIQ")
  list(items = out, flow = flow)
}

load_new <- function(root) {
  archive <- file.path(root, FILES$new$path)
  flow <- list()
  parts <- list()
  floors <- list()
  for (study in c("Exp1.1003", "Exp3.1020")) {
    con <- unz(archive, sprintf("Analyses/%s.txt", study), encoding = "latin1")
    df <- read.delim(con, colClasses = "character", check.names = FALSE)
    require_columns(df, c("nbact", NEW_SENSES), study)
    flow[[study]] <- list(rows = nrow(df))
    attention <- suppressWarnings(as.numeric(df$nbact))
    df <- df[!is.na(attention) & attention >= 3, , drop = FALSE]
    flow[[study]]$after_attention_check <- nrow(df)
    scores <- sapply(NEW_SENSES, function(s) suppressWarnings(as.numeric(df[[s]])))
    scores <- scores[complete.cases(scores), , drop = FALSE]
    flow[[study]]$complete_scores <- nrow(scores)
    check_range(scores, 5, 35, study)
    floors[[study]] <- rowSums(scores == 5)  # number of senses at the lowest possible score
    parts[[study]] <- scale(scores)  # z-scores within each survey
  }
  list(senses = do.call(rbind, parts), n_floor = unlist(floors), flow = flow)
}

# ---- indicators: higher = weaker imagery ----

scene_indicators <- function(items) {
  sapply(SCENES, function(cols) 24 - rowSums(items[, cols, drop = FALSE]))
}

pair_indicators <- function(items) {
  out <- sapply(seq(1, 15, by = 2), function(i) 12 - rowSums(items[, c(i, i + 1), drop = FALSE]))
  colnames(out) <- sprintf("items_%d_%d", seq(1, 15, by = 2), seq(2, 16, by = 2))
  out
}

share_at_or_below <- function(items, cut) mean(rowSums(items) <= cut)

floor_summary <- function(items) {
  scenes <- scene_indicators(items)
  list(pct_total_16 = 100 * mean(rowSums(items) == 16),
       pct_all_four_scenes_at_floor = 100 * mean(apply(scenes == 20, 1, all)),
       pct_each_scene_at_floor = as.list(100 * colMeans(scenes == 20)),
       pct_at_or_below_32 = 100 * share_at_or_below(items, 32),
       pct_at_or_below_23 = 100 * share_at_or_below(items, 23))
}

# ---- population-matched subsample (plan section 3.2) ----

band_of <- function(total) pmin(floor((total - 16) / 4), 15)  # 16 bands; 80 joins the top band

matched_subsample <- function(items, reference_items, seed = SEED) {
  bands <- band_of(rowSums(items))
  target <- tabulate(band_of(rowSums(reference_items)) + 1, nbins = 16) / nrow(reference_items)
  available <- tabulate(bands + 1, nbins = 16)
  usable <- target > 0
  n <- floor(min(available[usable] / target[usable]))
  wanted <- round(n * target)
  set.seed(seed)
  keep <- unlist(lapply(which(wanted > 0), function(b) {
    rows <- which(bands == b - 1)
    rows[sample.int(length(rows), min(wanted[b], length(rows)))]
  }))
  list(rows = sort(keep), n = length(keep), target = target, achieved = tabulate(bands[keep] + 1, nbins = 16) / length(keep))
}

# ---- simulations (plan section 5.4) ----

# A continuum with the real floor: one normal factor, ordinal items cut to match each real item's answer proportions,
# and a common loading chosen so the simulated items correlate as strongly, on average, as the real ones.
simulate_floored_continuum <- function(items, seed = SEED) {
  n <- nrow(items)
  cuts <- lapply(seq_len(ncol(items)), function(j) {
    cum <- cumsum(tabulate(items[, j], nbins = 5)) / n
    qnorm(pmin(pmax(cum[1:4], 1e-6), 1 - 1e-6))
  })
  draw <- function(loading, size) {
    latent <- rnorm(size)
    sapply(cuts, function(cj) findInterval(loading * latent + sqrt(1 - loading^2) * rnorm(size), cj) + 1)
  }
  mean_r <- function(m) { r <- cor(m); mean(r[upper.tri(r)]) }
  target <- mean_r(items)
  set.seed(seed)
  grid <- seq(0.30, 0.98, by = 0.01)
  fit <- sapply(grid, function(l) mean_r(draw(l, 20000)))
  best <- which.min(abs(fit - target))
  set.seed(seed + 1)
  list(items = draw(grid[best], n), loading = grid[best], target_mean_r = target, achieved_mean_r = fit[best])
}

# A known two-group population the size of the matched subsample, with its observed taxon share, validity and
# within-group correlations, to show whether the matched check could detect a taxon of that size.
simulate_detectable_taxon <- function(n, p, d, r_taxon, r_rest, seed = SEED) {
  CreateData("cat", n = n, k = 4, p = p, d = d, r.tax = max(0, r_taxon), r.comp = max(0, r_rest), seed = seed)[, 1:4]
}

# ---- one analysis (plan sections 4.2, 5.1, 5.2) ----

verdict <- function(ccfi, high = CCFI_TAXONIC, low = CCFI_DIMENSIONAL) {
  if (is.null(ccfi) || is.na(ccfi)) return("missing")
  if (ccfi >= high) "two_groups" else if (ccfi <= low) "continuum" else "unclear"
}

combined_verdict <- function(main_ccfi, profile_ccfi) {
  a <- verdict(main_ccfi); b <- verdict(profile_ccfi)
  if (a == b && a %in% c("two_groups", "continuum")) a else "unclear"
}

run_profile <- function(x, n.samples = 100, num.p = 39) {
  set.seed(SEED)
  use <- if (nrow(x) > PROFILE_MAX_N) x[sample.int(nrow(x), PROFILE_MAX_N), , drop = FALSE] else x
  old_device <- options(device = function(...) pdf(NULL))
  profile <- RunCCFIProfile(use, seed = SEED, n.samples = n.samples, num.p = num.p, graph = 0)
  while (dev.cur() > 1) dev.off()
  options(old_device)
  list(n_used = nrow(use), ccfi = profile$CCFI.mean, base_rate = profile$p.mean,
       ccfi_by_procedure = list(MAMBAC = profile$CCFI.MAMBAC, MAXEIG = profile$CCFI.MAXEIG, LMode = profile$CCFI.LMode),
       base_rate_by_procedure = list(MAMBAC = profile$p.MAMBAC, MAXEIG = profile$p.MAXEIG, LMode = profile$p.LMode))
}

within_correlations <- function(x, keep) {
  m <- suppressWarnings(cor(x[keep, , drop = FALSE]))
  values <- m[upper.tri(m)]
  list(matrix = unname(round(m, 3)), mean = if (all(is.na(values))) NA else mean(values, na.rm = TRUE),
       n_undefined = sum(is.na(values)))
}

analyse <- function(x, label, p, out_dir, with_profile = FALSE, graph_file = NULL, n.samples = 100, num.p = 39) {
  x <- as.matrix(x)
  storage.mode(x) <- "double"
  if (is.na(p) || round(p * nrow(x)) < MIN_TAXON_N) {
    return(list(label = label, n = nrow(x), requested_taxon_share = p, status = "not_run_too_few_in_provisional_taxon"))
  }
  profile <- if (with_profile) run_profile(x, n.samples = n.samples, num.p = num.p) else NULL
  grouped <- ClassifyCases(x, p = p)
  groups <- grouped[, ncol(grouped)]
  writeLines(capture.output(CheckData(grouped)), file.path(out_dir, sprintf("checkdata_%s.txt", label)))
  validity <- apply(x, 2, function(v) {
    a <- v[groups == 2]; b <- v[groups == 1]
    (mean(a) - mean(b)) / sqrt(((length(a) - 1) * var(a) + (length(b) - 1) * var(b)) / (length(v) - 2))
  })
  taxon_r <- within_correlations(x, groups == 2)
  rest_r <- within_correlations(x, groups == 1)
  # The package opens its own graphics device, so point R's default device at the file we want (or at nothing).
  old_device <- options(device = if (is.null(graph_file)) function(...) pdf(NULL) else function(...) pdf(graph_file, width = 12, height = 8))
  result <- RunTaxometrics(grouped, seed = SEED, n.samples = n.samples, graph = if (is.null(graph_file)) 0 else 1)
  while (dev.cur() > 1) dev.off()
  options(old_device)
  by_procedure <- c(result$CCFI.MAMBAC, result$CCFI.MAXEIG, result$CCFI.LMode)
  out <- list(label = label, n = nrow(x), indicators = colnames(x), status = "run",
              requested_taxon_share = p, actual_taxon_share = mean(groups == 2),
              checks = list(validity_d = as.list(validity), mean_validity_d = mean(validity),
                            low_validity_flag = mean(validity < GOOD_VALIDITY_D) > 0.5,
                            within_r_taxon = taxon_r, within_r_rest = rest_r,
                            high_within_r_flag = isTRUE(taxon_r$mean > GOOD_WITHIN_R) || isTRUE(rest_r$mean > GOOD_WITHIN_R)),
              ccfi = list(mean = result$CCFI.mean, MAMBAC = result$CCFI.MAMBAC, MAXEIG = result$CCFI.MAXEIG, LMode = result$CCFI.LMode),
              procedures_disagree = any(by_procedure >= CCFI_TAXONIC) && any(by_procedure <= CCFI_DIMENSIONAL),
              base_rate_estimates = list(mean = result$p.mean, MAMBAC = result$p.MAMBAC, MAXEIG = result$p.MAXEIG, LMode = result$p.LMode),
              verdict = verdict(result$CCFI.mean),
              profile = profile)
  if (with_profile) out$combined_verdict <- combined_verdict(result$CCFI.mean, profile$ccfi)
  out$lower_trust <- out$checks$low_validity_flag || out$checks$high_within_r_flag
  out
}

# ---- fast CCFI profile: the package's RunCCFIProfile, split by taxon size (deviation logged 2026-10-11) ----
# RunCCFIProfile draws one random stream for all 39 sizes in turn, so it cannot be split across cores. Here each size
# gets its own seed (SEED + i); the steps for each size are the package's own (same internal functions, same order).

rt <- function(name) get(name, envir = asNamespace("RTaxometrics"))

profile_setup <- function(x, n.samples = 100, num.p = 39) {
  set.seed(SEED)
  x <- as.matrix(x)
  storage.mode(x) <- "double"
  if (nrow(x) > PROFILE_MAX_N) x <- x[sample.int(nrow(x), PROFILE_MAX_N), , drop = FALSE]
  n_used <- nrow(x)
  parameters <- list(min.p = 0.025, max.p = 0.975, num.p = num.p, n = nrow(x), k = ncol(x), n.pop = 1e5, n.samples = n.samples,
                     reps = 1, MAMBAC = TRUE, assign.MAMBAC = 1, n.cuts = 50, n.end = 25, MAXEIG = TRUE, assign.MAXEIG = 1,
                     windows = 50, overlap = 0.9, LMode = TRUE, mode.l = -0.001, mode.r = 0.001, MAXSLOPE = FALSE,
                     graph = 0, profile = TRUE)
  x <- rt("RemoveMissingData")(x)
  x <- rt("AddVariance")(x, ncol(x), parameters)
  x <- apply(x, 2, scale)
  parameters <- rt("CheckParameters")(x, parameters)
  x.results <- rt("RunProcedures")(x, parameters)
  x.dim <- rt("GenerateData")(x, n = parameters$n.pop)
  x.dim.results <- rt("RunProceduresComp")(x.dim, parameters)
  list(x = x, parameters = parameters, x.results = x.results, x.dim.results = x.dim.results, n_used = n_used,
       ps = seq(parameters$min.p, parameters$max.p, length = parameters$num.p))
}

profile_part <- function(setup, i) {
  set.seed(SEED + i)
  k <- ncol(setup$x)
  p <- setup$ps[i]
  x.classes <- ClassifyCases(setup$x, p = p)
  group <- x.classes[, k + 1]
  taxon <- rt("GenerateData")(x.classes[(group == 2), 1:k], n = round(setup$parameters$n.pop * p))
  complement <- rt("GenerateData")(x.classes[(group == 1), 1:k], n = setup$parameters$n.pop - round(setup$parameters$n.pop * p))
  x.cat.results <- rt("RunProceduresComp")(rbind(taxon, complement), setup$parameters)
  rt("CalculateCCFIsProfile")(setup$x.results, setup$x.dim.results, x.cat.results, setup$parameters)
}

profile_summary <- function(setup, columns) {
  ccfis <- do.call(cbind, columns)
  profile <- rt("CalculateProfileOutput")(ccfis, setup$parameters)
  list(n_used = setup$n_used, ccfi = profile$CCFI.mean, base_rate = profile$p.mean,
       ccfi_by_procedure = list(MAMBAC = profile$CCFI.MAMBAC, MAXEIG = profile$CCFI.MAXEIG, LMode = profile$CCFI.LMode),
       base_rate_by_procedure = list(MAMBAC = profile$p.MAMBAC, MAXEIG = profile$p.MAXEIG, LMode = profile$p.LMode),
       ccfi_by_size = unname(ccfis[5, ]), sizes = setup$ps, method = "split_by_size")
}

# One share of the profile pieces, so several machines can work at once. Every piece has its own seed and is saved
# under its own name, so a later full run reuses it and computes the same results. shard is "i/n" or "profile_size".
# "i/n" takes every n-th piece, starting from the end, because a full run works through the pieces from the start.
# "profile_size" computes the main sample's 39 sizes and then, if the main profile reads as two groups, the
# profile-size check. Nothing is printed; the results are only in the saved files.
run_shard <- function(shard, phase2, parts_for, one, main_x, out_dir, cores, n.samples) {
  if (identical(shard, "profile_size")) {
    setup <- one$setup__main
    parts <- run_tasks(parts_for("main", setup), cores)
    profile <- profile_summary(setup, parts)
    if (isTRUE(profile$ccfi >= CCFI_TAXONIC)) {
      run_tasks(list(profile_size = function() analyse(main_x, "main_profile_size", profile$base_rate, out_dir,
                                                        n.samples = n.samples)), 1)
    }
    return(list(shard = shard, pieces = length(parts) + isTRUE(profile$ccfi >= CCFI_TAXONIC)))
  }
  where <- as.integer(strsplit(shard, "/", fixed = TRUE)[[1]])
  stopifnot(length(where) == 2, where[1] >= 1, where[1] <= where[2])
  pieces <- phase2[setdiff(names(phase2), "setup__detect")]
  if (!is.null(phase2$setup__detect)) {
    # Every shard computes the same detectability setup (fixed seed), so each can take some of its sizes.
    setup <- run_tasks(phase2["setup__detect"], 1)$setup__detect
    pieces <- c(pieces, parts_for("detect", setup))
  }
  pieces <- rev(pieces)
  mine <- pieces[(seq_along(pieces) - 1) %% where[2] == where[1] - 1]
  run_tasks(mine, cores)
  list(shard = shard, pieces = length(mine))
}

# Same analyses as run_analyses(), in four parallel phases: (1) every analysis without its profile, plus each profile's
# shared setup; (2) every profile size, plus the detectability analysis and its setup; (3) the detectability profile
# sizes and the profile-size check; (4) assembly.
run_analyses_fast <- function(monzel_items, dance_items, new, out_dir, cores, n.samples = 100, num.p = 39) {
  main_x <- scene_indicators(monzel_items)
  p32 <- share_at_or_below(monzel_items, 32)
  matched <- matched_subsample(monzel_items, dance_items)
  matched_items <- monzel_items[matched$rows, , drop = FALSE]
  set.seed(SEED)
  half <- sample(rep(1:2, length.out = nrow(main_x)))
  floored <- simulate_floored_continuum(monzel_items)
  inputs <- list(
    main = list(x = main_x, p = p32, profile = TRUE, graph = file.path(out_dir, "graphs_main.pdf"), label = "main_scenes"),
    matched = list(x = main_x[matched$rows, ], p = share_at_or_below(matched_items, 32), profile = TRUE, label = "matched_scenes"),
    item_pairs = list(x = pair_indicators(monzel_items), p = p32, profile = FALSE, label = "main_pairs"),
    cutoff_23 = list(x = main_x, p = share_at_or_below(monzel_items, 23), profile = FALSE, label = "main_cut23"),
    half_1 = list(x = main_x[half == 1, ], p = share_at_or_below(monzel_items[half == 1, ], 32), profile = FALSE, label = "half_1"),
    half_2 = list(x = main_x[half == 2, ], p = share_at_or_below(monzel_items[half == 2, ], 32), profile = FALSE, label = "half_2"),
    floored = list(x = scene_indicators(floored$items), p = share_at_or_below(floored$items, 32), profile = TRUE,
                   label = "floored_continuum"),
    dance = list(x = scene_indicators(dance_items), p = share_at_or_below(dance_items, 32), profile = TRUE, label = "dance_scenes"),
    multisensory = list(x = -new$senses, p = mean(new$n_floor >= 4), profile = TRUE, label = "new_multisensory"))
  run_one <- function(input) analyse(input$x, input$label, input$p, out_dir, graph_file = input$graph, n.samples = n.samples)
  runnable <- function(input) !is.na(input$p) && round(input$p * nrow(as.matrix(input$x))) >= MIN_TAXON_N
  with_profile <- names(inputs)[vapply(inputs, function(i) i$profile && runnable(i), logical(1))]

  phase1 <- c(lapply(inputs, function(input) function() run_one(input)),
              setNames(lapply(with_profile, function(name) function() profile_setup(inputs[[name]]$x, n.samples, num.p)),
                       paste0("setup__", with_profile)))
  # P8_SHARD set: this session only computes a share of the profile pieces (see run_shard), from saved setups.
  shard <- Sys.getenv("P8_SHARD")
  if (nzchar(shard)) phase1 <- phase1[c("matched", paste0("setup__", with_profile))]
  one <- run_tasks(phase1, cores)
  parts_for <- function(name, setup) setNames(lapply(seq_along(setup$ps), function(i) function() profile_part(setup, i)),
                                              sprintf("part__%s__%02d", name, seq_along(setup$ps)))
  phase2 <- do.call(c, lapply(with_profile, function(name) parts_for(name, one[[paste0("setup__", name)]])))
  detect <- NULL
  if (identical(one$matched$status, "run")) {
    taxon_r <- one$matched$checks$within_r_taxon$mean
    rest_r <- one$matched$checks$within_r_rest$mean
    detect <- list(x = simulate_detectable_taxon(matched$n, one$matched$actual_taxon_share, one$matched$checks$mean_validity_d,
                                                 ifelse(is.na(taxon_r), 0, taxon_r), ifelse(is.na(rest_r), 0, rest_r)),
                   p = one$matched$actual_taxon_share, label = "matched_detectability")
    phase2$detect <- function() run_one(detect)
    phase2$setup__detect <- function() profile_setup(detect$x, n.samples, num.p)
  }
  if (nzchar(shard)) return(run_shard(shard, phase2, parts_for, one, main_x, out_dir, cores, n.samples))
  two <- run_tasks(phase2, cores)
  attach_profile <- function(result, name, parts_from, setup) {
    columns <- parts_from[sprintf("part__%s__%02d", name, seq_along(setup$ps))]
    result$profile <- profile_summary(setup, columns)
    result$combined_verdict <- combined_verdict(result$ccfi$mean, result$profile$ccfi)
    result
  }
  for (name in with_profile) one[[name]] <- attach_profile(one[[name]], name, two, one[[paste0("setup__", name)]])

  phase3 <- list()
  if (!is.null(detect)) phase3 <- parts_for("detect", two$setup__detect)
  if (isTRUE(one$main$profile$ccfi >= CCFI_TAXONIC)) {
    size <- one$main$profile$base_rate
    phase3$profile_size <- function() analyse(main_x, "main_profile_size", size, out_dir, n.samples = n.samples)
  }
  three <- if (length(phase3)) run_tasks(phase3, cores) else list()
  detectability <- if (!is.null(detect)) attach_profile(two$detect, "detect", three, two$setup__detect) else NULL

  results <- list(main = one$main)
  results$robustness <- list(
    matched_subsample = c(list(n = matched$n, band_target = matched$target, band_achieved = matched$achieved,
                               floor = floor_summary(matched_items)), one$matched),
    matched_detectability = detectability,
    item_pairs = one$item_pairs, cutoff_23 = one$cutoff_23, profile_size = three$profile_size,
    half_1 = one$half_1, half_2 = one$half_2,
    floored_continuum = c(list(loading = floored$loading, target_mean_r = floored$target_mean_r,
                               achieved_mean_r = floored$achieved_mean_r, floor = floor_summary(floored$items)), one$floored))
  results$robustness <- results$robustness[!vapply(results$robustness, is.null, logical(1))]
  results$secondary <- list(dance = one$dance, multisensory = one$multisensory)
  results$conclusion <- conclude(results)
  results$profile_method <- "split_by_size: each of the 39 taxon sizes run with its own seed (SEED + i); see deviations log"
  results
}

# ---- reading the main result (plan section 6) ----

conclude <- function(results) {
  main <- results$main
  rob <- results$robustness
  reading <- main$combined_verdict
  notes <- character()
  if (identical(reading, "two_groups")) {
    if (identical(rob$floored_continuum$combined_verdict, "two_groups")) {
      reading <- "cannot_separate_from_floor_effect"
      notes <- c(notes, "A simulated continuum with the same floor also reads as two groups.")
    }
    if (!identical(rob$half_1$verdict, "two_groups") || !identical(rob$half_2$verdict, "two_groups")) {
      if (reading == "two_groups") reading <- "unclear"
      notes <- c(notes, "The two random halves do not both read as two groups.")
    }
    if (identical(rob$matched_subsample$combined_verdict, "continuum") &&
        identical(rob$matched_detectability$combined_verdict, "two_groups")) {
      if (reading == "two_groups") reading <- "two_groups_but_may_reflect_selection"
      notes <- c(notes, "The population-matched subsample reads as a continuum, and a taxon of that size would have been detected.")
    }
  }
  if (isTRUE(main$procedures_disagree)) notes <- c(notes, "The three procedures point in opposite directions.")
  if (isTRUE(main$lower_trust)) notes <- c(notes, "The data checks call for lower trust (indicator separation or within-group correlations).")
  list(reading = reading, notes = notes,
       taxon_size_estimate = if (identical(reading, "two_groups")) main$profile$base_rate else NA,
       wide_zone_verdict_main = verdict(main$ccfi$mean, WIDE_TAXONIC, WIDE_DIMENSIONAL))
}

# ---- full registered run ----

run_tasks <- function(tasks, cores) {
  # Each analysis sets its own seeds, so running them in parallel gives the same results as running them in turn.
  # If P8_CHECKPOINT_DIR is set, each finished analysis is saved there and reused on a restart.
  checkpoints <- Sys.getenv("P8_CHECKPOINT_DIR")
  wrapped <- lapply(names(tasks), function(name) {
    force(name)
    function() {
      file <- if (nzchar(checkpoints)) file.path(checkpoints, paste0(name, ".rds")) else ""
      if (nzchar(file) && file.exists(file)) return(readRDS(file))
      value <- tasks[[name]]()
      if (nzchar(file)) saveRDS(value, file)
      value
    }
  })
  names(wrapped) <- names(tasks)
  out <- parallel::mclapply(wrapped, function(task) task(), mc.cores = max(1, min(cores, length(tasks))),
                            mc.preschedule = FALSE, mc.set.seed = FALSE)
  failed <- vapply(out, function(x) inherits(x, "try-error") || is.null(x), logical(1))
  if (any(failed)) stop(sprintf("analysis failed: %s\n%s", paste(names(tasks)[failed], collapse = ", "),
                                paste(vapply(out[failed], function(x) paste(as.character(x), collapse = " "), ""), collapse = "\n")))
  out
}

# Builds and runs every analysis in plan sections 5.2-5.5; returns the results list without run metadata.
run_analyses <- function(monzel_items, dance_items, new, out_dir, cores, n.samples = 100, num.p = 39) {
  main_x <- scene_indicators(monzel_items)
  p32 <- share_at_or_below(monzel_items, 32)
  matched <- matched_subsample(monzel_items, dance_items)
  matched_items <- monzel_items[matched$rows, , drop = FALSE]
  set.seed(SEED)
  half <- sample(rep(1:2, length.out = nrow(main_x)))
  run <- function(...) analyse(..., n.samples = n.samples, num.p = num.p)
  first <- run_tasks(list(
    main = function() run(main_x, "main_scenes", p32, out_dir, with_profile = TRUE, graph_file = file.path(out_dir, "graphs_main.pdf")),
    matched = function() run(main_x[matched$rows, ], "matched_scenes", share_at_or_below(matched_items, 32), out_dir, with_profile = TRUE),
    item_pairs = function() run(pair_indicators(monzel_items), "main_pairs", p32, out_dir),
    cutoff_23 = function() run(main_x, "main_cut23", share_at_or_below(monzel_items, 23), out_dir),
    half_1 = function() run(main_x[half == 1, ], "half_1", share_at_or_below(monzel_items[half == 1, ], 32), out_dir),
    half_2 = function() run(main_x[half == 2, ], "half_2", share_at_or_below(monzel_items[half == 2, ], 32), out_dir),
    floored = function() {
      floored <- simulate_floored_continuum(monzel_items)
      c(list(loading = floored$loading, target_mean_r = floored$target_mean_r, achieved_mean_r = floored$achieved_mean_r,
             floor = floor_summary(floored$items)),
        run(scene_indicators(floored$items), "floored_continuum", share_at_or_below(floored$items, 32), out_dir, with_profile = TRUE))
    },
    dance = function() run(scene_indicators(dance_items), "dance_scenes", share_at_or_below(dance_items, 32), out_dir, with_profile = TRUE),
    multisensory = function() run(-new$senses, "new_multisensory", mean(new$n_floor >= 4), out_dir, with_profile = TRUE)
  ), cores)
  second <- list()
  if (identical(first$matched$status, "run")) {
    taxon_r <- first$matched$checks$within_r_taxon$mean
    rest_r <- first$matched$checks$within_r_rest$mean
    second$matched_detectability <- function() {
      sim <- simulate_detectable_taxon(matched$n, first$matched$actual_taxon_share, first$matched$checks$mean_validity_d,
                                       ifelse(is.na(taxon_r), 0, taxon_r), ifelse(is.na(rest_r), 0, rest_r))
      run(sim, "matched_detectability", first$matched$actual_taxon_share, out_dir, with_profile = TRUE)
    }
  }
  if (isTRUE(first$main$profile$ccfi >= CCFI_TAXONIC)) {
    second$profile_size <- function() run(main_x, "main_profile_size", first$main$profile$base_rate, out_dir)
  }
  second <- if (length(second)) run_tasks(second, cores) else list()
  results <- list(main = first$main)
  results$robustness <- list(
    matched_subsample = c(list(n = matched$n, band_target = matched$target, band_achieved = matched$achieved,
                               floor = floor_summary(matched_items)), first$matched),
    matched_detectability = second$matched_detectability,
    item_pairs = first$item_pairs, cutoff_23 = first$cutoff_23, profile_size = second$profile_size,
    half_1 = first$half_1, half_2 = first$half_2, floored_continuum = first$floored)
  results$robustness <- results$robustness[!vapply(results$robustness, is.null, logical(1))]
  results$secondary <- list(dance = first$dance, multisensory = first$multisensory)
  results$conclusion <- conclude(results)
  results
}

run_p8 <- function(root, out_dir, registration, cores = parallel::detectCores()) {
  plan_sha <- verify_registration(root, registration)
  verify_data(root)
  dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
  monzel <- load_monzel(root)
  dance <- load_dance(root)
  new <- load_new(root)
  if (nzchar(Sys.getenv("P8_SHARD"))) {
    done <- run_analyses_fast(monzel$items, dance$items, new, out_dir, cores)
    cat(toJSON(list(P8 = c(list(status = "shard_done"), done)), auto_unbox = TRUE), "\n")
    return(invisible(done))
  }
  results <- c(list(project = "P8", registration = registration, plan_sha256 = plan_sha, seed = SEED,
                    rtaxometrics = as.character(packageVersion("RTaxometrics")), r = R.version.string, cores = cores,
                    flow = list(monzel = monzel$flow, dance = dance$flow, new = new$flow),
                    floor = list(main = floor_summary(monzel$items), dance = floor_summary(dance$items))),
               if (identical(Sys.getenv("P8_FAST_PROFILE"), "1")) run_analyses_fast(monzel$items, dance$items, new, out_dir, cores)
               else run_analyses(monzel$items, dance$items, new, out_dir, cores))
  write_json(results, file.path(out_dir, "p8_results.json"), auto_unbox = TRUE, digits = 6, pretty = TRUE, na = "null")
  cat(toJSON(list(P8 = list(status = "complete", reading = results$conclusion$reading,
                            main_ccfi = results$main$ccfi$mean, profile_ccfi = results$main$profile$ccfi)), auto_unbox = TRUE), "\n")
}

# ---- self-test on simulated data (no real data) ----

# The whole pipeline on simulated data, with small settings, to check the wiring (no real data).
selftest_pipeline <- function(cores = 4, fast = FALSE, return_results = FALSE) {
  set.seed(2)
  draw_items <- function(n, floor_share) {
    latent <- rnorm(n)
    items <- sapply(1:16, function(j) findInterval(0.8 * latent + 0.6 * rnorm(n), c(-1.2, -0.4, 0.4, 1.2)) + 1)
    items[seq_len(round(n * floor_share)), ] <- 1L
    items
  }
  monzel_items <- draw_items(3000, 0.15)
  dance_items <- draw_items(600, 0.01)
  senses <- matrix(rnorm(1200 * 8), ncol = 8)
  new <- list(senses = senses, n_floor = c(rep(5L, 60), rep(0L, 1140)))
  out_dir <- file.path(tempdir(), "p8_pipeline")
  dir.create(out_dir, showWarnings = FALSE)
  runner <- if (fast) run_analyses_fast else run_analyses
  results <- runner(monzel_items, dance_items, new, out_dir, cores, n.samples = 3, num.p = 20)
  if (return_results || nzchar(Sys.getenv("P8_SHARD"))) return(results)
  expected <- c("matched_subsample", "item_pairs", "cutoff_23", "half_1", "half_2", "floored_continuum")
  out <- list(pipeline_keys_ok = all(expected %in% names(results$robustness)),
              detectability_present = !is.null(results$robustness$matched_detectability) ||
                !identical(results$robustness$matched_subsample$status, "run"),
              secondary_ok = all(c("dance", "multisensory") %in% names(results$secondary)),
              conclusion = results$conclusion$reading,
              graph_written = isTRUE(file.info(file.path(out_dir, "graphs_main.pdf"))$size > 1000),
              profiles_attached = !is.null(results$main$profile$ccfi) && !is.null(results$robustness$floored_continuum$combined_verdict))
  cat(toJSON(out, auto_unbox = TRUE), "\n")
}

# Shards then a full run must give exactly the same results as one full run (simulated data, fresh checkpoint folders).
selftest_shards <- function(cores = 4) {
  run_in <- function(shards) {
    dir <- tempfile("p8_checkpoints_")
    dir.create(dir)
    Sys.setenv(P8_CHECKPOINT_DIR = dir)
    for (shard in shards) {
      Sys.setenv(P8_SHARD = shard)
      selftest_pipeline(cores, fast = TRUE)
    }
    Sys.setenv(P8_SHARD = "")
    before <- length(list.files(dir))
    results <- selftest_pipeline(cores, fast = TRUE, return_results = TRUE)
    list(results = results, saved_by_shards = before, saved_total = length(list.files(dir)))
  }
  one <- run_in(character())
  split <- run_in(c("profile_size", "1/2", "2/2"))
  same <- identical(toJSON(one$results, digits = NA), toJSON(split$results, digits = NA))
  cat(toJSON(list(shards_match_full_run = same, profile_size_present = !is.null(one$results$robustness$profile_size),
                  saved_by_shards = split$saved_by_shards, saved_total = split$saved_total), auto_unbox = TRUE), "\n")
}

# Split profile versus the package's RunCCFIProfile on simulated data (different random draws, same method).
selftest_profile_agreement <- function(cores = 16) {
  pdf(NULL)
  out <- list()
  for (kind in c("cat", "dim")) {
    x <- CreateData(kind, n = 1500, k = 4, p = 0.3, seed = 7)[, 1:4]
    package <- RunCCFIProfile(x, seed = SEED, n.samples = 25, num.p = 20, graph = 0)
    setup <- profile_setup(x, n.samples = 25, num.p = 20)
    parts <- parallel::mclapply(seq_along(setup$ps), function(i) profile_part(setup, i), mc.cores = cores)
    split <- profile_summary(setup, parts)
    out[[kind]] <- list(package_ccfi = package$CCFI.mean, split_ccfi = split$ccfi,
                        package_p = package$p.mean, split_p = split$base_rate)
  }
  cat(toJSON(out, auto_unbox = TRUE), "\n")
}

selftest <- function(full = FALSE) {
  set.seed(1)
  pdf(NULL)
  out <- list()
  if (full) {
    taxonic <- CreateData("cat", n = 800, k = 4, p = 0.3)[, 1:4]
    continuous <- CreateData("dim", n = 800, k = 4)[, 1:4]
    tmp <- tempdir()
    a <- analyse(taxonic, "sim_taxonic", 0.3, tmp, with_profile = TRUE, n.samples = 10, num.p = 20)
    b <- analyse(continuous, "sim_continuous", 0.3, tmp, with_profile = TRUE, n.samples = 10, num.p = 20)
    out <- list(taxonic_ccfi = a$ccfi$mean, taxonic_verdict = a$combined_verdict,
                continuous_ccfi = b$ccfi$mean, continuous_verdict = b$combined_verdict)
  }
  items <- matrix(sample(1:5, 16 * 3000, replace = TRUE), ncol = 16)
  scenes <- scene_indicators(items)
  pairs <- pair_indicators(items)
  reference <- matrix(sample(1:5, 16 * 300, replace = TRUE), ncol = 16)
  matched <- matched_subsample(items, reference)
  floored_source <- rbind(matrix(1L, 300, 16), matrix(sample(1:5, 16 * 2700, replace = TRUE, prob = c(1, 2, 3, 3, 2)), ncol = 16))
  floored <- simulate_floored_continuum(floored_source)
  tied_scores <- c(rep(0, 60), 1:40)
  tied <- ClassifyCases(cbind(tied_scores, tied_scores), p = 0.5)
  out <- c(out, list(
    scenes_ok = all(scenes[, 1] == 24 - rowSums(items[, 1:4])) && all(range(scenes) >= 4 & range(scenes) <= 20),
    pairs_ok = ncol(pairs) == 8 && all(pairs[, 8] == 12 - rowSums(items[, 15:16])),
    matched_rows_unique = !anyDuplicated(matched$rows), matched_n = matched$n,
    matched_band_gap = max(abs(matched$achieved - matched$target)),
    band_edges_ok = identical(band_of(c(16, 19, 20, 76, 79, 80)), c(0, 0, 1, 15, 15, 15)),
    verdict_rule_ok = identical(c(verdict(0.55), verdict(0.45), verdict(0.5)), c("two_groups", "continuum", "unclear")),
    combined_rule_ok = identical(c(combined_verdict(0.6, 0.6), combined_verdict(0.6, 0.5), combined_verdict(0.4, 0.3)),
                                 c("two_groups", "unclear", "continuum")),
    floored_item1_floor_gap = abs(mean(floored$items[, 1] == 1) - mean(floored_source[, 1] == 1)),
    floored_mean_r_gap = abs(floored$achieved_mean_r - floored$target_mean_r),
    tie_moves_block = mean(tied[, 3] == 2) != 0.5,
    too_few_skipped = identical(analyse(matrix(rnorm(400), 100), "tiny", 0.1, tempdir())$status,
                                "not_run_too_few_in_provisional_taxon")
  ))
  cat(toJSON(out, auto_unbox = TRUE), "\n")
}

args <- commandArgs(trailingOnly = TRUE)
value_of <- function(flag) {
  i <- match(flag, args)
  if (is.na(i) || i == length(args)) NULL else args[i + 1]
}
if ("--selftest" %in% args && "--shards" %in% args) {
  selftest_shards()
} else if ("--selftest" %in% args && "--agreement" %in% args) {
  selftest_profile_agreement()
} else if ("--selftest" %in% args && "--pipeline" %in% args) {
  selftest_pipeline(cores = if ("--fast" %in% args) 32 else 4, fast = "--fast" %in% args)
} else if ("--selftest" %in% args) {
  selftest(full = "--full" %in% args)
} else {
  root <- normalizePath(if (is.null(value_of("--root"))) "." else value_of("--root"))
  out_dir <- if (is.null(value_of("--out"))) file.path(root, "runs", "latest", "P8") else value_of("--out")
  run_p8(root, out_dir, value_of("--registration"))
}
