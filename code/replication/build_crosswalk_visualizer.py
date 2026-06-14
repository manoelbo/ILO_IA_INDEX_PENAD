#!/usr/bin/env python3
"""Build a static CBO -> ISCO-08 crosswalk visualizer.

This is a standalone audit artifact. It reads existing crosswalk outputs and
does not run any dissertation regressions or change the main analysis pipeline.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "outputs" / "crosswalk_visualizer"
ASSET_DIR = OUT_DIR / "assets"

BRIDGE_FILE = ROOT / "outputs" / "crosswalk_audit" / "official_mte_bridge" / "caged_mte_bridge_full.csv"
ILO_FILE = ROOT / "data" / "processed" / "ilo_exposure_clean.csv"
PANEL_FILE = ROOT / "data" / "output" / "painel_2b_ready.parquet"

CSV_PATH = OUT_DIR / "cbo_isco08_crosswalk_visual.csv"
HTML_PATH = OUT_DIR / "index.html"
JS_PATH = ASSET_DIR / "crosswalk_visualizer.js"
CSS_PATH = ASSET_DIR / "crosswalk_visualizer.css"

MATCHED_STATUS = "matched_official_mte"
NO_MATCH_STATUS = "sem_match_mte_no_result"
MEAN_SCORE_HIGH_EXPOSURE_CUTOFF = 0.50
MEAN_SCORE_ANY_EXPOSURE_CUTOFF = 0.28
ILO_HIGH_EXPOSURE_BOUNDARY = 0.50
ILO_GRADIENT_4_MEAN_CUTOFF = 0.60
ILO_GRADIENT_3_MEAN_CUTOFF = 0.50
ILO_GRADIENT_2_MEAN_CUTOFF = 0.40
ILO_MINIMAL_EXPOSURE_BOUNDARY = 0.40


def ensure_dirs() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ASSET_DIR.mkdir(parents=True, exist_ok=True)


def read_inputs() -> tuple[pd.DataFrame, pd.DataFrame]:
    missing = [path for path in [BRIDGE_FILE, ILO_FILE] if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing required inputs:\n" + "\n".join(str(path) for path in missing))

    bridge = pd.read_csv(BRIDGE_FILE, dtype={"cbo_4d": str, "cbo_3d": str, "cbo_2d": str, "cbo_1d": str})
    ilo = pd.read_csv(ILO_FILE, dtype={"isco_08_str": str})

    bridge["cbo_4d"] = bridge["cbo_4d"].astype(str).str.zfill(4)
    for col in ["cbo_3d", "cbo_2d", "cbo_1d"]:
        if col in bridge.columns:
            width = int(col.split("_")[1][0])
            bridge[col] = bridge[col].astype(str).str.extract(r"(\d+)", expand=False).str.zfill(width)
    ilo["isco_08_str"] = ilo["isco_08_str"].astype(str).str.extract(r"(\d+)", expand=False).str.zfill(4)
    return bridge, ilo


def split_codes(value: object, width: int = 4) -> list[str]:
    if value is None or pd.isna(value):
        return []
    return [code.zfill(width) for code in re.findall(r"\d+", str(value))]


def split_titles(value: object) -> list[str]:
    if value is None or pd.isna(value):
        return []
    return [part.strip() for part in str(value).split(";") if part.strip()]


def as_float(value: object) -> float:
    if value is None or pd.isna(value):
        return np.nan
    try:
        return float(value)
    except (TypeError, ValueError):
        return np.nan


def as_int(value: object) -> int:
    if value is None or pd.isna(value):
        return 0
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def fmt_score(value: float) -> str:
    return "" if pd.isna(value) else f"{float(value):.6f}"


def pooled_equal_weight_sd(scores: list[float], sds: list[float]) -> float:
    if not scores or len(scores) != len(sds):
        return np.nan
    mean_score = float(np.mean(scores))
    variances = [(sd ** 2) + ((score - mean_score) ** 2) for score, sd in zip(scores, sds)]
    return float(np.sqrt(np.mean(variances)))


def classify_ilo_mean_sd(mean_score: float, sd_score: float) -> str:
    if pd.isna(mean_score) or pd.isna(sd_score):
        return "No score"
    if mean_score >= ILO_GRADIENT_4_MEAN_CUTOFF and mean_score - sd_score >= ILO_HIGH_EXPOSURE_BOUNDARY:
        return "Exposed: Gradient 4"
    if ILO_GRADIENT_3_MEAN_CUTOFF <= mean_score < ILO_GRADIENT_4_MEAN_CUTOFF and mean_score + sd_score >= ILO_HIGH_EXPOSURE_BOUNDARY:
        return "Exposed: Gradient 3"
    if ILO_GRADIENT_2_MEAN_CUTOFF <= mean_score < ILO_GRADIENT_3_MEAN_CUTOFF and mean_score + sd_score >= ILO_HIGH_EXPOSURE_BOUNDARY:
        return "Exposed: Gradient 2"
    if mean_score < ILO_GRADIENT_2_MEAN_CUTOFF and mean_score + sd_score >= ILO_HIGH_EXPOSURE_BOUNDARY:
        return "Exposed: Gradient 1"
    if mean_score < ILO_HIGH_EXPOSURE_BOUNDARY and mean_score + sd_score > ILO_MINIMAL_EXPOSURE_BOUNDARY:
        return "Minimal Exposure"
    return "Not Exposed"


def gradient_number(label: object) -> int:
    if label is None or pd.isna(label):
        return 0
    match = re.search(r"Gradient\s+([1-4])", str(label))
    return int(match.group(1)) if match else 0


def gradient_key(label: str | None) -> str:
    if not label:
        return "no_score"
    number = gradient_number(label)
    if number:
        return f"gradient_{number}"
    text = label.lower()
    if "minimal" in text:
        return "minimal"
    if "not exposed" in text:
        return "not_exposed"
    return "no_score"


def share_in(values: list[int], accepted: set[int]) -> float:
    if not values:
        return np.nan
    return sum(value in accepted for value in values) / len(values)


def json_safe(value: object) -> object:
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [json_safe(item) for item in value]
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (np.integer, int)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return None if pd.isna(value) or np.isinf(value) else float(value)
    if value is None:
        return None
    if pd.isna(value):
        return None
    return value


def build_rows(bridge: pd.DataFrame, ilo: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, object], list[dict[str, object]]]:
    title_map = dict(zip(ilo["isco_08_str"], ilo["occupation_title"]))
    score_map = dict(zip(ilo["isco_08_str"], pd.to_numeric(ilo["exposure_score"], errors="coerce")))
    sd_map = dict(zip(ilo["isco_08_str"], pd.to_numeric(ilo["exposure_sd"], errors="coerce")))
    gradient_map = dict(zip(ilo["isco_08_str"], ilo["exposure_gradient"]))

    total_admissions = float(pd.to_numeric(bridge["admissoes_total"], errors="coerce").fillna(0).sum())
    valid_mte_scores = pd.to_numeric(
        bridge.loc[bridge["mte_match_status"].eq(MATCHED_STATUS), "exposure_score_mte_2d"],
        errors="coerce",
    ).dropna()

    thresholds = {
        "mte_top10_cutoff": float(valid_mte_scores.quantile(0.90)),
        "mte_top20_cutoff": float(valid_mte_scores.quantile(0.80)),
        "mte_top30_cutoff": float(valid_mte_scores.quantile(0.70)),
    }

    records = []
    ui_records = []

    for _, row in bridge.sort_values("cbo_4d").iterrows():
        codes = split_codes(row.get("target_isco08_codes"))
        bridge_titles = split_titles(row.get("target_isco08_titles"))
        isco_items = []
        scored_gradients = []
        scored_codes = []
        scored_scores = []
        scored_sds = []
        scored_score_sd_pairs = []

        for idx, code in enumerate(codes):
            score = as_float(score_map.get(code, np.nan))
            sd = as_float(sd_map.get(code, np.nan))
            gradient = gradient_map.get(code, "")
            fallback_title = bridge_titles[idx] if idx < len(bridge_titles) else ""
            title = str(title_map.get(code, fallback_title) or fallback_title or "ISCO-08 title not found")
            item = {
                "code": code,
                "title": title,
                "score": None if pd.isna(score) else round(float(score), 6),
                "score_display": fmt_score(score),
                "sd": None if pd.isna(sd) else round(float(sd), 6),
                "sd_display": fmt_score(sd),
                "gradient": "" if pd.isna(gradient) else str(gradient),
                "gradient_key": gradient_key("" if pd.isna(gradient) else str(gradient)),
            }
            isco_items.append(item)
            if not pd.isna(score):
                scored_codes.append(code)
                scored_scores.append(float(score))
                scored_gradients.append(gradient_number(gradient))
            if not pd.isna(sd):
                scored_sds.append(float(sd))
            if not pd.isna(score) and not pd.isna(sd):
                scored_score_sd_pairs.append((float(score), float(sd)))

        share_g34 = share_in(scored_gradients, {3, 4})
        share_g12 = share_in(scored_gradients, {1, 2})
        share_g1234 = share_in(scored_gradients, {1, 2, 3, 4})
        isco08_mean_score = float(np.mean(scored_scores)) if scored_scores else np.nan
        isco08_pooled_sd = pooled_equal_weight_sd(
            [score for score, _ in scored_score_sd_pairs],
            [sd for _, sd in scored_score_sd_pairs],
        )
        cbo_ilo_gradient = classify_ilo_mean_sd(isco08_mean_score, isco08_pooled_sd)
        cbo_ilo_gradient_number = gradient_number(cbo_ilo_gradient)
        mte_score = as_float(row.get("exposure_score_mte_2d"))
        admissions = as_int(row.get("admissoes_total"))
        panel_rows = as_int(row.get("panel_rows"))
        admissions_pct = admissions / total_admissions if total_admissions else 0.0
        status = str(row.get("mte_match_status", ""))
        is_matched = status == MATCHED_STATUS
        gradient_keys = sorted({item["gradient_key"] for item in isco_items})
        gradient_labels = [item["gradient"] or "No score" for item in isco_items]
        score_values = [item["score_display"] for item in isco_items]
        is_mixed = len({key for key in gradient_keys if key != "no_score"}) > 1
        high_caged_weight = admissions_pct >= 0.002
        legacy_alta_expo = bool(not pd.isna(share_g34) and share_g34 >= 0.75)
        legacy_media_expo = bool(not pd.isna(share_g12) and share_g12 >= 0.75)
        legacy_expostos = bool(not pd.isna(share_g1234) and share_g1234 >= 0.75)

        if not scored_scores:
            mean_score_alta_expo = False
            mean_score_media_expo = False
            mean_score_expostos = False
        elif is_mixed:
            mean_score_alta_expo = isco08_mean_score >= MEAN_SCORE_HIGH_EXPOSURE_CUTOFF
            mean_score_media_expo = (
                MEAN_SCORE_ANY_EXPOSURE_CUTOFF <= isco08_mean_score < MEAN_SCORE_HIGH_EXPOSURE_CUTOFF
            )
            mean_score_expostos = isco08_mean_score >= MEAN_SCORE_ANY_EXPOSURE_CUTOFF
        else:
            mean_score_alta_expo = legacy_alta_expo
            mean_score_media_expo = legacy_media_expo
            mean_score_expostos = legacy_expostos

        trat_alta_expo = cbo_ilo_gradient_number in {3, 4}
        trat_media_expo = cbo_ilo_gradient_number in {1, 2}
        trat_expostos = cbo_ilo_gradient_number in {1, 2, 3, 4}
        treatment_rule_source = "no_scored_isco08" if not scored_score_sd_pairs else "ilo_mean_sd_crosswalk"

        treatment_changed_by_ilo_rule = bool(
            trat_alta_expo != mean_score_alta_expo
            or trat_media_expo != mean_score_media_expo
            or trat_expostos != mean_score_expostos
        )

        n_missing_sds = len(codes) - len(
            {
                code
                for code in codes
                if not pd.isna(sd_map.get(code, np.nan))
            }
        )
        sd_values = [
            item["sd_display"]
            for item in isco_items
        ]

        if not scored_score_sd_pairs:
            trat_alta_expo = False
            trat_media_expo = False
            trat_expostos = False
            treatment_changed_by_ilo_rule = bool(
                mean_score_alta_expo or mean_score_media_expo or mean_score_expostos
            )

        record = {
            "cbo_4d": row.get("cbo_4d", ""),
            "cbo_title": "" if pd.isna(row.get("source_cbo_title")) else row.get("source_cbo_title"),
            "cbo_2d": "" if pd.isna(row.get("cbo_2d")) else row.get("cbo_2d"),
            "cbo_2d_title": "" if pd.isna(row.get("source_cbo_2d_title")) else row.get("source_cbo_2d_title"),
            "mte_match_status": status,
            "crosswalk_status_label": "Com MTE" if is_matched else "Sem crosswalk MTE",
            "isco08_codes": "; ".join(codes),
            "isco08_titles": "; ".join([item["title"] for item in isco_items]),
            "isco08_gradients": "; ".join(gradient_labels),
            "isco08_scores": "; ".join(score_values),
            "isco08_sds": "; ".join(sd_values),
            "n_isco08_codes": len(codes),
            "n_scored_isco08_codes": len(scored_codes),
            "n_missing_isco08_scores": len(codes) - len(scored_codes),
            "n_missing_isco08_sds": n_missing_sds,
            "share_gradient_3_4": share_g34,
            "share_gradient_1_2": share_g12,
            "share_gradient_1_4": share_g1234,
            "isco08_mean_score": isco08_mean_score,
            "isco08_pooled_sd": isco08_pooled_sd,
            "cbo_ilo_gradient": cbo_ilo_gradient,
            "cbo_ilo_gradient_key": gradient_key(cbo_ilo_gradient),
            "trat_alta_expo": bool(trat_alta_expo),
            "trat_media_expo": bool(trat_media_expo),
            "trat_expostos": bool(trat_expostos),
            "treatment_rule_source": treatment_rule_source,
            "treatment_changed_by_ilo_rule": treatment_changed_by_ilo_rule,
            "trat_alta_expo_mean_score_legacy": bool(mean_score_alta_expo),
            "trat_media_expo_mean_score_legacy": bool(mean_score_media_expo),
            "trat_expostos_mean_score_legacy": bool(mean_score_expostos),
            "trat_alta_expo_75pct_legacy": legacy_alta_expo,
            "trat_media_expo_75pct_legacy": legacy_media_expo,
            "trat_expostos_75pct_legacy": legacy_expostos,
            "mte_2d_mean_score": mte_score,
            "trat_mte_top10": bool(is_matched and not pd.isna(mte_score) and mte_score >= thresholds["mte_top10_cutoff"]),
            "trat_mte_top20": bool(is_matched and not pd.isna(mte_score) and mte_score >= thresholds["mte_top20_cutoff"]),
            "trat_mte_top30": bool(is_matched and not pd.isna(mte_score) and mte_score >= thresholds["mte_top30_cutoff"]),
            "caged_admissions_total": admissions,
            "caged_admissions_pct": admissions_pct,
            "caged_panel_rows": panel_rows,
            "mixed_gradient_profile": bool(is_mixed),
            "high_caged_weight": bool(high_caged_weight),
            "isco08_items_json": json.dumps(isco_items, ensure_ascii=False),
        }
        records.append(record)

        ui_record = dict(record)
        ui_record.pop("isco08_items_json")
        ui_record["isco08_items"] = isco_items
        ui_record["gradient_keys"] = gradient_keys
        ui_records.append(ui_record)

    out = pd.DataFrame(records)
    summary = {
        "total_cbo": int(len(out)),
        "matched_cbo": int(out["mte_match_status"].eq(MATCHED_STATUS).sum()),
        "unmatched_cbo": int(out["mte_match_status"].eq(NO_MATCH_STATUS).sum()),
        "total_admissions": int(out["caged_admissions_total"].sum()),
        "matched_admissions": int(out.loc[out["mte_match_status"].eq(MATCHED_STATUS), "caged_admissions_total"].sum()),
        "unmatched_admissions": int(out.loc[out["mte_match_status"].eq(NO_MATCH_STATUS), "caged_admissions_total"].sum()),
        "mixed_cbo": int(out["mixed_gradient_profile"].sum()),
        "ilo_rule_changed_cbo": int(out["treatment_changed_by_ilo_rule"].sum()),
        "treatment_counts": {
            "trat_alta_expo": int(out["trat_alta_expo"].sum()),
            "trat_media_expo": int(out["trat_media_expo"].sum()),
            "trat_expostos": int(out["trat_expostos"].sum()),
        },
        "cbo_ilo_gradient_counts": {
            key: int(value)
            for key, value in out["cbo_ilo_gradient"].value_counts().sort_index().to_dict().items()
        },
        "thresholds": thresholds,
        "ilo_mean_sd_rule": {
            "applies_to": "all_cbo_with_scored_isco08_and_sd",
            "gradient_4": "mu >= 0.6 and mu - sd >= 0.5",
            "gradient_3": "0.5 <= mu < 0.6 and mu + sd >= 0.5",
            "gradient_2": "0.4 <= mu < 0.5 and mu + sd >= 0.5",
            "gradient_1": "mu < 0.4 and mu + sd >= 0.5",
            "minimal_exposure": "mu < 0.5 and mu + sd > 0.4",
        },
        "generated_from": {
            "bridge_file": str(BRIDGE_FILE.relative_to(ROOT)),
            "ilo_file": str(ILO_FILE.relative_to(ROOT)),
            "panel_file_for_context": str(PANEL_FILE.relative_to(ROOT)) if PANEL_FILE.exists() else "",
        },
    }
    return out, summary, ui_records


def write_csv(df: pd.DataFrame) -> None:
    ordered_columns = [
        "cbo_4d",
        "cbo_title",
        "cbo_2d",
        "cbo_2d_title",
        "mte_match_status",
        "crosswalk_status_label",
        "isco08_codes",
        "isco08_titles",
        "isco08_gradients",
        "isco08_scores",
        "isco08_sds",
        "n_isco08_codes",
        "n_scored_isco08_codes",
        "n_missing_isco08_scores",
        "n_missing_isco08_sds",
        "share_gradient_3_4",
        "share_gradient_1_2",
        "share_gradient_1_4",
        "isco08_mean_score",
        "isco08_pooled_sd",
        "cbo_ilo_gradient",
        "cbo_ilo_gradient_key",
        "trat_alta_expo",
        "trat_media_expo",
        "trat_expostos",
        "treatment_rule_source",
        "treatment_changed_by_ilo_rule",
        "trat_alta_expo_mean_score_legacy",
        "trat_media_expo_mean_score_legacy",
        "trat_expostos_mean_score_legacy",
        "trat_alta_expo_75pct_legacy",
        "trat_media_expo_75pct_legacy",
        "trat_expostos_75pct_legacy",
        "mte_2d_mean_score",
        "trat_mte_top10",
        "trat_mte_top20",
        "trat_mte_top30",
        "caged_admissions_total",
        "caged_admissions_pct",
        "caged_panel_rows",
        "mixed_gradient_profile",
        "high_caged_weight",
        "isco08_items_json",
    ]
    df[ordered_columns].to_csv(CSV_PATH, index=False)


def write_html(summary: dict[str, object], records: list[dict[str, object]]) -> None:
    payload = json.dumps(
        json_safe({"summary": summary, "records": records}),
        ensure_ascii=False,
        allow_nan=False,
    ).replace("</", "<\\/")
    HTML_PATH.write_text(
        f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Visualizador CBO -> ISCO-08</title>
  <link rel="stylesheet" href="assets/crosswalk_visualizer.css">
</head>
<body>
  <header class="app-header">
    <div>
      <p class="eyebrow">Crosswalk oficial MTE</p>
      <h1>Visualizador CBO -> ISCO-08</h1>
      <p class="subtitle">Explore quais CBOs entram na ponte MTE, quais ficam de fora e como os destinos ISCO-08 definem exposição.</p>
    </div>
    <div class="header-actions">
      <a class="button secondary" href="cbo_isco08_crosswalk_visual.csv" download>Baixar CSV completo</a>
      <button class="button" id="exportFiltered">Exportar filtro</button>
    </div>
  </header>

  <main>
    <section class="summary-grid" id="summaryGrid" aria-label="Resumo do crosswalk"></section>

    <section class="method-note">
      <strong>Critério de tratamento:</strong> a classificação principal replica a Table 5 da OIT, usando média μ e desvio-padrão σ agregados dos destinos ISCO-08. Alta exposição corresponde aos Gradients 3 e 4; média exposição aos Gradients 1 e 2; expostos aos Gradients 1 a 4. Minimal Exposure, Not Exposed, sem crosswalk e sem score ficam fora dos tratamentos.
    </section>

    <section class="toolbar" aria-label="Filtros">
      <div class="search-box">
        <label for="searchInput">Busca</label>
        <input id="searchInput" type="search" placeholder="CBO, título, ISCO-08 ou título ISCO">
      </div>
      <div>
        <label for="statusFilter">Status MTE</label>
        <select id="statusFilter">
          <option value="all">Todos</option>
          <option value="matched_official_mte">Com MTE</option>
          <option value="sem_match_mte_no_result">Sem crosswalk MTE</option>
        </select>
      </div>
      <div>
        <label for="gradientFilter">Gradiente ISCO-08</label>
        <select id="gradientFilter">
          <option value="all">Todos</option>
          <option value="gradient_4">Gradient 4</option>
          <option value="gradient_3">Gradient 3</option>
          <option value="gradient_2">Gradient 2</option>
          <option value="gradient_1">Gradient 1</option>
          <option value="minimal">Minimal Exposure</option>
          <option value="not_exposed">Not Exposed</option>
          <option value="no_score">Sem score / sem destino</option>
        </select>
      </div>
      <div>
        <label for="treatmentFilter">Tratamento</label>
        <select id="treatmentFilter">
          <option value="all">Todos</option>
          <option value="trat_alta_expo">Trat. Alta Expo</option>
          <option value="trat_media_expo">Trat. Média Expo</option>
          <option value="trat_expostos">Trat. Expostos</option>
          <option value="trat_mte_top10">Trat. MTE 10%</option>
          <option value="trat_mte_top20">Trat. MTE 20%</option>
          <option value="trat_mte_top30">Trat. MTE 30%</option>
        </select>
      </div>
      <label class="check-filter">
        <input id="onlyNoCrosswalk" type="checkbox">
        Somente sem crosswalk
      </label>
      <label class="check-filter">
        <input id="onlyMixed" type="checkbox">
        Somente perfil misto
      </label>
      <label class="check-filter">
        <input id="onlyChanged" type="checkbox">
        Mudou pela regra OIT
      </label>
    </section>

    <section class="legend" aria-label="Legenda dos gradientes">
      <span class="legend-item chip gradient_4">Gradient 4</span>
      <span class="legend-item chip gradient_3">Gradient 3</span>
      <span class="legend-item chip gradient_2">Gradient 2</span>
      <span class="legend-item chip gradient_1">Gradient 1</span>
      <span class="legend-item chip minimal">Minimal Exposure</span>
      <span class="legend-item chip not_exposed">Not Exposed</span>
      <span class="legend-item chip no_score">Sem score / sem MTE</span>
    </section>

    <section class="table-section">
      <div class="table-meta">
        <div id="resultCount"></div>
        <div id="thresholdNote"></div>
      </div>
      <div class="table-wrap">
        <table id="crosswalkTable">
          <thead>
            <tr>
              <th data-sort="cbo_4d">Código CBO</th>
              <th data-sort="cbo_title">Título do Código</th>
              <th>Códigos ISCO-08</th>
              <th data-sort="trat_alta_expo">Trat. Alta Expo</th>
              <th data-sort="trat_media_expo">Trat. Média Expo</th>
              <th data-sort="trat_expostos">Trat. Expostos</th>
              <th data-sort="cbo_ilo_gradient">Gradiente CBO OIT</th>
              <th data-sort="isco08_mean_score">Média ISCO</th>
              <th data-sort="isco08_pooled_sd">SD agregado</th>
              <th data-sort="mte_2d_mean_score">MTE 2d</th>
              <th data-sort="trat_mte_top10">MTE 10%</th>
              <th data-sort="trat_mte_top20">MTE 20%</th>
              <th data-sort="trat_mte_top30">MTE 30%</th>
              <th data-sort="caged_admissions_total">Admissões CAGED</th>
            </tr>
          </thead>
          <tbody id="tableBody"></tbody>
        </table>
      </div>
    </section>
  </main>

  <script id="crosswalk-data" type="application/json">{payload}</script>
  <script src="assets/crosswalk_visualizer.js"></script>
</body>
</html>
""",
        encoding="utf-8",
    )


def write_css() -> None:
    CSS_PATH.write_text(
        """* {
  box-sizing: border-box;
}

:root {
  color-scheme: light;
  --bg: #f6f7f9;
  --surface: #ffffff;
  --surface-muted: #f0f3f5;
  --text: #162029;
  --muted: #64717d;
  --border: #d8dee4;
  --accent: #2454a6;
  --accent-dark: #183b73;
  --danger-soft: #fff1f0;
  --danger-border: #f2b8b5;
  --ok: #147a45;
  --no: #9aa3ad;
  --g4-bg: #7f1d1d;
  --g4-fg: #ffffff;
  --g3-bg: #ef8f8a;
  --g3-fg: #4a1111;
  --g2-bg: #b7791f;
  --g2-fg: #ffffff;
  --g1-bg: #fde68a;
  --g1-fg: #4b3b07;
  --min-bg: #166534;
  --min-fg: #ffffff;
  --none-bg: #bbf7d0;
  --none-fg: #164e2d;
  --gray-bg: #e5e7eb;
  --gray-fg: #374151;
}

body {
  margin: 0;
  background: var(--bg);
  color: var(--text);
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  font-size: 14px;
}

.app-header {
  display: flex;
  justify-content: space-between;
  gap: 24px;
  padding: 28px 32px 20px;
  background: var(--surface);
  border-bottom: 1px solid var(--border);
}

.eyebrow {
  margin: 0 0 4px;
  color: var(--accent);
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .04em;
  font-size: 12px;
}

h1 {
  margin: 0;
  font-size: 28px;
  line-height: 1.2;
}

.subtitle {
  max-width: 820px;
  color: var(--muted);
  margin: 8px 0 0;
  line-height: 1.45;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.button {
  border: 1px solid var(--accent-dark);
  background: var(--accent);
  color: #fff;
  border-radius: 6px;
  padding: 9px 12px;
  font-weight: 700;
  cursor: pointer;
  text-decoration: none;
  white-space: nowrap;
}

.button.secondary {
  background: #fff;
  color: var(--accent-dark);
}

main {
  padding: 20px 32px 36px;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.summary-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 14px;
}

.summary-card .label {
  color: var(--muted);
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
}

.summary-card .value {
  display: block;
  margin-top: 6px;
  font-size: 24px;
  font-weight: 800;
}

.summary-card .detail {
  display: block;
  margin-top: 4px;
  color: var(--muted);
  font-size: 12px;
}

.method-note {
  background: #eef6ff;
  border: 1px solid #bfdbfe;
  border-radius: 8px;
  color: #17324d;
  line-height: 1.45;
  margin-bottom: 12px;
  padding: 12px 14px;
}

.toolbar {
  display: grid;
  grid-template-columns: minmax(260px, 1.4fr) repeat(3, minmax(170px, 1fr)) repeat(3, auto);
  gap: 12px;
  align-items: end;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 14px;
  margin-bottom: 12px;
}

label {
  display: block;
  color: var(--muted);
  font-size: 12px;
  font-weight: 700;
  margin-bottom: 5px;
}

input[type="search"],
select {
  width: 100%;
  min-height: 38px;
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 8px 10px;
  background: #fff;
  color: var(--text);
}

.check-filter {
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 38px;
  margin: 0;
  color: var(--text);
  white-space: nowrap;
}

.legend {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}

.table-section {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  overflow: hidden;
}

.table-meta {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 14px;
  border-bottom: 1px solid var(--border);
  color: var(--muted);
}

.table-wrap {
  overflow: auto;
  max-height: calc(100vh - 340px);
}

table {
  width: 100%;
  min-width: 1600px;
  border-collapse: collapse;
}

th,
td {
  padding: 10px 9px;
  border-bottom: 1px solid var(--border);
  vertical-align: top;
  text-align: left;
}

th {
  position: sticky;
  top: 0;
  z-index: 1;
  background: #f9fafb;
  font-size: 12px;
  color: #334155;
  cursor: default;
}

th[data-sort] {
  cursor: pointer;
}

th[data-sort]::after {
  content: " ↆ";
  color: #9aa3ad;
}

tr.no-crosswalk {
  background: var(--danger-soft);
}

tr.no-crosswalk td {
  border-bottom-color: var(--danger-border);
}

.cbo-code {
  font-weight: 800;
  font-variant-numeric: tabular-nums;
}

.cbo-title {
  min-width: 280px;
  max-width: 360px;
  line-height: 1.35;
}

.badges {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  margin-top: 7px;
}

.badge {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: var(--surface-muted);
  color: #334155;
  padding: 2px 7px;
  font-size: 11px;
  font-weight: 700;
}

.badge.warn {
  background: #fff7ed;
  border-color: #fed7aa;
  color: #9a3412;
}

.badge.mean {
  background: #dbeafe;
  border-color: #93c5fd;
  color: #1d4ed8;
}

.badge.danger {
  background: #fee2e2;
  border-color: #fecaca;
  color: #991b1b;
}

.isco-cell {
  min-width: 330px;
}

.chip-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.chip {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 4px 8px;
  font-size: 12px;
  font-weight: 800;
  line-height: 1;
  cursor: default;
}

.gradient_4 { background: var(--g4-bg); color: var(--g4-fg); }
.gradient_3 { background: var(--g3-bg); color: var(--g3-fg); }
.gradient_2 { background: var(--g2-bg); color: var(--g2-fg); }
.gradient_1 { background: var(--g1-bg); color: var(--g1-fg); }
.minimal { background: var(--min-bg); color: var(--min-fg); }
.not_exposed { background: var(--none-bg); color: var(--none-fg); }
.no_score { background: var(--gray-bg); color: var(--gray-fg); }

.check {
  font-size: 16px;
  font-weight: 900;
  color: var(--ok);
}

.xmark {
  font-size: 16px;
  font-weight: 900;
  color: var(--no);
}

.num {
  text-align: right;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.small {
  color: var(--muted);
  font-size: 12px;
  margin-top: 3px;
}

@media (max-width: 1100px) {
  .app-header,
  .table-meta {
    flex-direction: column;
  }

  .summary-grid {
    grid-template-columns: repeat(2, minmax(140px, 1fr));
  }

  .toolbar {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 720px) {
  .app-header,
  main {
    padding-left: 16px;
    padding-right: 16px;
  }

  .summary-grid,
  .toolbar {
    grid-template-columns: 1fr;
  }
}
""",
        encoding="utf-8",
    )


def write_js() -> None:
    JS_PATH.write_text(
        """const payload = JSON.parse(document.getElementById("crosswalk-data").textContent);
const allRows = payload.records;
const summary = payload.summary;

const state = {
  query: "",
  status: "all",
  gradient: "all",
  treatment: "all",
  onlyNoCrosswalk: false,
  onlyMixed: false,
  onlyChanged: false,
  sortKey: "cbo_4d",
  sortDir: "asc",
};

const els = {
  summaryGrid: document.getElementById("summaryGrid"),
  searchInput: document.getElementById("searchInput"),
  statusFilter: document.getElementById("statusFilter"),
  gradientFilter: document.getElementById("gradientFilter"),
  treatmentFilter: document.getElementById("treatmentFilter"),
  onlyNoCrosswalk: document.getElementById("onlyNoCrosswalk"),
  onlyMixed: document.getElementById("onlyMixed"),
  onlyChanged: document.getElementById("onlyChanged"),
  tableBody: document.getElementById("tableBody"),
  resultCount: document.getElementById("resultCount"),
  thresholdNote: document.getElementById("thresholdNote"),
  exportFiltered: document.getElementById("exportFiltered"),
};

function formatInt(value) {
  return Number(value || 0).toLocaleString("pt-BR");
}

function formatPct(value, digits = 2) {
  return `${Number(value || 0).toLocaleString("pt-BR", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  })}%`;
}

function formatScore(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "";
  return Number(value).toLocaleString("pt-BR", {
    minimumFractionDigits: 3,
    maximumFractionDigits: 3,
  });
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function boolIcon(value) {
  return value ? '<span class="check" title="Sim">✓</span>' : '<span class="xmark" title="Não">–</span>';
}

function renderSummary() {
  const matchedShare = summary.total_admissions
    ? (summary.matched_admissions / summary.total_admissions) * 100
    : 0;
  const unmatchedShare = summary.total_admissions
    ? (summary.unmatched_admissions / summary.total_admissions) * 100
    : 0;
  const cards = [
    ["Total CBOs", formatInt(summary.total_cbo), "Famílias CBO no crosswalk"],
    ["Com MTE", formatInt(summary.matched_cbo), `${formatPct((summary.matched_cbo / summary.total_cbo) * 100, 1)} dos CBOs`],
    ["Sem MTE", formatInt(summary.unmatched_cbo), `${formatPct((summary.unmatched_cbo / summary.total_cbo) * 100, 1)} dos CBOs`],
    ["Admissões cobertas", formatInt(summary.matched_admissions), `${formatPct(matchedShare, 2)} do CAGED`],
    ["Admissões sem MTE", formatInt(summary.unmatched_admissions), `${formatPct(unmatchedShare, 2)} do CAGED`],
    ["Perfis mistos", formatInt(summary.mixed_cbo), "Mais de um gradiente ISCO-08"],
    ["Mudou pela regra OIT", formatInt(summary.ilo_rule_changed_cbo), "Comparado à regra de média simples"],
    ["Alta / Média / Expostos", `${formatInt(summary.treatment_counts.trat_alta_expo)} / ${formatInt(summary.treatment_counts.trat_media_expo)} / ${formatInt(summary.treatment_counts.trat_expostos)}`, "CBOs nos tratamentos principais"],
  ];
  els.summaryGrid.innerHTML = cards
    .map(([label, value, detail]) => `
      <article class="summary-card">
        <span class="label">${escapeHtml(label)}</span>
        <span class="value">${escapeHtml(value)}</span>
        <span class="detail">${escapeHtml(detail)}</span>
      </article>
    `)
    .join("");
  const t = summary.thresholds;
  els.thresholdNote.textContent =
    `Regra OIT: usa μ e σ agregados dos ISCOs · MTE 2d: top 10% ≥ ${formatScore(t.mte_top10_cutoff)} · top 20% ≥ ${formatScore(t.mte_top20_cutoff)} · top 30% ≥ ${formatScore(t.mte_top30_cutoff)}`;
}

function rowSearchText(row) {
  return [
    row.cbo_4d,
    row.cbo_title,
    row.cbo_2d,
    row.cbo_2d_title,
    row.mte_match_status,
    row.isco08_codes,
    row.isco08_titles,
    row.isco08_gradients,
    row.cbo_ilo_gradient,
    row.treatment_rule_source,
  ]
    .join(" ")
    .toLowerCase();
}

function filterRows() {
  const query = state.query.trim().toLowerCase();
  return allRows.filter((row) => {
    if (query && !rowSearchText(row).includes(query)) return false;
    if (state.status !== "all" && row.mte_match_status !== state.status) return false;
    if (state.gradient !== "all" && !(row.gradient_keys || []).includes(state.gradient)) return false;
    if (state.treatment !== "all" && !row[state.treatment]) return false;
    if (state.onlyNoCrosswalk && row.mte_match_status !== "sem_match_mte_no_result") return false;
    if (state.onlyMixed && !row.mixed_gradient_profile) return false;
    if (state.onlyChanged && !row.treatment_changed_by_ilo_rule) return false;
    return true;
  });
}

function compareValues(a, b, key) {
  const av = a[key];
  const bv = b[key];
  if (typeof av === "boolean" || typeof bv === "boolean") {
    return Number(Boolean(av)) - Number(Boolean(bv));
  }
  const an = Number(av);
  const bn = Number(bv);
  if (!Number.isNaN(an) && !Number.isNaN(bn)) {
    return an - bn;
  }
  return String(av ?? "").localeCompare(String(bv ?? ""), "pt-BR", { numeric: true });
}

function sortRows(rows) {
  const sorted = [...rows].sort((a, b) => compareValues(a, b, state.sortKey));
  if (state.sortDir === "desc") sorted.reverse();
  return sorted;
}

function chipHtml(item) {
  const title = [
    `ISCO-08 ${item.code}`,
    item.title || "Título não encontrado",
    item.gradient || "Sem gradiente / sem score",
    item.score_display ? `Score OIT: ${item.score_display}` : "Score OIT: ausente",
    item.sd_display ? `SD OIT: ${item.sd_display}` : "SD OIT: ausente",
  ].join("\\n");
  return `<span class="chip ${escapeHtml(item.gradient_key)}" title="${escapeHtml(title)}">${escapeHtml(item.code)}</span>`;
}

function badgesHtml(row) {
  const badges = [];
  if (row.mte_match_status === "sem_match_mte_no_result") badges.push('<span class="badge danger">Sem MTE</span>');
  if (row.mixed_gradient_profile) badges.push('<span class="badge warn">Misto</span>');
  if (row.treatment_changed_by_ilo_rule) badges.push('<span class="badge mean">Regra OIT</span>');
  if (row.high_caged_weight) badges.push('<span class="badge warn">Peso alto CAGED</span>');
  if (row.n_missing_isco08_scores > 0) badges.push('<span class="badge">ISCO sem score</span>');
  return badges.length ? `<div class="badges">${badges.join("")}</div>` : "";
}

function rowHtml(row) {
  const noCrosswalk = row.mte_match_status === "sem_match_mte_no_result";
  const chips = row.isco08_items && row.isco08_items.length
    ? row.isco08_items.map(chipHtml).join("")
    : '<span class="chip no_score" title="A tábua MTE não retornou destino ISCO-08 para este CBO.">Sem ISCO-08</span>';
  return `
    <tr class="${noCrosswalk ? "no-crosswalk" : ""}">
      <td>
        <div class="cbo-code">${escapeHtml(row.cbo_4d)}</div>
        <div class="small">${escapeHtml(row.crosswalk_status_label)}</div>
        ${badgesHtml(row)}
      </td>
      <td class="cbo-title">
        ${escapeHtml(row.cbo_title || "Título CBO ausente")}
        <div class="small">${escapeHtml(row.cbo_2d || "")} ${escapeHtml(row.cbo_2d_title || "")}</div>
      </td>
      <td class="isco-cell">
        <div class="chip-list">${chips}</div>
        <div class="small">${escapeHtml(row.isco08_gradients || "Sem destino pontuado")}</div>
      </td>
      <td>${boolIcon(row.trat_alta_expo)}</td>
      <td>${boolIcon(row.trat_media_expo)}</td>
      <td>${boolIcon(row.trat_expostos)}</td>
      <td>
        <span class="chip ${escapeHtml(row.cbo_ilo_gradient_key || "no_score")}">${escapeHtml(row.cbo_ilo_gradient || "No score")}</span>
      </td>
      <td class="num">
        ${formatScore(row.isco08_mean_score)}
        <div class="small">${escapeHtml(row.treatment_rule_source || "")}</div>
      </td>
      <td class="num">${formatScore(row.isco08_pooled_sd)}</td>
      <td class="num">${formatScore(row.mte_2d_mean_score)}</td>
      <td>${boolIcon(row.trat_mte_top10)}</td>
      <td>${boolIcon(row.trat_mte_top20)}</td>
      <td>${boolIcon(row.trat_mte_top30)}</td>
      <td class="num">
        ${formatInt(row.caged_admissions_total)}
        <div class="small">${formatPct(row.caged_admissions_pct * 100, 2)} do total</div>
      </td>
    </tr>
  `;
}

function renderTable() {
  const filtered = sortRows(filterRows());
  els.resultCount.textContent = `${formatInt(filtered.length)} CBOs exibidos de ${formatInt(allRows.length)}`;
  els.tableBody.innerHTML = filtered.map(rowHtml).join("");
  return filtered;
}

function downloadCsv(rows) {
  const cols = [
    "cbo_4d",
    "cbo_title",
    "mte_match_status",
    "isco08_codes",
    "isco08_titles",
    "isco08_gradients",
    "isco08_scores",
    "isco08_sds",
    "isco08_mean_score",
    "isco08_pooled_sd",
    "cbo_ilo_gradient",
    "trat_alta_expo",
    "trat_media_expo",
    "trat_expostos",
    "treatment_rule_source",
    "treatment_changed_by_ilo_rule",
    "trat_alta_expo_mean_score_legacy",
    "trat_media_expo_mean_score_legacy",
    "trat_expostos_mean_score_legacy",
    "trat_alta_expo_75pct_legacy",
    "trat_media_expo_75pct_legacy",
    "trat_expostos_75pct_legacy",
    "mte_2d_mean_score",
    "trat_mte_top10",
    "trat_mte_top20",
    "trat_mte_top30",
    "caged_admissions_total",
    "caged_admissions_pct",
    "caged_panel_rows",
  ];
  const escapeCsv = (value) => `"${String(value ?? "").replaceAll('"', '""')}"`;
  const csv = [
    cols.join(","),
    ...rows.map((row) => cols.map((col) => escapeCsv(row[col])).join(",")),
  ].join("\\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "cbo_isco08_crosswalk_filtered.csv";
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function bindEvents() {
  els.searchInput.addEventListener("input", (event) => {
    state.query = event.target.value;
    renderTable();
  });
  els.statusFilter.addEventListener("change", (event) => {
    state.status = event.target.value;
    renderTable();
  });
  els.gradientFilter.addEventListener("change", (event) => {
    state.gradient = event.target.value;
    renderTable();
  });
  els.treatmentFilter.addEventListener("change", (event) => {
    state.treatment = event.target.value;
    renderTable();
  });
  els.onlyNoCrosswalk.addEventListener("change", (event) => {
    state.onlyNoCrosswalk = event.target.checked;
    if (state.onlyNoCrosswalk) {
      state.status = "all";
      els.statusFilter.value = "all";
    }
    renderTable();
  });
  els.onlyMixed.addEventListener("change", (event) => {
    state.onlyMixed = event.target.checked;
    renderTable();
  });
  els.onlyChanged.addEventListener("change", (event) => {
    state.onlyChanged = event.target.checked;
    renderTable();
  });
  document.querySelectorAll("th[data-sort]").forEach((th) => {
    th.addEventListener("click", () => {
      const key = th.dataset.sort;
      if (state.sortKey === key) {
        state.sortDir = state.sortDir === "asc" ? "desc" : "asc";
      } else {
        state.sortKey = key;
        state.sortDir = "asc";
      }
      renderTable();
    });
  });
  els.exportFiltered.addEventListener("click", () => {
    downloadCsv(sortRows(filterRows()));
  });
}

renderSummary();
bindEvents();
renderTable();
""",
        encoding="utf-8",
    )


def run_validation(df: pd.DataFrame) -> None:
    status_counts = df["mte_match_status"].value_counts().to_dict()
    if int(status_counts.get(NO_MATCH_STATUS, 0)) != 193:
        raise RuntimeError(f"Expected 193 CBOs without MTE match; found {status_counts.get(NO_MATCH_STATUS, 0)}")
    if int(status_counts.get(MATCHED_STATUS, 0)) != 436:
        raise RuntimeError(f"Expected 436 CBOs with MTE match; found {status_counts.get(MATCHED_STATUS, 0)}")

    critical_unmatched = {"1425", "2534", "2122", "1236"}
    critical_matched = {"2124", "2123", "3171", "3172"}
    by_cbo = df.set_index("cbo_4d")
    bad_unmatched = [
        code for code in critical_unmatched
        if code not in by_cbo.index or by_cbo.loc[code, "mte_match_status"] != NO_MATCH_STATUS
    ]
    bad_matched = [
        code for code in critical_matched
        if code not in by_cbo.index or by_cbo.loc[code, "mte_match_status"] != MATCHED_STATUS
    ]
    if bad_unmatched:
        raise RuntimeError(f"Expected these CBOs to be unmatched but they were not: {bad_unmatched}")
    if bad_matched:
        raise RuntimeError(f"Expected these CBOs to be matched but they were not: {bad_matched}")

    unmatched = df["mte_match_status"].eq(NO_MATCH_STATUS)
    if df.loc[unmatched, ["trat_mte_top10", "trat_mte_top20", "trat_mte_top30"]].any().any():
        raise RuntimeError("Unmatched CBOs must not be marked as MTE treatment.")
    if df.loc[unmatched, ["trat_alta_expo", "trat_media_expo", "trat_expostos"]].any().any():
        raise RuntimeError("Unmatched CBOs must not be marked as main treatment.")

    expected_treatment_counts = {
        "trat_alta_expo": 31,
        "trat_media_expo": 44,
        "trat_expostos": 75,
    }
    actual_treatment_counts = {
        column: int(df[column].sum())
        for column in expected_treatment_counts
    }
    if actual_treatment_counts != expected_treatment_counts:
        raise RuntimeError(
            "Unexpected treatment counts after ILO mean+SD crosswalk rule: "
            f"expected {expected_treatment_counts}, found {actual_treatment_counts}"
        )

    expected_critical_flags = {
        "2617": {"trat_alta_expo": True, "trat_expostos": True},
        "2124": {"trat_alta_expo": True, "trat_expostos": True},
        "2123": {"trat_alta_expo": True, "trat_expostos": True},
        "1425": {"trat_alta_expo": False, "trat_media_expo": False, "trat_expostos": False},
        "7841": {"trat_alta_expo": False, "trat_media_expo": False, "trat_expostos": False},
    }
    for code, expected_flags in expected_critical_flags.items():
        if code not in by_cbo.index:
            raise RuntimeError(f"Critical CBO not found after rebuild: {code}")
        for column, expected_value in expected_flags.items():
            actual_value = bool(by_cbo.loc[code, column])
            if actual_value != expected_value:
                raise RuntimeError(
                    f"Unexpected {column} for CBO {code}: expected {expected_value}, found {actual_value}"
                )

    if by_cbo.loc["7841", "cbo_ilo_gradient"] != "Minimal Exposure":
        raise RuntimeError(f"Expected CBO 7841 to be Minimal Exposure; found {by_cbo.loc['7841', 'cbo_ilo_gradient']}")
    if by_cbo.loc["3171", "treatment_rule_source"] != "ilo_mean_sd_crosswalk":
        raise RuntimeError("Expected CBO 3171 to be classified by the ILO mean+SD crosswalk rule.")


def main() -> None:
    ensure_dirs()
    bridge, ilo = read_inputs()
    df, summary, ui_records = build_rows(bridge, ilo)
    run_validation(df)
    write_csv(df)
    write_css()
    write_js()
    write_html(summary, ui_records)
    print(f"CSV written: {CSV_PATH}")
    print(f"HTML written: {HTML_PATH}")
    print(f"Assets written: {ASSET_DIR}")
    print(
        "Summary: "
        f"{summary['total_cbo']} CBOs, "
        f"{summary['matched_cbo']} matched, "
        f"{summary['unmatched_cbo']} unmatched."
    )


if __name__ == "__main__":
    main()
