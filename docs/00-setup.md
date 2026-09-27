# 수업 전 준비 — 수업 시간에는 AI에 집중하기

**준비 완료 기준: 내 프로젝트에서 모델 답변을 받고, Python에서 같은 모델을 호출할 수 있습니다.**

준비는 7시간에 포함하지 않습니다. 설치·리소스 준비에 **45~75분을 별도로 확보**하고, 조직의 권한 승인은 더 일찍 요청하세요. 혼자 학습한다면 아래의 “운영 담당자” 역할도 본인이 수행합니다.

## 1. 준비할 화면과 파일

| 작업할 곳 | 여기서 하는 일 |
|---|---|
| 이 가이드 | 다음 단계 읽기 |
| [Foundry 포털](https://ai.azure.com) | 프로젝트, 모델, 에이전트, 평가, trace |
| VS Code 등의 편집기 | 이 폴더 열기, `.env` 수정, 결과 읽기 |
| **이 폴더에서 연 터미널** | `python lab.py ...` 명령 실행 |
| Excel 또는 CSV 편집기 | `review.csv`의 사람 검토 결과 입력 |

**지침은 포털의 Instructions에, 질문은 채팅 입력창에, `python` 명령은 터미널에 넣습니다.** 서로 바꿔 붙여 넣지 마세요.

이 폴더 전체를 사용합니다. 기본 경로의 SDK와 원본 v1.2의 `.env`를 섞어 쓰지 않습니다. v1.2 기능은 [전용 호환 환경](features/README.md)에서 유지합니다. [워크북](../worksheets/workbook.md)은 개인 사본으로 저장하세요.

## 2. 운영 담당자: Azure 환경 준비

참가자는 담당자에게 준비된 프로젝트 정보를 받습니다. 준비된 환경을 받았다면 새 리소스를 중복 생성하지 않습니다.

### 2-1. Foundry 프로젝트 만들기

1. 사용할 구독, 비용 책임자, 허용 리전, 수업 후 삭제 범위를 정합니다.
2. [Foundry 포털](https://ai.azure.com)에 로그인합니다. **New Foundry** 전환이 보이면 현재 환경을 선택합니다.
3. 왼쪽 위 프로젝트 선택 영역 → **Create new project**를 선택합니다.
4. 프로젝트 이름을 정합니다. 예: `foundry-lab-01`.
5. 고급 옵션에서 **실습 전용 리소스 그룹**, Foundry 리소스, 승인된 리전을 확인합니다.
6. 생성 후 프로젝트의 **Overview / Project details**에서 프로젝트 Endpoint를 복사합니다.

예시 형식:

```text
https://<리소스이름>.services.ai.azure.com/api/projects/<프로젝트이름>
```

포털에 표시된 값을 그대로 씁니다. `.openai.azure.com`의 모델 Endpoint나 구독 ID를 넣지 않습니다. 계정에 따라 `*.ai.azure.com/api/projects/...` 형식이 표시될 수도 있습니다.

권장 구성은 **참가자별 프로젝트, 참가자별 고유 에이전트 이름**입니다. 하나의 Foundry 리소스에서 프로젝트를 나누면 모델 배포와 할당량은 공유될 수 있습니다. 프로젝트가 다르다고 모델 호출 한도까지 독립인 것은 아닙니다.

### 2-2. 작은 모델 하나 배포하기

1. **Discover → Models** 또는 **Model catalog**에서 모델을 찾습니다.
2. 기본 후보는 **`gpt-4.1-mini`**입니다. 빠른 짧은 답변, Responses API, 함수 호출을 중심으로 선택했습니다.
3. 모델 상세의 지원 기능·리전·수명 주기를 확인합니다. **최신 최고 성능 모델을 무조건 고르는 수업이 아닙니다.**
4. **Deploy / Use this model**을 열고 배포 이름을 **`workshop-chat`**으로 지정합니다.
5. 조직이 허용하는 종량제 Standard 계열 배포를 선택합니다. Global Standard는 데이터 처리 위치 정책에 맞는 경우에만 선택합니다. 실습에 Provisioned/PTU 계약은 필요하지 않습니다.
6. 배포가 준비되면 Playground에서 “한국어로 인사 한 문장”을 전송합니다.

`gpt-4.1-mini`를 사용할 수 없다면 **수업 전에** Responses, File Search, 함수 호출이 함께 동작하는 모델로 변경합니다. `gpt-5-mini`는 공식 File Search 예제의 다른 후보지만, 구독의 배포 가능 여부와 평가 모델 지원은 별도 점검해야 합니다. 코드의 배포 별칭은 계속 `workshop-chat`으로 유지할 수 있습니다.

**카탈로그에 있다는 사실은 내 구독의 리전·할당량·도구 지원이 확인되었다는 뜻이 아닙니다.** File Search 성공까지 확인하는 절차는 [강사 사전 점검](instructor.md)에 있습니다.

### 2-3. 필요한 권한만 부여하기

| 할 일 | 준비할 권한/접근 |
|---|---|
| 프로젝트에서 에이전트·데이터 작업 | 프로젝트의 **Foundry User** 또는 같은 작업을 허용하는 조직 역할 |
| Foundry 리소스·모델 배포 생성 | 담당자의 해당 범위 관리 권한. 일반 참가자에게 구독 Owner를 주지 않음 |
| 역할 부여 | 역할 할당 권한이 있는 담당자가 수행. 리소스 생성 권한과 별개 |
| 연결한 자체 Storage에 업로드 | 필요할 때 해당 Storage의 **Storage Blob Data Contributor** |
| trace 조회 | 연결된 Application Insights/Log Analytics의 조회 권한. 공식 문서의 **Log Analytics Reader** 등 확인 |

역할 이름 변경이 반영되지 않은 화면에서는 **Azure AI User** 등 이전 이름이 보일 수 있습니다. Foundry User와 같은 역할인지 [공식 RBAC 문서](https://learn.microsoft.com/azure/foundry/concepts/rbac-foundry)를 대조하세요. **Azure Contributor만 있다고 모든 데이터 작업이 되는 것은 아닙니다.**

### 2-4. 포털 평가와 trace 미리 켜 두기

**Lab 06도 필수 실습입니다. 첫날 수업 중에 연결·권한 문제를 해결하려고 미루지 않습니다.**

1. 프로젝트의 **Agents → Traces → Connect**에서 준비한 Application Insights를 연결합니다.
2. Connect가 없으면 **Manage → Project details → Connected resources → Add connection → Application Insights** 경로를 확인합니다.
3. 참가자가 새 trace를 조회할 수 있는지 확인합니다. 연결만 했다고 조회 권한까지 부여되지는 않습니다.
4. **Evaluation → Create → Dataset → Individual turns** 흐름을 확인합니다.
5. AI-assisted 평가에 필요한 **Azure OpenAI 연결과 GPT judge 모델**을 준비합니다. 기존 `workshop-chat` 배포를 judge 선택기에서 사용할 수 있으면 재사용합니다. 안 보이면 담당자가 평가용 연결/지원 배포를 준비합니다.
6. 작은 실제 응답 데이터로 **Relevance 하나**가 완료되는지 확인합니다.

프로젝트를 Private Endpoint로 제한했다면 참가자 PC가 승인된 네트워크 경로에 있어야 합니다. 접근 문제를 해결하려고 방화벽이나 조직 정책을 임의로 해제하지 않습니다.

공식 절차: [프로젝트 생성](https://learn.microsoft.com/azure/foundry/how-to/create-projects) · [trace 연결](https://learn.microsoft.com/azure/foundry/observability/how-to/trace-agent-setup) · [포털 평가](https://learn.microsoft.com/azure/foundry/how-to/evaluate-generative-ai-app).

## 3. 참가자: Python 준비

**권장 Python 3.13, 지원 범위 3.11~3.14.** Python과 [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli)를 준비합니다. 패키지는 프로젝트 안의 가상 환경에 설치합니다. Docker, Node.js, 별도 Search 서비스 직접 구축, azd 설치는 이 수업에 필요하지 않습니다.

VS Code에서 **이 폴더를 열고 새 터미널**을 만듭니다. `lab.py`와 `requirements.txt`가 보이는 폴더여야 합니다.

### macOS / Linux

```bash
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

이미 Python 3.11~3.14의 다른 버전을 쓰면 첫 명령의 `python3.13`만 설치된 실행 파일 이름으로 바꿉니다.

### Windows PowerShell

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

회사 정책 때문에 활성화가 차단되면 보안 정책을 낮추지 마세요. 이후 모든 `python ...`을 `.\.venv\Scripts\python.exe ...`로 실행하면 활성화 없이 같은 가상 환경을 사용할 수 있습니다.

**새 터미널을 열 때마다 가상 환경을 다시 활성화합니다.** `python --version`으로 버전을 확인하세요.

## 4. 참가자: 내 설정 세 개 넣기

`.env.example`을 **`.env`라는 이름으로 복사**합니다. 이미 `.env`가 있으면 덮어쓰지 말고 기존 값을 확인합니다.

```text
FOUNDRY_PROJECT_ENDPOINT=https://내리소스.services.ai.azure.com/api/projects/내프로젝트
FOUNDRY_MODEL_DEPLOYMENT_NAME=workshop-chat
FOUNDRY_AGENT_NAME=trip-coach-01
```

- 위 Endpoint는 형식 설명입니다. 실제 포털 값을 넣습니다.
- `trip-coach-01`은 예시입니다. 담당자가 정한 본인 실습 ID로 고유하게 만듭니다. 영문 소문자·숫자·하이픈만 사용합니다.
- 모델명과 배포 이름을 구분합니다. 모델명이 `gpt-4.1-mini`여도 코드가 호출할 이름은 `workshop-chat`입니다.
- API key는 넣지 않습니다. 로컬 예제는 **Azure CLI에 로그인한 사용자**로 인증합니다.
- 셸에 같은 환경변수가 이미 있으면 셸 값이 `.env`보다 우선합니다. 예전 실습 값이 남았는지 확인합니다.

인증합니다. 아래 구독 자리에 담당자가 알려 준 실제 구독 이름 또는 ID를 넣습니다.

```bash
az login
az account set --subscription "사용할-구독-이름-또는-ID"
```

브라우저와 CLI에 서로 다른 계정으로 로그인하지 않도록 주의하세요. 조직의 정상적인 로그인·MFA 절차를 따릅니다.

## 5. 준비 확인: 로컬과 Azure를 따로 확인

```bash
python lab.py doctor
```

기대 표시:

```json
{"local_setup":"PASS","azure_tested":false,"agent_tested":false}
```

실제 출력에는 패키지 목록도 있습니다. **이 명령은 Azure 인증·모델·File Search를 시험한 것이 아닙니다.**

담당자가 모델 호출 비용을 허용한 후 한 번 실행합니다.

```bash
python lab.py doctor --live
```

`azure_tested: true`와 실제 응답 ID, 답변이 있어야 합니다. 여전히 `agent_tested: false`입니다. 모델 호출 성공과 파일 검색·도구 성공은 서로 다릅니다.

## 준비 완료 체크

- [ ] 프로젝트, 구독, 모델 배포 이름을 기록했다.
- [ ] `doctor`와 `doctor --live`가 각각 무엇을 확인했는지 설명할 수 있다.
- [ ] 담당자가 이 환경에서 File Search, 함수 호출, 포털 평가, trace를 사전 실행했다.
- [ ] 내 에이전트 이름이 다른 사람과 겹치지 않는다.
- [ ] CSV를 열고 저장할 편집기가 있다.
- [ ] 비용 책임자, 허용 예산, 수업 후 삭제 책임자를 알고 있다.
- [ ] 실제 회사 문서나 개인정보 대신 **동봉한 가상 문서만** 사용한다.

Azure 권한이 없으면 로컬 함수와 문서를 학습할 수 있지만, 이를 Foundry 실습 완료로 기록하지 않습니다. [문제 해결](troubleshooting.md) 후 본인 환경 또는 담당자가 허용한 짝 실습 환경에서 재개하세요.

**다음 실습 → [Lab 01. Foundry 이해와 첫 성공](01-foundry.md)**
