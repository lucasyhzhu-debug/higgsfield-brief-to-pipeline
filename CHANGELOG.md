# Changelog

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
