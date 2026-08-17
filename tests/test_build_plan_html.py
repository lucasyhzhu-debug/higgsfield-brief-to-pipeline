#!/usr/bin/env python
"""Tests for build_plan_html.py, focused on the copy-review gate.

The gate has four states and they must never read the same:
  no copy            -> exit 0, normal approve footer
  copy, no review    -> exit 2, REVIEW NOT RUN            (a missing review is not a clean one)
  copy, open blocker -> exit 2, HARD STOP
  copy, all clean    -> exit 0, normal approve footer, findings still shown

Run: python tests/test_build_plan_html.py
"""
import json, os, subprocess, sys, tempfile, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = os.path.join(ROOT, "plugins", "higgsfield-brief-to-pipeline",
                     "skills", "higgsfield-brief-to-pipeline")
SCRIPT = os.path.join(SKILL, "scripts", "build_plan_html.py")
EXAMPLE = os.path.join(SKILL, "examples", "plan.example.json")

BASE = {"project": "T", "brief_summary": "b",
        "stages": [{"n": "1", "name": "s", "credits": 1}],
        "credit_estimate": {"min": 1, "max": 1, "budget": 10}}


def build(plan):
    """Render a plan dict; return (exit_code, stdout, html)."""
    with tempfile.TemporaryDirectory() as d:
        pj, out = os.path.join(d, "p.json"), os.path.join(d, "p.html")
        with open(pj, "w", encoding="utf-8") as f:
            json.dump(plan, f)
        r = subprocess.run([sys.executable, SCRIPT, pj, out],
                           capture_output=True, text=True)
        html = ""
        if os.path.exists(out):
            with open(out, encoding="utf-8") as f:
                html = f.read()
    return r.returncode, r.stdout, html


def plan_with(copy=None, review=None):
    p = dict(BASE)
    if copy is not None:
        p["copy"] = copy
    if review is not None:
        p["copy_review"] = review
    return p


LINE = [{"id": "h1", "text": "Now bulk billed.", "surface": "overlay",
         "stage": "1", "status": "FIX"}]


def finding(sev, rule="R1"):
    return {"severity": sev, "affects": ["h1"], "rule": rule,
            "source": "https://example.test/rule", "quote": "Now bulk billed.",
            "why": "because", "fix": "Bulk billed for eligible patients."}


class NoCopy(unittest.TestCase):
    def test_plan_without_copy_is_unaffected(self):
        code, out, html = build(BASE)
        self.assertEqual(code, 0)
        self.assertIn("no copy", out)
        self.assertIn("This is a preview, not a commitment", html)
        self.assertNotIn("Copy under review", html)
        self.assertNotIn("HARD STOP", html)


class MissingReview(unittest.TestCase):
    """The failure mode that matters most: copy that silently skipped the gate."""

    def test_copy_without_review_blocks(self):
        code, out, html = build(plan_with(copy=LINE))
        self.assertEqual(code, 2)
        self.assertIn("BLOCKED: copy review not run", out)
        self.assertIn("REVIEW NOT RUN", html)

    def test_copy_without_review_withholds_the_approve_footer(self):
        _, _, html = build(plan_with(copy=LINE))
        self.assertNotIn("This is a preview, not a commitment", html)
        self.assertIn("Not approvable as it stands", html)

    def test_empty_review_object_still_blocks_nothing_silently(self):
        # An empty review is a review that found nothing, not a missing one.
        code, _, html = build(plan_with(copy=LINE, review={}))
        self.assertEqual(code, 0)
        self.assertNotIn("REVIEW NOT RUN", html)
        self.assertIn("No findings survived the refute pass", html)


class OpenBlocker(unittest.TestCase):
    def test_open_blocker_hard_stops(self):
        code, out, html = build(plan_with(LINE, {"findings": [finding("blocker")]}))
        self.assertEqual(code, 2)
        self.assertIn("BLOCKED: 1 open copy blocker", out)
        self.assertIn("HARD STOP", html)
        self.assertNotIn("This is a preview, not a commitment", html)

    def test_waived_blocker_passes_but_is_still_shown(self):
        code, _, html = build(plan_with(
            LINE, {"findings": [finding("blocker", "R-waived")], "waived": ["R-waived"]}))
        self.assertEqual(code, 0)
        self.assertNotIn("HARD STOP", html)
        self.assertIn("WAIVED by the user", html)
        self.assertIn("R-waived", html)

    def test_non_blocker_severities_are_advisory(self):
        for sev in ("high", "medium", "low"):
            with self.subTest(sev=sev):
                code, _, html = build(plan_with(LINE, {"findings": [finding(sev)]}))
                self.assertEqual(code, 0, f"{sev} must not hard-stop")
                self.assertIn("This is a preview, not a commitment", html)
                self.assertIn(f"sev-{sev}", html)

    def test_findings_render_blockers_first(self):
        review = {"findings": [finding("low", "R-low"), finding("blocker", "R-block"),
                               finding("medium", "R-med")]}
        _, _, html = build(plan_with(LINE, review))
        self.assertLess(html.index("R-block"), html.index("R-med"))
        self.assertLess(html.index("R-med"), html.index("R-low"))


class Reporting(unittest.TestCase):
    def test_not_verified_source_is_flagged_not_linked(self):
        f = finding("medium"); f["source"] = "NOT-VERIFIED"
        _, _, html = build(plan_with(LINE, {"findings": [f]}))
        self.assertIn('class="nv">NOT-VERIFIED', html)
        self.assertNotIn('<a href="NOT-VERIFIED"', html)

    def test_unverified_and_disagreements_render(self):
        review = {"findings": [], "unverified": [{"question": "Q1", "settled_by": "S1"}],
                  "disagreements": [{"issue": "I1", "call": "C1"}]}
        _, _, html = build(plan_with(LINE, review))
        for s in ("Q1", "S1", "I1", "C1", "Unverified", "Where the reviewers disagreed"):
            self.assertIn(s, html)

    def test_copy_text_is_html_escaped(self):
        copy = [{"id": "x", "text": '<script>alert("x")</script>', "surface": "overlay",
                 "stage": "1", "status": "FIX"}]
        _, _, html = build(plan_with(copy, {"findings": []}))
        self.assertNotIn("<script>alert", html)
        self.assertIn("&lt;script&gt;", html)

    def test_refuted_count_surfaces(self):
        _, _, html = build(plan_with(LINE, {"findings": [], "refuted": 11}))
        self.assertIn("11", html)
        self.assertIn("killed by the refute pass", html)


class BundledExample(unittest.TestCase):
    """The example doubles as the skill's self-test, so it must stay exit-0."""

    def test_example_plan_builds_clean(self):
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "e.html")
            r = subprocess.run([sys.executable, SCRIPT, EXAMPLE, out],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("copy OK", r.stdout)
            html = open(out, encoding="utf-8").read()
        self.assertIn("Copy under review", html)
        self.assertIn("Adversarial copy review", html)
        self.assertIn("This is a preview, not a commitment", html)

    def test_example_declares_no_open_blockers(self):
        plan = json.load(open(EXAMPLE, encoding="utf-8"))
        waived = set(plan["copy_review"].get("waived", []))
        open_b = [f for f in plan["copy_review"]["findings"]
                  if f["severity"] == "blocker" and f["rule"] not in waived]
        self.assertEqual(open_b, [], "the bundled example must stay approvable")

    def test_every_finding_names_an_affected_copy_id(self):
        plan = json.load(open(EXAMPLE, encoding="utf-8"))
        ids = {c["id"] for c in plan["copy"]}
        for f in plan["copy_review"]["findings"]:
            self.assertTrue(set(f["affects"]) <= ids,
                            f"{f['rule']} points at a copy id that does not exist")


if __name__ == "__main__":
    unittest.main(verbosity=2)
