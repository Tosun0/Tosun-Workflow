# Stage 05 — Infographic

Remotion은 구조화된 데이터로 렌더링합니다. 영상에서 텍스트와 수치를 추측하지 말고 승인된 스토리보드와 모션 그래픽 입력을 사용합니다.

## Preview render

- 프로젝트의 composition과 canonical render 명령을 먼저 확인합니다.
- 빠른 확인용 프리뷰를 `artifacts/previews/motion-graphics-preview.mp4`에 렌더합니다.
- 필요하면 `npx remotion still`로 첫 프레임 레이아웃을 먼저 확인합니다.
- 타이밍, 레이아웃, 폰트, 자막 잘림, 색상, 화면 비율을 확인하고 실제 프리뷰를 사용자에게 표시합니다.
- 프리뷰 승인 전에는 풀 렌더하지 않습니다.

## Full render

- 승인된 프리뷰를 기준으로 최종 해상도, 프레임레이트, 길이, 오디오, 코덱 설정으로 렌더합니다.
- `artifacts/final/infographic.mp4`의 실제 존재 여부와 메타데이터를 확인합니다.
- 풀 렌더 결과를 사용자에게 표시하고 최종 승인을 받은 뒤 `public/`에 복사합니다.
