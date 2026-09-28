# North Central US CLI 요약 영상

**한국어** | [English](en/videos.md) · [실습 홈](../README.ko.md)

새 North Central US 실행과 원본 증거 확인을 **각 3분 28초**로 편집했습니다. 음성·음악 없이 화면과 자막으로 설명합니다. **이번 개정판은 CLI 전용**입니다. 인증된 포털 재녹화는 새 로그인이 필요해 보류했으며, 이전 Sweden 포털 영상을 섞지 않았습니다.

| 언어 | 영상 | 자막 |
|---|---|---|
| 한국어 | [MP4](assets/videos/foundry-v1.5-summary-ko.mp4) | [SRT](assets/videos/foundry-v1.5-summary-ko.srt) |
| English | [MP4](assets/videos/foundry-v1.5-summary-en.mp4) | [SRT](assets/videos/foundry-v1.5-summary-en.srt) |

## 무엇을 녹화했나요?

**실제 subprocess 출력을 실시간으로 표시하는 Playwright Headless 브라우저**를 녹화했습니다. macOS Terminal 앱의 녹화나 모의 모델 응답이 아닙니다. 일부 장면은 `read-only-saved-NC-evidence`로 표시한 **저장된 실제 결과의 조회**이며, 새 모델 호출과 구분합니다.

화면의 `[local]/.../summarize_nc.py`는 원본 결과를 짧게 표시하는 녹화용 개인 도구이며 실습 의존성이 아닙니다. 재현할 때는 각 장에 포함된 `workshop.py`, `managed_redteam.py`, `routine_runs.py` 명령을 사용합니다.

대기 시간과 녹화기 종료 시 축소 프레임을 제외하고, 결과를 읽도록 마지막 정상 프레임을 유지했습니다. 계정·구독 식별자와 개인 경로는 가리거나 잘랐습니다. 초기 NC 원본 일부에는 녹화기의 오래된 Sweden 부제목이 남아 있었지만 **실제 명령·자원·Endpoint는 NC**였습니다. 편집에서는 그 헤더를 제외하고 실제 명령/결과 영역만 사용했으며, 응답이나 원래 점수는 변경하지 않았습니다.

## 결과를 해석할 때

- NC의 Search/IQ/Hybrid와 Sol, 실제 영어 IQ/Memory를 구분합니다. 공유 한국어 Hosted/진단은 화면의 원본 언어 표시를 유지하며 별도 영어 시험으로 바꾸지 않습니다.
- Hosted IQ v1/v2 dev 6/6, 한국어 진단 8/8, calibration 각각 24/24, 알려진 4문항 재검증은 서로 다른 증거입니다. 새 미공개 holdout이나 운영 승인을 주장하지 않습니다.
- **새 관리형 Task Adherence-only 5/5와 이전 혼합 6행·5 pass/1 fail은 별도 job**입니다. Prohibited Actions의 불일치·입력 가림·response ID 미노출을 보존합니다.
- Optimizer의 필수 초기화 오류는 **차단 상태**로 보여 줍니다. Coherence v13의 별도 성공이 이 오류나 Prohibited Actions를 고친 것은 아닙니다.
- Memory TTL 0, 실제 timer의 원래 답변, 8개 세션 파일 보관과 **실제 OIDC 릴리스/영어 6/6 artifact**를 확인합니다. CI의 로컬 검색 프로필과 별도 Hosted IQ를 혼동하지 않습니다.

원본 이름·SHA256·구간·자막·가림 정보는 [provenance JSON](assets/videos/foundry-v1.5-summary-provenance.json)에 있습니다. 원본 녹화는 개인 실습 폴더의 `dist/recordings/`에 보관하며 공개 묶음에는 편집본만 포함합니다.

**화면/코덱:** 1600×1000, 25 fps, H.264/yuv420p, MP4 faststart. 각 영상은 5,200프레임, 25개 장면이며 SRT 27개 구간이 전체 208초를 포함합니다.

이전 [Sweden R2 영상/출처](https://github.com/junwoojeong100/microsoft-foundry-v1.5-labs/blob/0a8ab50/docs/videos.md)는 원래 revision에 보존합니다.

전체 수행 범위와 제한은 [실제 검증 보고서](validation-report.md)를 확인하세요.
