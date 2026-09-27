# v1.5 기능별 실습 — v1.2 기능은 그대로, 시작은 더 짧게

**v1.5는 v1.2의 기능을 삭제하지 않습니다.** 기본 7시간은 하나의 도우미를 완성하는 동선이고, 이 기능 카드는 v1.2의 넓은 기능을 **목적 → 준비 → 첫 실행 → 확인 → 정리** 순서로 다시 안내합니다.

모든 카드를 420분 안에 다 수행하라는 뜻은 아닙니다. 추가 소요 시간은 준비 완료 후의 설계 시간이며, 인프라·권한 승인 대기는 별도입니다. 전체 기능의 범위는 [대응표](../feature-map.md)에서 확인합니다.

## 기능으로 바로 가기

| 하고 싶은 일 | 첫 카드 | 추가 시간 예시 |
|---|---|---:|
| 모델을 비교하고 Router를 이해한다 | [F01. 모델 선택과 운영](01-models.md) | 30~45분 |
| MAF, 함수, MCP, 추가 도구를 쓴다 | [F02. 에이전트와 도구](02-agents-tools.md) | 30~45분 |
| 순차·병렬·Group Chat과 승인/복구를 배운다 | [F03. 워크플로](03-workflows.md) | 40~60분 |
| Search, IQ, Toolbox로 지식을 확장한다 | [F04. 지식과 도구 공유](04-knowledge.md) | 45~75분 |
| 대화 평가, Optimizer, Insights, 회귀를 배운다 | [F05. 평가와 학습 루프](05-evaluation.md) | 45~75분 |
| 코드를 Hosted Agent로 옮긴다 | [F06. Hosted](06-hosted.md) | 45~75분 |
| Memory, A2A, Routines를 연결한다 | [F07. 기억·위임·예약](07-collaboration.md) | 기능당 30~45분 |
| 안전·권한·네트워크·IQ 확장 경계를 확인한다 | [F08. 거버넌스와 전문 영역](08-governance.md) | 30~45분 |

## 한 번만 준비

**동작 범위를 새로 구현하다 기능이 빠지지 않도록**, v1.2의 실행 구현을 커밋으로 고정해서 재사용합니다. 이 폴더에서 다음을 실행하면 `.reference/v1.2/`에 원본 코드·문서·데이터와 원본 LICENSE가 준비됩니다. 큰 녹화·캡처 미디어는 받지 않습니다.

```bash
python scripts/prepare_v12.py --install
python scripts/v12.py doctor
```

Git과 **Python 3.13**이 필요합니다. 설치는 `.reference/v1.2/.venv/`에만 수행하며 기본 7시간의 `.venv`와 분리됩니다. 두 환경의 패키지 버전을 섞거나 강제로 업그레이드하지 않습니다.

`doctor`의 `azure_tested: false`는 정상입니다. 아직 Azure를 호출하지 않았습니다. 이 준비 도구는 로그인·리소스 생성·역할 변경·구독 변경을 하지 않습니다.

소스가 이미 준비되어 있으면 커밋만 확인하고 재사용합니다. 개인 `.env`, 출력, 원본 수정사항을 덮어쓰지 않습니다. 기준은 [v12-reference.json](../../v12-reference.json)입니다.

## Azure를 쓰는 카드에서만 채울 값

`.reference/v1.2/.env.example`을 **같은 폴더의 `.env`**로 복사합니다. 이미 있으면 덮어쓰지 않습니다.

첫 모델·MAF 실행에 필요한 값:

```text
AZURE_SUBSCRIPTION_ID=담당자가-확인한-구독-ID
AZURE_TENANT_ID=담당자가-확인한-테넌트-ID
AZURE_RESOURCE_GROUP=실제-리소스-그룹
AZURE_AI_ACCOUNT_NAME=실제-Foundry-리소스
AZURE_AI_PROJECT_ENDPOINT=실제-프로젝트-Endpoint
AZURE_AI_MODEL_DEPLOYMENT_NAME=검증된-배포-이름
WORKSHOP_PREFIX=mfv2-01-0927
WORKSHOP_AUTH_MODE=cli
```

예시를 그대로 사용하지 않습니다. Prefix는 본인의 고유 값으로 바꾸며 `mfv2-`로 시작하는 원본 코드의 소유권 규칙을 유지합니다. `mfv2`는 여기서 사용하는 원본 네임스페이스이지 새로 발표된 제품 버전이 아닙니다.

기본 과정에서 검증한 모델을 재사용하려면 실제 배포 이름을 명시합니다. 원본 예시의 `gpt-6-sol`이 있다는 이유로 새 모델을 자동 생성하지 않습니다. Search, embedding, judge, Hosted ID 등은 **선택한 카드에서 요구하는 값만** 추가합니다.

```bash
python scripts/v12.py doctor --cloud
```

이는 설정·인증·배포 메타데이터 확인이지 추론 성공 증거가 아닙니다. 각 카드의 실제 요청으로 별도 확인합니다.

## 명령은 계속 v1.5 루트에서

```bash
python scripts/v12.py maf --tools
```

위 명령은 내부적으로 고정 원본의 올바른 Python과 작업 폴더를 선택합니다. 원본 문서의 `python scripts/workshop.py ...`를 실행하고 싶다면 같은 인자를 **`python scripts/v12.py ...`** 뒤에 붙이면 됩니다.

보조 스크립트도 루트에서 실행합니다.

```bash
python scripts/v12.py --script package-hosted --help
python scripts/v12.py --script prepare-hosted --help
python scripts/v12.py --script export-evaluation --help
```

`azd`의 Hosted 배포 명령만은 **새로 준비한 독립 Hosted 프로젝트**를 지정합니다. 원본 소스 전체를 배포하지 않습니다.

## 데이터·결과를 섞지 않기

| 구분 | 기본 7시간 | 기능 호환 실습 |
|---|---|---|
| 합성 회사 / 문서 | 다온테크 / 3개 | v1.2 한빛기술 / 6개 |
| 설정 | 루트 `.env` | `.reference/v1.2/.env` |
| SDK | 루트 `.venv` | `.reference/v1.2/.venv` |
| 결과 | 루트 `outputs/` | `.reference/v1.2/outputs/` |
| 지침/평가 | baseline/improved, 기본 dev/holdout | 원본 v1/v2, 원본 dev/holdout |
| 정리 | `python lab.py cleanup` | 각 기능의 원본 소유권 기록과 정리 절차 |

**두 데이터 세트와 점수는 호환되지 않습니다.** 원본 기능을 보존하기 위해 원본 실험 조건도 유지했습니다. 기존 결과를 덮어 쓰거나 기본 과정의 점수를 상세 기능의 점수로 옮기지 않습니다.

새 결과에 `v1.5 기능 실습 / 사용 코드 v1.2 고정 커밋`이라고 기록합니다. 원본의 이전 실행·녹화는 이번 실습의 증거가 아닙니다. 복사본에 없는 과거 미디어는 원본 온라인 자료에서 참고할 수 있지만 필수 준비물이 아닙니다.

**처음 방문했다면 카드 하나만 여세요.** 본 과정은 [Lab 01](../01-foundry.md)부터 진행하며, 이 기능 목록을 별도의 거대한 필수 순서로 따라가지 않습니다.
