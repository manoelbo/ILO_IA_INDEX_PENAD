#!/usr/bin/env Rscript

args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 1L) {
  stop("Usage: validate_environment.R RENV_LOCK")
}
if (!requireNamespace("jsonlite", quietly = TRUE)) {
  stop("Package jsonlite is required; run renv::restore() first.")
}

lock_path <- normalizePath(args[[1L]], mustWork = TRUE)
lock <- jsonlite::fromJSON(lock_path, simplifyVector = FALSE)
expected_r <- lock$R$Version
actual_r <- as.character(getRversion())
if (utils::compareVersion(actual_r, expected_r) != 0L) {
  stop(sprintf("R version mismatch: expected %s, found %s", expected_r, actual_r))
}

expected_packages <- names(lock$Packages)
installed_packages <- rownames(utils::installed.packages())
missing_packages <- setdiff(expected_packages, installed_packages)
if (length(missing_packages) > 0L) {
  stop(
    sprintf(
      "Locked packages are missing: %s. Run renv::restore() first.",
      paste(missing_packages, collapse = ", ")
    )
  )
}

mismatches <- Filter(
  Negate(is.null),
  lapply(expected_packages, function(package) {
    expected <- lock$Packages[[package]]$Version
    actual <- as.character(utils::packageVersion(package))
    if (utils::compareVersion(actual, expected) == 0L) {
      return(NULL)
    }
    sprintf("%s expected %s found %s", package, expected, actual)
  })
)
if (length(mismatches) > 0L) {
  stop(sprintf("Locked package mismatch: %s", paste(mismatches, collapse = "; ")))
}

cat(
  jsonlite::toJSON(
    list(
      locked_packages = length(expected_packages),
      r_version = actual_r,
      status = "pass"
    ),
    auto_unbox = TRUE
  ),
  "\n",
  sep = ""
)
