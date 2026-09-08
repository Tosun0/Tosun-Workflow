---
name: video
description: Produce or validate Tosun videos by invoking the connected Higgsfield plugin and collecting real generation results for approval.
---

# Video

Work only on the video sequence. Master-Tosun owns state changes and approval.

- Read only approved storyboard motion fields, approved source images, and required media settings.
- Discover and invoke the connected Higgsfield plugin. Do not use a paid API, browser automation, request artifact, or another provider as a silent substitute.
- Submit one bounded generation per cut when separate clips are required. Preserve character identity and avoid motion or anatomy deformation.
- Wait for the provider's real completion state and collect the actual returned media result.
- If Higgsfield returns a local media file, copy it into project artifacts without overwriting the source. If it returns only a hosted result, display it and do not claim a local file exists.
- Validate actual decoding, duration, resolution, frame rate, codec, and audio presence when applicable.
- If Higgsfield is missing, disconnected, rejected, or returns no media, report `waiting_external` or `failed`.
- Stop after the real video is displayed and validated. Master-Tosun must record explicit approval before routing to `remotion`.
