# Referee Report

Project: Dissertation Section 4 final event-study package  
Round: 1  
Date: 2026-06-26  
Scope: Methodological audit of the final Section 4 event-study outputs and interpretation readiness.

## Summary

The package is organized, reproducible from a single Python entrypoint, and suitable as the basis for writing the dissertation section. The empirical evidence is not strong enough to support a broad causal claim that ChatGPT reduced employment flows. The defensible narrative is narrower: exposed occupations show suggestive negative effects on admission wages, while employment-flow estimates fail pre-trend diagnostics and should be interpreted cautiously.

## Audit 1: Code And Data Construction

The final package has clear sample restrictions: exposed gradients versus `Not Exposed`, with `Minimal Exposure` excluded from the base control and included in robustness. The strict sample has 75 treated CBOs, 266 controls, and 18,307 observations. The final CBO-level classification contains no `Exposed: Gradient 4` occupations, so the realized treated set is G1-G3 despite the rule accepting G1-G4.

The wage construction is now explicit. The main wage is nominal log admission wage. A real-wage supplement deflates wages using monthly IPCA with December 2024 as base 100. Because the specification includes month fixed effects, the real admission-wage coefficient is numerically identical to the nominal admission-wage coefficient.

## Audit 2: Replication And Automation

No cross-language replication was run in this round. The Python pipeline compiles, runs end-to-end, and produces automated tables, figures, and audit files. The output package is adequate for dissertation writing, but not yet a complete public replication archive because dependency versions, a replication README, and cross-language validation are not fully packaged.

## Audit 3: Output Automation

Tables and figures are generated programmatically by `src/scripts/build_section4_final_event_study_package.py`. The final report, real-wage supplement, event-study figures, robustness tables, heterogeneity tables, and audit outputs are all produced by code.

## Audit 4: Econometrics

The preferred design is coherent: two-way fixed effects with CBO and month fixed effects, treatment defined by exposure gradients, and clustered standard errors at CBO 4d. The number of clusters is sufficient for the base model.

The main limitation is identification strength. Event-study pre-trends fail for admissions and dismissals, but pass for admission wages and dismissal wages. Therefore, only wage outcomes are viable as causal or quasi-causal evidence. Employment-flow outcomes should be framed as descriptive or exploratory.

The admission-wage coefficient is negative but not conventionally significant in the controlled base specification: -0.0207, p=0.140. Without contemporaneous demographic controls, the coefficient is -0.0251, p=0.086. This strengthens the case for reporting a no-controls or pre-treatment-controls version, because contemporaneous admission composition controls may be post-treatment variables.

Robustness is mixed. The negative wage sign survives several unweighted specifications, but flips under pre-admission weights and becomes small in the continuous exposure specification. This means the result is suggestive, not robust in the strong publication sense.

## Major Concerns

1. **Contemporaneous controls may be bad controls.** The controls `idade_media_adm`, `pct_mulher_adm`, `pct_superior_adm`, and `pct_negra_adm` are calculated from monthly admissions and may themselves respond to treatment. They should not be the only headline specification. At minimum, report the base model without these controls or with pre-treatment baseline controls.

2. **Employment-flow pre-trends fail.** Admissions and dismissals should not be interpreted as causal effects. They can remain in the main table because the advisor requested them, but the text must explicitly downgrade them.

3. **Robustness does not uniformly support the wage hypothesis.** Weighted specifications and continuous exposure weaken or reverse the admission-wage result. The dissertation should not claim a robust wage effect; it should claim suggestive evidence concentrated in the unweighted occupation-level estimand.

## Minor Concerns

1. The realized treatment is G1-G3 because no CBO is classified as G4 in the final CBO-level gradient. This should remain visible in the crosswalk table and text.
2. Heterogeneity has many tests and should be treated as exploratory. Multiple-testing adjustments are not reported.
3. The real-wage result is valuable for transparency, but it should be explained as mechanically similar to nominal wages under month fixed effects.
4. The final report is suitable for internal dissertation drafting, but a public replication package still needs a README and dependency lock/version record.

## Verdict

Major revisions before making a strong causal/publication claim. Minor revisions before writing the dissertation chapter.

The author can begin writing the dissertation now if the narrative is cautious and honest about the evidence. The core claim should be narrowed to wage-setting at entry, not employment displacement.

## Recommended Changes Before Writing The Final Text

1. Add or present a no-controls base specification for the four main outcomes.
2. Decide whether the headline wage table should use no controls, contemporaneous controls, or both side by side.
3. Keep real wage as a supplement and explain why it is nearly identical under month fixed effects.
4. Move admissions and dismissals into a lower-confidence interpretation because of failed pre-trends.
5. Present heterogeneity as exploratory, with emphasis only on cells that pass pre-trends and have adequate power.
6. State explicitly that the final observed treated set is G1-G3, even though the rule is G1-G4.
