"""Shared Section 3 data and publication contracts."""

from __future__ import annotations


SALARY_MINIMUM_BRL = 1518
SEM_CLASS = "Sem classificação"

GRADIENT_ORDER = [
    "Not Exposed",
    "Minimal Exposure",
    "Exposed: Gradient 1",
    "Exposed: Gradient 2",
    "Exposed: Gradient 3",
    "Exposed: Gradient 4",
]
GRADIENT_LABELS = {
    "Not Exposed": "Not exposed",
    "Minimal Exposure": "Minimal exposure",
    "Exposed: Gradient 1": "Gradient 1",
    "Exposed: Gradient 2": "Gradient 2",
    "Exposed: Gradient 3": "Gradient 3",
    "Exposed: Gradient 4": "Gradient 4",
    SEM_CLASS: "Unclassified",
}
GRADIENT_LABELS_PT = {
    "Not Exposed": "Não exposto",
    "Minimal Exposure": "Exposição mínima",
    "Exposed: Gradient 1": "Gradiente 1",
    "Exposed: Gradient 2": "Gradiente 2",
    "Exposed: Gradient 3": "Gradiente 3",
    "Exposed: Gradient 4": "Gradiente 4",
    SEM_CLASS: "Sem classificação",
}
GRADIENT_INTERPRETATION = {
    "Not Exposed": "Occupations with no relevant exposure condition.",
    "Minimal Exposure": "Residual or punctual exposure.",
    "Exposed: Gradient 1": "Partial exposure, mostly augmentation.",
    "Exposed: Gradient 2": "More intense partial exposure.",
    "Exposed: Gradient 3": "High exposure and deep task transformation.",
    "Exposed: Gradient 4": "Maximum exposure and potentially substitutable tasks.",
    SEM_CLASS: "Score assigned through aggregation; no WP140 gradient label.",
}
GRADIENT_TO_GROUP = {
    "Not Exposed": "Low",
    "Minimal Exposure": "Low",
    "Exposed: Gradient 1": "Moderate",
    "Exposed: Gradient 2": "Moderate",
    "Exposed: Gradient 3": "High",
    "Exposed: Gradient 4": "High",
}
HIGH_GRADIENTS = {"Exposed: Gradient 3", "Exposed: Gradient 4"}
MODERATE_GRADIENTS = {"Exposed: Gradient 1", "Exposed: Gradient 2"}
LOW_GRADIENTS = {"Not Exposed", "Minimal Exposure"}

GROUP_COLORS = {
    "Low": "#2f6fae",
    "Moderate": "#d99a1e",
    "High": "#c7352f",
}
GROUP_LABELS_PT = {
    "Low": "Baixa",
    "Moderate": "Média",
    "High": "Alta",
}
GRADIENT_COLORS = {
    "Not Exposed": "#3b78b8",
    "Minimal Exposure": "#76a9d6",
    "Exposed: Gradient 1": "#f0c35a",
    "Exposed: Gradient 2": "#df8f2d",
    "Exposed: Gradient 3": "#d55345",
    "Exposed: Gradient 4": "#a8232f",
    SEM_CLASS: "#8c8c8c",
}
FIGURE_TITLES_PT = {
    "3.1": "Figura 3.1: Distribuição da exposição à IA no Brasil",
    "3.2": "Figura 3.2: População ocupada por gradiente de exposição à IA",
    "3.3": (
        "Figura 3.3: Composição da população ocupada por faixa de score "
        "de exposição à IA, segundo o grande grupo ocupacional"
    ),
    "3.4": "Figura 3.4: Alta exposição à IA por estado",
    "3.5": "Figura 3.5: Exposição à IA por sexo",
    "3.6": "Figura 3.6: Exposição à IA por raça",
    "3.7": "Figura 3.7: Exposição à IA por faixa etária",
    "3.8": "Figura 3.8: Exposição à IA por nível de escolaridade",
    "3.9": "Figura 3.9: Exposição à IA por faixa de renda",
    "3.10": "Figura 3.10: Exposição à IA por situação de formalidade",
}

RAW_PNAD_QUERY_ALIASES = [
    "ano",
    "trimestre",
    "sigla_uf",
    "sexo",
    "idade",
    "raca_cor",
    "nivel_instrucao",
    "cod_ocupacao",
    "grupamento_atividade",
    "posicao_ocupacao",
    "rendimento_habitual",
    "rendimento_efetivo",
    "horas_habituais",
    "horas_efetivas",
    "peso",
]

CNAE_SECAO_TO_SETOR = {
    "01": "Agropecuária",
    "02": "Agropecuária",
    "03": "Agropecuária",
    "05": "Ind. Extrativa",
    "06": "Ind. Extrativa",
    "07": "Ind. Extrativa",
    "08": "Ind. Extrativa",
    "09": "Ind. Extrativa",
    **{f"{number:02d}": "Ind. Transformação" for number in range(10, 34)},
    **{
        f"{number:02d}": "Utilidades"
        for number in [35, 36, 37, 38, 39]
    },
    "41": "Construção",
    "42": "Construção",
    "43": "Construção",
    "45": "Comércio",
    "46": "Comércio",
    "47": "Comércio",
    "48": "Comércio",
    **{
        f"{number:02d}": "Transporte"
        for number in [49, 50, 51, 52, 53]
    },
    "55": "Alojamento e Alimentação",
    "56": "Alojamento e Alimentação",
    **{
        f"{number:02d}": "Informação e Comunicação"
        for number in [58, 59, 60, 61, 62, 63]
    },
    "64": "Finanças e Seguros",
    "65": "Finanças e Seguros",
    "66": "Finanças e Seguros",
    "68": "Atividades Imobiliárias",
    **{
        f"{number:02d}": "Serviços Profissionais"
        for number in [69, 70, 71, 72, 73, 74, 75]
    },
    **{
        f"{number:02d}": "Serviços Administrativos"
        for number in [77, 78, 79, 80, 81, 82]
    },
    "84": "Administração Pública",
    "85": "Educação",
    "86": "Saúde",
    "87": "Saúde",
    "88": "Saúde",
    **{
        f"{number:02d}": "Artes e Cultura"
        for number in [90, 91, 92, 93]
    },
    **{
        f"{number:02d}": "Outros Serviços"
        for number in [94, 95, 96]
    },
    "97": "Serviços Domésticos",
    "99": "Outros Serviços",
}

RACE_ORDER = ["Branca", "Negra", "Outras"]
SEX_ORDER = ["Homem", "Mulher"]
AGE_ORDER = ["18-24", "25-34", "35-44", "45-54", "55+"]
INCOME_ORDER = ["Até 1 SM", "1-2 SM", "2-3 SM", "3-5 SM", "5+ SM"]
FORMAL_LABELS = {1: "Formal", 0: "Informal"}
FORMAL_LABELS_PT = {1: "Formal", 0: "Informal"}
EDUCATION_LABELS = {
    1: "No instruction",
    2: "No/Fund. incomplete",
    3: "Fund. complete",
    4: "High school incomplete",
    5: "High school complete",
    6: "College incomplete",
    7: "College complete",
}
EDUCATION_LABELS_PT = {
    1: "Sem instrução",
    2: "Sem/Fund. incompleto",
    3: "Fund. completo",
    4: "Médio incompleto",
    5: "Médio completo",
    6: "Superior incompleto",
    7: "Superior completo",
}
