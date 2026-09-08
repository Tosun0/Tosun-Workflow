---
name: storyboard
description: Create, parse, revise, or validate the storyboard sequence for a Tosun Workflow project before its approval gate.
---

# Storyboard

Work only on the storyboard sequence. Master-Tosun owns state changes and approval.

- Use an attached storyboard when present; otherwise draft one from the user's chat input.
- Structure each cut with cut ID, time range, visual action, narration, on-screen text, image direction, video motion, and motion-graphic direction.
- Preserve supplied names, numbers, wording, and claims. Mark missing facts instead of inventing them.
- Check that cut durations sum to the required video duration and that aspect ratio, resolution, and frame rate are available.
- Keep image, video, and motion-graphic directions distinct so downstream skills receive compact inputs.
- Return the complete storyboard for display. Do not prepare or reveal generation prompts unless requested.
- Stop after display. Master-Tosun must record explicit approval before routing to `image`.
