# Changelog

## 1.1.0 — 2026-08-17

**New: copy is adversarially reviewed before it is rendered, not after.**

Any plan carrying user-facing text now passes through a review at step 2.5, before `plan.html` is
built and therefore before a credit is spent. Multiple reviewer lenses run concurrently, then an
independent skeptic attacks each finding and defaults to rejecting it unless it can locate the
actual rule text. Only what survives that second pass reaches the plan.

The refute pass is the point. In the review that motivated this, 43 raw findings went in; the
skeptics killed an entire regulatory framework that four of them rested on, and corrected clause
numbers quoted from a superseded edition of a guideline. An unrefuted list cites rules that do not
reach the advertiser, and one bad citation gets the whole report discounted.

This also closes a gap the skill had by construction. Deterministic overlays were treated as the
safe layer because they cost nothing and cannot misspell. Free is not the same as compliant, and the
overlay layer is exactly where the final user-facing text lands.

- New `references/copy-review-lenses.md`: four lenses, when each applies, depth and escalation
  rules, the refute-pass failure modes, and what a finding must carry to count.
- `plan.json` gains `copy` (every line, its surface, its stage, its status) and `copy_review`
  (lenses, findings, unverified items, disagreements, waivers).
- `build_plan_html.py` renders both, sorts findings blockers-first, links or flags each source, and
  **exits 2** when the gate is closed. A plan carrying `copy` with no `copy_review` key renders
  REVIEW NOT RUN and withholds the approve footer: a skipped review must never read like a clean
  one. Surviving `blocker` findings hard-stop; `high` and below are advisory.
- `allowed-tools` gains `Agent`, `WebSearch` and `WebFetch`. The review is close to worthless
  without live sources, since platform policies and regulator guidance both move and a confidently
  quoted stale clause is the most expensive kind of wrong.
- New `tests/test_build_plan_html.py` (stdlib, 15 tests) covering the four gate states.
- `style-spec.json` gains a `copy_review` block so a set locks its lenses and cleared wording once
  instead of re-reviewing an unchanged template per variant.

## 1.0.2 — 2026-08-11

**Fix: YAML frontmatter did not parse — all skill metadata was silently dropped.**

The `description` was an unquoted plain scalar containing `Triggers: "…"`. A colon
followed by a space is not legal inside a plain YAML scalar, so the whole frontmatter
block failed to parse and `name`, `description`, and `allowed-tools` were all discarded
at load time — meaning the skill ran without its declared tool restriction. Present since
the skill was first written; surfaced by `claude plugin validate`, which a runtime smoke
test cannot catch. Now a folded block scalar (`>-`), with the trigger phrasing intact.

**The skill is also now self-testable from any install.**

`plan.example.json` moved from the repo root into the skill itself
(`skills/higgsfield-brief-to-pipeline/examples/`). It previously shipped only in the repo,
so a plugin user had no bundled plan to render and no offline way to confirm the toolchain
worked — a fresh-session smoke test could verify the scripts were *found* but not that they
*ran*.

- New **Self-test** section in `SKILL.md`: one command, 0 credits, no Higgsfield account.
- Added to the quick-reference table, and cited as the `plan.json` shape reference alongside
  the schema docstring.
- `.gitignore` made path-agnostic for generated preview HTML.

No changes to the pipeline protocol, prompting guidance, or either script.

## 1.0.1 — 2026-08-11

**Fix: script paths did not resolve under a real plugin install.**

`SKILL.md` told Claude to build paths from `$CLAUDE_PLUGIN_ROOT`, but that variable is
**not exported into the Bash tool environment** — it is only set for hooks and MCP
servers. Under a plugin install the path expanded to `/skills/...` and every script
invocation failed. Caught by a headless fresh-session smoke test after 1.0.0 shipped.

Replaced with a three-branch probe that resolves the skill directory by checking, in
order: the env var (hook/MCP context), the plugin cache (highest version wins), then a
manual `~/.claude/skills/` install. Added a "Common mistakes" entry so the wrong pattern
is not reintroduced, and a note that Bash state does not persist between tool calls.

No changes to the pipeline protocol, prompting guidance, or either script.

## 1.0.0 — 2026-08-11

Initial open-source release.

- `SKILL.md` — the brief → pipeline orchestration protocol: project scaffolding,
  role-labelled reference ingest, credit-aware stage design, the mandatory HTML
  approval gate, staged execution with auto-verification and human gates, and
  `style-spec.json` as persistent locked state.
- `references/higgsfield-models.md` — model → use map, validated multi-reference CLI
  pattern, concurrency guidance, and six credit-optimisation rules.
- `references/prompting-principles.md` — multi-reference prompting levers and three
  reusable template skeletons (spec elevation, derived view, in-location composite).
- `scripts/build_plan_html.py` — renders `plan.json` into the self-contained HTML
  approval gate. Pure stdlib. Optional `theme` key.
- `scripts/overlay.py` — deterministic zero-credit `dims` and `annotate` compositing.
  Optional `banner` / `accent` keys.
- `examples/plan.example.json` — a complete five-stage plan, renderable without a
  Higgsfield account.

Script paths resolve via `$CLAUDE_PLUGIN_ROOT` when installed as a plugin, with a
documented fallback for manual `~/.claude/skills/` installs.
*(Superseded in 1.0.1 — that variable is not exported to the Bash tool, so this did not
actually work under a plugin install.)*
