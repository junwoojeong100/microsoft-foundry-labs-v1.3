# 보존된 축약 예제

루트의 `app.py`, `lab.py`, `workshop.py`, `tools.py`, `evaluation.py`, `data/`, `prompts/`, `requirements.txt`는 **초기 축약 예제 구현**입니다. 현재 자가 실습의 기본 경로가 아닙니다.

| 구분 | 현재 전체 과정 | 보존된 축약 예제 |
|---|---|---|
| 업무 데이터 | 한빛기술 6문서 | 다온테크 3문서 |
| 명령 | `python scripts/workshop.py ...` | `python lab.py ...` |
| SDK | `.reference/v1.2/.venv` | 별도 루트 `.venv`, 루트 requirements |
| 설정 | `.reference/v1.2/.env` | 루트 `.env.example`의 세 값 |
| 결과 | `.reference/v1.2/outputs/` | 루트 `outputs/` |
| 자산 기록 | 원본 ownership ledger와 `.selfstudy` | 루트 `.lab/state.json` |

두 정책은 다른 가상 회사입니다. 금액·날짜·평가 문항과 점수를 섞지 않습니다. 현재 과정만 진행하려면 이 예제를 실행할 필요가 없습니다.

이전에 축약 예제를 실행했다면 해당 환경에서 다음으로 **자산을 조회**합니다.

```bash
python lab.py cleanup
```

출력된 본인 agent·버전·파일/저장소를 확인한 뒤 정리를 결정한 경우에만 그 정확한 이름으로 `cleanup --confirm`을 사용합니다. 이 명령은 현재 과정의 Search/Toolbox/Hosted나 공유 그룹을 정리하지 않습니다.

현재 과정의 시작점은 [00](00-setup.md)입니다.
