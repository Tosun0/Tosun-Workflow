---
name: 02-image
description: Produce or validate Tosun thumbnail and cut images by invoking native Codex image generation, then return them for approval.
---

# Image

Work only on the image sequence. Master-Tosun owns state changes and approval.

- Read only approved storyboard fields needed for the requested thumbnail or cuts and attached visual references.
- Prepare prompts internally per cut. Preserve character identity, art direction, composition, aspect ratio, and continuity.
- Invoke native Codex image generation. Do not substitute a request JSON, external API, placeholder, or text description for an actual image.
- For related cuts, generate sequentially: establish the first approved cut as the visual anchor, then pass that image as a reference to every subsequent cut. Do not generate related cuts in parallel.
- Lock character identity, proportions, face, line weight, palette, lighting, camera language, background treatment, and recurring props in every related-cut prompt. Change only the requested action, pose, or camera angle.
- Use bounded parallel generation only for genuinely independent assets with no continuity requirement.
- If the first cut is not approved, revise it before generating dependent cuts.
- Display every generated or attached image and validate that it opens, matches the requested ratio, and represents its cut.
- If image generation is unavailable, return `waiting_external` without claiming output.
- Stop after display and validation. Master-Tosun must record explicit approval before routing to `video`.
