#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(data.table)
  library(fixest)
})

script_argument <- grep(
  "^--file=",
  commandArgs(trailingOnly = FALSE),
  value = TRUE
)
if (length(script_argument) != 1L) {
  stop("Unable to resolve r12_cross_replication.R location.")
}
script_path_raw <- sub("^--file=", "", script_argument)
if (!file.exists(script_path_raw)) {
  script_path_raw <- gsub("~\\+~", " ", script_path_raw)
}
script_path <- normalizePath(script_path_raw, mustWork = TRUE)
front_root <- dirname(dirname(script_path))
input_path <- file.path(
  front_root,
  "data",
  "vintage",
  "rais_cross_replication_input.csv"
)
output_path <- file.path(
  front_root,
  "results",
  "rais_cross_replication_r.csv"
)

if (!file.exists(input_path)) {
  stop("The frozen RAIS cross-replication input is missing.")
}

setFixest_nthreads(1L)
sample <- fread(
  input_path,
  colClasses = list(character = c("model_id", "outcome", "cbo_4d"))
)

fit_principal <- function(model_key) {
  model_data <- sample[model_id == model_key]
  if (nrow(model_data) == 0L) {
    stop(paste("Missing cross-replication model:", model_key))
  }
  estimator <- unique(model_data$estimator)
  outcome <- unique(model_data$outcome)
  if (length(estimator) != 1L || length(outcome) != 1L) {
    stop(paste("Model metadata is not unique:", model_key))
  }
  model_data[, cbo_4d := factor(cbo_4d)]
  model_data[, ano := factor(ano)]
  if (estimator == "ppml") {
    model <- fepois(
      y ~ post_treat | cbo_4d + ano,
      data = model_data,
      vcov = ~cbo_4d,
      fixef.rm = "perfect_fit",
      notes = FALSE,
      warn = TRUE
    )
  } else if (estimator == "ols") {
    model <- feols(
      y ~ post_treat | cbo_4d + ano,
      data = model_data,
      vcov = ~cbo_4d,
      fixef.rm = "perfect_fit",
      notes = FALSE,
      warn = TRUE
    )
  } else {
    stop(paste("Unsupported estimator:", estimator))
  }
  fixed_effects <- fixef(model, sorted = FALSE, notes = FALSE)
  data.table(
    outcome = outcome,
    estimator = estimator,
    coefficient = unname(coef(model)[["post_treat"]]),
    standard_error = unname(se(model)[["post_treat"]]),
    n_obs = nobs(model),
    n_clusters = length(fixed_effects[["cbo_4d"]])
  )
}

model_ids <- unique(sample$model_id)
results <- rbindlist(
  lapply(model_ids, fit_principal),
  use.names = TRUE
)
setorder(results, outcome)

temporary_path <- paste0(output_path, ".tmp")
fwrite(results, temporary_path)
if (!file.rename(temporary_path, output_path)) {
  stop("Unable to atomically publish the R result.")
}
cat(
  sprintf(
    "{\"models\":%d,\"rows\":%d}\n",
    nrow(results),
    sum(results$n_obs)
  )
)
