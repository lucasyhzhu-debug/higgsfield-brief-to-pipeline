#!/usr/bin/env python
"""Render a Higgsfield workflow plan (JSON) into a styled, self-contained HTML
process-preview page. Zero dependencies (pure stdlib). This page is the MANDATORY
review gate shown to the user BEFORE any credit-spending render runs.

Usage: python build_plan_html.py <plan.json> <out.html>

plan.json schema (all fields optional except project, stages):
{
  "project": "Retail Kiosk Reskin v1",
  "brief_summary": "one-paragraph restatement of the user's intent",
  "theme": {"accent":"#26303f","gold":"#c98a2e"},   # optional; neutral slate/amber by default
  "deliverables": [{"name":"front spec (dimensioned)","count":2,"format":"orthographic elevation"}],
  "references": [{"file":"front spec.jpeg","role":"structure","stages":"2","note":"replicate geometry"}],
  "models": [{"need":"spec render","model":"nano_banana_2","credits":"~2/img","why":"identity+structure fusion"}],
  "stages": [{
     "n":"2","name":"Front spec (anchor)","model":"nano_banana_2","params":"2k 4:3",
     "refs":["front spec=structure","style-dna","logo"],"variants":5,
     "verify":["orthographic","stepped counter reads","palette hex","signage spelled"],
     "credits":10,"gate":"HUMAN — pick 1 per option","derives_from":"-"}],
  "optimizations":["1 cheap validation render before batch","parallel background renders",
                   "derive don't regenerate","deterministic overlays for text+dims (0 credits)"],
  "credit_estimate":{"min":30,"max":40,"budget":860},

  # --- copy + adversarial review (gate rules: SKILL.md § The Copy Rule; how to run the
  #     review itself: references/copy-review-lenses.md) --------------------------------
  # Omit BOTH blocks when a plan carries no user-facing text.
  "copy":[{"id":"h1","text":"Now bulk billed.","surface":"overlay","stage":"5","status":"FIX"}],
  #   surface: overlay | depicted | caption      status: SHIP | FIX | KILL
  "copy_review":{
    "lenses":["L1 platform policy","L3 claim substantiation"],
    "refuted":11,                                    # findings killed by the refute pass
    "findings":[{"id":"f1",                          # stable handle; what `waived` refers to
                 "severity":"blocker",               # blocker | high | medium | low
                 "affects":["h1"],                   # copy[].id values
                 "rule":"AHPRA advertising guidelines cl 4.2",
                 "source":"https://www.ahpra.gov.au/…",   # or the token NOT-VERIFIED
                 "quote":"Now bulk billed.",         # the exact offending words
                 "why":"why the rule reaches this advertiser and this product",
                 "fix":"replacement wording"}],
    # unverified = questions about the PLAN that no lens could source. A finding whose source is
    # NOT-VERIFIED is a separate thing (a specific line's rule is unconfirmed); list it here too
    # only if settling it would change whether the plan can run.
    "unverified":[{"question":"…","settled_by":"…"}],
    "disagreements":[{"issue":"…","call":"…"}],
    "waived":["f1"]  # finding ids the user waived in writing (a rule string still works for
                     # older plans). A near-miss fails closed — the gate stays shut.
  }
}
"""
import os, sys, json, html

with open(sys.argv[1], encoding="utf-8") as _f:
    plan = json.load(_f)
OUT = sys.argv[2]
e = lambda s: html.escape(str(s))
chips = lambda xs: "".join(f"<span class='chip'>{e(x)}</span>" for x in xs or [])

def cell(v, render=None):
    if isinstance(v, list):
        v = ", ".join(str(x) for x in v)
    return render(v) if render else e(v)

def table(items, cols):
    """cols: [(key, label)] or [(key, label, render)]. One spec drives header AND body,
    so a column can't drift out of sync with its heading."""
    head = "".join(f"<th>{c[1]}</th>" for c in cols)
    body = "".join(
        "<tr>" + "".join(f"<td>{cell(it.get(c[0], ''), c[2] if len(c) > 2 else None)}</td>"
                         for c in cols) + "</tr>"
        for it in items or [])
    return f"<table><tr>{head}</tr>{body}</table>"

DELIV_COLS = [("name", "Deliverable"), ("count", "Count"), ("format", "Format")]
REF_COLS = [("file", "Reference"), ("role", "Role"), ("stages", "Stages"), ("note", "Note")]
MODEL_COLS = [("need", "Need"), ("model", "Model"), ("credits", "Cost"), ("why", "Why")]

theme = plan.get("theme", {})
ACC = e(theme.get("accent", "#26303f"))   # headings, stage numbers, tag pill
GOLD = e(theme.get("gold", "#c98a2e"))    # card rule, chips, footer border

ce = plan.get("credit_estimate", {})
budget = ce.get("budget")
cmax = ce.get("max")
# Over budget must not render as a full healthy bar — on a page whose job is "authorise this
# spend?", the overrun case is the one the visual has to get right.
over_budget = bool(budget and cmax and cmax > budget)
pct = int(min(100, (cmax / budget) * 100)) if (budget and cmax) else 0
bar_label = (f"OVER BUDGET by {e(cmax - budget)} cr" if over_budget
             else f"{e(cmax)} cr of {e(budget)} budget")

stage_cards = ""
for s in plan.get("stages", []):
    gate = s.get("gate", "")
    gate_html = f'<div class="gate">⛔ GATE · {e(gate)}</div>' if gate else ""
    derives = s.get("derives_from", "")
    derives_html = (f'&nbsp;·&nbsp; <b>Derives from:</b> {e(derives)}'
                    if derives and derives != "-" else "")
    verify = "".join(f"<li>{e(v)}</li>" for v in s.get("verify", []))
    stage_cards += f"""
    <div class="card">
      <div class="card-h"><span class="sn">{e(s.get('n',''))}</span><h3>{e(s.get('name',''))}</h3>
        <span class="cred">{e(s.get('credits','?'))} cr</span></div>
      <div class="meta"><b>Model:</b> <code>{e(s.get('model',''))}</code> &nbsp;·&nbsp;
        <b>Params:</b> {e(s.get('params',''))} &nbsp;·&nbsp;
        <b>Variants:</b> {e(s.get('variants',''))}
        {derives_html}</div>
      <div class="refs">{chips(s.get('refs'))}</div>
      <div class="verify"><b>Auto-verify →</b><ul>{verify}</ul></div>
      {gate_html}
    </div>"""

opt_html = "".join(f"<li>{e(o)}</li>" for o in plan.get("optimizations", []))
deliv = table(plan.get("deliverables"), DELIV_COLS)
refs_t = table(plan.get("references"), REF_COLS)
models_t = table(plan.get("models"), MODEL_COLS)

# ---- copy + adversarial copy review -------------------------------------------------------
copy_lines = plan.get("copy") or []
# One derivation of "has this plan been reviewed", used everywhere. Keyed on PRESENCE of the key,
# not on truthiness: an explicit `copy_review: {}` means the review ran and found nothing, which
# is a pass. Asking the question two ways is what lets a third state (`null`) slip through.
has_review = "copy_review" in plan and plan["copy_review"] is not None
review = plan.get("copy_review") or {}
findings = review.get("findings") or []
waived = set(review.get("waived") or [])
SEV_ORDER = {"blocker": 0, "high": 1, "medium": 2, "low": 3}
findings = sorted(findings, key=lambda f: SEV_ORDER.get(f.get("severity", "low"), 9))
# Waivers key on the finding's `id`, falling back to its `rule` string for older plans.
is_waived = lambda f: f.get("id") in waived or f.get("rule") in waived
open_blockers = [f for f in findings if f.get("severity") == "blocker" and not is_waived(f)]

# Every reason a plan is not approvable lands in one list. The banner, the footer, the exit
# status and the gate marker all derive from it, so adding a fourth gate is one append, not
# four f-strings to reconcile.
stops = []
if copy_lines and not has_review:
    stops.append({"id": "no-review",
                  "banner": "REVIEW NOT RUN. This plan carries user-facing copy that has not "
                            "been through the adversarial review.",
                  "status": "BLOCKED: copy review not run"})
elif open_blockers:
    stops.append({"id": "blocked",
                  "banner": f"{len(open_blockers)} unresolved copy blocker(s). No render and no "
                            f"overlay runs until these are fixed, or waived by you in writing.",
                  "status": f"BLOCKED: {len(open_blockers)} open copy blocker(s)"})
hard_stop = bool(stops)
gate_state = stops[0]["id"] if stops else "approvable"

COPY_COLS = [("id", "ID", lambda v: f"<code>{e(v)}</code>"),
             ("text", "Text"), ("surface", "Surface"), ("stage", "Stage"),
             ("status", "Status",
              lambda v: f"<span class='pill "
                        f"{ {'SHIP':'ok','FIX':'warn','KILL':'bad'}.get(v, '') }'>"
                        f"{e(v or 'UNREVIEWED')}</span>")]
UNVER_COLS = [("question", "Question"), ("settled_by", "Settled by")]

copy_html = f"""
<h2>Copy under review ({len(copy_lines)} lines)</h2>
<p class="lead">Every piece of user-facing text in this plan, and where it lands. Deterministic
overlays guarantee spelling and position at 0 credits; they have no opinion on whether a line is
publishable. That is what the review below is for.</p>
{table(copy_lines, COPY_COLS)}""" if copy_lines else ""

def _finding_card(f):
    sev = f.get("severity", "low")
    src = str(f.get("source") or "")
    src_html = ('<span class="nv">NOT-VERIFIED</span>' if src.upper() == "NOT-VERIFIED"
                else f'<a href="{e(src)}">{e(src)}</a>' if src.startswith("http")
                else e(src))
    quote = f'<blockquote>{e(f["quote"])}</blockquote>' if f.get("quote") else ""
    why = f'<p class="why">{e(f["why"])}</p>' if f.get("why") else ""
    fix = f'<p class="fix"><b>Replace with:</b> {e(f["fix"])}</p>' if f.get("fix") else ""
    waived_html = ('<div class="waived">WAIVED by the user for this run</div>'
                   if is_waived(f) else "")
    return f"""
    <div class="find sev-{e(sev)}">
      <div class="find-h"><span class="sev">{e(sev)}</span><b>{e(f.get('rule',''))}</b></div>
      {quote}{why}{fix}
      <div class="find-f">{chips(f.get('affects'))}<span class="src">{src_html}</span></div>
      {waived_html}
    </div>"""

review_html = ""
if copy_lines and not has_review:
    review_html = """
<h2>Adversarial copy review</h2>
<div class="stop"><b>REVIEW NOT RUN.</b> This plan carries user-facing copy that has not been
through the adversarial review. The gate is not passable in this state. Run step 2.5 and rebuild
this page.</div>"""
elif has_review:
    refuted = review.get("refuted")
    cards = "".join(_finding_card(f) for f in findings) or \
        '<p class="lead">No findings survived the refute pass.</p>'
    unver = review.get("unverified") or []
    unver_html = f"""
<h3>Unverified</h3>
<p class="lead">Nobody could source these to a primary document. They are not dismissed; they are
open questions, and some of them decide whether the copy above can run at all.</p>
{table(unver, UNVER_COLS)}""" if unver else ""
    disag = "".join(f"<li><b>{e(d.get('issue',''))}</b> — {e(d.get('call',''))}</li>"
                    for d in review.get("disagreements") or [])
    disag_html = f"<h3>Where the reviewers disagreed</h3><ul class='opt'>{disag}</ul>" if disag else ""
    review_html = f"""
<h2>Adversarial copy review</h2>
<div class="refstat">Lenses: {chips(review.get('lenses')) or '<span class="chip">none recorded</span>'}
{f'&nbsp;·&nbsp; <b>{e(refuted)}</b> findings killed by the refute pass' if refuted is not None else ''}
&nbsp;·&nbsp; <b>{len(open_blockers)}</b> open blocker(s)</div>
{cards}{unver_html}{disag_html}"""
HTML = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(plan.get('project','Workflow'))} — Process Preview</title>
<style>
:root{{--ink:#1f232b;--mut:#666d78;--line:#e4e7ec;--bg:#f8f9fb;--soft:#eef1f5;--acc:{ACC};--gold:{GOLD};--ok:#2f7d4f}}
*{{box-sizing:border-box}}body{{margin:0;font:15px/1.55 -apple-system,Segoe UI,Roboto,sans-serif;color:var(--ink);background:var(--bg)}}
.wrap{{max-width:1040px;margin:0 auto;padding:38px 26px 80px}}
.tag{{display:inline-block;background:var(--acc);color:#f4f4f7;font-size:12px;letter-spacing:.12em;text-transform:uppercase;padding:5px 12px;border-radius:20px}}
h1{{font-size:30px;margin:14px 0 4px}}h2{{font-size:19px;margin:38px 0 12px;border-bottom:2px solid var(--line);padding-bottom:6px}}
.lead{{color:var(--mut);font-size:16px;max-width:70ch}}
table{{width:100%;border-collapse:collapse;margin:6px 0;background:#fff;border:1px solid var(--line);border-radius:10px;overflow:hidden}}
th,td{{text-align:left;padding:9px 12px;border-bottom:1px solid var(--line);vertical-align:top}}
th{{background:var(--soft);font-size:12px;letter-spacing:.04em;text-transform:uppercase;color:var(--mut)}}
tr:last-child td{{border-bottom:none}}
.card{{background:#fff;border:1px solid var(--line);border-left:4px solid var(--gold);border-radius:12px;padding:16px 18px;margin:12px 0;box-shadow:0 1px 3px rgba(20,10,40,.04)}}
.card-h{{display:flex;align-items:center;gap:10px}}.card-h h3{{margin:0;font-size:17px;flex:1}}
.sn{{background:var(--acc);color:#fff;width:28px;height:28px;border-radius:50%;display:grid;place-items:center;font-weight:700;font-size:14px}}
.cred{{background:var(--soft);color:var(--acc);font-weight:700;padding:3px 10px;border-radius:14px;font-size:13px}}
.meta{{color:var(--mut);font-size:13px;margin:8px 0}}code{{background:var(--soft);padding:1px 6px;border-radius:5px;font-size:12px}}
.refs{{margin:8px 0}}.chip{{display:inline-block;background:var(--soft);border:1px solid var(--line);color:var(--mut);font-size:12px;padding:3px 9px;border-radius:14px;margin:2px 4px 2px 0}}
.verify ul{{margin:4px 0 0;padding-left:20px}}.verify li{{font-size:13px;color:var(--ink)}}
.gate{{margin-top:10px;background:#fff4f4;border:1px solid #f0c9c9;color:#9b2222;font-weight:700;padding:8px 12px;border-radius:8px;font-size:13px}}
.bar{{height:26px;background:#eee;border-radius:13px;overflow:hidden;border:1px solid var(--line)}}
.fill{{height:100%;background:linear-gradient(90deg,var(--ok),#7bbf93);width:{pct}%;display:grid;place-items:center;color:#fff;font-size:12px;font-weight:700}}
.fill.over{{background:linear-gradient(90deg,#c0392b,#e06055)}}
.opt li{{margin:3px 0}}.foot{{margin-top:30px;padding:16px 18px;background:#fff;border:1px dashed var(--gold);border-radius:12px;color:var(--mut)}}
.foot b{{color:var(--acc)}}
h3{{font-size:15px;margin:22px 0 6px}}
.pill{{display:inline-block;font-size:11px;font-weight:700;letter-spacing:.06em;padding:3px 9px;border-radius:12px;background:var(--soft);color:var(--mut)}}
.pill.ok{{background:#e6f4ec;color:#1e6b40}}.pill.warn{{background:#fdf1dd;color:#8a5a12}}.pill.bad{{background:#fdeaea;color:#9b2222}}
.find{{background:#fff;border:1px solid var(--line);border-left:4px solid var(--mut);border-radius:10px;padding:12px 15px;margin:9px 0}}
.find-h{{display:flex;align-items:center;gap:9px;font-size:14px}}
.sev{{font-size:10px;font-weight:800;letter-spacing:.1em;text-transform:uppercase;padding:3px 8px;border-radius:10px;background:var(--soft);color:var(--mut)}}
.sev-blocker{{border-left-color:#c0392b;background:#fffafa}}.sev-blocker .sev{{background:#c0392b;color:#fff}}
.sev-high{{border-left-color:#d98324}}.sev-high .sev{{background:#fdf1dd;color:#8a5a12}}
.sev-medium{{border-left-color:#c9a227}}.sev-low{{border-left-color:#b9c0ca}}
.find blockquote{{margin:8px 0;padding:6px 12px;border-left:3px solid var(--line);color:var(--ink);font-style:italic;background:var(--soft);border-radius:0 6px 6px 0}}
.find .why{{margin:6px 0;font-size:13px;color:var(--mut)}}
.find .fix{{margin:6px 0;font-size:13px}}.find .fix b{{color:var(--ok)}}
.find-f{{margin-top:8px;font-size:12px}}.src{{color:var(--mut);word-break:break-all}}
.src a{{color:var(--mut)}}.nv{{background:#fdf1dd;color:#8a5a12;font-weight:700;padding:2px 8px;border-radius:10px}}
.waived{{margin-top:8px;font-size:12px;font-weight:700;color:#8a5a12}}
.refstat{{background:#fff;border:1px solid var(--line);border-radius:10px;padding:10px 14px;font-size:13px;color:var(--mut)}}
.stop{{margin:12px 0;padding:14px 18px;background:#fdeaea;border:2px solid #c0392b;border-radius:12px;color:#7d1d1d;font-size:14px}}
.stop b{{color:#c0392b}}
</style></head><body data-gate="{gate_state}"><div class="wrap">
<span class="tag">Higgsfield · Process Preview</span>
<h1>{e(plan.get('project','Workflow'))}</h1>
<p class="lead">{e(plan.get('brief_summary',''))}</p>
{"".join(f'<div class="stop"><b>⛔ HARD STOP.</b> {e(s["banner"])}</div>' for s in stops)}

<h2>Deliverables</h2>{deliv}
{copy_html}
{review_html}

<h2>References &amp; roles</h2>
<p class="lead">Every reference is role-labelled — the single biggest quality lever when fusing multiple images.</p>
{refs_t}

<h2>Model selection</h2>{models_t}

<h2>Pipeline ({len(plan.get('stages',[]))} stages)</h2>{stage_cards}

<h2>Credit optimisation</h2><ul class="opt">{opt_html}</ul>

<h2>Estimated spend</h2>
<div class="bar"><div class="fill{' over' if over_budget else ''}">{bar_label}</div></div>
<p class="lead" style="margin-top:8px">Range {e(ce.get('min','?'))}–{e(cmax)} credits (incl. variants &amp; up to 2 retries/stage). Overlays &amp; dimensioning add <b>0 credits</b>.</p>

{'''<div class="stop"><b>Not approvable as it stands.</b> The open item is stated at the top of
this page. Fix it and rebuild, or tell me explicitly which blocker you are waiving and why.
Nothing renders and no overlay is composited until then.</div>'''
 if hard_stop else
 '''<div class="foot"><b>This is a preview, not a commitment.</b> No credits are spent until you approve.
Reply with changes (swap a model, fewer variants, tighter scope) or <b>approve</b> to run the pipeline stage-by-stage with auto-verification and the human gate(s) above.</div>'''}
</div></body></html>"""
# A shut gate must not leave an approvable artifact on disk. An exit code lives for one tool
# call; a stale clean plan.html from an earlier build sits at the exact path the skill tells the
# agent to open. So write the blocked page beside it under a name nobody will mistake for the
# gate, and remove any previous pass. The state is then visible from `ls`, not just from a value
# that evaporates across a compaction or a second agent picking up the project.
if hard_stop:
    root, ext = os.path.splitext(OUT)
    OUT, stale = root + ".BLOCKED" + ext, OUT
    if os.path.exists(stale):
        os.remove(stale)
with open(OUT, "w", encoding="utf-8") as _f:
    _f.write(HTML)

status = (stops[0]["status"] if stops
          else f"copy OK ({len(copy_lines)} lines)" if copy_lines
          else "no copy")
print(f"wrote {OUT} ({len(plan.get('stages',[]))} stages, "
      f"est {ce.get('min','?')}-{cmax} cr, {status})")
sys.exit(2 if hard_stop else 0)
