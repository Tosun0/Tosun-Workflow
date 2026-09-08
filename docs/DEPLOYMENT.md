# Tosun Workflow Git 배포

## 저장소 구성

- `.agents/plugins/marketplace.json`: Git 배포용 마켓플레이스
- `plugins/tosun-workflow/`: Codex 플러그인 본체
- `plugins/tosun-workflow/assets/`: composer 아이콘과 로고
- `plugins/tosun-workflow/skills/master-tosun/SKILL.md`: 전체 워크플로우·승인 지침
- `plugins/tosun-workflow/skills/{storyboard,image,video,remotion}/SKILL.md`: 시퀀스별 실행 지침

## 설치

저장소를 받은 뒤 저장소 루트에서 실행합니다.

```powershell
codex plugin marketplace add .
codex plugin add tosun-workflow@tosun-team
```

설치 후 새 Codex 작업을 열어야 최신 지침이 적용됩니다.

## 비밀값

개인 지침, Higgsfield 인증 정보, API 키, 작업 결과물은 저장소에 커밋하지 않습니다.
