# 포털·CLI 요약 영상

**한국어** | [English](en/videos.md) · [실습 홈](../README.ko.md)

R2 재검증의 실제 Azure 실행 화면을 **각 3분 52초**로 편집했습니다. 음성·음악 없이 화면과 자막으로 설명합니다.

| 언어 | 영상 | 자막 |
|---|---|---|
| 한국어 | [MP4](assets/videos/foundry-v1.5-summary-ko.mp4) | [SRT](assets/videos/foundry-v1.5-summary-ko.srt) |
| English | [MP4](assets/videos/foundry-v1.5-summary-en.mp4) | [SRT](assets/videos/foundry-v1.5-summary-en.srt) |

## 무엇을 녹화했나요?

포털은 인증된 **Playwright Headless 브라우저의 실제 화면**입니다. CLI 화면은 **실제 실행한 subprocess의 출력을 실시간으로 표시하는 Headless 브라우저**를 녹화했습니다. macOS Terminal 앱의 화면 녹화나 모의 응답이 아닙니다.

대기 시간은 줄였고, 결과를 읽을 수 있도록 일부 마지막 프레임을 유지했습니다. 계정·구독 식별자와 개인 경로는 가리거나 잘랐습니다. 편집 자막은 실제 결과를 설명하며 원점수나 응답을 변경하지 않습니다.

## 결과를 해석할 때

- `swedencentral`의 Basic Search 생성에 성공했고, 최종 Hosted 워크플로는 **실제 Foundry IQ와 Sol**을 사용합니다. 최초 용량 오류는 이전 기록으로 남습니다.
- 영문 영상에는 실제 영문 Sol·IQ·Memory 실행이 포함됩니다. 공유된 최종 한국어 8개 진단은 영문 설명으로 명확히 표시하며, 별도의 영문 8개 시험이나 새 holdout이라고 부르지 않습니다.
- 원문 참조 평가와 한·영 각각 24/24 calibration, 명시적인 8개 진단의 0/8 정책 위반을 구분합니다. Fixture 검증을 agent 응답 검증으로, 실습 진단을 운영 안전 인증으로 바꾸지 않습니다.
- Optimizer는 원문 echo·reference ID·counterfactual을 검증한 결과이며 내부 judge 요청을 캡처했다고 주장하지 않습니다. 새 개선 후보나 성능 향상도 주장하지 않습니다.
- Memory TTL 0, 실제 예약 실행의 원래 응답 조회, 세션 증거의 보관을 보여 줍니다. CI 장면은 OIDC 설정을 녹화한 것이고, 이후 실제 릴리스의 성공 근거는 [검증 보고서](validation-report.md)에 별도로 있습니다.

원본 이름·SHA256·구간·자막·가림 정보는 [provenance JSON](assets/videos/foundry-v1.5-summary-provenance.json)에 있습니다. 원본 녹화는 개인 실습 폴더의 `dist/recordings/`에 보관하며 공개 묶음에는 편집본만 포함합니다.

**화면/코덱:** 1600×1000, 25 fps, H.264/yuv420p, MP4 faststart. 각 영상은 5,800프레임이며 SRT 36개 구간이 전체 232초를 포함합니다.

전체 수행 범위와 제한은 [실제 검증 보고서](validation-report.md)를 확인하세요.
