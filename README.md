# higgsfield-brief-to-pipeline

**A credit-aware orchestration skill for [Higgsfield](https://higgsfield.ai) image/video batches.**
Give Claude a brief and a folder of reference images; it designs the whole render pipeline, shows you
an HTML preview as a **mandatory approval gate**, and only then spends credits — executing
stage-by-stage with auto-verification, human gates, and zero-credit deterministic overlays.

> **Core principle: spend tokens to save credits.**
> Planning, verification, and Pillow-composited text are cheap. Renders are not.

---

## The problem this solves

The Higgsfield CLI ships excellent per-task skills (`higgsfield-generate`, `higgsfield-soul-id`,
`higgsfield-product-photoshoot`, …). They're great at *one render*. They have nothing to say about
the layer above:

- You have 12 deliverables, 6 references, and a credit balance.
- Half the deliverables should be *derived* from an approved anchor, not regenerated — otherwise the
  design drifts and you pay twice.
- A third of the "renders" are actually text and dimension labels, which image models misspell and
  charge you for.
- You want to see the plan before it burns 300 credits, not after.

This skill is that layer. It sits *above* the vendor skills and turns an ad-hoc pile of prompts into
a reviewable, reproducible, cost-bounded pipeline.

## What it actually does

```
Name + scaffold project
        ↓
Ingest brief; open every reference; assign each a ROLE
   (structure / material / style-DNA / logo / product / format / scene)
        ↓
Design pipeline — models, params, ordered refs, variant counts,
   explicit auto-verify criteria, credit estimate, human gates
        ↓
Carries copy? → adversarial review: lenses in parallel, then a
   skeptic that must find the rule text or drop the finding
        ↓  (surviving blockers loop back and get fixed)
┌──────────────────────────────────────────────┐
│  BUILD plan.html  ←── THE GATE. Stop. Wait.  │   ← no credits spent yet
└──────────────────────────────────────────────┘
        ↓ approve
Execute stage → auto-verify vs spec → FAIL? re-roll ONE variable (≤2)
        ↓
Human gate: you pick the anchor → every later stage DERIVES from it
        ↓
Deterministic overlays for text/dimensions (0 credits)
        ↓
scores.md — every verdict logged
```

### The six ideas worth stealing

1. **The HTML gate is non-negotiable.** No credit-spending render runs before you approve a rendered
   preview showing stages, models, references, verify criteria, and a credit estimate against your
   budget. The skill ships an explicit rationalization table to stop Claude talking itself past it.
2. **Role-label every reference.** The single biggest quality lever when fusing multiple images.
   "Use the FIRST image as STRUCTURE, the SECOND for MATERIAL, the THIRD as STYLE-DNA" beats dumping
   five images into one prompt and hoping.
3. **Derive, don't regenerate.** Lock one anchor at a human gate, then feed it as image-1 *identity*
   into every downstream view. The design stops drifting and you stop paying to re-roll it.
4. **Never let an image model type text.** Dimension callouts, labels, menu prices → composited with
   Pillow at **0 credits**, spelled correctly, repeatable across a whole set.
5. **`style-spec.json` turns a batch into a system.** Locked decisions, prompt templates with
   `{PLACEHOLDERS}`, and overlay coordinates persist, so producing the *next* 25 variants is
   substitution — not re-deciding.
6. **Review the copy before you pay to render it, and make the reviewers argue.** Reviewer agents
   run per lens, then an independent skeptic attacks every finding and drops it unless it can quote
   the actual rule. Unrefuted compliance review is worse than none: it cites regimes that don't
   reach the advertiser and clause numbers from superseded editions, and one bad citation gets the
   whole report ignored. The gate also covers the 0-credit overlay layer, because free to composite
   and safe to publish are different properties.

## Install

**As a plugin (recommended):**

```
/plugin marketplace add lucasyhzhu-debug/higgsfield-brief-to-pipeline
/plugin install higgsfield-brief-to-pipeline
```

**Manually** (also works in Codex, Copilot CLI, Gemini CLI, and anything else that reads `SKILL.md`):

```bash
git clone https://github.com/lucasyhzhu-debug/higgsfield-brief-to-pipeline
cp -r higgsfield-brief-to-pipeline/plugins/higgsfield-brief-to-pipeline/skills/higgsfield-brief-to-pipeline \
      ~/.claude/skills/
```

### Requirements

| | |
|---|---|
| Higgsfield CLI | on `PATH`, authenticated — `higgsfield auth login` |
| Python | 3.9+ |
| `build_plan_html.py` | pure stdlib, no dependencies |
| `overlay.py` | `pip install pillow numpy` |

This project is **not affiliated with Higgsfield**. You need your own account and credits.

## Use it

Just describe what you want and point at your references:

> Here's the brief and a folder of references — design the Higgsfield workflow.

The skill takes it from there: names the project, tells you where to drop references, plans, and
stops at the HTML gate.

## What's in the box

```
plugins/higgsfield-brief-to-pipeline/skills/higgsfield-brief-to-pipeline/
  SKILL.md                          the orchestration protocol
  references/
    higgsfield-models.md            model → use map, credit-optimisation rules, CLI patterns
    prompting-principles.md         multi-reference prompting levers + reusable templates,
                                    distilled from Google / OpenAI / BFL official guidance
    copy-review-lenses.md           which reviewers to run on copy, how deep, and the refute pass
  scripts/
    build_plan_html.py              plan.json → the approval gate (stdlib only, themeable)
    overlay.py                      dims | annotate — 0-credit text & dimension compositing
  examples/
    plan.example.json               a complete 5-stage plan; also the plan.json shape reference

tests/
  test_build_plan_html.py           15 stdlib tests over the four copy-gate states
```

The example ships **inside the skill**, so the toolchain is self-testable from any install without
cloning this repo — see the *Self-test* section of `SKILL.md`.

Try the gate right now, no Higgsfield account needed:

```bash
SKILL=plugins/higgsfield-brief-to-pipeline/skills/higgsfield-brief-to-pipeline
python "$SKILL/scripts/build_plan_html.py" "$SKILL/examples/plan.example.json" /tmp/plan.html
```

### Theming the preview

`plan.json` accepts an optional `theme` key; it defaults to a neutral slate/amber.

```json
"theme": { "accent": "#26303f", "gold": "#c98a2e" }
```

`overlay.py` takes `banner` and `accent` hex keys in its annotation config for the same reason.

## A note on credit costs

`higgsfield model list --json` reports `display_name`, `type`, and `job_set_type` — but **no cost
field**. Every figure in `references/higgsfield-models.md` is a *typical estimate*; your Higgsfield
dashboard and `higgsfield account status` are the source of truth. The skill is instructed to always
present costs as estimates and never as guaranteed prices. Costs drift — re-check them.

## Contributing

Issues and PRs welcome. The most useful contributions are:

- **Model map corrections** as Higgsfield ships and deprecates models.
- **Prompt template additions** for deliverable shapes not yet covered (packaging, apparel flats,
  architectural interiors, character sheets).
- **New overlay modes** — the two shipped (`dims`, `annotate`) cover spec sheets; callout styles for
  other document types would extend the 0-credit principle further.

## Licence

MIT — see [LICENSE](LICENSE).
