#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(data.table)
  library(jsonlite)
})

script_argument <- grep(
  "^--file=",
  commandArgs(trailingOnly = FALSE),
  value = TRUE
)
if (length(script_argument) != 1L) {
  stop("Unable to resolve cross_replication.R location.")
}
script_path_raw <- sub("^--file=", "", script_argument)
if (!file.exists(script_path_raw)) {
  script_path_raw <- gsub("~\\+~", " ", script_path_raw)
}
script_path <- normalizePath(script_path_raw, mustWork = TRUE)
package_root <- dirname(dirname(script_path))
input_path <- file.path(
  package_root,
  "data",
  "derived",
  "cross_replication_input.csv"
)
python_path <- file.path(
  package_root,
  "results",
  "models",
  "specification_ladder.csv"
)
output_dir <- file.path(package_root, "results", "replication")
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)
r_results_path <- file.path(output_dir, "cross_replication_r.csv")
comparison_path <- file.path(
  output_dir,
  "cross_replication_comparison.csv"
)
status_path <- file.path(
  output_dir,
  "cross_replication_status.json"
)

if (!file.exists(input_path)) {
  stop(
    "Cross-replication input is missing. Run ",
    "code/replication/export_cross_replication.py first."
  )
}
if (!file.exists(python_path)) {
  stop("Python specification-ladder results are missing.")
}

sample <- fread(
  input_path,
  colClasses = list(character = c("cbo_4d", "periodo"))
)

two_way_residualize <- function(
  values,
  row_codes,
  column_codes,
  weights = NULL,
  tolerance = 1e-12,
  maximum_iterations = 10000L
) {
  residual <- as.numeric(values)
  if (is.null(weights)) {
    weights <- rep(1, length(residual))
  }
  weights <- as.numeric(weights)
  row_weight <- rowsum(
    weights,
    row_codes,
    reorder = FALSE
  )[, 1]
  column_weight <- rowsum(
    weights,
    column_codes,
    reorder = FALSE
  )[, 1]
  if (any(row_weight <= 0) || any(column_weight <= 0)) {
    stop("Fixed-effect weights must have positive margins.")
  }
  for (iteration in seq_len(maximum_iterations)) {
    previous <- residual
    row_mean <- (
      rowsum(weights * residual, row_codes, reorder = FALSE)[, 1]
        / row_weight
    )
    residual <- residual - row_mean[row_codes]
    column_mean <- (
      rowsum(
        weights * residual,
        column_codes,
        reorder = FALSE
      )[, 1] / column_weight
    )
    residual <- residual - column_mean[column_codes]
    if (max(abs(residual - previous)) < tolerance) {
      return(residual)
    }
  }
  stop("Two-way residualization did not converge.")
}

model_vectors <- function(outcome) {
  model_data <- sample[!is.na(get(outcome))]
  cbo_levels <- sort(unique(model_data$cbo_4d))
  period_levels <- sort(unique(model_data$periodo))
  model_data[, row_code := match(cbo_4d, cbo_levels)]
  model_data[, column_code := match(periodo, period_levels)]
  list(
    data = model_data,
    outcome = model_data[[outcome]],
    treatment = model_data$post_treat,
    row_code = model_data$row_code,
    column_code = model_data$column_code,
    n_rows = length(cbo_levels),
    n_columns = length(period_levels)
  )
}

fit_ppml_margin <- function(vectors, coefficient, tolerance = 1e-12) {
  row_index <- vectors$row_code
  column_index <- vectors$column_code
  row_margin <- rowsum(
    vectors$outcome,
    row_index,
    reorder = FALSE
  )[, 1]
  column_margin <- rowsum(
    vectors$outcome,
    column_index,
    reorder = FALSE
  )[, 1]
  base_weight <- exp(coefficient * vectors$treatment)
  row_effect <- rep(1, vectors$n_rows)
  column_effect <- rep(1, vectors$n_columns)
  for (iteration in seq_len(10000L)) {
    previous <- row_effect
    row_denominator <- rowsum(
      base_weight * column_effect[column_index],
      row_index,
      reorder = FALSE
    )[, 1]
    row_effect <- row_margin / row_denominator
    column_denominator <- rowsum(
      base_weight * row_effect[row_index],
      column_index,
      reorder = FALSE
    )[, 1]
    column_effect <- column_margin / column_denominator
    relative_change <- max(
      abs(row_effect - previous) / (1 + abs(previous))
    )
    if (relative_change < tolerance) {
      fitted <- (
        row_effect[row_index]
          * column_effect[column_index]
          * base_weight
      )
      score <- sum(
        vectors$treatment * (vectors$outcome - fitted)
      )
      return(list(score = score, fitted = fitted))
    }
  }
  stop("PPML margin fitting did not converge.")
}

fit_ppml <- function(outcome) {
  vectors <- model_vectors(outcome)
  lower <- -2
  upper <- 2
  lower_fit <- fit_ppml_margin(vectors, lower)
  upper_fit <- fit_ppml_margin(vectors, upper)
  while (lower_fit$score < 0) {
    lower <- lower * 2
    lower_fit <- fit_ppml_margin(vectors, lower)
  }
  while (upper_fit$score > 0) {
    upper <- upper * 2
    upper_fit <- fit_ppml_margin(vectors, upper)
  }
  total <- sum(vectors$outcome)
  final_fit <- NULL
  for (iteration in seq_len(100L)) {
    midpoint <- (lower + upper) / 2
    midpoint_fit <- fit_ppml_margin(vectors, midpoint)
    if (
      abs(midpoint_fit$score) <= 1e-11 * max(total, 1)
        || upper - lower <= 1e-11
    ) {
      final_fit <- midpoint_fit
      break
    }
    if (midpoint_fit$score > 0) {
      lower <- midpoint
    } else {
      upper <- midpoint
    }
  }
  coefficient <- (lower + upper) / 2
  if (is.null(final_fit)) {
    final_fit <- fit_ppml_margin(vectors, coefficient)
  } else {
    coefficient <- midpoint
  }
  residualized_treatment <- two_way_residualize(
    vectors$treatment,
    vectors$row_code,
    vectors$column_code,
    weights = final_fit$fitted
  )
  score_by_cluster <- rowsum(
    residualized_treatment * (
      vectors$outcome - final_fit$fitted
    ),
    vectors$row_code,
    reorder = FALSE
  )[, 1]
  bread <- sum(
    final_fit$fitted * residualized_treatment^2
  )
  cluster_count <- vectors$n_rows
  observation_count <- length(vectors$outcome)
  effective_parameter_count <- vectors$n_columns + 1L
  crv1 <- (
    cluster_count / (cluster_count - 1)
      * (observation_count - 1)
      / (observation_count - effective_parameter_count)
  )
  standard_error <- sqrt(
    crv1 * sum(score_by_cluster^2) / bread^2
  )
  data.table(
    outcome = outcome,
    estimator = "ppml",
    coefficient = coefficient,
    standard_error = standard_error,
    n_obs = length(vectors$outcome),
    n_clusters = cluster_count
  )
}

fit_ols <- function(outcome) {
  vectors <- model_vectors(outcome)
  residualized_outcome <- two_way_residualize(
    vectors$outcome,
    vectors$row_code,
    vectors$column_code
  )
  residualized_treatment <- two_way_residualize(
    vectors$treatment,
    vectors$row_code,
    vectors$column_code
  )
  bread <- sum(residualized_treatment^2)
  coefficient <- sum(
    residualized_treatment * residualized_outcome
  ) / bread
  residual <- (
    residualized_outcome
      - coefficient * residualized_treatment
  )
  score_by_cluster <- rowsum(
    residualized_treatment * residual,
    vectors$row_code,
    reorder = FALSE
  )[, 1]
  cluster_count <- vectors$n_rows
  observation_count <- length(vectors$outcome)
  effective_parameter_count <- vectors$n_columns + 1L
  crv1 <- (
    cluster_count / (cluster_count - 1)
      * (observation_count - 1)
      / (observation_count - effective_parameter_count)
  )
  standard_error <- sqrt(
    crv1 * sum(score_by_cluster^2) / bread^2
  )
  data.table(
    outcome = outcome,
    estimator = "ols",
    coefficient = coefficient,
    standard_error = standard_error,
    n_obs = length(vectors$outcome),
    n_clusters = cluster_count
  )
}

r_results <- rbindlist(
  list(
    fit_ppml("admissoes"),
    fit_ppml("desligamentos"),
    fit_ppml("n_movimentacoes"),
    fit_ols("ln_salario_real_adm"),
    fit_ols("asinh_saldo")
  ),
  use.names = TRUE
)
fwrite(r_results, r_results_path)

python_results <- fread(python_path)[
  step_id == "01_no_controls",
  .(
    outcome,
    python_estimator = estimator,
    python_coefficient = coefficient,
    python_standard_error = standard_error,
    python_n_obs = n_obs,
    python_n_clusters = minimum_clusters
  )
]
comparison <- merge(
  python_results,
  r_results,
  by = "outcome",
  all = TRUE,
  suffixes = c("", "_r")
)
if (nrow(comparison) != 5L || anyNA(comparison$outcome)) {
  stop("Python and R model sets do not align.")
}
setnames(
  comparison,
  c(
    "estimator",
    "coefficient",
    "standard_error",
    "n_obs",
    "n_clusters"
  ),
  c(
    "r_estimator",
    "r_coefficient",
    "r_standard_error",
    "r_n_obs",
    "r_n_clusters"
  )
)
comparison[
  ,
  coefficient_absolute_difference := abs(
    python_coefficient - r_coefficient
  )
]
comparison[
  ,
  standard_error_absolute_difference := abs(
    python_standard_error - r_standard_error
  )
]
comparison[
  ,
  same_n := python_n_obs == r_n_obs
]
comparison[
  ,
  same_clusters := python_n_clusters == r_n_clusters
]
comparison[
  ,
  coefficient_six_decimals := (
    round(python_coefficient, 6) == round(r_coefficient, 6)
  )
]
comparison[
  ,
  standard_error_six_decimals := (
    round(python_standard_error, 6) == round(r_standard_error, 6)
  )
]
setorder(comparison, outcome)
fwrite(comparison, comparison_path)

status <- list(
  models = nrow(comparison),
  same_n_and_clusters = all(
    comparison$same_n & comparison$same_clusters
  ),
  six_decimal_agreement = all(
    comparison$coefficient_six_decimals
      & comparison$standard_error_six_decimals
  ),
  max_coefficient_absolute_difference = max(
    comparison$coefficient_absolute_difference
  ),
  max_standard_error_absolute_difference = max(
    comparison$standard_error_absolute_difference
  ),
  r_backend = list(
    ppml = "independent iterative proportional fitting in base R",
    ols = "independent two-way Frisch-Waugh-Lovell in base R",
    covariance = paste(
      "independent one-way CBO4 CRV1 score sandwich;",
      "CBO effects nested in cluster, 65 month effects plus regressor"
    )
  )
)
write_json(
  status,
  status_path,
  auto_unbox = TRUE,
  pretty = TRUE,
  digits = 16
)
cat(toJSON(status, auto_unbox = TRUE, digits = 16), "\n")
if (
  !isTRUE(status$same_n_and_clusters)
    || !isTRUE(status$six_decimal_agreement)
) {
  quit(status = 2L)
}
