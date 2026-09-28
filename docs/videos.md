# 리포 이름 변경 후 실습 재실행 영상

**한국어** | [English](en/videos.md) · [실습 홈](../README.ko.md)

새 North Central US 그룹 `rg-mflabs15-jw-0928`의 실제 실행을 **각 4분 32초·31개 장면**으로 편집했습니다. 음성·음악 없이 한국어/영어 자막으로 설명합니다. 이전 NC·Sweden 영상을 재사용하지 않았으며, 새 관리형 결과의 실패와 최종 인수 보류도 그대로 포함했습니다.

| 언어 | 영상 | 자막 |
|---|---|---|
| 한국어 | [MP4](assets/videos/foundry-v1.5-summary-ko.mp4) | [SRT](assets/videos/foundry-v1.5-summary-ko.srt) |
| English | [MP4](assets/videos/foundry-v1.5-summary-en.mp4) | [SRT](assets/videos/foundry-v1.5-summary-en.srt) |

## 무엇을 녹화했나요?

**인증된 포털 5개 장면:** 새 모델 배포, 첫 Sol Playground 응답, Agents, Hosted candidate 평가, 관리형 Task Adherence 결과입니다. 첫 응답은 기본 Web search를 제거한 **실제 새 요청**이고, 나머지는 이번 실행에서 만든 자원/결과의 읽기 전용 확인입니다.

**CLI 장면:** 실제 subprocess 출력을 Playwright Headless의 화면에 실시간으로 표시하며 녹화했습니다. macOS Terminal 앱 자체를 녹화한 것은 아닙니다. 새 그룹 생성부터 파일·도구·검색·평가·배포·중지까지의 원본을 사용합니다. `review-*-settled` 장면은 **이번 실행의 보존한 실제 결과를 읽는 화면**이며 새 추론이 아닙니다. 화면 하단에서 실제 실행과 저장 증거 조회를 구분합니다. 개인 녹화 도구는 실습 의존성이 아니며 재현에는 각 장의 포함된 실행기를 사용합니다.

**언어 범위:** 한국어 본 실습에 별도 영어 Prompt Agent/File Search와 한·영 OIDC 릴리스를 포함했습니다. 포털 UI는 영어이며 두 자막판은 같은 원본을 설명합니다. 한국어 검색·Memory·평가를 별도 영어 실행으로 바꾸거나 전체 과정을 두 번 수행했다고 주장하지 않습니다.

**편집과 개인정보:** 원래 영상의 정상 속도 구간 뒤에 **같은 녹화에서 캡처한 실제 결과 스크린샷**을 정지 화면으로 유지합니다. 기다림과 녹화기 viewport 축소 구간은 제외했으며, 결과 텍스트나 점수를 합성하지 않았습니다. 빠른 CLI 출력의 마지막 갱신이 녹화에 빠지는 문제는 화면 렌더링 대기 후 저장 증거만 재녹화해 해결했습니다. 원래 녹화는 수정하지 않았고 각 장면의 최종 화면을 원본 스크린샷과 수치 대조했습니다.

로그인 화면·계정 이메일·구독 식별자·인증 정보·개인 경로는 자르기 또는 가림으로 편집본에서 제외했습니다. 기존에 승인된 브라우저 인증 상태는 메모리 안에서만 사용했고 별도 파일로 내보내지 않았습니다. 녹화용 임시 브라우저 context는 모두 닫았으며 기존 사용자 프로필은 삭제하지 않았습니다.

## 결과를 해석할 때

- SDK와 Hosted IQ 전후 dev 각각 6/6, 세 policy 기준 각각 6/6, 한국어 calibration 24/24, 보완 진단 8/8은 서로 다른 증거입니다. 높은 점수가 최종 안전 인수를 대신하지 않습니다.
- **새 관리형 Task Adherence는 6행·5 pass/1 fail입니다.** 실패 행 severity 0/문턱 3과 원래 fail/attack-success flag가 불일치합니다. 이전 환경의 5/5를 복사하거나 flag·ASR을 고치지 않았습니다. 서비스가 가린 입력과 미노출 response ID는 그대로 둡니다.
- **새 Optimizer는 baseline 1.0, 새 전체 후보 0개입니다.** 원래 세 평가기·문턱 4와 dev 6행 참조 감사는 확인했지만 개선·승격은 없었습니다. 이전 NC의 후보를 새 결과에 섞지 않았습니다.
- 실제 timer의 원래 답변, 8개 세션 파일과 **한국어 CI v1/영어 CI v2 각각 6/6 artifact**를 확인했습니다. CI local 검색과 별도 IQ Hosted는 다른 프로필입니다.
- 최종 관리형 gate 미충족으로 **holdout을 새로 열지 않고 인수를 보류**했습니다. 실습 세션 13개는 모두 idle이며, timer·반복 평가·Insights 예약은 껐습니다. 새 Search·파일/volume·로그의 보존 비용은 남습니다.

원본 영상/결과 스크린샷의 이름·SHA256·사용 구간·정지 시간·자막·자르기는 [provenance JSON](assets/videos/foundry-v1.5-summary-provenance.json)에 있습니다. 새 원본은 private `dist/recordings/rename-20260928/`에 있고 이전 상태/영상은 hash와 함께 비공개 보관했습니다. 배포 묶음에는 편집본만 포함합니다.

**화면/코덱:** 1600×1000, 25 fps, H.264/yuv420p, MP4 faststart. 각 영상은 **6,800프레임·31개 장면**, SRT **31개 구간·272초**이며 각각 20 MB 미만입니다. 전체 디코딩·자막 일치와 **모든 장면의 마지막 실제 결과 화면**을 확인했습니다.

이전 [NC 포털판](https://github.com/junwoojeong100/microsoft-foundry-labs-v1.5/blob/7b7ca26/docs/videos.md), [NC CLI판](https://github.com/junwoojeong100/microsoft-foundry-labs-v1.5/blob/1d53a68/docs/videos.md), [Sweden R2판](https://github.com/junwoojeong100/microsoft-foundry-labs-v1.5/blob/0a8ab50/docs/videos.md)은 원래 revision에 보존합니다.

전체 수행 범위와 제한은 [실제 검증 보고서](validation-report.md)를 확인하세요.
