#!/usr/bin/env Rscript

# T8A.9: add the smoothness restriction beside the relative-magnitude one.
#
# The V2 release reported only C-LF Delta^RM, which bounds the post-treatment
# violation by the *largest* pre-treatment violation. For a pre-period that
# oscillates without a trend — which is the wage case, where the linear slope
# test does not reject but the joint test does — one noisy lead is enough to
# blow the bound up. Delta^SD bounds the curvature of the differential trend
# instead of its magnitude, so it is the informative restriction for exactly
# that pattern.
#
# This script does not recompute Delta^RM. It reads the released sensitivity
# file, drops any previously appended Delta^SD rows so that repeated runs are
# idempotent, computes Delta^SD, and writes the combined artefacts.
#
# Method: C-LF, the same conditional least-favourable approach used for
# Delta^RM, so the two curves are comparable. The package default for
# Delta^SD is FLCI, which is unavailable here: HonestDiD 0.2.6's FLCI path
# calls CVXR expecting the pre-1.8 return contract and fails on the installed
# CVXR 1.8.1 with "$ operator is invalid for atomic vectors". C-LF is valid
# for both restrictions, so using it for both is the honest resolution rather
# than a silent downgrade.
#
# Grid: M for Delta^SD is in the outcome's own units — it bounds the second
# difference of the differential trend. The grid is declared before
# estimation, spans five orders of magnitude, and ends at the largest absolute
# second difference actually observed in the pre-period, so the reader can see
# where the estimated wiggle sits relative to the breakdown point.

# `HonestDiD` dyn.loads Matrix, lpSolveAPI, TruncatedNormal and pracma lazily,
# from inside its `foreach` loop. On macOS with library validation that late
# load is refused for a process that has already been running, and the run
# dies mid-grid with a `dlopen` policy error rather than a statistical one.
# Loading every native dependency up front removes the failure mode.
suppressPackageStartupMessages({
  library(data.table)
  library(Matrix)
  library(lpSolveAPI)
  library(spacefillr)
  library(TruncatedNormal)
  library(pracma)
  library(foreach)
  library(HonestDiD)
})

script_argument <- grep(
  "^--file=",
  commandArgs(trailingOnly = FALSE),
  value = TRUE
)
if (length(script_argument) != 1L) {
  stop("Unable to resolve honest_did_sd.R location.")
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
results_path <- file.path(diagnostics_dir, "honest_did_sensitivity.csv")
summary_path <- file.path(diagnostics_dir, "honest_did_summary.csv")

coefficients <- fread(coefficients_path)
vcov_long <- fread(vcov_path)
expected_outcomes <- c("asinh_saldo", "ln_salario_real_adm")
observed_outcomes <- sort(unique(coefficients$outcome))
if (!identical(observed_outcomes, expected_outcomes)) {
  stop("HonestDiD inputs must contain exactly the two linear outcomes.")
}
if (!file.exists(results_path) || !file.exists(summary_path)) {
  stop(
    "Delta^RM sensitivity must be produced by honest_did.R before Delta^SD."
  )
}

existing_results <- fread(results_path)
existing_summary <- fread(summary_path)
relative_results <- existing_results[Delta != "DeltaSD"]
relative_summary <- existing_summary[Delta != "DeltaSD"]
if (nrow(relative_results) == 0L || nrow(relative_summary) == 0L) {
  stop("No Delta^RM rows found; refusing to write a Delta^SD-only file.")
}

pre_event_times <- -23:-2
post_event_times <- 0:23
all_event_times <- c(pre_event_times, post_event_times)
num_pre_periods <- length(pre_event_times)
num_post_periods <- length(post_event_times)
l_vec <- rep(1 / num_post_periods, num_post_periods)

# Declared before estimation. The final point is replaced, per outcome, by the
# largest absolute pre-period second difference.
base_m_grid <- c(
  0,
  1e-5,
  2e-5,
  5e-5,
  1e-4,
  2e-4,
  5e-4,
  1e-3,
  2e-3,
  5e-3,
  1e-2
)

# Search region and resolution, declared before estimation.
#
# `createSensitivityResults` chooses its own internal grid of 1000 points and
# does not expose it. For this design that is both unauditable and extremely
# expensive: 22 pre-periods and 24 post-periods make each conditional test
# costly, and a single M can take over an hour. `computeConditionalCS_DeltaSD`
# is called directly instead, with an explicit two-stage grid.
#
# Stage 1 sweeps the whole search region coarsely and locates the accepted set
# to within one coarse step. Stage 2 refines that bracket, so any endpoint that
# is interior — and therefore a real bound — is reported at full resolution
# rather than to the nearest coarse step. Refinement is skipped only when the
# accepted set reaches both boundaries, because then there is no bound to
# locate and a finer grid cannot change the conclusion.
GRID_HALF_WIDTH_IN_TARGET_SE <- 20
COARSE_GRID_POINTS <- 25L
REFINED_GRID_POINTS <- 201L
# An interval is uninformative when it reaches the search boundary, or when it
# is wider than this many target standard errors. Both conditions are recorded;
# neither is presented as a bound.
UNINFORMATIVE_WIDTH_IN_TARGET_SE <- 10

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

evaluate_delta_sd <- function(
  betahat,
  sigma,
  num_pre_periods,
  num_post_periods,
  l_vec,
  m_value,
  target_standard_error
) {
  bound <- GRID_HALF_WIDTH_IN_TARGET_SE * target_standard_error
  accepted_range <- function(grid_lb, grid_ub, grid_points) {
    result <- suppressWarnings(
      computeConditionalCS_DeltaSD(
        betahat = betahat,
        sigma = sigma,
        numPrePeriods = num_pre_periods,
        numPostPeriods = num_post_periods,
        l_vec = l_vec,
        M = m_value,
        alpha = 0.05,
        hybrid_flag = "LF",
        gridPoints = grid_points,
        grid.lb = grid_lb,
        grid.ub = grid_ub,
        seed = 20260726
      )
    )
    accepted <- result$grid[result$accept == 1]
    list(
      accepted = accepted,
      step = (grid_ub - grid_lb) / (grid_points - 1L)
    )
  }

  coarse <- accepted_range(-bound, bound, COARSE_GRID_POINTS)
  if (length(coarse$accepted) == 0L) {
    return(
      list(
        lb = NA_real_,
        ub = NA_real_,
        open_below = FALSE,
        open_above = FALSE,
        empty = TRUE,
        stage = "coarse_empty",
        grid_points = COARSE_GRID_POINTS
      )
    )
  }
  lower <- min(coarse$accepted)
  upper <- max(coarse$accepted)
  tolerance <- 1e-9 * max(1, bound)
  open_below <- lower <= -bound + tolerance
  open_above <- upper >= bound - tolerance
  if (open_below && open_above) {
    return(
      list(
        lb = lower,
        ub = upper,
        open_below = TRUE,
        open_above = TRUE,
        empty = FALSE,
        stage = "coarse_open_both_sides",
        grid_points = COARSE_GRID_POINTS
      )
    )
  }
  # At least one endpoint is a real bound, so it is worth locating precisely.
  # The bracket is widened by one coarse step on each closed side and clipped
  # to the search region on the open side.
  refined <- accepted_range(
    max(lower - coarse$step, -bound),
    min(upper + coarse$step, bound),
    REFINED_GRID_POINTS
  )
  if (length(refined$accepted) == 0L) {
    return(
      list(
        lb = lower,
        ub = upper,
        open_below = open_below,
        open_above = open_above,
        empty = FALSE,
        stage = "refined_empty_fallback_to_coarse",
        grid_points = REFINED_GRID_POINTS
      )
    )
  }
  list(
    lb = min(refined$accepted),
    ub = max(refined$accepted),
    open_below = open_below,
    open_above = open_above,
    empty = FALSE,
    stage = "refined",
    grid_points = REFINED_GRID_POINTS
  )
}

sd_results <- list()
sd_summaries <- list()

for (outcome_name in expected_outcomes) {
  outcome_coefficients <- coefficients[
    outcome == outcome_name
  ][order(position)]
  if (!identical(outcome_coefficients$event_time, all_event_times)) {
    stop(paste("Unexpected event-time order for", outcome_name))
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
  # The pre-period path includes the normalised zero at t = -1, because the
  # curvature of the differential trend is only defined on the full path.
  pre_path <- c(betahat[seq_len(num_pre_periods)], 0)
  pre_second_differences <- diff(diff(pre_path))
  observed_curvature <- max(abs(pre_second_differences))
  m_grid <- sort(unique(c(base_m_grid, observed_curvature)))

  post_indices <- (num_pre_periods + 1L):length(all_event_times)
  post_sigma <- sigma[post_indices, post_indices, drop = FALSE]
  target_standard_error <- sqrt(
    as.numeric(t(l_vec) %*% post_sigma %*% l_vec)
  )
  target_estimate <- sum(l_vec * tail(betahat, num_post_periods))

  rows <- deterministic_map(
    seq_along(m_grid),
    function(index) {
      message(
        sprintf(
          "[DeltaSD] %s M=%.6g (%d/%d)",
          outcome_name,
          m_grid[index],
          index,
          length(m_grid)
        )
      )
      evaluation <- evaluate_delta_sd(
        betahat = betahat,
        sigma = sigma,
        num_pre_periods = num_pre_periods,
        num_post_periods = num_post_periods,
        l_vec = l_vec,
        m_value = m_grid[index],
        target_standard_error = target_standard_error
      )
      row <- data.table(
        M = m_grid[index],
        lb = evaluation$lb,
        ub = evaluation$ub,
        method = "C-LF",
        Delta = "DeltaSD",
        grid_stage = evaluation$stage,
        grid_points = evaluation$grid_points,
        ci_open_below = evaluation$open_below,
        ci_open_above = evaluation$open_above,
        ci_open_at_internal_grid = (
          evaluation$open_below | evaluation$open_above
        ),
        identified_set_empty = evaluation$empty
      )
      gc(verbose = FALSE)
      row
    }
  )
  sensitivity <- rbindlist(rows, use.names = TRUE)
  sensitivity[, outcome := outcome_name]
  sensitivity[, target := "average_post_event_time_0_to_23"]
  sensitivity[, excludes_zero := !is.na(lb) & !is.na(ub) & (lb > 0 | ub < 0)]
  sensitivity[, observed_pre_period_curvature := observed_curvature]
  sensitivity[, internal_grid_lower := (
    -GRID_HALF_WIDTH_IN_TARGET_SE * target_standard_error
  )]
  sensitivity[, internal_grid_upper := (
    GRID_HALF_WIDTH_IN_TARGET_SE * target_standard_error
  )]
  # An interval wider than the declared multiple of the target standard error
  # carries no information about the sign; it is flagged rather than presented
  # as a bound.
  sensitivity[, interval_uninformative := (
    is.na(lb)
      | is.na(ub)
      | (ci_open_below & ci_open_above)
      | (ub - lb) > UNINFORMATIVE_WIDTH_IN_TARGET_SE * target_standard_error
  )]

  robust_rows <- sensitivity[excludes_zero == TRUE]
  largest_m <- if (nrow(robust_rows) == 0L) NA_real_ else max(robust_rows$M)
  threshold_status <- if (is.na(largest_m)) {
    "not_robust_at_M_0"
  } else if (largest_m == max(m_grid)) {
    "at_least_grid_max"
  } else {
    "finite_within_grid"
  }

  sd_results[[outcome_name]] <- sensitivity
  sd_summaries[[outcome_name]] <- data.table(
    outcome = outcome_name,
    target = "average_post_event_time_0_to_23",
    target_estimate = target_estimate,
    target_standard_error = target_standard_error,
    largest_evaluated_M_excluding_zero = largest_m,
    threshold_status = threshold_status,
    observed_pre_period_curvature = observed_curvature,
    breakdown_below_observed_curvature = (
      is.na(largest_m) || largest_m < observed_curvature
    ),
    uninformative_interval_count = sum(sensitivity$interval_uninformative),
    open_interval_count = sum(sensitivity$ci_open_at_internal_grid),
    grid_min = min(m_grid),
    grid_max = max(m_grid),
    grid_points = length(m_grid),
    search_half_width_in_target_se = GRID_HALF_WIDTH_IN_TARGET_SE,
    coarse_grid_points = COARSE_GRID_POINTS,
    refined_grid_points = REFINED_GRID_POINTS,
    num_pre_periods = num_pre_periods,
    num_post_periods = num_post_periods,
    method = "C-LF",
    Delta = "DeltaSD",
    m_units = "absolute_second_difference_of_the_differential_trend"
  )
}

combined_sd <- rbindlist(sd_results, use.names = TRUE, fill = TRUE)
combined_results <- rbindlist(
  list(relative_results, combined_sd),
  use.names = TRUE,
  fill = TRUE
)
combined_summary <- rbindlist(
  list(relative_summary, rbindlist(sd_summaries, use.names = TRUE)),
  use.names = TRUE,
  fill = TRUE
)
setorder(combined_results, outcome, Delta, M)
setorder(combined_summary, outcome, Delta)
fwrite(combined_results, results_path)
fwrite(combined_summary, summary_path)

# One figure per outcome with both restrictions overlaid. Delta^RM's M is a
# ratio and Delta^SD's M is in outcome units, so the horizontal axis is the
# fraction of each restriction's own grid; the axis label says so.
for (outcome_name in expected_outcomes) {
  plot_path <- file.path(
    diagnostics_dir,
    paste0("honest_did_delta_comparison_", outcome_name, ".png")
  )
  png(plot_path, width = 1500, height = 950, res = 150)
  relative <- combined_results[outcome == outcome_name & Delta != "DeltaSD"]
  smooth <- combined_results[outcome == outcome_name & Delta == "DeltaSD"]
  relative_x <- relative$M / max(relative$M)
  smooth_x <- smooth$M / max(smooth$M)
  # The vertical axis is set by DeltaRM. When DeltaSD is uninformative its
  # bounds sit far outside that range by construction, and stretching the axis
  # to fit them would make the informative curve unreadable. The DeltaSD
  # curves are drawn anyway and the legend says how they behave.
  relative_bounds <- c(relative$lb, relative$ub, 0)
  y_range <- range(relative_bounds[is.finite(relative_bounds)])
  padding <- 0.15 * diff(y_range)
  y_range <- c(y_range[1] - padding, y_range[2] + padding)
  smooth_uninformative <- all(smooth$interval_uninformative)
  plot(
    relative_x,
    relative$lb,
    type = "l",
    lwd = 3,
    col = "#1F4E79",
    ylim = y_range,
    xlab = "Share of each restriction's own M grid",
    ylab = "95% robust confidence interval",
    main = paste("HonestDiD: DeltaRM vs DeltaSD -", outcome_name)
  )
  lines(relative_x, relative$ub, lwd = 3, col = "#1F4E79")
  lines(smooth_x, smooth$lb, lwd = 3, col = "#C55A11", lty = 3)
  lines(smooth_x, smooth$ub, lwd = 3, col = "#C55A11", lty = 3)
  abline(h = 0, lty = 2, lwd = 2, col = "#4D4D4D")
  legend(
    "bottomleft",
    legend = c(
      sprintf("DeltaRM (C-LF), M up to %.2f", max(relative$M)),
      sprintf(
        "DeltaSD (C-LF), M up to %.4g%s",
        max(smooth$M),
        if (smooth_uninformative) " - uninformative at every M" else ""
      ),
      "Zero"
    ),
    col = c("#1F4E79", "#C55A11", "#4D4D4D"),
    lty = c(1, 3, 2),
    lwd = c(3, 3, 2),
    bty = "n"
  )
  dev.off()
}

print(combined_summary)
