# 데이터와 결과를 구분하기

| 위치 | 내용 | 용도 |
|---|---|---|
| `data/knowledge/` | 한빛기술 합성 정책 | 검색과 답변 근거 |
| `data/policies/` | 같은 정책의 TXT 파일 | File Search 업로드 |
| `data/evaluation/dev.jsonl` | 개발용 6문항 | 반복 개선 |
| `data/evaluation/holdout.jsonl` | 최종 확인용 4문항 | 후보를 고정한 뒤 한 번 확인 |
| `data/evaluation/calibration.jsonl` | 알려진 좋은/나쁜 답 | 평가자 점검 |
| `data/fixtures/` | 미리 작성한 답변 | 로컬 검사기 연습 |
| `outputs/` | 내가 실제로 실행한 결과 | 검토·비교·정리 |

`demo`의 fixture는 모델이 방금 만든 답변이 아닙니다. 실제 응답·인용·사용량·trace의 증거로 사용하지 않습니다.

영문 데이터는 `en/`에 따로 있으며 ID·금액·날짜와 판단 기준을 유지합니다. 서로 다른 언어의 결과를 한 번의 고정 실험으로 합치지 않습니다.

정책이나 지침을 바꾸면 사용한 버전과 hash를 보관합니다. 원시 응답·평가 점수·holdout을 고쳐 통과시키지 않습니다.

[07 평가](07-evaluation.md) · [15 최종 확인](15-capstone-cleanup.md)
