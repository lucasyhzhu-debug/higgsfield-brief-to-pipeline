# Higgsfield model selection & credit map

Confirm model **IDs + availability** with `higgsfield model list --json` (that output has
`display_name`, `type`, `job_set_type` — but **no cost field**). **Credit costs are NOT in the
CLI** — the figures below are typical estimates; the source of truth is your Higgsfield
dashboard / pricing page and your live balance from `higgsfield account status`. Always present
costs as estimates, never as guaranteed prices.

## Model → use map

| Need | Model (`--model` id) | Typical cost | Notes |
|---|---|---|---|
| Spec / structure-faithful render fusing multiple references | Nano Banana Pro (`nano_banana_2`) | ~2 cr @ 2k | Best multi-image identity+structure fusion. Workhorse for product/spec/scene reskins. |
| Identity-faithful person stills | Soul 2.0 (`text2image_soul_v2`) | ~2 cr | Pass the trained `reference_id` (chain `higgsfield-soul-id`). |
| Generic text-to-image / design / hero | GPT Image 2 (`gpt_image_2`) | ~7 cr @ high | Strong at dense legible text (menus, signage). `quality:high`. |
| Scene motion / b-roll (image→video) | Seedance 2.0 (`seedance_2_0`) | varies | `--start-image` from a generated still. |
| Talking-presenter / UGC ad video | Marketing Studio | varies | Avatar+product+hook ad shape. |
| Precise edit of existing render (text/element swap) | Flux Kontext (`flux_kontext`) | ~1.5 cr | "Replace 'X' with 'Y', keep everything else identical." Never "transform". |
| Video virality QA | Virality Predictor (`brain_activity`) | varies | video-in → text report. |

## Validated CLI pattern (multi-reference render)

```
higgsfield generate create nano_banana_2 \
  --image "<ref1>" --image "<ref2>" ... \   # repeat --image per reference, IN ROLE ORDER
  --resolution 2k --aspect_ratio 4:3 --wait \
  --prompt "<role-labelled prompt>"
```

- `--wait` blocks and prints the result URL; download with `curl -s -o out.png "<url>"`.
- `--image` accepts a local path OR a UUID (no manual pre-upload).
- Resolutions: `2k` for specs (sharp, cheap), `4k` only for hero/in-location composites.
- Aspect: match the deliverable's reference (`4:3` elevations; source-photo ratio for composites — measure it, don't guess).
- Auth: `higgsfield account status`. If it fails → user runs `higgsfield auth login`.

## Run many renders concurrently

Each `--wait` blocks one command. Launch independent renders as separate background
processes (tee each to its own log), then poll the logs for the URL. ~5 renders finish in
the time of 1. NEVER serialize independent renders.

## Credit-optimisation rules (apply every plan)

1. **Validation-first.** One cheap render (2k, thin prompt) to prove the engine holds the
   hard constraint BEFORE batching variants. Discard, then batch with the full template.
2. **Parallelise** independent renders (background + poll).
3. **Derive, don't regenerate.** Lock one anchor at a human gate; feed it as image-1 identity
   into all downstream stages (back view, in-location) so the design never re-rolls.
4. **One change per re-roll.** On a FAIL, change exactly one variable, not the whole prompt.
5. **Deterministic overlays for text + dimensions.** Dimension callouts, annotation labels,
   exact menu prices → composite with `scripts/overlay.py` (Pillow, **0 credits**) instead of
   paying an image model to type text it will misspell.
6. **Right-size resolution.** 2k for specs/variants; 4k only for final hero/composite.
