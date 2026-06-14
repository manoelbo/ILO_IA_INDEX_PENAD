# T004 Judge Audit - Section 4 Results Package

## Verdict

Complete.

`full_outcome_complete: true`

## Artifact Checklist

- Portuguese final report exists: pass.
- Figure 1 aggregate event-study PNG exists: pass.
- Table 1 Markdown and CSV exist: pass.
- Table 2 Markdown and CSV exist: pass.
- Four Table 3 scenario Markdown and CSV files exist: pass.
- Long Table 3 audit CSV exists: pass.
- Table 3 includes all four required outcomes for all four scenarios: pass.
- Long audit includes `race_color`: pass.
- Markdown tables include the significance-star legend with `*`, `**`, and `***`: pass.
- Sample-loss rows have `sample_loss_reason`: pass.

## Command Checklist

- Stage 2a rerun after the sex-code correction: pass.
- Stage 2b rerun after Stage 2a regeneration: pass.
- Treatment scenario grid rerun after Stage 2b: pass.
- Section 4 builder rerun after its own fixes: pass.
- Py compile check for Stage 2a and builder: pass.
- Requested `git diff --check -- src/scripts outputs/dissertation_section4`: pass.
- Additional whitespace check for untracked relevant scripts and Markdown outputs: pass.

## Residual Risks

- The relevant implementation and output paths are currently untracked by git in this checkout, so the requested `git diff --check` returned clean but does not expose a normal tracked diff for these paths.
- Four long-audit-only race/color code 9 salary regressions failed because `post_treat` was dropped after sparse non-missing wage observations. This does not affect the required main Table 3 panels and is recorded in `sample_loss_reason`.

