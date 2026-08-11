# Prompting principles for multi-reference Higgsfield renders

Distilled from official Google (Nano Banana / Gemini image), OpenAI (GPT Image 2), and BFL
(Flux Kontext) guidance. These are the rules that actually move quality. Build every prompt
from them; do not freehand.

## The levers (in priority order)

1. **Role-label every reference in the prompt text.** Biggest single lever. Name what each
   image governs: "Use the FIRST image as the STRUCTURE reference… the SECOND for MATERIAL…
   the THIRD as STYLE/DESIGN-DNA… apply the wordmark from the FOURTH unaltered." The model
   fuses blindly otherwise.
2. **Lock structure explicitly.** "Replicate the exact geometry/proportions of [structure
   ref]; change ONLY colour, finish and branding." Then enumerate the invariants by name.
3. **Negatives as positives** (no negative field exists). Say "plain seamless neutral-gray
   background, nothing else in frame" not "no clutter"; "flat orthographic elevation" not
   "no perspective".
4. **Force a technical view with draftsman vocab** when you need an elevation: "orthographic
   front elevation, parallel projection, zero perspective, no vanishing point, dead straight-on,
   drawn to scale." This is the lowest-confidence area — expect 1–2 re-rolls, and **repeat the
   hardest constraint again at the END of the prompt** (proven to flip 3/4 → true elevation).
5. **Text handling.** Quote exact strings and spell them letter-by-letter (`B-R-A-N-D-N-A-M-E`),
   name the font, keep signage large and few. Prefer applying a logo from a reference over typed text.
   Dense menu text → GPT Image 2 (`quality:high`). Text fixes on an existing render → Flux
   Kontext ("Replace 'X' with 'Y', keep everything else identical").
6. **Narrative prose, 3–5 roled references** (not the max). Hardest constraint stated first
   and repeated near the end. **One change per re-roll** when refining.

## Reusable template skeletons

Adapt these; keep the role-labelling and the repeated hard constraint.

**Spec / elevation render (Nano Banana Pro, 2k, ratio of the format ref):**
```
Orthographic FRONT ELEVATION of <subject>, flat 2D technical product-render to scale —
camera perpendicular to the facade, parallel projection, zero perspective, no vanishing
point, dead straight-on, centred.
Use the FIRST image as STRUCTURE (replicate geometry/proportions/framing one-to-one). Use
the SECOND for MATERIAL/build. Use the THIRD as STYLE/DESIGN-DNA. Apply the <logo> from the
FOURTH unaltered. <product placement from FIFTH>.
Keep the structure EXACTLY the same — do not change the form: <enumerate invariants>.
Change ONLY colour, finish, branding. Reskin to <palette with hex>. {STYLE_VARIANT}.
Signage, spelled exactly: "<words>". Plain seamless neutral light-gray studio background,
soft even frontal light, flat catalog look, centred, full in frame — nothing else.
Drawn perfectly straight-on as an orthographic elevation — no perspective, no 3/4 angle.
```

**Derived view (back/side) — image-1 = approved render (IDENTITY), image-2 = format ref:**
```
…REAR ELEVATION of the SAME <subject>. Use the FIRST image (approved render) as the IDENTITY
reference — match materials, palette, proportions, finish; you are turning it 180°. Forward-
facing signage is edge-on / not legible from behind — do not duplicate it. Change nothing but
the viewing angle. {STYLE_VARIANT}. <same background/format closer>.
```

**In-location composite — image-1 = approved render (SUBJECT), image-2 = scene photo:**
```
Photorealistic composite: place <subject> into the real <scene> so it looks installed, not
pasted. Use the FIRST image as the SUBJECT (keep identity/structure/branding exactly). Use the
SECOND as the BACKGROUND SCENE — do not alter its architecture/floor/storefronts.
PLACEMENT & ORIENTATION (critical): <where it sits, which way the front faces, what it
replaces>. Natural 3/4 matching the scene's perspective/vanishing lines, flat on the floor at
realistic scale. Match lighting colour-temperature + shadow direction; add a grounded contact
shadow; match grain/white-balance/DoF. Output at the scene photo's aspect ratio.
```

**Verification couples to the prompt.** Each stage's auto-verify checks the prompt's hard
constraints actually landed (orthographic, invariants present, palette hex, signage spelled,
composite perspective/shadow). FAIL → re-roll changing ONE variable.
