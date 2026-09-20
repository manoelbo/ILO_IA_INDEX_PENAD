#!/usr/bin/env Rscript

suppressPackageStartupMessages(library(fixest))

args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 2) {
  stop("Usage: pnadc_cross_replication.R INPUT_CSV OUTPUT_CSV")
}

input_path <- args[[1]]
output_path <- args[[2]]
data <- read.csv(input_path, stringsAsFactors = FALSE)

required_columns <- c(
  "model_id",
  "outcome",
  "arm",
  "cod3",
  "trimestre_num",
  "post_treat",
  "outcome_value",
  "regression_weight",
  "source_observations",
  "original_n"
)
if (!all(required_columns %in% names(data))) {
  stop("Cross-replication input has an invalid schema")
}
if (any(grepl("cod4", names(data), ignore.case = TRUE))) {
  stop("COD4 is forbidden in the PNADc cross-replication")
}

model_ids <- unique(data$model_id)
if (length(model_ids) != 6) {
  stop("The PNADc cross-replication requires six models")
}

rows <- vector("list", length(model_ids))
for (index in seq_along(model_ids)) {
  model_id <- model_ids[[index]]
  subset <- data[data$model_id == model_id, , drop = FALSE]
  arm <- unique(subset$arm)
  outcome <- unique(subset$outcome)
  original_n <- unique(subset$original_n)
  if (length(arm) != 1 || length(outcome) != 1 || length(original_n) != 1) {
    stop(paste("Inconsistent identifiers for", model_id))
  }

  if (arm == "A") {
    fit <- feols(
      outcome_value ~ post_treat | cod3 + trimestre_num,
      data = subset,
      weights = ~regression_weight,
      cluster = ~cod3,
      ssc = ssc(
        K.adj = TRUE,
        K.fixef = "nonnested",
        G.adj = TRUE,
        G.df = "min",
        t.df = "min"
      ),
      warn = TRUE
    )
    df_k <- as.integer(degrees_freedom(fit, type = "k"))
    collapsed_n <- nobs(fit)
    collapsed_adjustment <- (collapsed_n - 1) / (collapsed_n - df_k)
    original_adjustment <- (original_n - 1) / (original_n - df_k)
    standard_error <- unname(se(fit)[["post_treat"]]) *
      sqrt(original_adjustment / collapsed_adjustment)
  } else if (arm == "B") {
    fit <- fepois(
      outcome_value ~ post_treat | cod3 + trimestre_num,
      data = subset,
      cluster = ~cod3,
      ssc = ssc(
        K.adj = TRUE,
        K.fixef = "nonnested",
        G.adj = TRUE,
        G.df = "min",
        t.df = "min"
      ),
      warn = TRUE
    )
    df_k <- as.integer(degrees_freedom(fit, type = "k"))
    collapsed_n <- nobs(fit)
    standard_error <- unname(se(fit)[["post_treat"]])
  } else {
    stop(paste("Unknown arm for", model_id))
  }

  rows[[index]] <- data.frame(
    model_id = model_id,
    outcome = outcome,
    arm = arm,
    coefficient = unname(coef(fit)[["post_treat"]]),
    standard_error = standard_error,
    n_obs = as.integer(original_n),
    n_clusters = length(unique(subset$cod3)),
    computational_rows = as.integer(collapsed_n),
    df_k = df_k,
    engine = "fixest",
    stringsAsFactors = FALSE
  )
}

result <- do.call(rbind, rows)
temporary_path <- paste0(output_path, ".tmp")
write.csv(result, temporary_path, row.names = FALSE, na = "")
if (!file.rename(temporary_path, output_path)) {
  stop("Unable to atomically publish R cross-replication results")
}
