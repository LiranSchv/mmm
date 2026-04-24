#!/usr/bin/env Rscript
# Robyn MMM runner — called via subprocess from robyn_worker.py
# Args: <data_csv> <config_json> <output_json>

suppressPackageStartupMessages({
  library(Robyn)
  library(jsonlite)
  library(data.table)
  library(reticulate)
})

args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 3) stop("Usage: robyn_runner.R <data.csv> <config.json> <output.json>")

data_path   <- args[1]
config_path <- args[2]
output_path <- args[3]

cat("[Robyn] Reading data and config\n")
dt   <- fread(data_path)
cfg  <- fromJSON(config_path)

spend_cols <- cfg$spend_cols          # e.g. ["spend_facebook", "spend_google"]
channels   <- cfg$channels            # e.g. ["facebook", "google"]
iterations <- as.integer(cfg$iterations %||% 200L)
trials     <- as.integer(cfg$trials   %||% 1L)

# Point reticulate at the system Python that has nevergrad installed
python_path <- Sys.getenv("RETICULATE_PYTHON", unset = "/usr/local/bin/python3")
use_python(python_path, required = TRUE)

# Confirm nevergrad is available
if (!py_module_available("nevergrad")) {
  stop("nevergrad Python module not found. Install it with: pip install nevergrad")
}

cat("[Robyn] Building InputCollect\n")

# Build hyperparameter bounds for each channel
# Geometric adstock: thetas (decay 0-0.9), alphas (shape 0.5-3), gammas (saturation 0.3-1)
hyp <- list()
for (col in spend_cols) {
  hyp[[paste0(col, "_thetas")]] <- c(0.0, 0.5)
  hyp[[paste0(col, "_alphas")]] <- c(0.5, 3.0)
  hyp[[paste0(col, "_gammas")]] <- c(0.3, 1.0)
}
hyp[["train_size"]] <- c(0.5, 0.8)

InputCollect <- robyn_inputs(
  dt_input          = dt,
  date_var          = "date",
  dep_var           = "ftbs",
  dep_var_type      = "conversion",
  paid_media_spends = spend_cols,
  paid_media_vars   = spend_cols,
  adstock           = "geometric",
  hyperparameters   = hyp
)

cat("[Robyn] Running model (iterations=", iterations, ", trials=", trials, ")\n", sep = "")

OutputModels <- robyn_run(
  InputCollect    = InputCollect,
  cores           = 1L,
  iterations      = iterations,
  trials          = trials,
  nevergrad_algo  = "TwoPointsDE",
  intercept_sign  = "non_negative",
  add_penalty_factor = FALSE
)

cat("[Robyn] Processing outputs\n")

OutputCollect <- robyn_outputs(
  InputCollect  = InputCollect,
  OutputModels  = OutputModels,
  pareto_fronts = 1L,
  export        = FALSE,
  quiet         = TRUE
)

# Pick best solution (lowest NRMSE on Pareto front)
hyp_df  <- as.data.frame(OutputModels$resultHypParam)
pareto_ids <- OutputCollect$allSolutions
best_id <- pareto_ids[which.min(hyp_df[hyp_df$solID %in% pareto_ids, "nrmse"])]

cat("[Robyn] Best solution:", best_id, "\n")

# ── Channel contributions ────────────────────────────────────────────────────
xda       <- as.data.frame(OutputCollect$xDecompAgg)
xda_best  <- xda[xda$solID == best_id, ]

total_response <- sum(dt$ftbs)

contributions <- lapply(seq_along(channels), function(i) {
  col <- spend_cols[i]
  ch  <- channels[i]
  row <- xda_best[xda_best$rn == col, ]
  contrib_pct <- if (nrow(row) > 0 && "xDecompPerc" %in% names(row))
    as.numeric(row$xDecompPerc[1]) * 100 else 0
  spend_total <- sum(dt[[col]], na.rm = TRUE)
  roi <- if ("roi_total" %in% names(row) && nrow(row) > 0)
    as.numeric(row$roi_total[1])
  else if (spend_total > 0)
    (contrib_pct / 100 * total_response) / spend_total
  else 0
  list(
    channel          = ch,
    contribution_pct = round(contrib_pct, 2),
    spend            = round(spend_total, 2),
    roi              = round(roi, 4)
  )
})

# ── Saturation curves ────────────────────────────────────────────────────────
best_hyps <- hyp_df[hyp_df$solID == best_id, , drop = FALSE]

saturation <- lapply(seq_along(channels), function(i) {
  col   <- spend_cols[i]
  ch    <- channels[i]
  vals  <- dt[[col]]
  max_s <- max(vals, na.rm = TRUE) * 1.5
  if (max_s == 0) max_s <- 1

  spend_range <- seq(0, max_s, length.out = 50)

  # Hill saturation: response = x^alpha / (x^alpha + gamma^alpha * inflection^alpha)
  alpha_col <- paste0(col, "_alphas")
  gamma_col <- paste0(col, "_gammas")
  alpha_val <- if (alpha_col %in% names(best_hyps)) as.numeric(best_hyps[[alpha_col]][1]) else 1.0
  gamma_val <- if (gamma_col %in% names(best_hyps)) as.numeric(best_hyps[[gamma_col]][1]) else 0.5

  inflection <- max_s * gamma_val
  curve <- spend_range^alpha_val / (spend_range^alpha_val + inflection^alpha_val + 1e-10)

  current   <- mean(vals, na.rm = TRUE)
  threshold <- quantile(vals, 0.75, na.rm = TRUE)

  list(
    channel     = ch,
    curve_points = lapply(seq_along(spend_range), function(j)
      list(spend = round(spend_range[j], 2), response = round(curve[j], 4))
    ),
    current_spend = round(current, 2),
    threshold     = round(as.numeric(threshold), 2),
    is_saturated  = current > as.numeric(threshold)
  )
})

# ── Model metrics ────────────────────────────────────────────────────────────
best_row <- hyp_df[hyp_df$solID == best_id, , drop = FALSE]
metrics <- list(
  r2    = round(if ("rsq_train" %in% names(best_row)) as.numeric(best_row$rsq_train[1]) else 0.0, 4),
  mape  = round(if ("mape"      %in% names(best_row)) as.numeric(best_row$mape[1]) * 100 else 0.0, 2),
  nrmse = round(if ("nrmse"     %in% names(best_row)) as.numeric(best_row$nrmse[1]) else 0.0, 4)
)

# ── Decomposition by date ────────────────────────────────────────────────────
decomp_vec <- tryCatch({
  dv <- as.data.frame(OutputCollect$xDecompVec)
  dv[dv$solID == best_id, ]
}, error = function(e) NULL)

decomposition <- if (!is.null(decomp_vec) && nrow(decomp_vec) > 0) {
  lapply(seq_len(nrow(decomp_vec)), function(j) {
    row <- list(
      date     = format(as.Date(decomp_vec$ds[j]), "%Y-%m-%d"),
      baseline = round(as.numeric(decomp_vec$intercept[j]), 1)
    )
    for (i in seq_along(channels)) {
      col <- spend_cols[i]
      ch  <- channels[i]
      if (col %in% names(decomp_vec))
        row[[ch]] <- round(as.numeric(decomp_vec[[col]][j]), 1)
    }
    row
  })
} else {
  # Fallback: even split across dates
  lapply(seq_len(nrow(dt)), function(j) {
    row <- list(date = as.character(dt$date[j]), baseline = round(dt$ftbs[j] * 0.35, 1))
    for (i in seq_along(channels)) {
      ch <- channels[i]
      contrib_pct <- contributions[[i]]$contribution_pct
      row[[ch]] <- round(dt$ftbs[j] * contrib_pct / 100, 1)
    }
    row
  })
}

# ── Write output ─────────────────────────────────────────────────────────────
results <- list(
  metrics        = metrics,
  contributions  = contributions,
  saturation     = saturation,
  decomposition  = decomposition
)

write(toJSON(results, auto_unbox = TRUE, null = "null"), output_path)
cat("[Robyn] Done. Results written to", output_path, "\n")
