#!/usr/bin/env python3
"""Build a stable official-CBO metadata extract for the Section 5.3 dictionary."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE_DIR = ROOT / "tmp" / "occupation_semantic_audit"
DEFAULT_DICTIONARY = ROOT / "data" / "input" / "occupation_case_dictionary.csv"
DEFAULT_OUTPUT = (
    ROOT / "data" / "input" / "occupation_case_official_metadata.csv"
)
SOURCE_URL = (
    "https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/"
    "cbo/servicos/downloads/downloads"
)
RETRIEVED_ON = "2026-07-24"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _ordered_unique(values: pd.Series) -> str:
    observed: list[str] = []
    seen: set[str] = set()
    for value in values.fillna("").astype(str):
        clean = " ".join(value.split())
        if clean and clean not in seen:
            seen.add(clean)
            observed.append(clean)
    return " | ".join(observed)


def _read_profiles(path: Path, eligible_codes: set[str]) -> pd.DataFrame:
    """Read the official semicolon file while preserving semicolons in task text."""
    rows: list[dict[str, str]] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        header = handle.readline().rstrip("\r\n").split(";")
        if len(header) != 9:
            raise RuntimeError(f"Unexpected official profile header: {header}")
        for line_number, line in enumerate(handle, start=2):
            values = line.rstrip("\r\n").split(";", 8)
            if len(values) != 9:
                raise RuntimeError(
                    f"Malformed official profile row at line {line_number}: {len(values)} fields"
                )
            row = dict(zip(header, values))
            code = str(row["COD_OCUPACAO"]).zfill(6)
            if code in eligible_codes:
                rows.append(
                    {
                        "cbo_6d": code,
                        "major_area": row["NOME_GRANDE_AREA"],
                        "activity": row["NOME_ATIVIDADE"],
                    }
                )
    return pd.DataFrame(rows)


def build_extract(
    *,
    source_dir: Path,
    dictionary_path: Path,
    output_path: Path,
) -> pd.DataFrame:
    dictionary = pd.read_csv(dictionary_path, dtype={"cbo_6d": str})
    dictionary["cbo_6d"] = dictionary["cbo_6d"].str.zfill(6)
    eligible_codes = set(dictionary["cbo_6d"])

    title_path = source_dir / "cbo2002-ocupacao-utf8.csv"
    profile_path = source_dir / "cbo2002-perfilocupacional-utf8.csv"
    synonym_path = source_dir / "cbo2002-sinonimo-utf8.csv"
    for source in [title_path, profile_path, synonym_path]:
        if not source.exists():
            raise FileNotFoundError(source)

    titles = pd.read_csv(
        title_path,
        sep=";",
        dtype=str,
        keep_default_na=False,
    ).rename(columns={"CODIGO": "cbo_6d", "TITULO": "official_title"})
    titles["cbo_6d"] = titles["cbo_6d"].str.zfill(6)
    titles = titles[titles["cbo_6d"].isin(eligible_codes)].copy()

    synonyms = pd.read_csv(
        synonym_path,
        sep=";",
        dtype=str,
        keep_default_na=False,
    ).rename(columns={"CODIGO": "cbo_6d", "TITULO": "synonym"})
    synonyms["cbo_6d"] = synonyms["cbo_6d"].str.zfill(6)
    synonyms = synonyms[synonyms["cbo_6d"].isin(eligible_codes)]
    synonym_summary = (
        synonyms.groupby("cbo_6d", observed=True)["synonym"]
        .agg(_ordered_unique)
        .rename("official_synonyms")
        .reset_index()
    )

    profiles = _read_profiles(profile_path, eligible_codes)
    profile_summary = (
        profiles.groupby("cbo_6d", observed=True)
        .agg(
            official_major_areas=("major_area", _ordered_unique),
            official_activities=("activity", _ordered_unique),
        )
        .reset_index()
    )

    output = (
        titles.merge(synonym_summary, on="cbo_6d", how="left", validate="one_to_one")
        .merge(profile_summary, on="cbo_6d", how="left", validate="one_to_one")
        .sort_values("cbo_6d")
        .reset_index(drop=True)
    )
    output["official_synonyms"] = output["official_synonyms"].fillna("")
    output["source_title_sha256"] = sha256_file(title_path)
    output["source_profile_sha256"] = sha256_file(profile_path)
    output["source_synonym_sha256"] = sha256_file(synonym_path)
    output["source_url"] = SOURCE_URL
    output["retrieved_on"] = RETRIEVED_ON

    if len(output) != len(eligible_codes) or output["cbo_6d"].duplicated().any():
        raise RuntimeError("Stable official metadata extract does not cover the dictionary.")
    if output["official_activities"].fillna("").str.len().eq(0).any():
        missing = output.loc[
            output["official_activities"].fillna("").str.len().eq(0),
            "cbo_6d",
        ].tolist()
        raise RuntimeError(f"Official activities are missing for CBO codes: {missing}")

    expected_titles = dictionary.set_index("cbo_6d")["cbo_title"].sort_index()
    observed_titles = output.set_index("cbo_6d")["official_title"].sort_index()
    if not expected_titles.equals(observed_titles):
        mismatch = expected_titles[expected_titles.ne(observed_titles)].index.tolist()
        raise RuntimeError(f"Dictionary titles differ from the official extract: {mismatch}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(output_path, index=False)
    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE_DIR)
    parser.add_argument("--dictionary", type=Path, default=DEFAULT_DICTIONARY)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output = build_extract(
        source_dir=args.source_dir,
        dictionary_path=args.dictionary,
        output_path=args.output,
    )
    print(f"Wrote {len(output)} official CBO rows to {args.output}")


if __name__ == "__main__":
    main()
