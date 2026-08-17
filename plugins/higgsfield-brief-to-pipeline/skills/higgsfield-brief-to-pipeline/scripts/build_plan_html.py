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

  # --- copy + adversarial review (see references/copy-review-lenses.md) -------------------
  # Omit BOTH blocks when a plan carries no user-facing text. Never ship "copy" without
  # "copy_review": the page then renders a REVIEW NOT RUN banner and withholds approval.
  "copy":[{"id":"h1","text":"Now bulk billed.","surface":"overlay","stage":"5","status":"FIX"}],
  #   surface: overlay | depicted | caption      status: SHIP | FIX | KILL
  "copy_review":{
    "lenses":["L1 platform policy","L3 claim substantiation"],
    "refuted":11,                                    # findings killed by the refute pass
    "findings":[{"severity":"blocker",               # blocker | high | medium | low
                 "affects":["h1"],
                 "rule":"AHPRA advertising guidelines cl 4.2",
                 "source":"https://www.ahpra.gov.au/…",   # or the token NOT-VERIFIED
                 "quote":"Now bulk billed.",         # the exact offending words
                 "why":"why the rule reaches this advertiser and this product",
                 "fix":"replacement wording"}],
    "unverified":[{"question":"…","settled_by":"…"}],
    "disagreements":[{"issue":"…","call":"…"}],
    "waived":[]     # rule strings the user waived in writing. EXACT string match against
                    # findings[].rule — copy the rule verbatim, don't retype it. A near-miss
                    # silently fails to waive and the gate stays shut, which is the safe direction.
  }
}
"""
import sys, json, html

plan = json.load(open(sys.argv[1], encoding="utf-8"))
OUT = sys.argv[2]
e = lambda s: html.escape(str(s))

def rows(items, cols):
    out = []
    for it in items:
        tds = "".join(f"<td>{e(it.get(c[0],'')) if not isinstance(it.get(c[0],''),list) else e(', '.join(it.get(c[0],[])))}</td>" for c in cols)
        out.append(f"<tr>{tds}</tr>")
    return "".join(out)

theme = plan.get("theme", {})
ACC = e(theme.get("accent", "#26303f"))   # headings, stage numbers, tag pill
GOLD = e(theme.get("gold", "#c98a2e"))    # card rule, chips, footer border

ce = plan.get("credit_estimate", {})
budget = ce.get("budget")
cmax = ce.get("max")
pct = int(min(100, (cmax / budget) * 100)) if (budget and cmax) else 0

stage_cards = ""
for s in plan.get("stages", []):
    gate = s.get("gate", "")
    gate_html = f'<div class="gate">⛔ GATE · {e(gate)}</div>' if gate else ""
    verify = "".join(f"<li>{e(v)}</li>" for v in s.get("verify", []))
    refs = "".join(f"<span class='chip'>{e(r)}</span>" for r in s.get("refs", []))
    stage_cards += f"""
    <div class="card">
      <div class="card-h"><span class="sn">{e(s.get('n',''))}</span><h3>{e(s.get('name',''))}</h3>
        <span class="cred">{e(s.get('credits','?'))} cr</span></div>
      <div class="meta"><b>Model:</b> <code>{e(s.get('model',''))}</code> &nbsp;·&nbsp;
        <b>Params:</b> {e(s.get('params',''))} &nbsp;·&nbsp;
        <b>Variants:</b> {e(s.get('variants',''))}
        {('&nbsp;·&nbsp; <b>Derives from:</b> '+e(s.get('derives_from'))) if s.get('derives_from') and s.get('derives_from')!='-' else ''}</div>
      <div class="refs">{refs}</div>
      <div class="verify"><b>Auto-verify →</b><ul>{verify}</ul></div>
      {gate_html}
    </div>"""

opt_html = "".join(f"<li>{e(o)}</li>" for o in plan.get("optimizations", []))
deliv = rows(plan.get("deliverables", []), [("name","Deliverable"),("count","Count"),("format","Format")])
refs_t = rows(plan.get("references", []), [("file","Reference"),("role","Role"),("stages","Stages"),("note","Note")])
models_t = rows(plan.get("models", []), [("need","Need"),("model","Model"),("credits","Cost"),("why","Why")])

# ---- copy + adversarial copy review -------------------------------------------------------
copy_lines = plan.get("copy", []) or []
review = plan.get("copy_review")
# A plan that carries copy but no review has NOT passed the gate. Treat that as a hard stop:
# a missing review must never read the same as a clean one. Keyed on PRESENCE, not truthiness —
# an explicit empty `copy_review: {}` means the review ran and found nothing, which is a pass.
review_missing = bool(copy_lines) and "copy_review" not in plan
findings = (review or {}).get("findings", []) or []
waived = set((review or {}).get("waived", []) or [])
SEV_ORDER = {"blocker": 0, "high": 1, "medium": 2, "low": 3}
findings = sorted(findings, key=lambda f: SEV_ORDER.get(f.get("severity", "low"), 9))
open_blockers = [f for f in findings
                 if f.get("severity") == "blocker" and f.get("rule") not in waived]
hard_stop = review_missing or bool(open_blockers)

copy_html = ""
if copy_lines:
    st_cls = {"SHIP": "ok", "FIX": "warn", "KILL": "bad"}
    body = "".join(
        f"<tr><td><code>{e(c.get('id',''))}</code></td><td>{e(c.get('text',''))}</td>"
        f"<td>{e(c.get('surface',''))}</td><td>{e(c.get('stage',''))}</td>"
        f"<td><span class='pill {st_cls.get(c.get('status',''),'')}'>"
        f"{e(c.get('status','UNREVIEWED'))}</span></td></tr>"
        for c in copy_lines)
    copy_html = f"""
<h2>Copy under review ({len(copy_lines)} lines)</h2>
<p class="lead">Every piece of user-facing text in this plan, and where it lands. Deterministic
overlays guarantee spelling and position at 0 credits; they have no opinion on whether a line is
publishable. That is what the review below is for.</p>
<table><tr><th>ID</th><th>Text</th><th>Surface</th><th>Stage</th><th>Status</th></tr>{body}</table>"""

def _finding_card(f):
    sev = f.get("severity", "low")
    src = str(f.get("source", "") or "")
    src_html = ('<span class="nv">NOT-VERIFIED</span>' if src.upper() == "NOT-VERIFIED"
                else f'<a href="{e(src)}">{e(src)}</a>' if src.startswith("http")
                else e(src))
    affects = "".join(f"<span class='chip'>{e(a)}</span>" for a in f.get("affects", []))
    waived_html = ('<div class="waived">WAIVED by the user for this run</div>'
                   if f.get("rule") in waived else "")
    return f"""
    <div class="find sev-{e(sev)}">
      <div class="find-h"><span class="sev">{e(sev)}</span><b>{e(f.get('rule',''))}</b></div>
      {f'<blockquote>{e(f.get("quote"))}</blockquote>' if f.get("quote") else ""}
      {f'<p class="why">{e(f.get("why"))}</p>' if f.get("why") else ""}
      {f'<p class="fix"><b>Replace with:</b> {e(f.get("fix"))}</p>' if f.get("fix") else ""}
      <div class="find-f">{affects}<span class="src">{src_html}</span></div>
      {waived_html}
    </div>"""

review_html = ""
if review_missing:
    review_html = """
<h2>Copy review</h2>
<div class="stop"><b>REVIEW NOT RUN.</b> This plan carries user-facing copy that has not been
through the adversarial review. The gate is not passable in this state. Run step 2.5 and rebuild
this page.</div>"""
elif review is not None:
    lenses = "".join(f"<span class='chip'>{e(l)}</span>" for l in review.get("lenses", []))
    refuted = review.get("refuted")
    cards = "".join(_finding_card(f) for f in findings) or \
        '<p class="lead">No findings survived the refute pass.</p>'
    unver = "".join(
        f"<tr><td>{e(u.get('question',''))}</td><td>{e(u.get('settled_by',''))}</td></tr>"
        for u in review.get("unverified", []) or [])
    unver_html = f"""
<h3>Unverified</h3>
<p class="lead">Nobody could source these to a primary document. They are not dismissed; they are
open questions, and some of them decide whether the copy above can run at all.</p>
<table><tr><th>Question</th><th>Settled by</th></tr>{unver}</table>""" if unver else ""
    disag = "".join(
        f"<li><b>{e(d.get('issue',''))}</b> — {e(d.get('call',''))}</li>"
        for d in review.get("disagreements", []) or [])
    disag_html = f"<h3>Where the reviewers disagreed</h3><ul class='opt'>{disag}</ul>" if disag else ""
    review_html = f"""
<h2>Adversarial copy review</h2>
<div class="refstat">Lenses: {lenses or '<span class="chip">none recorded</span>'}
{f'&nbsp;·&nbsp; <b>{e(refuted)}</b> findings killed by the refute pass' if refuted is not None else ''}
&nbsp;·&nbsp; <b>{len(open_blockers)}</b> open blocker(s)</div>
{cards}{unver_html}{disag_html}"""

th = lambda cols: "".join(f"<th>{c[1]}</th>" for c in cols)
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
</style></head><body><div class="wrap">
<span class="tag">Higgsfield · Process Preview</span>
<h1>{e(plan.get('project','Workflow'))}</h1>
<p class="lead">{e(plan.get('brief_summary',''))}</p>
{f'''<div class="stop"><b>⛔ HARD STOP — {len(open_blockers)} unresolved copy blocker(s).</b>
No render and no overlay runs until these are fixed, or waived by you in writing. Everything else
in this plan is reviewable now; the blockers are listed under Adversarial copy review below.</div>'''
 if open_blockers else ''}

<h2>Deliverables</h2><table><tr>{th([('','Deliverable'),('','Count'),('','Format')])}</tr>{deliv}</table>
{copy_html}
{review_html}

<h2>References &amp; roles</h2>
<p class="lead">Every reference is role-labelled — the single biggest quality lever when fusing multiple images.</p>
<table><tr>{th([('','Reference'),('','Role'),('','Stages'),('','Note')])}</tr>{refs_t}</table>

<h2>Model selection</h2><table><tr>{th([('','Need'),('','Model'),('','Cost'),('','Why')])}</tr>{models_t}</table>

<h2>Pipeline ({len(plan.get('stages',[]))} stages)</h2>{stage_cards}

<h2>Credit optimisation</h2><ul class="opt">{opt_html}</ul>

<h2>Estimated spend</h2>
<div class="bar"><div class="fill">{e(cmax)} cr of {e(budget)} budget</div></div>
<p class="lead" style="margin-top:8px">Range {e(ce.get('min','?'))}–{e(cmax)} credits (incl. variants &amp; up to 2 retries/stage). Overlays &amp; dimensioning add <b>0 credits</b>.</p>

{f'''<div class="stop"><b>Not approvable as it stands.</b> {"This plan carries copy that has not been reviewed." if review_missing else f"{len(open_blockers)} copy blocker(s) are unresolved."}
Fix the copy and rebuild this page, or tell me explicitly which blocker you are waiving and why.
Nothing renders and no overlay is composited until then.</div>'''
 if hard_stop else
 '''<div class="foot"><b>This is a preview, not a commitment.</b> No credits are spent until you approve.
Reply with changes (swap a model, fewer variants, tighter scope) or <b>approve</b> to run the pipeline stage-by-stage with auto-verification and the human gate(s) above.</div>'''}
</div></body></html>"""
open(OUT, "w", encoding="utf-8").write(HTML)
_status = ("BLOCKED: copy review not run" if review_missing
           else f"BLOCKED: {len(open_blockers)} open copy blocker(s)" if open_blockers
           else f"copy OK ({len(copy_lines)} lines)" if copy_lines
           else "no copy")
print(f"wrote {OUT} ({len(plan.get('stages',[]))} stages, est {ce.get('min','?')}-{cmax} cr, {_status})")
sys.exit(2 if hard_stop else 0)
