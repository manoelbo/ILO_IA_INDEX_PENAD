from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = PACKAGE_ROOT / "code" / "caged" / "ingest" / "diagnose_vintage.py"


def load_diagnostics_module():
    spec = importlib.util.spec_from_file_location(
        "diagnose_vintage",
        MODULE_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load diagnose_vintage.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_completeness_uses_for_over_mov_and_flags_treatment_gap() -> None:
    module = load_diagnostics_module()
    treatment_counts = pd.DataFrame(
        {
            "competenciamov": ["202605"] * 4,
            "grupo_tratamento": [
                "treated",
                "treated",
                "control",
                "control",
            ],
            "origem": ["MOV", "FOR", "MOV", "FOR"],
            "linhas": [100, 3, 100, 1],
        }
    )

    result = module.finalize_treatment_completeness(
        treatment_counts,
        cutoff="202605",
    )

    treated = result[result["grupo_tratamento"].eq("treated")].iloc[0]
    control = result[result["grupo_tratamento"].eq("control")].iloc[0]
    assert treated["fracao_for_sobre_mov_pct"] == 3.0
    assert control["fracao_for_sobre_mov_pct"] == 1.0
    assert treated["diferencial_tratado_controle_pp"] == 2.0
    assert treated["diferencial_acima_1pp"]


def test_signed_continuity_preserves_exclusions_and_unknown_codes() -> None:
    module = load_diagnostics_module()
    frame = pd.DataFrame(
        {
            "competenciamov": ["202101"] * 4,
            "competencia_arquivo": [
                "202101",
                "202102",
                "202101",
                "202101",
            ],
            "origem": ["MOV", "FOR", "EXC", "MOV"],
            "peso": [1, 1, -1, 1],
            "cbo2002ocupacao": ["411005"] * 4,
            "saldomovimentacao": [1, 1, 1, -1],
            "tipomovimentacao": ["20", "97", "97", "98"],
            "categoria": ["101", "999", "999", "101"],
            "indicadoraprendiz": ["0", "9", "9", "0"],
            "unidadesalariocodigo": ["5", "99", "99", "1"],
            "racacor": ["1", "9", "9", "6"],
            "graudeinstrucao": ["9", "99", "99", "8"],
            "tipoempregador": ["0", "9", "9", "1"],
            "tipoestabelecimento": ["1", "-1", "1", "-1"],
            "horascontratuais": [44.0, 0.0, 0.0, 40.0],
        }
    )

    summaries = module.summarize_batch(
        frame,
        {"4110": "treated"},
    )
    continuity = module.finalize_continuity(summaries["continuity"])

    row = continuity.iloc[0]
    assert row["linhas_liquidas"] == 2
    assert row["admissoes_liquidas"] == 1
    assert row["desligamentos_liquidos"] == 1
    assert row["tipo_mov_admissao_ni_pct"] == 0.0
    assert row["tipo_mov_desligamento_ni_pct"] == 100.0
    assert row["tipo_empregador_codigo_1_pct"] == 50.0
    assert row["tipo_estabelecimento_codigo_menos_1_pct"] == 100.0
    assert row["exc_mesmo_mes_linhas"] == 1
