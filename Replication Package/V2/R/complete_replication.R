#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(data.table)
  library(fixest)
  library(jsonlite)
  library(MASS)
})

setFixest_notes(FALSE)

# The --contracts argument points to the generated model_contracts.csv file.
arguments <- commandArgs(trailingOnly = TRUE)

argument_value <- function(flag) {
  position <- match(flag, arguments)
  if (is.na(position) || position == length(arguments)) {
    stop("Missing required argument: ", flag)
  }
  arguments[[position + 1L]]
}

contract_path <- normalizePath(
  argument_value("--contracts"),
  mustWork = TRUE
)
input_dir <- normalizePath(
  argument_value("--input-dir"),
  mustWork = TRUE
)
output_dir <- argument_value("--output-dir")
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)

if (paste(R.version$major, R.version$minor, sep = ".") != "4.4.1") {
  stop("The locked replication runtime requires R 4.4.1.")
}

contracts <- fread(contract_path, na.strings = c("", "NA"))
forbidden_contract_columns <- c(
  "coefficient",
  "standard_error",
  "python_coefficient",
  "python_standard_error"
)
if (length(intersect(names(contracts), forbidden_contract_columns)) > 0L) {
  stop("Model contracts must not contain Python estimates.")
}
if (anyDuplicated(contracts$model_id)) {
  stop("Model identifiers are not unique.")
}

data_cache <- new.env(parent = emptyenv())

load_input <- function(filename) {
  if (!exists(filename, envir = data_cache, inherits = FALSE)) {
    path <- file.path(input_dir, filename)
    if (!file.exists(path)) {
      stop("Analytical input is missing: ", path)
    }
    assign(filename, fread(path), envir = data_cache)
  }
  get(filename, envir = data_cache, inherits = FALSE)
}

subset_for_contract <- function(data, contract) {
  expression <- parse(text = contract$sample_filter)[[1L]]
  keep <- eval(expression, envir = data, enclos = parent.frame())
  if (length(keep) == 1L && isTRUE(keep)) {
    sample <- copy(data)
  } else {
    if (length(keep) != nrow(data) || anyNA(keep)) {
      stop("Invalid sample filter for ", contract$model_id)
    }
    sample <- data[keep]
  }
  if (contract$model_type == "event") {
    sample <- sample[
      event_time >= as.integer(contract$event_min)
        & event_time <= as.integer(contract$event_max)
    ]
  }
  if (nrow(sample) == 0L) {
    stop("Model sample is empty for ", contract$model_id)
  }
  sample
}

fit_contract <- function(contract, sample) {
  formula <- as.formula(contract$formula)
  cluster_formula <- as.formula(
    paste0("~", contract$cluster_variables)
  )
  # Keep fixed-effect absorption at pyfixest's declared tolerance. fixest and
  # pyfixest use different IWLS stopping statistics, so the stricter R rule
  # below is needed for their independently computed clustered sandwich
  # matrices to satisfy the public 1e-6 contract. It does not use a Python
  # coefficient, standard error, or fitted value.
  if (contract$estimator == "ppml") {
    model <- fepois(
      formula,
      data = sample,
      fixef.rm = "perfect_fit",
      fixef.tol = 1e-8,
      fixef.iter = 100000,
      glm.tol = 1e-9,
      warn = TRUE
    )
  } else if (contract$estimator == "ols") {
    model <- feols(
      formula,
      data = sample,
      fixef.rm = "perfect_fit",
      fixef.tol = 1e-8,
      fixef.iter = 100000,
      warn = TRUE
    )
  } else {
    stop("Unsupported estimator: ", contract$estimator)
  }
  summary(model, vcov = cluster_formula, vcov_fix = FALSE)
}

cluster_count <- function(model) {
  value <- attr(vcov(model), "min_cluster_size")
  if (is.null(value) || length(value) != 1L || is.na(value)) {
    stop("Cluster count is unavailable for the fitted model.")
  }
  as.integer(value)
}

event_time_from_term <- function(term) {
  parsed <- sub("^event_time::(-?[0-9]+):.*$", "\\1", term)
  if (identical(parsed, term)) {
    return(NA_integer_)
  }
  as.integer(parsed)
}

base_result_fields <- function(contract, model) {
  list(
    analysis_family = contract$analysis_family,
    model_id = contract$model_id,
    outcome = contract$outcome,
    estimator = contract$estimator,
    n_obs = as.integer(nobs(model)),
    minimum_clusters = cluster_count(model),
    sample_id = contract$sample_id,
    status = "estimated",
    reference_event_time = if (
      contract$model_type == "event"
    ) as.integer(contract$reference_event_time) else NA_integer_
  )
}

extract_result_rows <- function(contract, model) {
  base <- base_result_fields(contract, model)
  coefficients <- coef(model)
  standard_errors <- se(model)
  if (contract$model_type == "static") {
    if (!(contract$term %in% names(coefficients))) {
      stop(
        "Registered term ", contract$term,
        " is absent for ", contract$model_id
      )
    }
    row <- data.table(
      term = contract$term,
      event_time = NA_integer_,
      is_reference = FALSE,
      coefficient = as.numeric(coefficients[[contract$term]]),
      standard_error = as.numeric(standard_errors[[contract$term]])
    )
    for (name in names(base)) {
      row[, (name) := base[[name]]]
    }
    setcolorder(
      row,
      c(
        names(base),
        "term",
        "event_time",
        "is_reference",
        "coefficient",
        "standard_error"
      )
    )
    return(row)
  }

  times <- vapply(names(coefficients), event_time_from_term, integer(1L))
  positions <- which(!is.na(times))
  expected <- setdiff(
    seq.int(as.integer(contract$event_min), as.integer(contract$event_max)),
    as.integer(contract$reference_event_time)
  )
  observed <- unname(sort(times[positions]))
  if (!identical(observed, expected)) {
    stop("Incomplete event-time grid for ", contract$model_id)
  }
  rows <- data.table(
    term = names(coefficients)[positions],
    event_time = times[positions],
    is_reference = FALSE,
    coefficient = as.numeric(coefficients[positions]),
    standard_error = as.numeric(standard_errors[positions])
  )
  rows <- rbind(
    rows,
    data.table(
      term = "reference_event_time",
      event_time = as.integer(contract$reference_event_time),
      is_reference = TRUE,
      coefficient = 0,
      standard_error = 0
    ),
    use.names = TRUE
  )
  for (name in names(base)) {
    rows[, (name) := base[[name]]]
  }
  setcolorder(
    rows,
    c(
      names(base),
      "term",
      "event_time",
      "is_reference",
      "coefficient",
      "standard_error"
    )
  )
  setorder(rows, event_time)
  rows
}

honest_did_inputs <- function(contract, model) {
  expected_model_ids <- paste0(
    "national_event::balanced::",
    c("asinh_saldo", "ln_salario_real_adm")
  )
  if (!(contract$model_id %in% expected_model_ids)) {
    return(NULL)
  }

  expected_event_times <- c(-23:-2, 0:23)
  coefficient_names <- names(coef(model))
  event_times <- vapply(
    coefficient_names,
    event_time_from_term,
    integer(1L)
  )
  positions <- match(expected_event_times, event_times)
  if (anyNA(positions)) {
    stop("Incomplete HonestDiD event grid for ", contract$model_id)
  }
  covariance <- vcov(model)[positions, positions, drop = FALSE]
  if (
    anyNA(covariance)
      || !isTRUE(all.equal(covariance, t(covariance), tolerance = 1e-10))
  ) {
    stop("Invalid HonestDiD covariance for ", contract$model_id)
  }

  coefficients <- data.table(
    outcome = contract$outcome,
    estimator = contract$estimator,
    position = 0:(length(expected_event_times) - 1L),
    event_time = expected_event_times,
    coefficient = as.numeric(coef(model)[positions]),
    is_pre = expected_event_times < -1L
  )
  covariance_long <- CJ(
    row_position = 0:(length(expected_event_times) - 1L),
    column_position = 0:(length(expected_event_times) - 1L)
  )
  covariance_long[, row_event_time := expected_event_times[row_position + 1L]]
  covariance_long[, column_event_time := expected_event_times[column_position + 1L]]
  covariance_long[, covariance := as.vector(t(covariance))]
  covariance_long[, outcome := contract$outcome]
  setcolorder(
    covariance_long,
    c(
      "outcome",
      "row_position",
      "column_position",
      "row_event_time",
      "column_event_time",
      "covariance"
    )
  )
  list(coefficients = coefficients, covariance = covariance_long)
}

classify_pretrend <- function(joint_p, linear_p, individual_count) {
  if (
    joint_p < 0.05
      || linear_p < 0.05
      || individual_count >= 2L
  ) {
    return("fail")
  }
  if (
    joint_p > 0.10
      && linear_p > 0.10
      && individual_count == 0L
  ) {
    return("pass")
  }
  "warning"
}

diagnose_model <- function(contract, model) {
  if (is.na(contract$diagnostic_lead_min)) {
    return(NULL)
  }
  coefficient_names <- names(coef(model))
  event_times <- vapply(
    coefficient_names,
    event_time_from_term,
    integer(1L)
  )
  lead_positions <- which(
    event_times >= as.integer(contract$diagnostic_lead_min)
      & event_times <= -2L
  )
  expected_leads <- seq.int(
    as.integer(contract$diagnostic_lead_min),
    -2L
  )
  if (!identical(unname(event_times[lead_positions]), expected_leads)) {
    stop("Incomplete diagnostic lead grid for ", contract$model_id)
  }
  coefficients <- as.numeric(coef(model)[lead_positions])
  full_covariance <- vcov(model)
  covariance <- full_covariance[lead_positions, lead_positions, drop = FALSE]
  symmetric_covariance <- 0.5 * (covariance + t(covariance))
  eigenvalues <- eigen(
    symmetric_covariance,
    symmetric = TRUE,
    only.values = TRUE
  )$values
  minimum_eigenvalue <- min(eigenvalues)
  scale <- max(abs(diag(symmetric_covariance)))
  psd_tolerance <- -1e-8 * max(scale, 1)
  covariance_is_psd <- minimum_eigenvalue >= psd_tolerance
  singular_values <- svd(
    symmetric_covariance,
    nu = 0L,
    nv = 0L
  )$d
  rank_tolerance <- max(dim(symmetric_covariance)) *
    .Machine$double.eps * max(singular_values)
  covariance_rank <- sum(singular_values > rank_tolerance)
  covariance_dimension <- nrow(symmetric_covariance)
  covariance_is_full_rank <- covariance_rank == covariance_dimension
  covariance_condition_number <- if (covariance_is_full_rank) {
    max(singular_values) / min(singular_values)
  } else {
    Inf
  }
  # Match the registered diagnostics, not fixest's optional PSD repair. The
  # joint Wald statistic uses a direct inverse of the raw covariance, while
  # the GLS slope uses the same SVD tolerance as numpy.linalg.pinv. Keeping
  # these paths separate is material for the explicitly reported non-PSD
  # diagnostics.
  # NumPy's registered Wald test delegates directly to LAPACK and does not
  # apply R's reciprocal-condition-number rejection. Setting tol = 0 keeps
  # this independent calculation on the same declared numerical contract;
  # the separate PSD diagnostic remains unchanged and visible.
  joint_df <- length(coefficients)
  degrees_freedom <- cluster_count(model) - 1L
  lead_standard_errors <- se(model)[lead_positions]
  individual_p <- 2 * pt(
    -abs(coefficients / lead_standard_errors),
    df = degrees_freedom
  )
  individual_count <- sum(individual_p < 0.05)
  if (covariance_is_full_rank) {
    joint_precision <- solve(covariance, tol = 0)
    joint_statistic <- as.numeric(
      t(coefficients) %*% joint_precision %*% coefficients
    )
    joint_p <- pchisq(
      joint_statistic,
      df = joint_df,
      lower.tail = FALSE
    )
    design <- as.numeric(
      expected_leads - as.integer(contract$reference_event_time)
    )
    decomposition <- svd(covariance)
    inverse_tolerance <- 1e-15 * max(decomposition$d)
    inverse_values <- ifelse(
      decomposition$d > inverse_tolerance,
      1 / decomposition$d,
      0
    )
    precision <- decomposition$v %*%
      diag(inverse_values, nrow = length(inverse_values)) %*%
      t(decomposition$u)
    denominator <- as.numeric(t(design) %*% precision %*% design)
    if (!is.finite(denominator) || denominator <= 0) {
      return(data.table(
        analysis_family = contract$analysis_family,
        model_id = contract$model_id,
        outcome = contract$outcome,
        estimator = contract$estimator,
        joint_lead_count = NA_integer_,
        joint_lead_statistic = NA_real_,
        joint_lead_p_value = NA_real_,
        lead_covariance_positive_semidefinite = covariance_is_psd,
        lead_covariance_min_eigenvalue = minimum_eigenvalue,
        lead_covariance_dimension = covariance_dimension,
        lead_covariance_rank = covariance_rank,
        lead_covariance_full_rank = covariance_is_full_rank,
        lead_covariance_condition_number = covariance_condition_number,
        lead_covariance_rank_tolerance = rank_tolerance,
        lead_covariance_psd_tolerance = psd_tolerance,
        linear_pretrend_coefficient = NA_real_,
        linear_pretrend_standard_error = NA_real_,
        linear_pretrend_p_value = NA_real_,
        dynamic_pre_p_lt_005 = individual_count,
        dynamic_min_p_value = min(individual_p),
        pretrend_status = "not_estimated",
        n_obs = as.integer(nobs(model)),
        minimum_clusters = cluster_count(model),
        sample_id = contract$sample_id,
        status = "failed_estimation",
        reference_event_time = as.integer(contract$reference_event_time)
      ))
    }
    linear_coefficient <- as.numeric(
      t(design) %*% precision %*% coefficients / denominator
    )
    linear_standard_error <- sqrt(1 / denominator)
    linear_p <- 2 * pt(
      -abs(linear_coefficient / linear_standard_error),
      df = degrees_freedom
    )
    pretrend_status <- classify_pretrend(
      joint_p,
      linear_p,
      individual_count
    )
  } else {
    joint_statistic <- NA_real_
    joint_p <- NA_real_
    linear_coefficient <- NA_real_
    linear_standard_error <- NA_real_
    linear_p <- NA_real_
    pretrend_status <- "not_interpretable_rank_deficient"
  }
  data.table(
    analysis_family = contract$analysis_family,
    model_id = contract$model_id,
    outcome = contract$outcome,
    estimator = contract$estimator,
    joint_lead_count = joint_df,
    joint_lead_statistic = joint_statistic,
    joint_lead_p_value = joint_p,
    lead_covariance_positive_semidefinite = covariance_is_psd,
    lead_covariance_min_eigenvalue = minimum_eigenvalue,
    lead_covariance_dimension = covariance_dimension,
    lead_covariance_rank = covariance_rank,
    lead_covariance_full_rank = covariance_is_full_rank,
    lead_covariance_condition_number = covariance_condition_number,
    lead_covariance_rank_tolerance = rank_tolerance,
    lead_covariance_psd_tolerance = psd_tolerance,
    linear_pretrend_coefficient = linear_coefficient,
    linear_pretrend_standard_error = linear_standard_error,
    linear_pretrend_p_value = linear_p,
    dynamic_pre_p_lt_005 = individual_count,
    dynamic_min_p_value = min(individual_p),
    pretrend_status = pretrend_status,
    n_obs = as.integer(nobs(model)),
    minimum_clusters = cluster_count(model),
    sample_id = contract$sample_id,
    status = "estimated",
    reference_event_time = as.integer(contract$reference_event_time)
  )
}

result_chunks <- list()
diagnostic_chunks <- list()
failure_rows <- list()
honest_coefficient_chunks <- list()
honest_covariance_chunks <- list()

for (index in seq_len(nrow(contracts))) {
  contract <- contracts[index]
  tryCatch(
    {
      data <- load_input(contract$data_file)
      sample <- subset_for_contract(data, contract)
      model <- fit_contract(contract, sample)
      result_chunks[[length(result_chunks) + 1L]] <- extract_result_rows(
        contract,
        model
      )
      honest_inputs <- honest_did_inputs(contract, model)
      if (!is.null(honest_inputs)) {
        honest_coefficient_chunks[[length(honest_coefficient_chunks) + 1L]] <-
          honest_inputs$coefficients
        honest_covariance_chunks[[length(honest_covariance_chunks) + 1L]] <-
          honest_inputs$covariance
      }
      diagnostic <- diagnose_model(contract, model)
      if (!is.null(diagnostic)) {
        diagnostic[, independent_engine_status := status]
        diagnostic[, independent_engine_pretrend_status := pretrend_status]
        diagnostic_chunks[[length(diagnostic_chunks) + 1L]] <- diagnostic
        if (!identical(diagnostic$status[[1L]], contract$expected_status)) {
          failure_rows[[length(failure_rows) + 1L]] <- data.table(
            model_id = contract$model_id,
            error = paste0(
              "Diagnostic status differs from the registered contract: ",
              diagnostic$status[[1L]],
              " vs ",
              contract$expected_status
            )
          )
        }
      }
      cat(
        sprintf(
          "[R COMPLETE] %d/%d %s estimated\n",
          index,
          nrow(contracts),
          contract$model_id
        )
      )
    },
    error = function(error) {
      failure_rows[[length(failure_rows) + 1L]] <<- data.table(
        model_id = contract$model_id,
        error = substr(conditionMessage(error), 1L, 1000L)
      )
      cat(
        sprintf(
          "[R COMPLETE] %d/%d %s failed: %s\n",
          index,
          nrow(contracts),
          contract$model_id,
          conditionMessage(error)
        )
      )
    }
  )
}

results <- if (length(result_chunks)) {
  rbindlist(result_chunks, use.names = TRUE, fill = TRUE)
} else {
  data.table()
}
diagnostics <- if (length(diagnostic_chunks)) {
  rbindlist(diagnostic_chunks, use.names = TRUE, fill = TRUE)
} else {
  data.table()
}
failures <- if (length(failure_rows)) {
  rbindlist(failure_rows, use.names = TRUE, fill = TRUE)
} else {
  data.table(model_id = character(), error = character())
}
honest_coefficients <- rbindlist(
  honest_coefficient_chunks,
  use.names = TRUE,
  fill = TRUE
)
honest_covariance <- rbindlist(
  honest_covariance_chunks,
  use.names = TRUE,
  fill = TRUE
)

if (
  nrow(honest_coefficients) != 92L
    || nrow(honest_covariance) != 4232L
    || anyDuplicated(honest_coefficients[, .(outcome, event_time)])
    || anyDuplicated(
      honest_covariance[, .(outcome, row_event_time, column_event_time)]
    )
) {
  stop("Independent R HonestDiD input grid is incomplete")
}

if (nrow(results)) {
  setorder(results, model_id, event_time, term)
}
if (nrow(diagnostics)) {
  setorder(diagnostics, model_id)
}
setorder(failures, model_id)

fwrite(results, file.path(output_dir, "r_model_results.csv"))
fwrite(diagnostics, file.path(output_dir, "r_pretrend_diagnostics.csv"))
fwrite(failures, file.path(output_dir, "r_failures.csv"))
fwrite(
  honest_coefficients,
  file.path(output_dir, "honest_did_event_coefficients.csv")
)
fwrite(
  honest_covariance,
  file.path(output_dir, "honest_did_event_vcov_long.csv")
)

package_names <- c("data.table", "fixest", "jsonlite", "MASS")
package_versions <- setNames(
  lapply(package_names, function(package) as.character(packageVersion(package))),
  package_names
)
status <- list(
  contracts = nrow(contracts),
  diagnostic_backend_status_divergences = if (nrow(diagnostics)) sum(
    diagnostics$status != diagnostics$independent_engine_status
  ) else 0L,
  diagnostic_models = nrow(diagnostics),
  failed_models = nrow(failures),
  honest_did_coefficient_rows = nrow(honest_coefficients),
  honest_did_covariance_rows = nrow(honest_covariance),
  model_result_rows = nrow(results),
  packages = package_versions,
  r_version = paste(R.version$major, R.version$minor, sep = "."),
  status = if (nrow(failures) == 0L) "pass" else "fail"
)
write_json(
  status,
  file.path(output_dir, "r_status.json"),
  auto_unbox = TRUE,
  pretty = TRUE,
  digits = 16
)
cat(toJSON(status, auto_unbox = TRUE, digits = 16), "\n")

if (nrow(failures) > 0L) {
  quit(status = 2L)
}
