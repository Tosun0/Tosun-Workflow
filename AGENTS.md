# Tosun Workflow Agent Rules

## Operating rules

1. Read the active project's `manifest.json` before changing a stage.
2. Never delete or overwrite source inputs. Copy them into the project `input/` folder.
3. Create a backup before every stage write or manual revision.
4. Keep only approved deliverables in `public/`. Drafts belong in `artifacts/`.
5. Do not advance a review gate without an explicit user approval event. Prompt preparation is an internal automatic step after storyboard approval.
6. Preserve the distinction between storyboard content and motion-graphic direction.
7. Treat numbers, names, and claims from the storyboard as source content; do not silently invent facts.
8. Use the naming rules in `config/naming.json`.
9. If an external provider is not configured, generate a request artifact and stop with `waiting_external`.
10. Report verification as `success`, `failed`, or `not_run`.

## User-facing response rules

1. Do not expose internal state or paths such as `manifest.json`, `workspace/inbox`, `활성 프로젝트 없음`, or `시작 인테이크가 필요합니다` to the user.
2. If a project has not started, say that a new task can begin and request only the project name, video duration, and aspect ratio.
3. Do not require a storyboard file. Explain that the storyboard can be written together in Codex chat and saved as Markdown when no file is supplied.
4. The permanent required intake fields are project name, video duration, video resolution, video frame rate, and aspect ratio. Do not remove or relax them unless the user explicitly requests a change to the default intake rules.

## Stage precedence

User review gates are: storyboard, image, video, and remotion. Input replacement at a gate preserves the old file and invalidates only downstream stages.

- User approval overrides every default.
- Storyboard controls message, timing, narration, and factual wording.
- Motion-graphic reference controls visual language, composition, and animation direction.
- Global instructions control file formats, safety, and delivery structure.

## Required handoff

At every handoff, update `manifest.json`, append one line to `events.jsonl`, and write a human-readable report under `reports/`.
