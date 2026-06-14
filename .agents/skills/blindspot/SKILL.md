---
name: blindspot
description: Peripheral-vision audit for empirical output. Finds what the author cannot see — problems hiding in plain sight (vices) and opportunities being overlooked (virtues). Inspired by Viktor Shklovsky's defamiliarization and conversations with Jason Fletcher. Use when output exists and interpretation is about to happen — a finished figure, table, or set of results that the user is about to describe, interpret, or write up. Auditors perception, NOT correctness (that is `referee2`).
---

# Blindspot: Make the Stone Stony Again

Viktor Shklovsky, the Soviet literary theorist, argued that art exists to restore perception. A man who walks barefoot up a mountain eventually cannot feel his feet. Everything becomes habitual, automatic, unconscious. Art exists to make the stone stony again — to force you to *feel* what you have stopped noticing.

Research has the same problem. By the time you've spent months on a paper, you can't feel the stones under your feet. The main finding has collapsed your attention. Everything else in the output — the spike at t=1, the missing subgroup, the heterogeneity richer than the average, the identification strategy stronger than you argued — has become invisible. Not because it's hidden, but because you stopped looking.

**Blindspot makes the stone stony again.**

This skill audits your *perception* of your own output. It is not checking whether your code is correct — that's `referee2`. It is checking whether you can see what's right in front of you.

---

## Blindspot and Referee 2: Complements, Not Substitutes

**Both should be run. Neither replaces the other.**

| | Blindspot | Referee 2 |
|---|---|---|
| **Question** | Can you see what's in front of you? | Is your code correct? |
| **Timing** | When output first appears, before writing begins | After the project is complete, in a fresh session |
| **Persona** | Shklovsky — restoring perception | Health inspector with a checklist |
| **Catches** | Overlooked problems (vices) and overlooked opportunities (virtues) | Coding errors, replication failures, bad controls |
| **Would have caught the t=1 spike?** | Yes | No |
| **Would have caught a merge error?** | Maybe | Yes |

**The workflow:**

1. Produce output → run `blindspot` → interpret and write
2. Complete the project → open fresh terminal → run `referee2`

---

## When to Invoke

Invoke Blindspot when the user has:
- A figure they're about to describe or publish
- A table they're about to interpret
- A set of results they're about to write up

The trigger is: **output exists and interpretation is about to happen.**

Do not invoke after the writing is done. Invoke before.

---

## How to Run It

The user supplies a path to a figure, table, or results file, plus a brief description of what they think the main finding is.

You will:
1. Read the output file (figure / table / results) and any accompanying notes
2. Work through the four quadrants below **in order**
3. Produce a Blindspot Report with a ruling: CLEAR, CONDITIONAL, or HOLD

Critically: **the user's stated finding is just one item on the list.** Do not let it anchor your audit.

---

## The Blindspot Grid

Every finding falls into one of four quadrants. Two are **vices** — problems hiding in plain sight. Two are **virtues** — opportunities being overlooked.

| | What's there but unseen | What's absent but unnoticed |
|---|---|---|
| **Problems** | **Vice 1: The Unexplained Feature** | **Vice 2: The Convenient Absence** |
| **Opportunities** | **Virtue 1: The Unasked Question** | **Virtue 2: The Unexploited Strength** |

Work through all four quadrants in order. For each finding: state what you found, then mark it **DONE** or **FLAG**. A FLAG means something doesn't have a clean explanation yet.

---

## Vice 1: The Unexplained Feature

*Something in the output that doesn't fit the story, but nobody asked about it.*

The t=1 spike. A coefficient that flips sign in one spec. A sample size that drops by 30% between columns 2 and 3. The author has trained themselves not to see it because they're focused on the main result.

### Protocol

1. **List every visible feature** of the output before interpreting any of them. Every coefficient and its sign. Every spike, dip, or discontinuity. Every pattern across columns. Every sample size. Every number that appears anywhere. The main finding is just one item on this list.

2. **For each feature, ask: what would generate this?** Not "what does this mean for my hypothesis." What could generate this feature — including explanations that have nothing to do with your hypothesis. Work through the mundane explanations first:
   - Rounding or discretization artifact?
   - Sample restriction?
   - Measurement issue?
   - Coincidence given small N?
   - Then work toward substantive explanations.
   - "That's just noise" requires justification, not just assertion.

3. **Identify the single hardest feature to explain under the preferred interpretation.** State it explicitly. Attempt to explain it. If you cannot:
   - Say so
   - State what additional information would resolve it
   - Mark it FLAG

**The rule:** If you can't explain every feature, you don't yet understand your output.

---

## Vice 2: The Convenient Absence

*Something that should be there but isn't. The dog that didn't bark.*

A robustness check that was never run. A subgroup that was never examined. A time period dropped without comment. A placebo test that doesn't exist. A pre-trend that was never plotted.

### Protocol

1. **What would a hostile referee demand to see?** List the robustness checks, falsification tests, and specification variants that a skeptical reader would consider essential. Which of them are missing?

2. **What subgroups were never examined?** Does the identification strategy apply to subpopulations that the paper never checks? Are there natural splits (by gender, by region, by time period, by treatment intensity) that should be in the table but aren't?

3. **What was dropped without comment?** Time periods excluded from the sample. Observations trimmed. Specifications that were tried and abandoned. Covariates that appeared in early drafts but disappeared. Any silent exclusion is a potential vice.

4. **Does N change across columns without explanation?** A sample size mismatch between specifications is almost never random. It traces to a decision — often an undocumented one.

**The rule:** The absence of evidence is not evidence of absence. If something should be there and isn't, that's a finding.

---

## Virtue 1: The Unasked Question

*A pattern in the output that suggests something more interesting than the finding being reported.*

The heterogeneity that's richer than the average effect. The mechanism visible in the data but absent from the hypothesis. The secondary finding hiding in the appendix or the descriptive statistics. The story the data is trying to tell you that you haven't heard yet because you came in with your own story.

### Protocol

1. **Look at the heterogeneity.** Is the average effect hiding a more interesting pattern? Does the treatment work differently for different groups in a way that tells you something about *why* it works?

2. **Look for mechanism evidence.** Is there a *how*, not just a *that*? Do intermediate outcomes move? Do the dynamics suggest a pathway the paper doesn't discuss?

3. **Look at secondary outcomes and descriptive statistics.** Are there patterns in the descriptives that are more interesting than the main regression? Is there a finding in the appendix that deserves the main text?

4. **Is there a paper inside this paper?** Sometimes the secondary finding is the real contribution. Is the author reporting the second-most-interesting thing in their data?

**The rule:** Don't just check whether the paper is right. Check whether it's missing the best version of itself.

---

## Virtue 2: The Unexploited Strength

*Something about the research design, data, or results that the author is underselling.*

Natural variation they haven't leveraged. A falsification test that would demolish the main objection but was never run. An identification argument that's stronger than the paper claims. Descriptive statistics that make the case more powerfully than the regression but are buried in a footnote.

### Protocol

1. **Is the identification strategy stronger than the paper argues?** Is there variation being left on the table? Is there a natural experiment within the natural experiment?

2. **Is there a falsification test that would crush the main objection?** Something easy to run that the author hasn't thought of — a placebo outcome, a placebo treatment group, a different time window where the effect should be zero?

3. **Are the descriptive statistics undersold?** Would a figure make the case more clearly than a table? Is there a visual that would land the argument in one image?

4. **Is the paper positioned too narrowly?** Does the finding speak to a larger literature the authors aren't citing? Is the contribution bigger than the paper claims?

**The rule:** A paper that undersells its strengths is leaving credibility on the table. Find what the author is too close to see.

---

## The Report

After working through all four quadrants, produce a Blindspot Report:

```
## Blindspot Report
**Output:** [what was audited]
**Date:** YYYY-MM-DD
**Stated finding:** [what the user said the main finding was]

### Vice 1: The Unexplained Feature
- Features listed: [count]
- Hardest to explain: [what it is]
- Resolved? [yes / FLAG]
- Findings: [details]

### Vice 2: The Convenient Absence
- Missing checks identified: [list]
- Missing subgroups: [list]
- Unexplained N changes: [if any]
- Findings: [details]

### Virtue 1: The Unasked Question
- Heterogeneity opportunities: [list]
- Mechanism evidence: [list]
- Secondary findings: [list]
- Findings: [details]

### Virtue 2: The Unexploited Strength
- Undersold design features: [list]
- Unused falsification tests: [list]
- Positioning opportunities: [list]
- Findings: [details]

### Ruling
[ ] CLEAR — proceed to interpretation. No vices found; virtues noted for consideration.
[ ] CONDITIONAL — proceed but acknowledge open questions explicitly. Vices flagged but manageable.
[ ] HOLD — do not interpret or publish until flagged vices are resolved.
```

Save the report alongside the output being audited (e.g., `output/figure3_blindspot.md` next to `output/figure3.png`) or in a dedicated folder like `correspondence/blindspot/`.

---

## A Worked Example (the t=1 spike)

To make the protocol concrete:

1. **The figure**: an event-study plot. Treatment at t=0. Coefficients shown for t=−4 through t=+4. The author argues the spike at t=2 is evidence of p-hacking.
2. **Vice 1 — the unexplained feature**: there is also a spike at t=1, smaller but visible. The author has not addressed it.
3. **Mundane explanation tried first**: the spike at t=1 is *inconsistent* with p-hacking (which would predict a spike at the round-number cutoff, not adjacent to it). What else could generate it? Rounding. The data is integer-valued and t=1 is the first post-treatment period where rounding asymmetries would show.
4. **Conclusion**: the t=1 spike is the tell. It points to a mechanism the author missed (rounding), not the one they're arguing for (p-hacking).

This is the move Blindspot is designed to force: **list every feature, ask what generates each one, and do not let the main story collapse your attention**.

---

## Origin and Inspiration

This skill was inspired by conversations with Jason Fletcher (University of Wisconsin), who commented on Scott Cunningham's Substack post (Claude Code 35, March 2026) and asked about the spikes at t=1 and t=3 in a figure where Scott had focused entirely on the spike at t=2. The spike at t=1 was the tell — it was inconsistent with the p-hacking interpretation and pointed immediately to rounding.

Fletcher described this as a habit from graduate training — stepping back from the main coefficient and asking about something else in the table. He wrote about it publicly in ["Owning All the Numbers"](https://jasonmfletcher.substack.com/p/owning-all-the-numbers) (March 2026).

The theoretical frame comes from Viktor Shklovsky's "Art as Device" (1917): the purpose of art is to restore perception, to make the stone stony again. Blindspot applies that principle to empirical research — forcing you to see your own output as a stranger would, before the story you want to tell has automated your perception.

The original implementation lives at [scunning1975/MixtapeTools](https://github.com/scunning1975/MixtapeTools).
