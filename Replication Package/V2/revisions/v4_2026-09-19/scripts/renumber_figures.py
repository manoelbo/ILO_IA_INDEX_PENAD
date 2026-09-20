"""Re-render existing saved series with V4 labels; preserve all plotted inputs."""
from pathlib import Path
import hashlib
import json
import sys
import matplotlib
matplotlib.use('Agg')
import pandas as pd

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'code/render'))
import phase8b_figures as figures
import canaries_wage_figure as cohort
REF=ROOT/'results/reference/artifacts/caged'
original_save=figures._save_figure

def save(figure,path):
    for text in figure.texts:
        if text.get_text().startswith('Nota:'):
            text.set_text('Nota: perfis relativos a nov/2022 até +41; os testes da janela −23 a +23 estão nas tabelas do apêndice. Sem leitura causal.')
    for ax in figure.axes:
        ax.set_title(ax.get_title(loc='left').replace('5.2.3.3','A.5.3'),loc='left')
    original_save(figure,path)

figures._save_figure=save
cohort._save_figure=save
data=pd.read_csv(REF/'models/group_event_study_coefficients.csv')
mapping=[]
for i,(old,dimension,outcome,slug) in enumerate(figures.GROUP_FIGURE_SPECS):
    section=3+i//2
    new=f'A.{section}.{i%2+1}'
    target=OUT/'figures'/f"figure_{new.replace('.','_')}_{slug}.png"
    figures.plot_group_event_study(data,figure_id=new,dimension=dimension,outcome=outcome,path=target)
    mapping.append({'old':old.replace('_','.'),'new':new,'file':str(target.relative_to(OUT)),'source':'results/reference/artifacts/caged/models/group_event_study_coefficients.csv','dimension':dimension,'outcome':outcome,'operation':'same series, intervals, and plotting function; title and note revised'})
cohort.COEFFICIENTS_PATH=REF/'models/canaries_22_25_wage_event_study.csv'
cohort.FIGURE_PATH=OUT/'figures/figure_A_5_3_canaries_wage.png'
cohort.render()
mapping.append({'old':'5.2.3.3','new':'A.5.3','file':str(cohort.FIGURE_PATH.relative_to(OUT)),'source':'results/reference/artifacts/caged/models/canaries_22_25_wage_event_study.csv','operation':'same series and intervals; title and incorrect uniqueness note revised'})
(OUT/'evidence/figure_numbering.json').write_text(json.dumps(mapping,ensure_ascii=False,indent=2))
