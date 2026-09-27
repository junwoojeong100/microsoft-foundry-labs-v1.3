# 포털·CLI 요약 영상

**한국어** | [English](en/videos.md) · [실습 홈](../README.ko.md)

실제 Azure 실행 화면을 **각 3분 38초**로 편집했습니다. 음성·음악 없이 화면과 자막으로 설명합니다.

| 언어 | 영상 | 자막 |
|---|---|---|
| 한국어 | [MP4](assets/videos/foundry-v1.5-summary-ko.mp4) | [SRT](assets/videos/foundry-v1.5-summary-ko.srt) |
| English | [MP4](assets/videos/foundry-v1.5-summary-en.mp4) | [SRT](assets/videos/foundry-v1.5-summary-en.srt) |

## 무엇을 녹화했나요?

포털은 인증된 **Playwright Headless 브라우저의 실제 화면**입니다. CLI 화면은 **실제 실행한 subprocess의 출력을 실시간으로 표시하는 Headless 브라우저**를 녹화했습니다. macOS Terminal 앱의 화면 녹화나 모의 응답이 아닙니다.

대기 시간은 줄였고, 결과를 읽을 수 있도록 일부 마지막 프레임을 유지했습니다. 계정·구독 식별자와 개인 경로는 가리거나 잘랐습니다. 편집 자막은 실제 결과를 설명하며 원점수나 응답을 변경하지 않습니다.

## 결과를 해석할 때

- 실제 생성 리전은 `swedencentral`입니다. Search는 용량/할당량 때문에 생성되지 않았고, Hosted matrix는 **명시적인 로컬 검색 경로**를 사용했습니다.
- 영문 영상은 실제 영문 프롬프트·데이터·에이전트 실행을 포함합니다. 마지막 인수 화면은 **공통 한국어 matrix 결과의 영문 설명**이며 별도의 영문 holdout 실행으로 표시하지 않습니다.
- 업무 검사 통과와 native 품질·생산 승인은 다릅니다. Relevance 경고와 `deployment_approved: false`를 그대로 남겼습니다.
- CI 구간은 저장소 한정 OIDC와 branch 제한의 실제 설정을 보여 줍니다. 해당 장면만으로 릴리스 workflow 실행을 검증한 것은 아닙니다.

원본 이름·SHA256·구간·자막·가림 정보는 [provenance JSON](assets/videos/foundry-v1.5-summary-provenance.json)에 있습니다. 원본 녹화는 개인 실습 폴더의 `dist/recordings/`에 보관하며 공개 묶음에는 편집본만 포함합니다.

**화면/코덱:** 1600×1000, 25 fps, H.264/yuv420p, MP4 faststart. 각 영상은 5,450프레임이며 SRT 33개 구간이 전체 218초를 포함합니다.

전체 수행 범위와 제한은 [실제 검증 보고서](validation-report.md)를 확인하세요.
