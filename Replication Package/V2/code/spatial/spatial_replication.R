#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(data.table)
  library(fixest)
  library(jsonlite)
})

setFixest_nthreads(1L)
setFixest_notes(FALSE)
arguments <- commandArgs(trailingOnly = TRUE)
if (length(arguments) != 7L) {
  stop(
    "Usage: spatial_replication.R STAGE0 SUPPORT CONTRACTS ",
    "MODELS PRETRENDS SUPPORT_RESULTS STATUS"
  )
}
if (paste(R.version$major, R.version$minor, sep = ".") != "4.4.1") {
  stop("The locked replication runtime requires R 4.4.1.")
}

stage0 <- fread(
  arguments[[1L]],
  colClasses = list(character = c(
    "id_municipio", "cbo_municipio", "cbo_periodo", "uf_periodo"
  ))
)
support <- fread(
  arguments[[2L]],
  colClasses = list(character = c(
    "id_municipio", "uf_code", "cbo_municipio", "cbo_periodo", "uf_periodo"
  ))
)
contracts <- fread(arguments[[3L]])

cluster_count <- function(model) {
  value <- attr(vcov(model), "min_cluster_size")
  if (is.null(value) || length(value) != 1L || is.na(value)) {
    stop("Cluster count is unavailable.")
  }
  as.integer(value)
}

event_time_from_term <- function(term) {
  parsed <- sub("^event_time::(-?[0-9]+):.*$", "\\1", term)
  if (identical(parsed, term)) return(NA_integer_)
  as.integer(parsed)
}

pinv <- function(matrix) {
  decomposition <- svd(matrix)
  tolerance <- 1e-15 * max(decomposition$d)
  inverse <- ifelse(decomposition$d > tolerance, 1 / decomposition$d, 0)
  decomposition$v %*% diag(inverse, nrow = length(inverse)) %*%
    t(decomposition$u)
}

classify_pretrend <- function(joint_p, linear_p, individual_count) {
  if (joint_p < 0.05 || linear_p < 0.05 || individual_count >= 2L) {
    return("fail")
  }
  if (joint_p > 0.10 && linear_p > 0.10 && individual_count == 0L) {
    return("pass")
  }
  "warning"
}

model_rows <- list()
diagnostic_rows <- list()
for (index in seq_len(nrow(contracts))) {
  contract <- contracts[index]
  high <- stage0[[contract$high_column]]
  y <- stage0[[contract$outcome]]
  model_data <- copy(stage0)
  model_data[, y := y]
  if (contract$kind == "placebo") {
    model_data[, placebo_post := as.integer(periodo_num >= 202112L)]
    model_data[, placebo_post_high := placebo_post * high]
    model_data[, placebo_triple := placebo_post * treated * high]
    base <- feols(
      y ~ placebo_triple + placebo_post_high |
        cbo_municipio + cbo_periodo + uf_periodo,
      data = model_data,
      fixef.rm = "singleton",
      warn = TRUE
    )
    model <- summary(base, vcov = ~id_municipio, vcov_fix = FALSE)
    model_rows[[length(model_rows) + 1L]] <- data.table(
      model_id = contract$model_id,
      event_time = NA_integer_,
      coefficient = as.numeric(coef(model)[["placebo_triple"]]),
      standard_error = as.numeric(se(model)[["placebo_triple"]]),
      n_obs = as.integer(nobs(model)),
      minimum_clusters = cluster_count(model),
      reference_event_time = NA_integer_,
      status = "estimated"
    )
  } else {
    model_data[, pretrend_high := high]
    model_data[, pretrend_treated_high := treated * high]
    base <- feols(
      y ~ i(event_time, pretrend_treated_high, ref = -1) +
        i(event_time, pretrend_high, ref = -1) |
        cbo_municipio + cbo_periodo + uf_periodo,
      data = model_data,
      fixef.rm = "singleton",
      warn = TRUE
    )
    model <- summary(base, vcov = ~id_municipio, vcov_fix = FALSE)
    coefficient_names <- names(coef(model))
    event_times <- vapply(coefficient_names, event_time_from_term, integer(1L))
    triple_positions <- which(
      !is.na(event_times) & grepl(":pretrend_treated_high$", coefficient_names)
    )
    expected <- -23L:-2L
    if (!identical(unname(event_times[triple_positions]), expected)) {
      stop("Incomplete spatial pretrend grid for ", contract$model_id)
    }
    coefficients <- as.numeric(coef(model)[triple_positions])
    standard_errors <- as.numeric(se(model)[triple_positions])
    model_rows[[length(model_rows) + 1L]] <- data.table(
      model_id = contract$model_id,
      event_time = event_times[triple_positions],
      coefficient = coefficients,
      standard_error = standard_errors,
      n_obs = as.integer(nobs(model)),
      minimum_clusters = cluster_count(model),
      reference_event_time = -1L,
      status = "estimated"
    )
    covariance <- vcov(model)[triple_positions, triple_positions, drop = FALSE]
    symmetric <- 0.5 * (covariance + t(covariance))
    minimum_eigenvalue <- min(eigen(symmetric, symmetric = TRUE)$values)
    scale <- max(abs(diag(symmetric)))
    covariance_is_psd <- minimum_eigenvalue >= -1e-8 * max(scale, 1)
    joint_precision <- solve(covariance, tol = 0)
    joint <- as.numeric(t(coefficients) %*% joint_precision %*% coefficients)
    joint_p <- pchisq(joint, df = length(coefficients), lower.tail = FALSE)
    precision <- pinv(covariance)
    design <- expected + 1L
    denominator <- as.numeric(t(design) %*% precision %*% design)
    slope <- as.numeric(t(design) %*% precision %*% coefficients / denominator)
    slope_se <- sqrt(1 / denominator)
    clusters <- cluster_count(model)
    slope_p <- 2 * pt(-abs(slope / slope_se), df = clusters - 1L)
    individual_p <- 2 * pt(
      -abs(coefficients / standard_errors),
      df = clusters - 1L
    )
    individual_count <- sum(individual_p < 0.05)
    diagnostic_rows[[length(diagnostic_rows) + 1L]] <- data.table(
      model_id = contract$model_id,
      joint_lead_count = length(coefficients),
      joint_lead_statistic = joint,
      joint_lead_p_value = joint_p,
      lead_covariance_min_eigenvalue = minimum_eigenvalue,
      lead_covariance_positive_semidefinite = covariance_is_psd,
      linear_pretrend_coefficient = slope,
      linear_pretrend_standard_error = slope_se,
      linear_pretrend_p_value = slope_p,
      dynamic_pre_p_lt_005 = individual_count,
      dynamic_min_p_value = min(individual_p),
      pretrend_status = classify_pretrend(joint_p, slope_p, individual_count),
      n_obs = as.integer(nobs(model)),
      minimum_clusters = clusters,
      reference_event_time = -1L,
      status = "estimated"
    )
  }
  rm(model_data, base, model)
  gc(verbose = FALSE)
}

effective_clusters <- function(residual, cluster) {
  mass <- data.table(cluster = cluster, mass = residual^2)[, .(mass = sum(mass)), by = cluster]
  shares <- mass$mass / sum(mass$mass)
  1 / sum(shares^2)
}

proxy_specs <- list(
  list(
    proxy = "fixed_broadband_penetration",
    continuous = "penetracao_bl",
    high = "high_connectivity"
  ),
  list(
    proxy = "digital_intensive_admission_share",
    continuous = "digital_admission_share",
    high = "high_digital_admission_share"
  ),
  list(
    proxy = "pnad_internet_use_2021",
    continuous = "internet_use_pct",
    high = "high_pnad_internet_use"
  )
)
support_rows <- list()
for (specification in proxy_specs) {
  support[, support_key := post * treated * get(specification$high)]
  residual_model <- feols(
    support_key ~ 1 | cbo_municipio + cbo_periodo + uf_periodo,
    data = support,
    fixef.rm = "none",
    warn = TRUE
  )
  support[, support_key := NULL]
  if (nobs(residual_model) != nrow(support)) {
    stop("R support residualization removed rows unexpectedly.")
  }
  residual <- resid(residual_model)
  effective_municipalities <- effective_clusters(
    residual,
    support$id_municipio
  )
  effective_ufs <- effective_clusters(residual, support$uf_code)
  municipality_status <- if (
    effective_municipalities >= 50
  ) "adequate" else if (effective_municipalities >= 25) "limited" else "thin"
  uf_status <- if (
    effective_ufs >= 20
  ) "adequate" else if (effective_ufs >= 10) "limited" else "thin"
  classification <- if (
    municipality_status == "thin" || uf_status == "thin"
  ) "thin" else if (
    municipality_status == "limited" || uf_status == "limited"
  ) "limited" else "adequate"
  uf_mass <- data.table(
    uf_code = support$uf_code,
    mass = residual^2
  )[, .(mass = sum(mass)), by = uf_code]
  uf_mass[, leverage := mass / sum(mass)]
  largest <- uf_mass[which.max(leverage)]
  support_rows[[length(support_rows) + 1L]] <- data.table(
    proxy = specification$proxy,
    municipality_clusters_nominal = uniqueN(support$id_municipio),
    uf_clusters_nominal = uniqueN(support$uf_code),
    continuous_proxy_distinct_values = uniqueN(
      support[[specification$continuous]]
    ),
    split_proxy_distinct_values = uniqueN(support[[specification$high]]),
    effective_municipality_clusters = effective_municipalities,
    effective_uf_clusters = effective_ufs,
    largest_uf_leverage_code = largest$uf_code,
    largest_uf_leverage_share = largest$leverage,
    classification = classification
  )
  rm(residual_model, residual)
  gc(verbose = FALSE)
}

model_results <- rbindlist(model_rows, use.names = TRUE)
pretrend_results <- rbindlist(diagnostic_rows, use.names = TRUE)
support_results <- rbindlist(support_rows, use.names = TRUE)
setorder(model_results, model_id, event_time)
setorder(pretrend_results, model_id)
setorder(support_results, proxy)
fwrite(model_results, arguments[[4L]])
fwrite(pretrend_results, arguments[[5L]])
fwrite(support_results, arguments[[6L]])
status <- list(
  family_f_declared_slots = 12L,
  family_f_coefficients_created = 0L,
  family_f_p_values_created = 0L,
  model_rows = nrow(model_results),
  pretrend_models = nrow(pretrend_results),
  r_version = paste(R.version$major, R.version$minor, sep = "."),
  status = "pass",
  support_proxies = nrow(support_results),
  treatment_coefficient_estimated = FALSE
)
write_json(status, arguments[[7L]], auto_unbox = TRUE, pretty = TRUE, digits = 16)
cat(toJSON(status, auto_unbox = TRUE, digits = 16), "\n")
