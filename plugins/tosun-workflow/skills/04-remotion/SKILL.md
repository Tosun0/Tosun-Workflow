---
name: 04-remotion
description: Build Tosun motion graphics by invoking the installed Remotion plugin for cut composition, preview review, and approved full rendering.
---

# Remotion

Work only on the motion-graphics sequence. Master-Tosun owns state changes and approval.

- Invoke installed Remotion skills. Start with `remotion:remotion-best-practices`, then use `remotion:remotion-create` or `remotion:remotion-markup`, `remotion:remotion-studio`, and `remotion:remotion-render` as required.
- Do not replace the Remotion plugin with a home-grown renderer or request JSON.
- Build one data-driven composition with cut definitions separated from reusable visual components. Do not create one project per cut.
- Keep cut IDs stable so cuts can be inserted, removed, reordered, or regenerated without rewriting the composition.
- Use approved storyboard timing and text, approved images and video, and attached motion-graphic references.
- Render and display a fast preview first. Check layout, clipping, timing, transitions, media loading, resolution, frame rate, and audio.
- Stop at the preview gate. Only after explicit preview approval may the Remotion render skill produce the full render.
- Display and validate the full render separately. Master-Tosun must receive a second explicit approval before publishing.
- If the Remotion plugin or runtime is unavailable, return `waiting_external` or `failed`; never claim a request artifact is a render.
