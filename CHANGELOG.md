# Changelog

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
