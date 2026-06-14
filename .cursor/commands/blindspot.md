# /blindspot — Peripheral-Vision Audit (Make the Stone Stony Again)

Invoke the **Blindspot** skill to audit *perception* of empirical output — finding vices (problems hiding in plain sight) and virtues (opportunities being overlooked).

You MUST start by reading the skill instructions at `.cursor/skills/blindspot/SKILL.md`. Follow the four-quadrant protocol exactly — do not skip quadrants and do not let the user's stated finding anchor your audit.

## Usage

```
/blindspot <path-to-figure-or-table> "<brief description of what the user thinks the main finding is>"
```

User input passed to the command: **$ARGUMENTS**

## Required behavior

1. **Read the skill file first** (`.cursor/skills/blindspot/SKILL.md`).
2. **Read the output file** the user supplied (figure / table / results) and any accompanying notes.
3. **Treat the user's stated finding as just one item on the list.** Do not let it collapse your attention.
4. **Work through all four quadrants in order:**
   - **Vice 1**: The Unexplained Feature — list every visible feature, ask what would generate each, identify the hardest one to explain.
   - **Vice 2**: The Convenient Absence — what should be there but isn't? Missing checks, missing subgroups, unexplained N changes.
   - **Virtue 1**: The Unasked Question — pattern in the data more interesting than the reported finding? Heterogeneity, mechanism, secondary outcomes.
   - **Virtue 2**: The Unexploited Strength — design feature, falsification test, or descriptive that's being undersold.
5. For each finding, mark **DONE** or **FLAG** (FLAG = no clean explanation yet).
6. **Produce a Blindspot Report** with one of three rulings:
   - **CLEAR** — proceed to interpretation
   - **CONDITIONAL** — proceed but acknowledge open questions
   - **HOLD** — do not interpret or publish until flagged vices are resolved
7. **Save the report** alongside the output (e.g., `output/figure3_blindspot.md`) or under `correspondence/blindspot/`.

## When to use

The trigger is: **output exists and interpretation is about to happen.**

- Use BEFORE the writing is done (`/blindspot` runs in the same session as the work).
- Use AFTER you have a finished figure / table / results file.
- Do NOT use this skill to check whether code is correct — that is `/referee2`.

Run `/blindspot` first, then `/referee2` later. Together they ensure both perception and implementation have been stress-tested.
