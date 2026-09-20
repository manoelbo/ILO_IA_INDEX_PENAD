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
  stop("Usage: pnadc_pretrend_cross_replication.R INPUT OUTPUT STATUS")
}
data <- fread(
  arguments[[1L]],
  colClasses = list(character = c("model_id", "outcome", "sample", "arm", "cod3"))
)
output_path <- arguments[[2L]]
status_path <- arguments[[3L]]

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
  sample_data <- data[model_id == current_model_id]
  arm <- unique(sample_data$arm)
  outcome <- unique(sample_data$outcome)
  sample_name <- unique(sample_data$sample)
  original_n <- unique(sample_data$original_n)
  if (arm == "A") {
    base <- feols(
      y ~ i(event_time, treated, ref = -1) | cod3 + trimestre_num,
      data = sample_data,
      weights = ~regression_weight,
      fixef.rm = "perfect_fit",
      warn = TRUE
    )
  } else {
    base <- fepois(
      y ~ i(event_time, treated, ref = -1) | cod3 + trimestre_num,
      data = sample_data,
      fixef.rm = "perfect_fit",
      warn = TRUE
    )
  }
  model <- summary(base, vcov = ~cod3, vcov_fix = FALSE)
  covariance <- vcov(model)
  if (arm == "A") {
    df_k <- as.integer(degrees_freedom(model, type = "k"))
    collapsed_n <- nobs(model)
    collapsed_adjustment <- (collapsed_n - 1) / (collapsed_n - df_k)
    original_adjustment <- (original_n - 1) / (original_n - df_k)
    covariance <- covariance * (original_adjustment / collapsed_adjustment)
  }
  coefficient_names <- names(coef(model))
  event_times <- as.integer(
    sub("^event_time::(-?[0-9]+):.*$", "\\1", coefficient_names)
  )
  expected <- setdiff(sort(unique(sample_data$event_time)), -1L)
  if (!identical(sort(event_times), expected)) {
    stop("Incomplete PNADc event grid for ", model_id)
  }
  lead_positions <- which(event_times < -1L)
  lead_times <- event_times[lead_positions]
  coefficients <- as.numeric(coef(model)[lead_positions])
  standard_errors <- sqrt(diag(covariance))[lead_positions]
  lead_covariance <- covariance[lead_positions, lead_positions, drop = FALSE]
  symmetric <- 0.5 * (lead_covariance + t(lead_covariance))
  minimum_eigenvalue <- min(eigen(symmetric, symmetric = TRUE)$values)
  scale <- max(abs(diag(symmetric)))
  psd <- minimum_eigenvalue >= -1e-8 * max(scale, 1)
  precision <- pinv(lead_covariance)
  joint <- as.numeric(
    t(coefficients) %*% solve(lead_covariance, coefficients, tol = 0)
  )
  joint_p <- pchisq(joint, df = length(coefficients), lower.tail = FALSE)
  design <- lead_times + 1L
  denominator <- as.numeric(t(design) %*% precision %*% design)
  slope <- as.numeric(t(design) %*% precision %*% coefficients / denominator)
  slope_se <- sqrt(1 / denominator)
  clusters <- uniqueN(sample_data$cod3)
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
    sample = sample_name,
    arm = arm,
    reference_event_time = -1L,
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
    n_obs = as.integer(original_n),
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
