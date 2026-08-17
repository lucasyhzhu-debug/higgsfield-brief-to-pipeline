# Adversarial copy review — lenses, depth, and the refute pass

Read this when a plan contains copy. It defines **who reviews it, how hard, and what makes a
finding survive**. The review runs at step 2.5, before `plan.html` is built and therefore before
any credit is spent.

## Why this sits before the render, not after

Copy defects are the one class of error that **deterministic overlays cannot save you from**.
`overlay.py` guarantees the text is spelled right and positioned right at 0 credits. It has no
opinion on whether the sentence is publishable. A line that breaches a platform policy or an
advertising rule is exactly as unusable when it is perfectly kerned.

The cost asymmetry is the whole argument. A review costs tokens. Discovering the same defect after
a 5-variant anchor stage costs the credits *and* the tokens *and* the wall-clock.

## What counts as copy

Three surfaces, all in scope, in descending order of risk:

| Surface | Where it appears | Why it is in scope |
|---|---|---|
| Overlay text | `overlay.py annotate` / `dims` payloads, `style-spec.json → overlays` | Final, user-facing, and currently treated as safe because it is free. Free is not the same as compliant. |
| Depicted text | Any prompt asking a model to render signage, packaging, labels, a wordmark, a price | It ships on the image whether or not a human wrote it |
| Campaign copy | Captions, headlines, CTAs carried in the brief | Usually the highest-risk text in the whole deliverable |

**Declare it, never infer it.** The plan carries a `copy` block listing every line and where it
lands. If the block is missing, ask once: *"does this plan contain any user-facing text?"* and
record the answer in `style-spec.json → copy_policy.applies`. A gate that decides for itself
whether it applies is a gate that gets skipped.

## The lens catalogue

Pick from these. **Do not run all of them by default** — an irrelevant lens produces confident,
well-sourced findings about a rule that does not reach the advertiser, which is worse than silence
because it teaches the user to ignore the whole report.

### L1 · Platform policy
Applies when: the deliverable runs as a paid or organic ad on any platform.
Reviews against: the destination platform's live ad standards. Personal attributes, prohibited and
restricted content, category-specific rules, targeting restrictions, age gating.
Must cite: the live policy page, quoted. Platform policies change without notice and the model's
recollection of them is routinely a year stale.

### L2 · Regulated-industry (jurisdiction-specific)
Applies when: the subject is health, medical, therapeutic, financial, legal, alcohol, gambling,
tobacco, food-health-claim, children's, or professional services.
Reviews against: the statute and regulator guidance that actually reaches **this advertiser**.
Must first settle a threshold question: *does this regime govern this entity and this thing?* Get
this wrong and every downstream finding is void.
Australian starting points, with the traps that cost time:

| Regime | Reaches | Trap |
|---|---|---|
| Therapeutic Goods Advertising Code | therapeutic **goods** | Does not regulate the promotion of health **services**. The TGA says so in its own guidance. |
| National Law s133 + AHPRA advertising guidelines | anyone advertising a regulated health service, including corporates | Cite the **current** edition (14 December 2020). Clause numbers from the 2014 edition are widely quoted and no longer exist. |
| Australian Consumer Law s18, s29, s48 | every trader | s48 single-pricing covers **this** supplier's components, not another supplier's separate fee. |
| AANA Codes | most advertising | Self-regulatory. Real, but not a legal prohibition; do not present it as one. |

Other jurisdictions need their own table. Do not port this one.

### L3 · Claim substantiation
Applies when: the copy contains a number, a statistic, a comparison, a superlative, an exclusivity
claim ("the only…"), or a certainty claim.
Reviews against: the primary source of each claim.
The two failures this lens exists to catch:
- **Scope drift.** A figure that is true of a narrow population restated as a general one. This is
  the single most common defect in marketing copy derived from a research source, and it survives
  every other lens because the number itself checks out.
- **Certainty on a probabilistic thing.** "The only way to know", "guaranteed", "eliminates".

### L4 · Brand and legal
Applies when: the copy names a third party, cites an authority, or carries a price or an offer.
Reviews: implied endorsement or affiliation, offers stated without their terms, prices that the
destination will not honour, trade mark use.

## Choosing lenses and depth

```
Ordinary commercial copy, no claims, no regulated subject
  → L1 + L4, one refuter.                              (~2 lenses + 1 refute)

Any number, comparison, superlative, or exclusivity claim
  → add L3.

Regulated subject, OR a health/financial/therapeutic claim, OR copy naming a regulator,
professional body, or clinical guideline
  → all four, one refuter per lens.                    (~4 lenses + 4 refute)
```

This ladder sets the refuter count too, and it is the only place that does: **one refuter on the
2-lens path, one per lens at full depth.** SKILL.md defers here on purpose so the number that bounds
the cost has a single authority.

**Escalate, never de-escalate mid-run.** If a reviewer surfaces a regulated claim the plan did not
declare, add the lens and rerun rather than reasoning around it. Cap the fix-and-re-review loop at
**2 rounds**; anything still open goes to `copy_review.unverified` and the user decides at the gate.
Escalation widens the fan-out, so an uncapped loop is the one place this gate can cost more than the
renders it protects.

## `style-spec.json → copy_policy` — reviewing a set without paying per item

Locking *which* lenses to run is not the same as locking *whether to run them*, and only the second
one scales. A 26-card set built by substituting `{LETTER}`/`{ANIMAL}` into a locked template has 26
different copy strings, so a naive "re-run when the copy changes" rule mandates 26 full fan-outs to
protect maybe 50 credits of renders. That is a failed gate.

Review the **template**, once, with its placeholder domain written down:

```jsonc
"copy_policy": {
  "applies": true,
  "lenses": ["L1 platform policy", "L4 brand and legal"],
  "cleared_templates": [
    { "template": "{LETTER} is for {ANIMAL}",
      "placeholders": { "LETTER": "A-Z", "ANIMAL": "common animal noun, no brand names" },
      "cleared_on": "2026-08-17", "status": "SHIP" }
  ],
  "cleared_wording": ["Bulk billed for eligible patients."],
  "standing_lines": ["Screening test. Talk to your doctor."],
  "open_items": []
}
```

A line that matches a cleared template with **every substitution inside the declared domain**
inherits its status with no subagent. Anything else — a new brand name, a number, a superlative
entering through a placeholder — is out of domain and gets a real review. 26 reviews become 1 plus
the exceptions.

Two constraints on that. `cleared_wording` is verbatim-match only, so it never covers a substituted
line; that is what `cleared_templates` is for. And a cleared template does not survive a change of
destination channel or jurisdiction, because L1 and L2 were decided against the old one.

It is called `copy_policy` and not `copy_review` because `plan.json → copy_review` is this run's
findings. Same neighbourhood, incompatible shapes; an agent that has read one will otherwise write
the other's keys.

## The refute pass is mandatory

Every finding set gets attacked by an independent reviewer that **defaults to refusing the finding**
unless it can locate the actual rule text.

This is not a formality. In the run that motivated this gate, 43 raw findings went in; the refute
pass killed an entire regulatory framework that four of them rested on, corrected clause numbers
from a superseded edition, and downgraded several blockers to advisory. Without it the deliverable
is a list of confident citations to rules that do not apply.

Give the refuter these failure modes by name:

- A regime cited against the wrong kind of entity or the wrong kind of thing (a goods code applied
  to a service, practitioner rules applied to a corporation).
- Policy quoted from memory of an older version, or a clause number from a repealed edition.
- Best-practice guidance or a self-regulatory code presented as a legal prohibition.
- "Misleading" asserted where the advertiser's own published material and a published guideline
  both support the copy.
- A finding whose cited source does not say what the finding claims it says.

And tell it the opposite too: **do not reflexively refute**. Where the rule is real and clearly
breached, confirm it and name the source that settles it. A refuter that kills everything is as
useless as a reviewer that flags everything.

## What a finding must carry

A finding with no source is not a finding. Required fields:

- the exact words objected to, quoted from the copy
- the rule, with its clause or section
- a URL or document name where that rule is stated, or the literal token `NOT-VERIFIED`
- why the rule reaches *this* advertiser and *this* product
- replacement wording that preserves the creative intent

`NOT-VERIFIED` findings are never dropped silently. They surface in plan.html under **Unverified**,
with what would settle each one. Some of the most decision-relevant items end up here: things that
render client-side, sit behind a login, or can only be confirmed inside the client's own account.

## Severity and what each one does

| Severity | Meaning | Effect on the gate |
|---|---|---|
| `blocker` | Unlawful, or will be rejected by the platform, as written | **Hard stop.** No render, no overlay, until resolved or explicitly waived in writing by the user. |
| `high` | A central claim is false or materially unstated | Renders red. Advisory; the user may approve over it. |
| `medium` | Incomplete, imprecise, or borrowing authority | Renders amber. Advisory. |
| `low` | Hygiene. Do it because it is free. | Renders in the list. Advisory. |

Only findings that **survived the refute pass at blocker severity** hard-stop. A reviewer's own
severity is a proposal, not a verdict.

## Reporting into the plan

Write results to `plan.json → copy_review` (schema in `build_plan_html.py`). Every line in the
`copy` block gets a status of `SHIP`, `FIX`, or `KILL`. Group blockers **by cause, not by line**, so
one defect hitting five creatives appears once with five affected IDs. A per-line list of the same
finding repeated is how a report becomes unreadable.

Record disagreements between lenses rather than smoothing them. Where two reviewers reached opposite
conclusions, say so, give the call, and give the reasoning. A suppressed disagreement is the finding
most likely to have been resolved wrongly.

## What this gate does not do

It reviews what goes to Higgsfield. It does not review the destination. Landing page contradictions,
prices the site shows two ways, purchase paths that contradict the stated process: all of these will
sink a campaign and none of them are in scope here. Note them and hand them back to the user.
