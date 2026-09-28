# North Central US 포털·CLI 요약 영상

**한국어** | [English](en/videos.md) · [실습 홈](../README.ko.md)

North Central US의 인증된 포털과 실제 CLI 원본을 **각 3분 52초**로 편집했습니다. 음성·음악 없이 자막으로 설명합니다. **Playwright Headless 포털 재녹화와 한·영 편집을 완료했습니다.** 이전 CLI 편집본은 별도로 보관했고 Sweden 포털 영상을 섞지 않았습니다.

| 언어 | 영상 | 자막 |
|---|---|---|
| 한국어 | [MP4](assets/videos/foundry-v1.5-summary-ko.mp4) | [SRT](assets/videos/foundry-v1.5-summary-ko.srt) |
| English | [MP4](assets/videos/foundry-v1.5-summary-en.mp4) | [SRT](assets/videos/foundry-v1.5-summary-en.srt) |

## 무엇을 녹화했나요?

**포털 8개 장면**은 사용자 로그인 후 같은 임시 프로필을 `headless=True`로 다시 열어 실제 NC 화면을 녹화했습니다. Agents, 모델 배포, 원래 Optimizer 실패, 수정 후 성공, baseline, candidate, Prohibited Actions v5, Task Adherence를 조회했습니다. 이 포털 녹화는 **이미 완료된 결과의 읽기 전용 확인**이며 새 모델 호출·승격·권한 변경을 하지 않았습니다.

**CLI 장면**은 실제 subprocess 출력을 실시간으로 표시한 기존 Playwright Headless 녹화입니다. macOS Terminal 앱 녹화나 모의 응답이 아닙니다. `read-only-saved-NC-evidence` 장면은 저장된 실제 결과의 조회입니다. `[local]/.../summarize_nc.py`는 개인 녹화 도구이며 실습 의존성이 아닙니다. 재현에는 각 장의 `workshop.py`, `managed_redteam.py`, `routine_runs.py`를 사용합니다.

포털 UI는 영어이며 **한·영 자막이 같은 원본 화면을 설명**합니다. Optimizer의 한국어 평가를 별도 영어 실행으로 바꾸지 않습니다. 로그인 화면·계정 이메일·구독 식별자·인증 정보는 편집 구간에서 제외했습니다. 인증 상태를 별도 파일로 내보내지 않았으며, 녹화 후 임시 브라우저와 로그인 프로필을 정리했습니다.

대기 시간과 녹화기 종료 시 축소 프레임을 제외하고, 결과를 읽도록 마지막 정상 프레임을 유지했습니다. 계정·구독 식별자와 개인 경로는 가리거나 잘랐습니다. 초기 NC 원본 일부에는 녹화기의 오래된 Sweden 부제목이 남아 있었지만 **실제 명령·자원·Endpoint는 NC**였습니다. 편집에서는 그 헤더를 제외하고 실제 명령/결과 영역만 사용했으며, 응답이나 원래 점수는 변경하지 않았습니다.

## 결과를 해석할 때

- NC의 Search/IQ/Hybrid와 Sol, 실제 영어 IQ/Memory를 구분합니다. 공유 한국어 Hosted/진단은 화면의 원본 언어 표시를 유지하며 별도 영어 시험으로 바꾸지 않습니다.
- Hosted IQ v1/v2 dev 6/6, 한국어 진단 8/8, calibration 각각 24/24, 알려진 4문항 재검증은 서로 다른 증거입니다. 새 미공개 holdout이나 운영 승인을 주장하지 않습니다.
- **관리형 Task Adherence-only 5/5, 이전 혼합 6행·5 pass/1 fail, 후속 Prohibited Actions v5 1행은 별도 job**입니다. V5도 Safe 설명과 Fail·ASR 100%가 모순되며, 입력 가림·response ID 미노출을 보존합니다. 도구 없는 이 비교는 Azure 도구 안전성 검증이 아닙니다.
- **원래 Optimizer 실패와 수정 후 성공을 모두 보여 줍니다.** 필수 초기화 인자 전달로 원래 평가기·문턱 4를 유지했습니다. Baseline·후보 각각 6/6과 원문 참조 감사를 통과했지만 1.0으로 동점이며 `best`는 baseline입니다. 중간 minibatch 실패를 보존했고 승격하지 않았습니다.
- Memory TTL 0, 실제 timer의 원래 답변, 8개 세션 파일 보관과 **실제 OIDC 릴리스/영어 6/6 artifact**를 확인합니다. CI의 로컬 검색 프로필과 별도 Hosted IQ를 혼동하지 않습니다.

원본 이름·SHA256·구간·자막·자르기 정보는 [provenance JSON](assets/videos/foundry-v1.5-summary-provenance.json)에 있습니다. 새 원본은 private `dist/recordings/portal/nc-headless-final-20260928/`, 이전 CLI 편집본과 출처는 `.selfstudy/archives/nc-cli-before-headless-20260928/`에 hash와 함께 보관합니다. 공개 묶음에는 편집본만 포함합니다.

**화면/코덱:** 1600×1000, 25 fps, H.264/yuv420p, MP4 faststart. 각 영상은 **5,800프레임·28개 장면**, SRT **30개 구간·232초**입니다. 한국어 약 13.95 MB, 영어 약 14.53 MB이며 두 영상 모두 전체 디코딩과 자막 일치를 확인했습니다.

이전 [NC CLI 영상/출처](https://github.com/junwoojeong100/microsoft-foundry-labs-v1.5/blob/1d53a68/docs/videos.md)와 [Sweden R2 영상/출처](https://github.com/junwoojeong100/microsoft-foundry-labs-v1.5/blob/0a8ab50/docs/videos.md)는 원래 revision에 보존합니다.

전체 수행 범위와 제한은 [실제 검증 보고서](validation-report.md)를 확인하세요.
