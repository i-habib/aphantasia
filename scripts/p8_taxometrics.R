# P8: taxometric analysis of visual and multisensory imagery.
#
# Implements projects/P8_aphantasia_taxometrics/protocol/preregistration.md.
# Run through the gate, which checks the registration first:
#   python3 scripts/run_available.py --project P8 --preregistration-url <URL>
# Self-test on simulated data only (no real data are read):
#   Rscript scripts/p8_taxometrics.R --selftest          # helpers only, seconds
#   Rscript scripts/p8_taxometrics.R --selftest --full   # also taxometric runs, about 6 minutes
#
# Writes summary results and graphs only, never individual rows.

suppressMessages({
  library(RTaxometrics)
  library(jsonlite)
})

SEED <- 20261011
PROFILE_MAX_N <- 5000
CCFI_TAXONIC <- 0.55
CCFI_DIMENSIONAL <- 0.45
WIDE_TAXONIC <- 0.60
WIDE_DIMENSIONAL <- 0.40
PLAN <- "projects/P8_aphantasia_taxometrics/protocol/preregistration.md"
FREEZE <- "projects/P8_aphantasia_taxometrics/protocol/preregistration.sha256"
DATA <- "projects/P8_aphantasia_taxometrics/data_raw"
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

# ---- loading (each returns item or sense scores, one row per person) ----

check_range <- function(x, low, high, label) {
  values <- unlist(x)
  if (any(values < low | values > high)) stop(sprintf("%s has answers outside %d-%d", label, low, high))
  x
}

load_monzel <- function(root) {
  env <- new.env()
  load(file.path(root, DATA, "monzel2026_total_data_set.Rdata"), envir = env)
  df <- as.data.frame(env$df)
  items <- sprintf("VVIQ_%02d", 1:16)
  flow <- list(rows = nrow(df))
  df <- df[complete.cases(df[, items]), , drop = FALSE]
  flow$complete_items <- nrow(df)
  df <- df[!duplicated(df$subject_id), , drop = FALSE]
  flow$after_removing_repeats <- nrow(df)
  out <- check_range(as.matrix(df[, items]), 1, 5, "Monzel VVIQ")
  list(items = out, flow = flow)
}

load_dance <- function(root) {
  df <- suppressWarnings(foreign::read.spss(file.path(root, DATA, "dance2021_prevalence.sav"), to.data.frame = TRUE,
                                            use.value.labels = FALSE))
  items <- sprintf("vviq_%d", 1:16)
  flow <- list(rows = nrow(df))
  df <- df[complete.cases(df[, items]), , drop = FALSE]
  flow$complete_items <- nrow(df)
  out <- check_range(as.matrix(df[, items]), 1, 5, "Dance VVIQ")
  list(items = out, flow = flow)
}

load_new <- function(root) {
  archive <- file.path(root, "2bdn6-osfstorage-archive.zip")
  read_one <- function(member) {
    con <- unz(archive, member, encoding = "latin1")
    df <- read.delim(con, colClasses = "character", check.names = FALSE)
    df
  }
  flow <- list()
  parts <- list()
  floors <- list()
  for (study in c("Exp1.1003", "Exp3.1020")) {
    df <- read_one(sprintf("Analyses/%s.txt", study))
    flow[[study]] <- list(rows = nrow(df))
    df <- df[suppressWarnings(as.numeric(df$nbact)) >= 3, , drop = FALSE]
    scores <- sapply(NEW_SENSES, function(s) suppressWarnings(as.numeric(df[[s]])))
    scores <- scores[complete.cases(scores), , drop = FALSE]
    flow[[study]]$after_attention_check_and_complete <- nrow(scores)
    check_range(scores, 5, 35, study)
    floors[[study]] <- apply(scores == 5, 1, any)  # at least one sense at the lowest possible score
    parts[[study]] <- scale(scores)  # z-scores within each survey
  }
  list(senses = do.call(rbind, parts), any_floor = unlist(floors), flow = flow)
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

# ---- one analysis (plan sections 4.2, 5.1, 5.2) ----

verdict <- function(ccfi, high = CCFI_TAXONIC, low = CCFI_DIMENSIONAL) {
  if (is.na(ccfi)) return("missing")
  if (ccfi >= high) "two_groups" else if (ccfi <= low) "continuum" else "unclear"
}

run_profile <- function(x, label, n.samples = 100, num.p = 39) {
  set.seed(SEED)
  use <- if (nrow(x) > PROFILE_MAX_N) x[sample.int(nrow(x), PROFILE_MAX_N), , drop = FALSE] else x
  profile <- RunCCFIProfile(use, seed = SEED, n.samples = n.samples, num.p = num.p, graph = 0)
  list(n_used = nrow(use), ccfi = profile$CCFI.mean, base_rate = profile$p.mean,
       ccfi_by_procedure = list(MAMBAC = profile$CCFI.MAMBAC, MAXEIG = profile$CCFI.MAXEIG, LMode = profile$CCFI.LMode))
}

analyse <- function(x, label, fallback_p, out_dir, profile = NULL, fixed_p = NULL, graph_file = NULL,
                    n.samples = 100, num.p = 39) {
  x <- as.matrix(x)
  storage.mode(x) <- "double"
  if (is.null(fixed_p)) {
    if (is.null(profile)) profile <- run_profile(x, label, n.samples = n.samples, num.p = num.p)
    p <- if (!is.na(profile$ccfi) && profile$ccfi >= CCFI_TAXONIC) profile$base_rate else fallback_p
    p_source <- if (identical(p, fallback_p)) "fallback" else "ccfi_profile"
  } else {
    p <- fixed_p
    p_source <- "fixed"
  }
  grouped <- ClassifyCases(x, p = p)
  check_text <- capture.output(CheckData(grouped))
  if (!is.null(graph_file)) png(graph_file, width = 2400, height = 1600, res = 200) else pdf(NULL)
  result <- RunTaxometrics(grouped, seed = SEED, n.samples = n.samples, graph = if (is.null(graph_file)) 0 else 1)
  dev.off()
  groups <- grouped[, ncol(grouped)]
  validity <- apply(x, 2, function(v) {
    a <- v[groups == 2]; b <- v[groups == 1]
    (mean(a) - mean(b)) / sqrt(((length(a) - 1) * var(a) + (length(b) - 1) * var(b)) / (length(v) - 2))
  })
  within <- function(g) {
    m <- suppressWarnings(cor(x[groups == g, , drop = FALSE]))
    mean(m[upper.tri(m)], na.rm = TRUE)
  }
  writeLines(check_text, file.path(out_dir, sprintf("checkdata_%s.txt", label)))
  list(label = label, n = nrow(x), indicators = colnames(x), provisional_base_rate = p, base_rate_source = p_source,
       profile = profile,
       checks = list(validity_d = as.list(validity), mean_validity_d = mean(validity),
                     mean_within_group_r_taxon = within(2), mean_within_group_r_rest = within(1)),
       ccfi = list(mean = result$CCFI.mean, MAMBAC = result$CCFI.MAMBAC, MAXEIG = result$CCFI.MAXEIG, LMode = result$CCFI.LMode),
       base_rate_estimates = list(mean = result$p.mean, MAMBAC = result$p.MAMBAC, MAXEIG = result$p.MAXEIG, LMode = result$p.LMode),
       verdict = verdict(result$CCFI.mean),
       verdict_wide_zone = verdict(result$CCFI.mean, WIDE_TAXONIC, WIDE_DIMENSIONAL))
}

# ---- full registered run ----

run_p8 <- function(root, out_dir, registration) {
  plan_sha <- verify_registration(root, registration)
  dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
  monzel <- load_monzel(root)
  dance <- load_dance(root)
  new <- load_new(root)
  cut32 <- function(items) mean(rowSums(items) <= 32)
  cut23 <- function(items) mean(rowSums(items) <= 23)
  results <- list(project = "P8", registration = registration, plan_sha256 = plan_sha, seed = SEED,
                  rtaxometrics = as.character(packageVersion("RTaxometrics")), r = R.version.string,
                  flow = list(monzel = monzel$flow, dance = dance$flow, new = new$flow))
  main_x <- scene_indicators(monzel$items)
  main <- analyse(main_x, "main_scenes", cut32(monzel$items), out_dir, graph_file = file.path(out_dir, "graphs_main.png"))
  results$main <- main

  matched <- matched_subsample(monzel$items, dance$items)
  results$robustness <- list(
    matched_subsample = c(list(n = matched$n, band_target = matched$target, band_achieved = matched$achieved),
                          analyse(main_x[matched$rows, ], "matched_scenes", cut32(monzel$items[matched$rows, ]), out_dir)),
    item_pairs = analyse(pair_indicators(monzel$items), "main_pairs", cut32(monzel$items), out_dir, profile = main$profile),
    cutoff_32 = analyse(main_x, "main_cut32", NULL, out_dir, fixed_p = cut32(monzel$items)),
    cutoff_23 = analyse(main_x, "main_cut23", NULL, out_dir, fixed_p = cut23(monzel$items))
  )
  set.seed(SEED)
  half <- sample(rep(1:2, length.out = nrow(main_x)))
  results$robustness$half_1 <- analyse(main_x[half == 1, ], "half_1", NULL, out_dir, fixed_p = main$provisional_base_rate)
  results$robustness$half_2 <- analyse(main_x[half == 2, ], "half_2", NULL, out_dir, fixed_p = main$provisional_base_rate)
  results$robustness$wide_zone_main <- main$verdict_wide_zone

  results$secondary <- list(
    dance = analyse(scene_indicators(dance$items), "dance_scenes", cut32(dance$items), out_dir),
    multisensory = analyse(-new$senses, "new_multisensory", mean(new$any_floor), out_dir)
  )
  write_json(results, file.path(out_dir, "p8_results.json"), auto_unbox = TRUE, digits = 6, pretty = TRUE, na = "null")
  cat(toJSON(list(P8 = list(status = "complete", main_ccfi = main$ccfi$mean, main_verdict = main$verdict)), auto_unbox = TRUE), "\n")
}

# ---- self-test on simulated data (no real data) ----

selftest <- function(full = FALSE) {
  set.seed(1)
  pdf(NULL)
  out <- list()
  if (full) {
    taxonic <- CreateData("cat", n = 800, k = 4, p = 0.3)[, 1:4]
    continuous <- CreateData("dim", n = 800, k = 4)[, 1:4]
    tmp <- tempdir()
    a <- analyse(taxonic, "sim_taxonic", 0.3, tmp, n.samples = 10, num.p = 20)
    b <- analyse(continuous, "sim_continuous", 0.3, tmp, n.samples = 10, num.p = 20)
    out <- list(taxonic_ccfi = a$ccfi$mean, taxonic_verdict = a$verdict,
                continuous_ccfi = b$ccfi$mean, continuous_verdict = b$verdict)
  }
  items <- matrix(sample(1:5, 16 * 3000, replace = TRUE), ncol = 16)
  scenes <- scene_indicators(items)
  pairs <- pair_indicators(items)
  reference <- matrix(sample(1:5, 16 * 300, replace = TRUE), ncol = 16)
  matched <- matched_subsample(items, reference)
  achieved_gap <- max(abs(matched$achieved - matched$target))
  out <- c(out, list(
              scenes_ok = all(scenes[, 1] == 24 - rowSums(items[, 1:4])) && all(range(scenes) >= 4 & range(scenes) <= 20),
              pairs_ok = ncol(pairs) == 8 && all(pairs[, 8] == 12 - rowSums(items[, 15:16])),
              matched_rows_unique = !anyDuplicated(matched$rows), matched_n = matched$n,
              band_edges_ok = identical(band_of(c(16, 19, 20, 76, 79, 80)), c(0, 0, 1, 15, 15, 15)),
              matched_band_gap = achieved_gap,
              verdict_rule_ok = identical(c(verdict(0.55), verdict(0.45), verdict(0.5)), c("two_groups", "continuum", "unclear"))))
  cat(toJSON(out, auto_unbox = TRUE), "\n")
}

args <- commandArgs(trailingOnly = TRUE)
value_of <- function(flag) {
  i <- match(flag, args)
  if (is.na(i) || i == length(args)) NULL else args[i + 1]
}
if ("--selftest" %in% args) {
  selftest(full = "--full" %in% args)
} else {
  root <- normalizePath(if (is.null(value_of("--root"))) "." else value_of("--root"))
  out_dir <- if (is.null(value_of("--out"))) file.path(root, "runs", "latest", "P8") else value_of("--out")
  run_p8(root, out_dir, value_of("--registration"))
}
