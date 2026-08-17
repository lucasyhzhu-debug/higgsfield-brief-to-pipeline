#!/usr/bin/env python
"""Tests for build_plan_html.py, focused on the copy-review gate.

The gate has these states and they must never read the same:
  no copy              -> exit 0, approvable, plan.html
  copy, no review      -> exit 2, no-review,  plan.BLOCKED.html   (missing != clean)
  copy, review null    -> exit 2, no-review                       (null != reviewed)
  copy, open blocker   -> exit 2, blocked,    plan.BLOCKED.html
  copy, clean/waived   -> exit 0, approvable, plan.html

Gate state is asserted on the <body data-gate> marker, not on footer prose. Content tests must
assert something that ONLY appears when the thing renders — the stylesheet is unconditional and
names every class it might use, so `assertIn("sev-blocker", html)` passes on an empty plan.

Run: python tests/test_build_plan_html.py
"""
import json, os, re, subprocess, sys, tempfile, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = os.path.join(ROOT, "plugins", "higgsfield-brief-to-pipeline",
                     "skills", "higgsfield-brief-to-pipeline")
SCRIPT = os.path.join(SKILL, "scripts", "build_plan_html.py")
EXAMPLE = os.path.join(SKILL, "examples", "plan.example.json")
with open(EXAMPLE, encoding="utf-8") as _f:
    EXAMPLE_PLAN = json.load(_f)

BASE = {"project": "T", "brief_summary": "b",
        "stages": [{"n": "1", "name": "s", "credits": 1}],
        "credit_estimate": {"min": 1, "max": 1, "budget": 10}}


def build(plan=None, path=None):
    """Render a plan (dict, or an on-disk path); return (exit_code, stdout, html, written).

    `written` is the basename actually produced, so the blocked-build rename is testable.
    """
    with tempfile.TemporaryDirectory() as d:
        pj = path
        if pj is None:
            pj = os.path.join(d, "p.json")
            with open(pj, "w", encoding="utf-8") as f:
                json.dump(plan, f)
        out = os.path.join(d, "p.html")
        r = subprocess.run([sys.executable, SCRIPT, pj, out],
                           capture_output=True, text=True)
        produced = sorted(f for f in os.listdir(d) if f.endswith(".html"))
        written = produced[0] if produced else None
        html = ""
        if written:
            with open(os.path.join(d, written), encoding="utf-8") as f:
                html = f.read()
    return r.returncode, r.stdout, html, written


def gate_of(html):
    m = re.search(r'<body data-gate="([a-z-]+)"', html)
    return m.group(1) if m else None


def body_of(html):
    """Everything after the stylesheet — what the reader actually sees."""
    return html.split("</style>", 1)[-1]


def plan_with(copy=None, review=..., **extra):
    p = dict(BASE, **extra)
    if copy is not None:
        p["copy"] = copy
    if review is not ...:
        p["copy_review"] = review
    return p


LINE = [{"id": "h1", "text": "Now bulk billed.", "surface": "overlay",
         "stage": "1", "status": "FIX"}]


def finding(sev, fid="f1", rule="R1"):
    return {"id": fid, "severity": sev, "affects": ["h1"], "rule": rule,
            "source": "https://example.test/rule", "quote": "Now bulk billed.",
            "why": "because", "fix": "Bulk billed for eligible patients."}


class NoCopy(unittest.TestCase):
    def test_plan_without_copy_is_unaffected(self):
        code, out, html, written = build(BASE)
        self.assertEqual(code, 0)
        self.assertIn("no copy", out)
        self.assertEqual(gate_of(html), "approvable")
        self.assertEqual(written, "p.html")
        self.assertNotIn("Copy under review", body_of(html))

    def test_stylesheet_alone_does_not_imply_findings(self):
        """Guards the trap this suite fell into: .sev-* and 11px live in the <style> block."""
        _, _, html, _ = build(BASE)
        self.assertIn("sev-blocker", html)                     # present in CSS...
        self.assertNotIn("sev-blocker", body_of(html))         # ...but not rendered
        self.assertNotIn("killed by the refute pass", html)


class MissingReview(unittest.TestCase):
    """The failure mode that matters most: copy that silently skipped the gate."""

    def test_copy_without_review_blocks(self):
        code, out, html, written = build(plan_with(copy=LINE))
        self.assertEqual(code, 2)
        self.assertIn("BLOCKED: copy review not run", out)
        self.assertEqual(gate_of(html), "no-review")
        self.assertIn("REVIEW NOT RUN", body_of(html))

    def test_null_review_is_not_a_review(self):
        """`copy_review: null` must not slip between the presence and render checks."""
        code, _, html, _ = build(plan_with(copy=LINE, review=None))
        self.assertEqual(code, 2)
        self.assertEqual(gate_of(html), "no-review")

    def test_empty_review_object_is_a_recorded_clean_pass(self):
        code, _, html, _ = build(plan_with(copy=LINE, review={}))
        self.assertEqual(code, 0)
        self.assertEqual(gate_of(html), "approvable")
        self.assertNotIn("REVIEW NOT RUN", body_of(html))
        self.assertIn("No findings survived the refute pass", html)


class OpenBlocker(unittest.TestCase):
    def test_open_blocker_hard_stops(self):
        code, out, html, _ = build(plan_with(LINE, {"findings": [finding("blocker")]}))
        self.assertEqual(code, 2)
        self.assertIn("BLOCKED: 1 open copy blocker", out)
        self.assertEqual(gate_of(html), "blocked")
        self.assertIn("HARD STOP", body_of(html))

    def test_blocked_build_does_not_produce_an_approvable_artifact(self):
        _, out, _, written = build(plan_with(LINE, {"findings": [finding("blocker")]}))
        self.assertEqual(written, "p.BLOCKED.html")
        self.assertIn("p.BLOCKED.html", out)

    def test_waiver_by_finding_id(self):
        code, _, html, written = build(plan_with(
            LINE, {"findings": [finding("blocker", fid="f9")], "waived": ["f9"]}))
        self.assertEqual(code, 0)
        self.assertEqual(gate_of(html), "approvable")
        self.assertEqual(written, "p.html")
        self.assertIn("WAIVED by the user", body_of(html))

    def test_waiver_by_rule_string_still_works(self):
        code, _, _, _ = build(plan_with(
            LINE, {"findings": [finding("blocker", rule="R-old")], "waived": ["R-old"]}))
        self.assertEqual(code, 0)

    def test_near_miss_waiver_fails_closed(self):
        code, _, html, _ = build(plan_with(
            LINE, {"findings": [finding("blocker", fid="f9")], "waived": ["f9 "]}))
        self.assertEqual(code, 2, "a near-miss waiver must not open the gate")
        self.assertEqual(gate_of(html), "blocked")

    def test_non_blocker_severities_are_advisory_and_render(self):
        for sev in ("high", "medium", "low"):
            with self.subTest(sev=sev):
                code, _, html, _ = build(plan_with(LINE, {"findings": [finding(sev)]}))
                self.assertEqual(code, 0, f"{sev} must not hard-stop")
                self.assertEqual(gate_of(html), "approvable")
                self.assertIn(f'class="find sev-{sev}"', body_of(html))

    def test_findings_render_blockers_first(self):
        review = {"findings": [finding("low", "a", "R-low"), finding("blocker", "b", "R-block"),
                               finding("medium", "c", "R-med")], "waived": ["b"]}
        _, _, html, _ = build(plan_with(LINE, review))
        b = body_of(html)
        self.assertLess(b.index("R-block"), b.index("R-med"))
        self.assertLess(b.index("R-med"), b.index("R-low"))


class Reporting(unittest.TestCase):
    def test_not_verified_source_is_flagged_not_linked(self):
        f = finding("medium"); f["source"] = "NOT-VERIFIED"
        _, _, html, _ = build(plan_with(LINE, {"findings": [f]}))
        self.assertIn('class="nv">NOT-VERIFIED', body_of(html))
        self.assertNotIn('<a href="NOT-VERIFIED"', html)

    def test_unverified_and_disagreements_render(self):
        review = {"findings": [], "unverified": [{"question": "Q1", "settled_by": "S1"}],
                  "disagreements": [{"issue": "I1", "call": "C1"}]}
        _, _, html, _ = build(plan_with(LINE, review))
        b = body_of(html)
        for s in ("Q1", "S1", "I1", "C1", "Unverified", "Where the reviewers disagreed"):
            self.assertIn(s, b)

    def test_copy_text_is_html_escaped(self):
        copy = [{"id": "x", "text": '<script>alert("x")</script>', "surface": "overlay",
                 "stage": "1", "status": "FIX"}]
        _, _, html, _ = build(plan_with(copy, {"findings": []}))
        self.assertNotIn("<script>alert", html)
        self.assertIn("&lt;script&gt;", html)

    def test_refuted_count_surfaces(self):
        _, _, html, _ = build(plan_with(LINE, {"findings": [], "refuted": 7}))
        self.assertIn("<b>7</b> findings killed by the refute pass", body_of(html))

    def test_refuted_absent_when_not_recorded(self):
        _, _, html, _ = build(plan_with(LINE, {"findings": []}))
        self.assertNotIn("killed by the refute pass", body_of(html))


class Budget(unittest.TestCase):
    def test_over_budget_does_not_render_as_a_full_healthy_bar(self):
        _, _, html, _ = build(dict(BASE, credit_estimate={"min": 1, "max": 900, "budget": 100}))
        b = body_of(html)
        self.assertIn("OVER BUDGET by 800 cr", b)
        self.assertIn('class="fill over"', b)

    def test_within_budget_is_unchanged(self):
        _, _, html, _ = build(BASE)
        b = body_of(html)
        self.assertIn("1 cr of 10 budget", b)
        self.assertNotIn('class="fill over"', b)


class BundledExample(unittest.TestCase):
    """The example doubles as the skill's self-test, so it must stay exit-0."""

    def test_example_plan_builds_clean(self):
        code, out, html, written = build(path=EXAMPLE)
        self.assertEqual(code, 0, out)
        self.assertIn("copy OK", out)
        self.assertEqual(written, "p.html")
        self.assertEqual(gate_of(html), "approvable")
        b = body_of(html)
        self.assertIn("Copy under review", b)
        self.assertIn("Adversarial copy review", b)

    def test_example_declares_no_open_blockers(self):
        waived = set(EXAMPLE_PLAN["copy_review"].get("waived", []))
        open_b = [f for f in EXAMPLE_PLAN["copy_review"]["findings"]
                  if f["severity"] == "blocker"
                  and f.get("id") not in waived and f["rule"] not in waived]
        self.assertEqual(open_b, [], "the bundled example must stay approvable")

    def test_every_finding_names_an_affected_copy_id(self):
        ids = {c["id"] for c in EXAMPLE_PLAN["copy"]}
        for f in EXAMPLE_PLAN["copy_review"]["findings"]:
            self.assertTrue(set(f["affects"]) <= ids,
                            f"{f['rule']} points at a copy id that does not exist")

    def test_every_finding_has_a_stable_id(self):
        ids = [f.get("id") for f in EXAMPLE_PLAN["copy_review"]["findings"]]
        self.assertTrue(all(ids), "findings need ids so waivers can key on them")
        self.assertEqual(len(ids), len(set(ids)), "finding ids must be unique")


if __name__ == "__main__":
    unittest.main(verbosity=2)
