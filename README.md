# Tosun Studio

스토리보드와 모션그래픽 자료를 넣고, Codex 대화창에서 각 단계의 결과를 확인·승인하는 반자동 제작 워크플로우입니다.

## 실행

1. `workspace/inbox/`에 스토리보드와 모션그래픽 텍스트·이미지를 넣습니다.
2. Codex에서 `스토리보드 분석해`라고 입력합니다.
3. 결과를 확인하고 `현재 결과 승인`, `다음 단계 진행`으로 작업합니다.

사용자는 플러그인 폴더나 Python 스크립트에 직접 접근할 필요가 없습니다. Tosun Studio 플러그인이 내부 bridge를 자동 호출합니다.

## 기본 워크플로우

1. 스토리보드 제작
2. 썸네일 이미지 제작
3. 영상 제작
4. 모션 그래픽 제작

각 단계는 Codex가 직접 제작하거나 사용자가 텍스트·이미지·영상·구조화 데이터를 인풋으로 주입해 진행할 수 있습니다. 결과를 표시한 뒤 사용자가 승인해야 다음 단계로 이동합니다. 모션 그래픽은 프리뷰 렌더를 먼저 확인한 뒤 풀 렌더합니다.

작업 시작 전 프로젝트명, 영상 길이, 영상 해상도, 영상 프레임, 화면 비율을 받습니다. 이 다섯 항목은 기본 영구 필수값입니다. 스토리보드는 파일을 주거나 Codex 채팅으로 함께 작성할 수 있습니다. 목적·대상·플랫폼·언어·레퍼런스는 선택 입력입니다. 양식은 `templates/project-intake-form.md`에 있습니다.

## 현재 제공하는 기능

- `workspace/inbox/`와 프로젝트 파일 탐색
- 텍스트/이미지/영상 파일 발견 및 역할 추정
- 프로젝트별 원본 입력 복사
- `manifest.json` 기반 단계 상태 관리
- 스토리보드 양식 → 이미지·영상 프롬프트 → 이미지 표시 → 비디오 표시 → Remotion 표시 → 공개
- 단계별 승인/수정/재시도 이벤트
- 단계 실행 전 자동 백업
- `public/`에 승인된 최종 표출 파일만 수집
- Windows DPAPI 기반 개인 지침 암호화 명령

이미지는 Codex 이미지 생성 기능을 사용하고, 영상은 연결된 Higgsfield 플러그인을 호출합니다. Higgsfield가 연결되지 않았거나 실제 결과를 반환하지 않으면 `waiting_external`에서 멈추며 생성 완료로 보고하지 않습니다.

## 파일 하이어라키

```text
Tosun Studio/
├─ AGENTS.md                         Codex 작업 지침
├─ README.md                         사람용 사용 설명
├─ tosun_studio.py                 상태/파일/백업/단계 로직
├─ plugins/
│  └─ tosun-studio/                Codex 반자동화 플러그인 소스
│     ├─ .codex-plugin/plugin.json
│     ├─ skills/00-master-tosun/SKILL.md  전체 순서·승인·백업·상태 관리
│     ├─ skills/01-storyboard/SKILL.md    스토리보드 작성·분석
│     ├─ skills/02-image/SKILL.md         Codex 이미지 생성 호출
│     ├─ skills/03-video/SKILL.md         Higgsfield 호출·결과 수집
│     ├─ skills/04-remotion/SKILL.md      Remotion 플러그인 호출·렌더
│     └─ scripts/bridge.py
├─ .gitignore
├─ config/
│  ├─ naming.json                    파일명 규칙
│  └─ workflow.json                  단계 정의와 확장자 역할
├─ instructions/
│  ├─ core.md                        공통 지침
│  ├─ private-template.md            개인 지침 작성용 템플릿
│  └─ stages/                        단계별 지침
├─ docs/
│  ├─ COMMANDS.md                    명령어 모음
│  └─ USER_GUIDE.md                  사용자 헬프
├─ templates/
│  ├─ project-intake-form.md           프로젝트 시작 정보 양식
│  └─ storyboard-form.md              스토리보드 작성 양식
├─ workspace/
   ├─ inbox/                         새 입력 파일 투입 위치
   ├─ projects/<project-id>/
   │  ├─ input/                       복사된 원본 입력
   │  ├─ artifacts/                   중간 산출물과 외부 생성 결과
   │  ├─ reports/                     단계별 사람이 읽는 보고서
   │  ├─ public/                      최종 UI 표출 파일만 보관
   │  ├─ manifest.json                현재 상태
   │  └─ events.jsonl                 승인/수정/실행 이벤트
   ├─ backups/<project-id>/            타임스탬프별 백업
│  └─ exports/                         최종 외부 전달물
```

## 실행 구조

Codex → Tosun Studio Master skill → storyboard/image/video/remotion 하위 skill → 플러그인 bridge → tosun_studio.py 엔진 → workspace

사용자는 Codex 대화창에서 명령을 입력하고 결과를 승인합니다. 플러그인 폴더, Python 파일, GUI를 직접 열 필요가 없습니다.

## 암호화된 개인 지침

개인 지침 원문은 저장소에 올리지 않고 사용자 계정에 묶인 암호화 저장소에 보관합니다. 생성된 instructions/private.enc는 저장소에 포함하지 않습니다.

## 명명 규칙

- 프로젝트: `YYYYMMDD_short-slug`
- 중간 산출물: `<project-id>__s<stage-number>__<role>__v###.<ext>`
- 백업 폴더: `<project-id>__backup__YYYYMMDD_HHMMSS__<reason>`
- 공개 파일: `manifest.json`, `thumbnail.png`, `video.mp4`, `infographic.mp4`

## 검증 상태

현재 Codex 플러그인과 로컬 상태/백업/파일 탐색 흐름을 기준으로 사용합니다. 외부 provider 연결은 `not_configured`로 표시되며, 실제 연결 전까지 자동 생성 완료로 보고하지 않습니다.
