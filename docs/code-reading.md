# 필요한 코드만 읽기

**전체 프레임워크를 외우지 않고, 방금 실행한 명령이 무엇을 하는지 추적합니다.** 기본 명령은 항상 v1.5 루트의 `python scripts/workshop.py`입니다.

| 궁금한 것 | 이 폴더에서 열 파일 |
|---|---|
| CLI 인자/실행 분기 | `scripts/workshop.py`, `src/foundry_workshop/cli.py` |
| 로그인·구독·Endpoint | `src/foundry_workshop/settings.py` |
| 모델·관리형 Prompt Agent | `src/foundry_workshop/cloud.py` |
| 함수·MCP·MAF 워크플로 | `src/foundry_workshop/agents.py`, `runtime.py`, `examples/mcp_server.py` |
| Search·IQ·Hybrid | `src/foundry_workshop/search.py`, `iq_chat.py` |
| 평가·고정 조건·calibration | `evaluation.py`, `cloud_evaluation.py`, `benchmark.py`, `calibration.py` |
| Toolbox·Hosted | `toolbox.py`, `toolbox_host.py`, `hosted.py`, `packaging.py` |
| Memory·A2A·Routines | `memory_lab.py`, `a2a_lab.py`, `routines_lab.py` |
| 최소 독립 SDK 예제 | `examples/recipes/` |

표의 짧은 파일명도 `src/foundry_workshop/` 아래입니다.

먼저 입력 → 허용 도구/근거 → SDK 요청 → 원래 결과 → 검사/저장을 찾습니다. 에이전트 정의와 모델 배포, 로컬 코드와 원격 런타임을 구분하세요.

소스를 바꾸면 기존 평가와 같은 코드 조건이 아닐 수 있습니다. 변경 전 결과를 보존하고 같은 수정 코드로 새 dev 비교를 합니다.

Azure 없이 시작할 수 있는 로컬 확인:

```bash
python scripts/workshop.py doctor
```

작은 예제를 보려면 [examples/recipes](../examples/recipes/)를 엽니다. 입력 한 가지를 바꾸고 관련 테스트를 실행해 차이를 확인하세요. 로컬 테스트는 실제 모델 품질의 증거가 아닙니다.

[전체 과정](../README.md)
