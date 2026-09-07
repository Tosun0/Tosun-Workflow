# Tosun Workflow 명령어 모음

## 시퀀스 구성

작업 시작 시 프로젝트명, 영상 길이, 영상 해상도, 영상 프레임, 화면 비율을 받습니다. 이 다섯 항목은 기본 영구 필수값입니다. 스토리보드 파일은 선택사항이며, 파일이 없으면 Codex 채팅으로 Markdown 스토리보드를 함께 작성할 수 있습니다.

사용자 자료는 `workspace/inbox/<프로젝트명>/` 폴더에 넣습니다. 이미지·영상·모션그래픽 영상·스토리보드를 함께 넣을 수 있습니다.

| 시퀀스 | 내용 |
|---|---|
| `S1` | 스토리보드 제작 |
| `S2` | 썸네일 이미지 제작 |
| `S3` | 영상 제작 |
| `S4` | 모션 그래픽 제작 |
| `전체` | S1 → S2 → S3 → S4 |

이미 승인된 결과나 인풋이 있으면 해당 시퀀스부터 시작할 수 있습니다. 각 시퀀스 결과를 사용자가 승인해야 다음 시퀀스로 넘어갑니다.

## 명령어

Codex에게 아래처럼 짧게 말하면 됩니다.

| 명령 | 동작 |
|---|---|
| `토순 워크플로우 상태 확인` | 현재 프로젝트와 단계 확인 |
| `스토리보드를 작성하라` | 스토리보드 양식 출력 또는 입력 자료를 양식으로 정리 |
| `이미지를 생성하라` | 승인된 스토리보드로 썸네일 이미지 제작 및 표시 |
| `영상을 제작하라` | 승인된 이미지로 영상 제작 및 표시 |
| `모션 그래픽을 제작하라` | 승인된 데이터로 Remotion 프리뷰 제작 및 표시 |
| `좋아` / `진행해` | 현재 표시 결과 승인 |
| `수정해` | 현재 결과를 수정하거나 새 인풋으로 교체 |
| `프로젝트 백업해` | 수동 백업 생성 |
| `토순 워크플로우 도움말` | 이 명령 모음 표시 |

프로젝트 시작 양식은 [templates/project-intake-form.md](../templates/project-intake-form.md)입니다.

명령어와 시퀀스는 별개입니다. 시퀀스는 작업 범위를 선택하고, 명령어는 선택한 시퀀스를 실행합니다.

## 내부 CLI 명령

일반 사용자는 실행할 필요가 없습니다. Codex 플러그인이 내부적으로 호출합니다. 장애 조사나 개발 시에만 프로젝트 루트에서 사용합니다.

```powershell
# GUI 실행
.\run.ps1

# EXE 패키징
.\package.ps1

# GUI 서버 직접 실행
python runner.py --serve --port 8765

# 프로젝트 생성
python runner.py --new-project "Project Title" inbox\storyboard.md inbox\motion-reference.png

# 내부 단계 실행
python runner.py --run PROJECT_ID storyboard
python runner.py --run PROJECT_ID image

# 사용자 확인은 Codex가 내부적으로 처리
python runner.py --approve PROJECT_ID storyboard
python runner.py --approve PROJECT_ID image

# 백업
python runner.py --backup PROJECT_ID manual-before-revision

# 개인 지침 암호화
python runner.py --encrypt-private instructions\private-template.md
```

## Codex bridge 명령 (내부용)

Codex 플러그인은 긴 로그 대신 짧은 JSON을 반환하는 bridge를 내부적으로 사용합니다. 사용자가 `plugins/` 폴더를 열거나 아래 명령을 직접 입력할 필요는 없습니다.

```powershell
python plugins\tosun-workflow\scripts\bridge.py status
python plugins\tosun-workflow\scripts\bridge.py status --project PROJECT_ID
python plugins\tosun-workflow\scripts\bridge.py task --project PROJECT_ID
python plugins\tosun-workflow\scripts\bridge.py task --project PROJECT_ID --stage image
python plugins\tosun-workflow\scripts\bridge.py attach --project PROJECT_ID --stage image --file PATH
```

## 파일 위치

- 입력: `workspace/inbox/`
- 프로젝트 상태: `workspace/projects/<project-id>/manifest.json`
- 중간 결과: `workspace/projects/<project-id>/artifacts/`
- 단계 보고서: `workspace/projects/<project-id>/reports/`
- 최종 UI 파일: `workspace/projects/<project-id>/public/`
- 백업: `workspace/backups/<project-id>/`
- Codex 작업 파일: `workspace/projects/<project-id>/codex_tasks/`

## 진행 규칙

1. 프로젝트명, 영상 길이, 영상 해상도, 영상 프레임, 화면 비율을 입력합니다.
2. 스토리보드 파일을 주거나 Codex 채팅으로 Markdown 스토리보드를 작성합니다.
3. `스토리보드를 작성하라`로 S1을 실행합니다.
4. 결과를 확인하고 승인한 뒤 `이미지를 생성하라`로 S2를 실행합니다.
5. 이미지 승인 후 `영상을 제작하라`로 S3를 실행합니다.
6. 영상 승인 후 `모션 그래픽을 제작하라`로 S4를 실행합니다.
7. 모션 그래픽 프리뷰 승인 후 풀 렌더를 진행하고 최종 결과를 승인합니다.

각 결과가 마음에 들지 않으면 `수정해`라고 말하거나 새 인풋을 함께 제공합니다. 다음 단계는 현재 결과를 승인한 뒤에만 실행됩니다.

승인 전에는 다음 단계가 실행되지 않습니다.
