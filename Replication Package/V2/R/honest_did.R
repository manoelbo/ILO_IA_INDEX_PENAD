#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(data.table)
  library(HonestDiD)
})

script_argument <- grep("^--file=", commandArgs(trailingOnly = FALSE), value = TRUE)
if (length(script_argument) != 1L) {
  stop("Unable to resolve honest_did.R location.")
}
script_path_raw <- sub("^--file=", "", script_argument)
if (!file.exists(script_path_raw)) {
  script_path_raw <- gsub("~\\+~", " ", script_path_raw)
}
script_path <- normalizePath(script_path_raw, mustWork = TRUE)
package_root <- dirname(dirname(script_path))
diagnostics_dir <- file.path(package_root, "results", "diagnostics")
arguments <- commandArgs(trailingOnly = TRUE)

argument_value <- function(flag) {
  position <- match(flag, arguments)
  if (is.na(position) || position == length(arguments)) {
    stop("Missing required argument: ", flag)
  }
  arguments[[position + 1L]]
}

input_dir <- normalizePath(
  argument_value("--input-dir"),
  mustWork = TRUE
)
coefficients_path <- file.path(input_dir, "honest_did_event_coefficients.csv")
vcov_path <- file.path(input_dir, "honest_did_event_vcov_long.csv")
results_path <- file.path(
  diagnostics_dir,
  "honest_did_sensitivity.csv"
)
summary_path <- file.path(
  diagnostics_dir,
  "honest_did_summary.csv"
)

coefficients <- fread(coefficients_path)
vcov_long <- fread(vcov_path)
expected_outcomes <- c("asinh_saldo", "ln_salario_real_adm")
observed_outcomes <- sort(unique(coefficients$outcome))
if (!identical(observed_outcomes, expected_outcomes)) {
  stop("HonestDiD inputs must contain exactly the two linear outcomes.")
}

pre_event_times <- -23:-2
post_event_times <- 0:23
all_event_times <- c(pre_event_times, post_event_times)
num_pre_periods <- length(pre_event_times)
num_post_periods <- length(post_event_times)
mbar_grid <- seq(0, 2, by = 0.05)
l_vec <- rep(1 / num_post_periods, num_post_periods)
all_results <- list()
all_summaries <- list()

replication_worker_count <- function(task_count) {
  requested <- suppressWarnings(
    as.integer(Sys.getenv("REPLICATION_R_WORKERS", unset = "4"))
  )
  if (is.na(requested) || requested < 1L) {
    stop("REPLICATION_R_WORKERS must be a positive integer.")
  }
  detected <- suppressWarnings(parallel::detectCores(logical = FALSE))
  if (is.na(detected) || detected < 1L) detected <- 1L
  if (.Platform$OS.type == "windows") return(1L)
  max(1L, min(requested, detected, task_count))
}

deterministic_map <- function(indices, function_to_run) {
  workers <- replication_worker_count(length(indices))
  if (workers == 1L) return(lapply(indices, function_to_run))
  parallel::mclapply(
    indices,
    function_to_run,
    mc.cores = workers,
    mc.preschedule = FALSE,
    mc.set.seed = FALSE
  )
}

plot_sensitivity <- function(result, outcome, original_lb, original_ub) {
  plot_path <- file.path(
    diagnostics_dir,
    paste0("honest_did_", outcome, ".png")
  )
  png(plot_path, width = 1400, height = 900, res = 150)
  y_range <- range(c(result$lb, result$ub, 0), finite = TRUE)
  plot(
    result$Mbar,
    result$lb,
    type = "l",
    lwd = 3,
    col = "#1F4E79",
    ylim = y_range,
    xlab = "Relative-magnitude bound (Mbar)",
    ylab = "95% robust confidence interval",
    main = paste("HonestDiD sensitivity:", outcome)
  )
  lines(result$Mbar, result$ub, lwd = 3, col = "#C55A11")
  abline(h = 0, lty = 2, lwd = 2, col = "#4D4D4D")
  points(
    0,
    original_lb,
    pch = 16,
    col = "#1F4E79"
  )
  points(
    0,
    original_ub,
    pch = 16,
    col = "#C55A11"
  )
  legend(
    "topright",
    legend = c(
      "Robust lower bound",
      "Robust upper bound",
      "Zero",
      "Original interval at Mbar=0"
    ),
    col = c("#1F4E79", "#C55A11", "#4D4D4D", "#000000"),
    lty = c(1, 1, 2, NA),
    pch = c(NA, NA, NA, 16),
    lwd = c(3, 3, 2, NA),
    bty = "n"
  )
  dev.off()
  plot_path
}

for (outcome_name in expected_outcomes) {
  outcome_coefficients <- coefficients[
    outcome == outcome_name
  ][order(position)]
  if (!identical(outcome_coefficients$event_time, all_event_times)) {
    stop(paste("Unexpected event-time order for", outcome_name))
  }
  if (!identical(outcome_coefficients$position, 0:45)) {
    stop(paste("Unexpected coefficient positions for", outcome_name))
  }

  outcome_vcov <- vcov_long[outcome == outcome_name]
  sigma <- matrix(
    NA_real_,
    nrow = length(all_event_times),
    ncol = length(all_event_times)
  )
  sigma[
    cbind(
      outcome_vcov$row_position + 1L,
      outcome_vcov$column_position + 1L
    )
  ] <- outcome_vcov$covariance
  if (anyNA(sigma) || !isTRUE(all.equal(sigma, t(sigma), tolerance = 1e-10))) {
    stop(paste("Invalid covariance matrix for", outcome_name))
  }

  betahat <- outcome_coefficients$coefficient
  post_indices <- (num_pre_periods + 1L):length(all_event_times)
  post_sigma <- sigma[post_indices, post_indices, drop = FALSE]
  target_standard_error <- sqrt(
    as.numeric(t(l_vec) %*% post_sigma %*% l_vec)
  )
  internal_grid_lower <- -20 * target_standard_error
  internal_grid_upper <- 20 * target_standard_error
  original <- constructOriginalCS(
    betahat = betahat,
    sigma = sigma,
    numPrePeriods = num_pre_periods,
    numPostPeriods = num_post_periods,
    l_vec = l_vec,
    alpha = 0.05
  )
  sensitivity_rows <- deterministic_map(
    seq_along(mbar_grid),
    function(mbar_index) {
      result <- as.data.table(
      createSensitivityResults_relativeMagnitudes(
        betahat = betahat,
        sigma = sigma,
        numPrePeriods = num_pre_periods,
        numPostPeriods = num_post_periods,
        bound = "deviation from parallel trends",
        method = "C-LF",
        Mbarvec = mbar_grid[mbar_index],
        l_vec = l_vec,
        alpha = 0.05,
        gridPoints = 1000,
        parallel = FALSE,
        seed = 20260726
      )
      )
      gc(verbose = FALSE)
      result
    }
  )
  sensitivity <- rbindlist(sensitivity_rows, use.names = TRUE)
  setnames(sensitivity, "Mbar", "M")
  sensitivity[, outcome := outcome_name]
  sensitivity[, target := "average_post_event_time_0_to_23"]
  sensitivity[, excludes_zero := lb > 0 | ub < 0]
  endpoint_tolerance <- 1e-8 * max(1, internal_grid_upper)
  sensitivity[, internal_grid_lower := internal_grid_lower]
  sensitivity[, internal_grid_upper := internal_grid_upper]
  sensitivity[, ci_open_at_internal_grid := (
    lb <= internal_grid_lower + endpoint_tolerance
      | ub >= internal_grid_upper - endpoint_tolerance
  )]
  setcolorder(
    sensitivity,
    c(
      "outcome",
      "target",
      "M",
      "lb",
      "ub",
      "excludes_zero",
      "internal_grid_lower",
      "internal_grid_upper",
      "ci_open_at_internal_grid",
      "method",
      "Delta"
    )
  )

  robust_rows <- sensitivity[excludes_zero == TRUE]
  largest_m <- if (nrow(robust_rows) == 0L) {
    NA_real_
  } else {
    max(robust_rows$M)
  }
  threshold_status <- if (is.na(largest_m)) {
    "not_robust_at_M_0"
  } else if (largest_m == max(mbar_grid)) {
    "at_least_grid_max"
  } else {
    "finite_within_grid"
  }
  open_rows <- sensitivity[ci_open_at_internal_grid == TRUE]
  first_open_m <- if (nrow(open_rows) == 0L) {
    NA_real_
  } else {
    min(open_rows$M)
  }
  plot_path <- plot_sensitivity(
    data.table(
      Mbar = sensitivity$M,
      lb = sensitivity$lb,
      ub = sensitivity$ub
    ),
    outcome_name,
    as.numeric(original$lb),
    as.numeric(original$ub)
  )
  all_results[[outcome_name]] <- sensitivity
  all_summaries[[outcome_name]] <- data.table(
    outcome = outcome_name,
    target = "average_post_event_time_0_to_23",
    target_estimate = sum(l_vec * tail(betahat, num_post_periods)),
    target_standard_error = target_standard_error,
    original_ci_low = as.numeric(original$lb),
    original_ci_high = as.numeric(original$ub),
    largest_evaluated_M_excluding_zero = largest_m,
    threshold_status = threshold_status,
    open_interval_count = nrow(open_rows),
    first_open_interval_M = first_open_m,
    robustness_threshold_precedes_open_grid = (
      is.na(largest_m)
        || is.na(first_open_m)
        || largest_m < first_open_m
    ),
    grid_min = min(mbar_grid),
    grid_max = max(mbar_grid),
    grid_step = mbar_grid[2] - mbar_grid[1],
    num_pre_periods = num_pre_periods,
    num_post_periods = num_post_periods,
    method = "C-LF",
    Delta = "DeltaRM",
    plot_path = basename(plot_path)
  )
}

combined_results <- rbindlist(all_results, use.names = TRUE)
combined_summaries <- rbindlist(all_summaries, use.names = TRUE)
fwrite(combined_results, results_path)
fwrite(combined_summaries, summary_path)

print(combined_summaries)
