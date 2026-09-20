#!/usr/bin/env Rscript

# Independent R replication of selected Sections 4–5 DiD and DDD estimates.
# The script uses base R OLS and a manually computed CRV1 covariance matrix.

suppressPackageStartupMessages({
  library(readr)
})

args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 2L) {
  stop(
    paste(
      "Usage: Rscript referee2_replicate_sections4_5_main.R",
      "INPUT_CSV OUTPUT_CSV"
    )
  )
}

input_path <- args[[1]]
output_path <- args[[2]]

data <- read_csv(
  input_path,
  show_col_types = FALSE,
  col_types = cols(
    cbo_4d = col_character(),
    periodo = col_character(),
    income_group_legacy = col_character()
  )
)

controls <- c(
  "idade_media_adm",
  "pct_mulher_adm",
  "pct_superior_adm",
  "pct_negra_adm"
)

cluster_crv1 <- function(model, cluster) {
  x_full <- model.matrix(model)
  rank <- model$rank
  active <- model$qr$pivot[seq_len(rank)]
  x <- x_full[, active, drop = FALSE]
  residuals <- residuals(model)
  cluster_factor <- factor(cluster)
  n_obs <- nrow(x)
  n_clusters <- nlevels(cluster_factor)

  score_rows <- x * as.numeric(residuals)
  scores <- rowsum(score_rows, cluster_factor, reorder = TRUE)
  bread <- solve(crossprod(x))
  meat <- crossprod(scores)

  effective_k <- rank - (n_clusters - 1L)
  correction <- (n_clusters / (n_clusters - 1)) *
    ((n_obs - 1) / (n_obs - effective_k))
  covariance <- correction * bread %*% meat %*% bread
  colnames(covariance) <- colnames(x)
  rownames(covariance) <- colnames(x)
  list(
    covariance = covariance,
    correction = correction,
    rank = rank,
    effective_k = effective_k,
    n_clusters = n_clusters
  )
}

fit_model <- function(
    model_data,
    outcome,
    rhs,
    term,
    model_id,
    estimand,
    group_id = "") {
  formula_text <- paste(
    outcome,
    "~",
    paste(
      c(rhs, controls, "factor(cbo_4d)", "factor(periodo)"),
      collapse = " + "
    )
  )
  model <- lm(as.formula(formula_text), data = model_data)
  retained <- as.integer(names(residuals(model)))
  vcov_result <- cluster_crv1(model, model_data$cbo_4d[retained])

  coefficient <- unname(coef(model)[term])
  standard_error <- sqrt(vcov_result$covariance[term, term])
  statistic <- coefficient / standard_error
  if (estimand == "DiD") {
    p_value <- 2 * pt(
      abs(statistic),
      df = vcov_result$n_clusters - 1L,
      lower.tail = FALSE
    )
    p_distribution <- paste0("t(", vcov_result$n_clusters - 1L, ")")
  } else {
    p_value <- 2 * pnorm(abs(statistic), lower.tail = FALSE)
    p_distribution <- "normal/chi-square(1)"
  }

  data.frame(
    language = "R",
    model_id = model_id,
    estimand = estimand,
    group_id = group_id,
    outcome = outcome,
    term = term,
    coefficient = coefficient,
    standard_error = standard_error,
    p_value = p_value,
    statistic = statistic,
    p_distribution = p_distribution,
    n_obs = nobs(model),
    n_cbo = vcov_result$n_clusters,
    rank = vcov_result$rank,
    effective_k_crv1 = vcov_result$effective_k,
    crv1_factor = vcov_result$correction,
    formula = formula_text,
    stringsAsFactors = FALSE
  )
}

rows <- list()
row_index <- 1L
for (outcome in c(
  "ln_admissoes",
  "ln_desligamentos",
  "ln_salario_adm"
)) {
  rows[[row_index]] <- fit_model(
    data,
    outcome,
    "post_treat",
    "post_treat",
    paste0("national_", outcome),
    "DiD"
  )
  row_index <- row_index + 1L
}

income_models <- data.frame(
  group_id = c(
    "low_income",
    "low_income",
    "middle_income",
    "middle_income",
    "high_income"
  ),
  outcome = c(
    "ln_admissoes",
    "ln_desligamentos",
    "ln_admissoes",
    "ln_desligamentos",
    "ln_desligamentos"
  ),
  stringsAsFactors = FALSE
)

for (index in seq_len(nrow(income_models))) {
  group_id <- income_models$group_id[[index]]
  outcome <- income_models$outcome[[index]]
  model_data <- data
  model_data$group <- as.integer(
    model_data$income_group_legacy == group_id
  )
  model_data$post_group <- model_data$post * model_data$group
  model_data$treat_group <- model_data$treated * model_data$group
  model_data$post_treat_group <- model_data$post_treat * model_data$group
  rows[[row_index]] <- fit_model(
    model_data,
    outcome,
    c(
      "post_treat_group",
      "post_treat",
      "post_group",
      "treat_group"
    ),
    "post_treat_group",
    paste0("income_", group_id, "_", outcome),
    "DDD",
    group_id
  )
  row_index <- row_index + 1L
}

results <- do.call(rbind, rows)
write_csv(results, output_path, na = "")
cat(
  sprintf(
    "Wrote %d independent R estimates to %s.\n",
    nrow(results),
    output_path
  )
)
