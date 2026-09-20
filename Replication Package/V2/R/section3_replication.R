#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(data.table)
  library(jsonlite)
})

arguments <- commandArgs(trailingOnly = TRUE)
argument_value <- function(flag) {
  position <- match(flag, arguments)
  if (is.na(position) || position == length(arguments)) {
    stop("Missing required argument: ", flag)
  }
  arguments[[position + 1L]]
}

input_path <- normalizePath(argument_value("--input"), mustWork = TRUE)
output_path <- argument_value("--output")
status_path <- argument_value("--status")
dir.create(dirname(output_path), recursive = TRUE, showWarnings = FALSE)

if (paste(R.version$major, R.version$minor, sep = ".") != "4.4.1") {
  stop("The locked replication runtime requires R 4.4.1.")
}

data <- fread(
  input_path,
  colClasses = list(
    character = c(
      "cod_ocupacao",
      "sigla_uf",
      "match_level",
      "exposure_gradient",
      "grande_grupo",
      "setor_agregado_original",
      "sector_corrected",
      "sexo_texto",
      "raca_agregada",
      "faixa_etaria",
      "faixa_renda_sm"
    )
  )
)

official_gradients <- c(
  "Not Exposed",
  "Minimal Exposure",
  "Exposed: Gradient 1",
  "Exposed: Gradient 2",
  "Exposed: Gradient 3",
  "Exposed: Gradient 4"
)
low_gradients <- c("Not Exposed", "Minimal Exposure")
moderate_gradients <- c("Exposed: Gradient 1", "Exposed: Gradient 2")
high_gradients <- c("Exposed: Gradient 3", "Exposed: Gradient 4")

aggregate_rows <- list()
add_aggregate <- function(scope, key, metric, value) {
  aggregate_rows[[length(aggregate_rows) + 1L]] <<- data.table(
    aggregate_id = paste(scope, key, metric, sep = "::"),
    scope = scope,
    aggregate_key = key,
    metric = metric,
    value = as.numeric(value)
  )
}

weighted_mean <- function(values, weights) {
  valid <- !is.na(values) & !is.na(weights)
  if (!any(valid)) {
    return(NA_real_)
  }
  sum(values[valid] * weights[valid]) / sum(weights[valid])
}

scored <- data[!is.na(exposure_score)]
official <- data[exposure_gradient %chin% official_gradients]
total_weight <- sum(data$peso)
score_weight <- sum(scored$peso)
add_aggregate("base", "sample", "observations", nrow(data))
add_aggregate("base", "sample", "population_m", total_weight / 1e6)
add_aggregate("base", "sample", "scored_population_m", score_weight / 1e6)
add_aggregate("base", "sample", "score_coverage_pct", score_weight / total_weight * 100)
add_aggregate("base", "sample", "four_digit_match_pct", mean(data$match_level == "4-digit") * 100)
add_aggregate("base", "sample", "three_digit_match_pct", mean(data$match_level == "3-digit") * 100)
add_aggregate("base", "sample", "unscored_rows_pct", mean(is.na(data$exposure_score)) * 100)
add_aggregate("base", "sample", "federal_units", uniqueN(data$sigla_uf, na.rm = TRUE))
add_aggregate("base", "sample", "occupations", uniqueN(data$cod_ocupacao, na.rm = TRUE))
add_aggregate("base", "sample", "matched_occupations", uniqueN(scored$cod_ocupacao, na.rm = TRUE))
add_aggregate("base", "sample", "original_sectors", uniqueN(data$setor_agregado_original, na.rm = TRUE))
add_aggregate("base", "sample", "corrected_sectors", uniqueN(data$sector_corrected, na.rm = TRUE))

for (gradient in c(official_gradients, "Sem classificação")) {
  group <- scored[exposure_gradient == gradient]
  weight <- sum(group$peso)
  add_aggregate("gradient", gradient, "population_m", weight / 1e6)
  add_aggregate("gradient", gradient, "share_pct", weight / score_weight * 100)
}

for (label in c("low", "moderate", "high")) {
  gradients <- switch(
    label,
    low = low_gradients,
    moderate = moderate_gradients,
    high = high_gradients
  )
  weight <- sum(official[exposure_gradient %chin% gradients]$peso)
  add_aggregate("exposure_group", label, "population_m", weight / 1e6)
  add_aggregate(
    "exposure_group",
    label,
    "share_pct",
    weight / sum(official$peso) * 100
  )
}

high <- official[exposure_gradient %chin% high_gradients]
top_occupations <- high[
  ,
  .(
    population_m = sum(peso) / 1e6,
    mean_score = weighted_mean(exposure_score, peso)
  ),
  by = .(cod_ocupacao, grande_grupo)
]
setorder(top_occupations, -population_m, cod_ocupacao)
top_occupations <- head(top_occupations, 5L)
for (rank in seq_len(nrow(top_occupations))) {
  row <- top_occupations[rank]
  key <- paste(rank, row$cod_ocupacao, row$grande_grupo, sep = ":")
  add_aggregate("high_occupation", key, "population_m", row$population_m)
  add_aggregate("high_occupation", key, "mean_score", row$mean_score)
}

official_total <- sum(official$peso)
for (sector in sort(unique(official$sector_corrected))) {
  group <- official[sector_corrected == sector]
  total <- sum(group$peso)
  low <- sum(group[exposure_gradient %chin% low_gradients]$peso)
  moderate <- sum(group[exposure_gradient %chin% moderate_gradients]$peso)
  high_weight <- sum(group[exposure_gradient %chin% high_gradients]$peso)
  values <- c(
    population_m = total / 1e6,
    brazil_share_pct = total / official_total * 100,
    mean_score = weighted_mean(group$exposure_score, group$peso),
    low_population_m = low / 1e6,
    low_share_pct = low / total * 100,
    moderate_population_m = moderate / 1e6,
    moderate_share_pct = moderate / total * 100,
    high_population_m = high_weight / 1e6,
    high_share_pct = high_weight / total * 100,
    exposed_population_m = (moderate + high_weight) / 1e6,
    exposed_share_pct = (moderate + high_weight) / total * 100
  )
  for (metric in names(values)) {
    add_aggregate("sector", sector, metric, values[[metric]])
  }
}

dimensions <- list(
  sex = list(column = "sexo_texto", income_only = FALSE),
  race = list(column = "raca_agregada", income_only = FALSE),
  age = list(column = "faixa_etaria", income_only = FALSE),
  education = list(column = "nivel_instrucao", income_only = FALSE),
  income = list(column = "faixa_renda_sm", income_only = TRUE),
  formality = list(column = "formal", income_only = FALSE)
)
for (dimension in names(dimensions)) {
  specification <- dimensions[[dimension]]
  base <- if (specification$income_only) data[tem_renda == 1] else data
  column <- specification$column
  score_base <- base[!is.na(exposure_score)]
  official_base <- base[exposure_gradient %chin% official_gradients]
  categories <- sort(
    unique(
      c(
        as.character(score_base[[column]]),
        as.character(official_base[[column]])
      )
    )
  )
  categories <- categories[!is.na(categories)]
  for (category in categories) {
    score_group <- score_base[as.character(get(column)) == category]
    group <- official_base[as.character(get(column)) == category]
    total <- sum(group$peso)
    low <- sum(group[exposure_gradient %chin% low_gradients]$peso)
    moderate <- sum(group[exposure_gradient %chin% moderate_gradients]$peso)
    high_weight <- sum(group[exposure_gradient %chin% high_gradients]$peso)
    values <- c(
      population_m = total / 1e6,
      mean_score = weighted_mean(score_group$exposure_score, score_group$peso),
      low_share_pct = low / total * 100,
      moderate_share_pct = moderate / total * 100,
      high_share_pct = high_weight / total * 100,
      high_population_m = high_weight / 1e6
    )
    key <- paste(dimension, category, sep = ":")
    for (metric in names(values)) {
      add_aggregate("demographic", key, metric, values[[metric]])
    }
  }
}

for (state in sort(unique(official$sigla_uf))) {
  group <- official[sigla_uf == state]
  total <- sum(group$peso)
  high_weight <- sum(group[exposure_gradient %chin% high_gradients]$peso)
  add_aggregate("state", state, "population_m", total / 1e6)
  add_aggregate("state", state, "high_population_m", high_weight / 1e6)
  add_aggregate("state", state, "high_share_pct", high_weight / total * 100)
}

for (major_group in sort(unique(scored$grande_grupo))) {
  group <- scored[grande_grupo == major_group]
  add_aggregate(
    "occupation_group",
    major_group,
    "population_m",
    sum(group$peso) / 1e6
  )
  add_aggregate(
    "occupation_group",
    major_group,
    "mean_score",
    weighted_mean(group$exposure_score, group$peso)
  )
}

add_aggregate("score_distribution", "all", "minimum", min(scored$exposure_score))
add_aggregate("score_distribution", "all", "maximum", max(scored$exposure_score))
add_aggregate(
  "score_distribution",
  "all",
  "weighted_mean",
  weighted_mean(scored$exposure_score, scored$peso)
)

aggregates <- rbindlist(aggregate_rows, use.names = TRUE)
setnames(aggregates, "aggregate_key", "key")
if (anyDuplicated(aggregates$aggregate_id)) {
  stop("Section 3 aggregate identifiers are not unique.")
}
setorder(aggregates, aggregate_id)
fwrite(aggregates, output_path)

status <- list(
  aggregate_rows = nrow(aggregates),
  data_table_version = as.character(packageVersion("data.table")),
  input_rows = nrow(data),
  r_version = paste(R.version$major, R.version$minor, sep = "."),
  status = "pass"
)
write_json(status, status_path, auto_unbox = TRUE, pretty = TRUE, digits = 16)
cat(toJSON(status, auto_unbox = TRUE, digits = 16), "\n")
