#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(data.table)
  library(fixest)
  library(jsonlite)
})

setFixest_nthreads(1L)
setFixest_notes(FALSE)
arguments <- commandArgs(trailingOnly = TRUE)
if (length(arguments) != 3L) {
  stop("Usage: r_pretrends.R INPUT_CSV OUTPUT_CSV STATUS_JSON")
}
input_path <- arguments[[1L]]
output_path <- arguments[[2L]]
status_path <- arguments[[3L]]
data <- fread(
  input_path,
  colClasses = list(character = c("model_id", "outcome", "cbo_4d"))
)

pinv <- function(matrix) {
  decomposition <- svd(matrix)
  tolerance <- 1e-15 * max(decomposition$d)
  inverse <- ifelse(decomposition$d > tolerance, 1 / decomposition$d, 0)
  decomposition$v %*% diag(inverse, nrow = length(inverse)) %*%
    t(decomposition$u)
}

rows <- list()
for (model_id in sort(unique(data$model_id))) {
  current_model_id <- model_id
  sample <- data[model_id == current_model_id]
  estimator <- unique(sample$estimator)
  outcome <- unique(sample$outcome)
  reference <- unique(sample$reference_event_time)
  expected <- sort(unique(sample$event_time))
  formula <- y ~ i(event_time, treated_main, ref = 0) | cbo_4d + ano
  base <- if (estimator == "ppml") {
    fepois(formula, data = sample, fixef.rm = "perfect_fit", warn = TRUE)
  } else {
    feols(formula, data = sample, fixef.rm = "perfect_fit", warn = TRUE)
  }
  model <- summary(base, vcov = ~cbo_4d, vcov_fix = FALSE)
  names <- names(coef(model))
  event_times <- as.integer(
    sub("^event_time::(-?[0-9]+):.*$", "\\1", names)
  )
  if (!identical(sort(event_times), setdiff(expected, reference))) {
    stop("Incomplete RAIS event grid for ", model_id)
  }
  lead_positions <- which(event_times < reference)
  lead_times <- event_times[lead_positions]
  coefficients <- as.numeric(coef(model)[lead_positions])
  standard_errors <- as.numeric(se(model)[lead_positions])
  covariance <- vcov(model)[lead_positions, lead_positions, drop = FALSE]
  symmetric <- 0.5 * (covariance + t(covariance))
  minimum_eigenvalue <- min(eigen(symmetric, symmetric = TRUE)$values)
  scale <- max(abs(diag(symmetric)))
  psd <- minimum_eigenvalue >= -1e-8 * max(scale, 1)
  precision <- pinv(covariance)
  joint <- as.numeric(t(coefficients) %*% precision %*% coefficients)
  joint_p <- pchisq(joint, df = length(coefficients), lower.tail = FALSE)
  design <- lead_times - reference
  denominator <- as.numeric(t(design) %*% precision %*% design)
  slope <- as.numeric(t(design) %*% precision %*% coefficients / denominator)
  slope_se <- sqrt(1 / denominator)
  clusters <- as.integer(attr(vcov(model), "min_cluster_size"))
  cluster_df <- clusters - 1L
  slope_p <- 2 * pt(-abs(slope / slope_se), df = cluster_df)
  individual_p <- 2 * pt(
    -abs(coefficients / standard_errors),
    df = cluster_df
  )
  individual_count <- sum(individual_p < 0.05)
  pretrend_status <- if (
    joint_p < 0.05 || slope_p < 0.05 || individual_count >= 2L
  ) {
    "fail"
  } else if (joint_p > 0.10 && slope_p > 0.10 && individual_count == 0L) {
    "pass"
  } else {
    "warning"
  }
  rows[[length(rows) + 1L]] <- data.table(
    model_id = model_id,
    outcome = outcome,
    estimator = estimator,
    reference_event_time = reference,
    joint_lead_count = length(coefficients),
    joint_lead_statistic = joint,
    joint_lead_p_value = joint_p,
    lead_covariance_min_eigenvalue = minimum_eigenvalue,
    lead_covariance_positive_semidefinite = psd,
    linear_pretrend_coefficient = slope,
    linear_pretrend_standard_error = slope_se,
    linear_pretrend_p_value = slope_p,
    dynamic_pre_p_lt_005 = individual_count,
    dynamic_min_p_value = min(individual_p),
    pretrend_status = pretrend_status,
    n_obs = nobs(model),
    minimum_clusters = clusters,
    status = "estimated"
  )
}

results <- rbindlist(rows, use.names = TRUE)
setorder(results, model_id)
fwrite(results, output_path)
status <- list(
  models = nrow(results),
  r_version = paste(R.version$major, R.version$minor, sep = "."),
  status = "pass"
)
write_json(status, status_path, auto_unbox = TRUE, pretty = TRUE, digits = 16)
cat(toJSON(status, auto_unbox = TRUE, digits = 16), "\n")
