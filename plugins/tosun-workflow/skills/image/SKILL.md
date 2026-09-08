---
name: image
description: Produce or validate Tosun thumbnail and cut images by invoking native Codex image generation, then return them for approval.
---

# Image

Work only on the image sequence. Master-Tosun owns state changes and approval.

- Read only approved storyboard fields needed for the requested thumbnail or cuts and attached visual references.
- Prepare prompts internally per cut. Preserve character identity, art direction, composition, aspect ratio, and continuity.
- Invoke native Codex image generation. Do not substitute a request JSON, external API, placeholder, or text description for an actual image.
- For independent cuts, use bounded parallel generation when available; keep each request scoped to one cut.
- Display every generated or attached image and validate that it opens, matches the requested ratio, and represents its cut.
- If image generation is unavailable, return `waiting_external` without claiming output.
- Stop after display and validation. Master-Tosun must record explicit approval before routing to `video`.
