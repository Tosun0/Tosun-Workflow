---
name: tosun-workflow
description: Run the Tosun storyboard-to-video workflow with compact task files, Codex image generation, approval gates, backups, and Remotion handoff.
---

# Tosun Workflow

Internal worker instructions. Keep user-facing copy in Korean; keep internal routing, policy, and quality guidance in English.

## Operating rules

- Resolve the project root from the current Codex task directory or `TOSUN_WORKFLOW_ROOT`.
- Read the active project's `manifest.json` before changing a stage.
- Read only the current stage task file and referenced inputs. Prefer compact JSON over logs.
- Use the internal bridge. Never ask the user to open plugin folders or run scripts.
- Never expose internal paths, cache paths, manifest state, bridge commands, or diagnostics.
- Copy source inputs into `input/`; back up before every stage write; keep drafts in `artifacts/`.
- Publish only approved manifest outputs to `public/`.

## User-facing start

Use this Korean sentence when starting a new task:

`좋습니다. 새 작업을 시작하겠습니다. 프로젝트명·영상 길이·영상 해상도·영상 프레임·화면 비율을 알려주세요. 스토리보드는 파일을 첨부하거나 Codex와 채팅으로 작성할 수 있습니다.`

Do not require a storyboard file. Offer chat drafting or file attachment.

## Fixed help response

When the user asks `토순 워크플로우 사용 방법을 알려줘`, `토순 워크플로우 사용법 알려줘`, or an equivalent usage question, output the Korean guide in the next section verbatim. Do not summarize or add content.

### Fixed Korean usage guide

````markdown
## 토순 워크플로우 사용법

### 1. 작업 시작
```
필수)
프로젝트명:
영상 길이:
영상 해상도:
영상 프레임:
화면 비율:

옵션)
제작 시퀀스:
```

스토리보드는 Codex와 채팅으로 작성하거나 파일을 첨부할 수 있습니다.

가급적이면 ChatGPT 채팅을 사용해 Codex 토큰 소모량을 줄이세요.

### 2. 제작 시퀀스

- 스토리보드
- 썸네일 이미지
- 영상
- 모션 그래픽

각 시퀀스는 Codex가 제작하거나 사용자가 인풋 데이터를 첨부할 수 있습니다.
중간 결과물을 첨부하면 해당 시퀀스는 확인 후 스킵하고 다음 시퀀스로 넘어갑니다.

첨부 파일과 오버라이드할 시퀀스를 입력해주세요.

### 3. 제작 명령

아래는 예시입니다. 자유롭게 작성하셔도 무관합니다.

```
스토리보드를 작성하라
이미지를 생성하라
영상을 제작하라
모션 그래픽을 제작하라
```

### 4. 결과 확인 명령

아래는 예시입니다. 자유롭게 작성하셔도 무관합니다.

승인:
```
좋다
진행하라
```

수정:
```
OO가 마음에 들지 않는다. 수정하라.
관련 파일을 재작성하라.
```

교체:
```
이 파일로 교체하라.
```

각 작업은 사용자 최종 승인 후 다음 시퀀스로 넘어갑니다.

모션 그래픽은 프리뷰 승인 후 **풀 렌더**를 진행합니다.
````

## Workflow rules

Permanent required intake: project name, video duration, video resolution, frame rate, and aspect ratio. Do not relax these unless the user explicitly changes the default rule.

Sequences: S1 storyboard -> S2 thumbnail image -> S3 video -> S4 motion graphics. The user may start later when inputs exist.

Input injection may skip a sequence only after review and explicit approval. Replacement preserves old files and invalidates only the replaced stage and downstream stages.

Review gates are storyboard, image, video, and remotion. Never advance without explicit approval. `좋다`, `좋아`, `괜찮아`, and `진행하라` approve only the displayed result. `수정`, `바꿔`, or a new file regenerates the current stage.

Prompt preparation is internal after storyboard approval. Do not display prompts unless requested.

Use native Codex image generation when available. Use connected Higgsfield generation for video when available; otherwise create a request artifact and stop at `waiting_external`.

Use local Remotion tooling. Render `artifacts/previews/motion-graphics-preview.mp4` first and full-render `artifacts/final/infographic.mp4` only after preview approval. Never publish the preview.

Storyboard controls message, timing, narration, subtitles, and factual wording. Motion-graphic references control visual language and animation direction. Remotion uses approved structured data.

Quality checks cover storyboard facts and timing, image composition and consistency, video motion and deformation, and Remotion layout, clipping, resolution, FPS, audio, and actual file metadata.

On failure, persist `failed`, the error, retryability, recovery guidance, a report, and an event. If media validation is `not_run`, do not claim successful verification.

Return only status, stage, output path, next action, and blocker. Do not return raw logs unless needed for a failure.

For unrelated questions, use a natural playful Korean handoff in this tone: `궁금한 게 있으면 1층 찬영님한테 가세요 ㅋㅋ`. Adapt it instead of repeating the exact sentence mechanically.
