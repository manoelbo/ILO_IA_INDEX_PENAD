#!/usr/bin/env Rscript

# Independent base-R replay of the four central V1 models.

suppressPackageStartupMessages(library(sandwich))

args <- commandArgs(trailingOnly = TRUE)
script_args <- commandArgs(trailingOnly = FALSE)
script_flag <- grep("^--file=", script_args, value = TRUE)
if (length(script_flag) != 1) {
  stop("Unable to resolve this script's directory.")
}
script_path <- sub("^--file=", "", script_flag)
script_path <- gsub("~\\+~", " ", script_path)
script_dir <- dirname(normalizePath(script_path))
input_path <- if (length(args) >= 1) args[[1]] else file.path(
  script_dir, "cross_language_input.csv"
)
output_path <- if (length(args) >= 2) args[[2]] else file.path(
  script_dir, "r_results.csv"
)

data <- read.csv(
  input_path,
  stringsAsFactors = FALSE,
  colClasses = c(cbo_4d = "character", periodo = "character")
)

outcomes <- c(
  "ln_admissoes",
  "ln_desligamentos",
  "ln_salario_adm",
  "asinh_saldo"
)
controls <- c(
  "idade_media_adm",
  "pct_mulher_adm",
  "pct_superior_adm",
  "pct_negra_adm"
)

rows <- lapply(outcomes, function(outcome) {
  slope_terms <- paste(c("post_treat", controls), collapse = " + ")
  full_formula <- as.formula(paste(
    outcome,
    "~",
    slope_terms,
    "+ factor(cbo_4d) + factor(periodo)"
  ))
  model <- lm(full_formula, data = data, na.action = na.omit)
  used <- as.integer(rownames(model$model))
  clusters <- data$cbo_4d[used]
  n_obs <- nobs(model)
  n_clusters <- length(unique(clusters))

  # pyfixest/fixest CRV1 counts non-nested time effects in the finite-sample
  # correction but not occupation effects nested in the clustering variable.
  nonnested_formula <- as.formula(paste(
    outcome,
    "~",
    slope_terms,
    "+ factor(periodo)"
  ))
  nonnested_matrix <- model.matrix(
    nonnested_formula,
    data = data[used, , drop = FALSE]
  )
  k_nonnested <- qr(nonnested_matrix)$rank
  correction <- (
    n_clusters / (n_clusters - 1)
    * (n_obs - 1) / (n_obs - k_nonnested)
  )
  raw_vcov <- vcovCL(
    model,
    cluster = clusters,
    type = "HC0",
    cadjust = FALSE
  )
  corrected_vcov <- raw_vcov * correction

  estimate <- unname(coef(model)[["post_treat"]])
  standard_error <- unname(sqrt(diag(corrected_vcov))[["post_treat"]])
  p_value <- 2 * pt(
    -abs(estimate / standard_error),
    df = n_clusters - 1
  )
  data.frame(
    outcome = outcome,
    coef = estimate,
    se = standard_error,
    p_value = p_value,
    n_obs = n_obs,
    n_clusters = n_clusters,
    formula = paste(deparse(full_formula), collapse = ""),
    estimator = "stats::lm",
    vcov = "sandwich::vcovCL CRV1, cluster=cbo_4d",
    stringsAsFactors = FALSE
  )
})

results <- do.call(rbind, rows)
options(digits = 17)
write.table(
  results,
  file = output_path,
  sep = ",",
  quote = TRUE,
  row.names = FALSE,
  col.names = TRUE,
  na = ""
)
cat(sprintf("Wrote R replay for %d outcomes to %s\n", nrow(results), output_path))
