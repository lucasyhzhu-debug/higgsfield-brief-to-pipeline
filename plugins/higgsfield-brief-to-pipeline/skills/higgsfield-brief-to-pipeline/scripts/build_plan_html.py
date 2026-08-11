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
  "credit_estimate":{"min":30,"max":40,"budget":860}
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
</style></head><body><div class="wrap">
<span class="tag">Higgsfield · Process Preview</span>
<h1>{e(plan.get('project','Workflow'))}</h1>
<p class="lead">{e(plan.get('brief_summary',''))}</p>

<h2>Deliverables</h2><table><tr>{th([('','Deliverable'),('','Count'),('','Format')])}</tr>{deliv}</table>

<h2>References &amp; roles</h2>
<p class="lead">Every reference is role-labelled — the single biggest quality lever when fusing multiple images.</p>
<table><tr>{th([('','Reference'),('','Role'),('','Stages'),('','Note')])}</tr>{refs_t}</table>

<h2>Model selection</h2><table><tr>{th([('','Need'),('','Model'),('','Cost'),('','Why')])}</tr>{models_t}</table>

<h2>Pipeline ({len(plan.get('stages',[]))} stages)</h2>{stage_cards}

<h2>Credit optimisation</h2><ul class="opt">{opt_html}</ul>

<h2>Estimated spend</h2>
<div class="bar"><div class="fill">{e(cmax)} cr of {e(budget)} budget</div></div>
<p class="lead" style="margin-top:8px">Range {e(ce.get('min','?'))}–{e(cmax)} credits (incl. variants &amp; up to 2 retries/stage). Overlays &amp; dimensioning add <b>0 credits</b>.</p>

<div class="foot"><b>This is a preview, not a commitment.</b> No credits are spent until you approve.
Reply with changes (swap a model, fewer variants, tighter scope) or <b>approve</b> to run the pipeline stage-by-stage with auto-verification and the human gate(s) above.</div>
</div></body></html>"""
open(OUT, "w", encoding="utf-8").write(HTML)
print(f"wrote {OUT} ({len(plan.get('stages',[]))} stages, est {ce.get('min','?')}-{cmax} cr)")
