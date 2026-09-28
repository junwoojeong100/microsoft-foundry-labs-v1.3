# 00. 내 실습 환경 만들기

**완료 목표:** 내 Azure 구독에 Foundry 프로젝트와 모델 배포를 만들고, 데이터 작업 권한과 로컬 실행 환경을 직접 준비합니다.

출발점은 **Microsoft Entra ID 계정 + Azure 구독 + 활성 구독 Owner**입니다. 이 장에서 다른 사람이 준비한 Endpoint나 Search를 받지 않습니다. 새 리소스와 모델 호출에는 비용이 발생할 수 있습니다.

## 1. 내 권한 확인

1. [Azure 포털](https://portal.azure.com)에 로그인합니다.
2. **Subscriptions → 사용할 구독 → Access control (IAM) → View my access**에서 Owner를 확인합니다.
3. PIM의 “할당 가능” 상태라면 조직의 정상 절차로 활성화합니다. 활성 역할과 자격만 있는 상태는 다릅니다.
4. 구독 ID와 연결된 Tenant ID를 개인 워크북에 기록합니다.
5. 조직의 허용 리전·서비스·네트워크 정책을 확인합니다. Owner도 관리 그룹의 거부 정책을 우회할 수 없습니다.

**중요:** 구독 Owner와 Entra Global Administrator는 다릅니다. 이 과정의 Azure 리소스 준비에는 디렉터리 전체 관리자나 새 client secret이 필요하지 않습니다. GitHub OIDC workflow의 실습 권한은 14장에서 다룹니다.

## 2. 실습 파일과 개발 도구

받은 **실습 ZIP을 압축 해제**하거나, 접근 권한이 있는 이 저장소를 복제합니다. 코드와 데이터가 모두 포함되어 있으므로 추가 저장소를 받지 않습니다. ZIP으로 시작하면 GitHub 계정과 Git 설치는 필수가 아닙니다.

PC에는 다음이 필요합니다. 회사 단말의 설치 제한은 Azure Owner로 해결되지 않으므로 승인된 개발 환경을 사용하세요.

| 도구 | 설치와 확인 |
|---|---|
| Python **3.13** | [Python](https://www.python.org/downloads/) 설치. macOS/Linux `python3.13 --version`, Windows `py -3.13 --version` |
| Azure CLI | [공식 설치](https://learn.microsoft.com/cli/azure/install-azure-cli) 후 `az version` |
| Azure Developer CLI | [azd 설치](https://learn.microsoft.com/azure/developer/azure-developer-cli/install-azd) 후 `azd version` |
| 편집기 | VS Code 등으로 **v1.5 폴더 전체** 열기 |

터미널의 현재 폴더에 `README.md`, `scripts/`, `curriculum.json`이 보여야 합니다.

이미 다른 Python으로 만든 `.venv`나 개인 실습 상태가 있다면 덮어쓰지 않습니다. 기존 폴더를 보관하고 **새 폴더에 ZIP을 풀어 시작**하세요.

### macOS / Linux

```bash
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

### Windows PowerShell

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

PowerShell 활성화가 차단되면 시스템 정책을 낮추지 않습니다. 이후 모든 `python ...`을 `.\.venv\Scripts\python.exe ...`로 실행할 수 있습니다.

이 단계는 로컬 패키지만 설치합니다. **Azure 리소스 생성·로그인·구독 변경은 하지 않습니다.** 이미 개인 설정이나 실행 결과가 있는 폴더를 덮어쓰지 말고 보관하세요.

```bash
python scripts/workshop.py doctor
```

`documents: 6`, `dev_cases: 6`, `holdout_cases: 4`, `azure_tested: false`, `result: PASS`를 확인합니다. 아직 Azure 연결 시험은 아닙니다.

**새 터미널마다 `.venv`를 활성화**합니다. 이후 모든 명령은 README.md가 있는 폴더에서 실행합니다.

## 3. 로그인과 이름 계획

```bash
az login
az account list --output table
azd auth login
```

조직의 정상 MFA 절차를 따릅니다. 브라우저·CLI·azd의 테넌트가 같은지 확인하세요. 이 가이드의 설정 수집기는 구독 ID를 명시하므로 기본 구독을 자동 변경하지 않습니다.

본인의 고유 접두사를 정합니다. 예시는 그대로 공유하지 마세요.

| 용도 | 이름 예시 |
|---|---|
| 내 자산을 구분할 접두사 | `lab-jw-0927` |
| 리소스 그룹 | `rg-mf15-jw-0927` |
| Foundry 프로젝트 | `mf15-jw-0927-project` |
| Foundry 리소스 | 포털이 생성한 실제 이름을 기록 |
| 처음 배포할 모델의 별칭 | `workshop-chat` |

접두사는 `lab-`로 시작하는 소문자·숫자·하이픈, 최대 32자로 정합니다. 모든 자산을 내 것과 구분하는 이름이므로 실습 도중 바꾸지 않습니다.

## 4. 실습 전용 리소스 그룹 만들기

1. Azure 포털 **Resource groups → Create**.
2. 내 Owner 구독과 새 그룹 이름을 선택합니다.
3. 리전을 정합니다. **Sweden Central은 시작 후보**이지 모든 모델·기능의 제공 보장이 아닙니다.
4. [Foundry 리전](https://learn.microsoft.com/azure/foundry/reference/region-support)과 [Search 리전](https://learn.microsoft.com/azure/search/search-region-support)에서 이후 사용할 Hosted, Semantic ranker, Agentic retrieval의 지원을 확인합니다.
5. `workshop=foundry-v1.5` 같은 비밀 아닌 태그를 달고 생성합니다.

이 그룹에는 실습 자원만 넣습니다. 기존 업무용 그룹을 사용하면 마지막에 그룹 전체를 삭제할 수 없습니다.

CLI로 만들려면 아래의 구독 ID와 이름을 본인 값으로 바꿉니다. 포털에서 이미 만든 그룹은 다시 만들 필요가 없습니다.

```bash
az group create --subscription "내-구독-ID" --name "rg-mf15-my-lab" --location swedencentral --tags workshop=foundry-v1.5 lifecycle=retain
```

`lifecycle=retain`은 보존 의사를 기록하는 태그이지 삭제 방지 잠금은 아닙니다. 자원을 남길 경우 [보존 모드](15-capstone-cleanup.md#보존-모드로-진행할-때)를 적용합니다.

구독/그룹의 **Cost Management → Budgets**에서 본인의 실습 예산 알림을 설정할 수 있습니다. 금액은 현재 가격과 자신의 예산으로 정합니다. **알림은 자동 사용 중지나 환불 보장이 아닙니다.**

## 5. Foundry 프로젝트 만들기

1. [Foundry](https://ai.azure.com)를 엽니다. **New Foundry** 전환이 보이면 현재 포털을 선택합니다.
2. 왼쪽 위 프로젝트 선택 영역 → **Create new project**.
3. 프로젝트 이름을 입력하고 **Advanced options**를 엽니다.
4. 사용할 구독, **방금 만든 실습 그룹**, 확인한 리전을 지정하고 생성합니다.
5. Foundry 리소스 이름은 자동 생성될 수 있습니다. 예시 이름을 추측하지 말고 실제 이름을 기록합니다.
6. 프로젝트 홈에서 **Project endpoint**를 복사합니다.

형식은 `https://<실제-domain>.services.ai.azure.com/api/projects/<실제-project>`입니다. 모델의 `.openai.azure.com` Endpoint와 다릅니다. 고정 실행 코드가 받는 형식과 다른 URL만 보이면 Libraries/API 영역에서 프로젝트 Endpoint를 다시 확인하고, 도메인을 임의로 바꾸지 않습니다.

Azure 포털에서 **프로젝트 리소스 → JSON View**를 열고 `id`도 복사합니다.

```text
/subscriptions/.../resourceGroups/.../providers/Microsoft.CognitiveServices/accounts/.../projects/...
```

부모 Foundry 계정 ID가 아니라 **`/projects/...`까지 포함한 ID**입니다.

### 같은 준비를 CLI로 할 때

포털 경로 대신 사용할 수 있습니다. `--assign-identity`와 `--allow-project-management true`를 빠뜨리지 않습니다. 이름은 전역에서 고유해야 하며 모든 명령에 같은 구독·그룹·리전을 지정합니다.

```bash
az cognitiveservices account create --subscription "내-구독-ID" --resource-group "rg-mf15-my-lab" --name "내-고유-foundry-이름" --custom-domain "내-고유-foundry-이름" --kind AIServices --sku S0 --location swedencentral --assign-identity --allow-project-management true
az cognitiveservices account project create --subscription "내-구독-ID" --resource-group "rg-mf15-my-lab" --name "내-고유-foundry-이름" --project-name "my-project" --location swedencentral
```

CLI 생성은 사용자·프로젝트의 **Foundry User 역할을 자동으로 보장하지 않습니다.** 7절에서 두 주체의 역할을 반드시 확인합니다.

## 6. 첫 모델 배포

1. Foundry **Discover → Models**에서 **`gpt-6-sol`**을 찾습니다.
2. 버전 **`2026-09-22`**, 지원 기능·리전·할당량을 확인합니다. 첫 응답부터 에이전트·도구 실습까지 Sol로 직접 진행합니다. [모델 역할과 기준](model-selection.md).
3. **Deploy / Use this model**에서 배포 이름을 `workshop-chat`으로 지정합니다.
4. 본인 정책에 맞는 종량제 Standard 계열을 고릅니다. Global Standard는 글로벌 처리 정책이 허용할 때만 선택합니다. PTU 계약은 필요하지 않습니다.
5. 상태가 **Succeeded**가 될 때까지 기다립니다. 실제 기반 모델·버전·유형·리전을 기록합니다.

할당량이 없거나 모델이 제공되지 않으면 **Create를 반복하지 않습니다**. 모델 배포 화면/Quota 메뉴에서 현재 가용성을 확인하고 필요한 증가를 요청하거나 준비될 때까지 멈춥니다. 고정 리전과 Sol 선택을 유지하며, 다른 모델로 바꿔 성공처럼 표시하지 않습니다.

기본 답변 모델은 Sol입니다. 02의 GPT-6 Luna 비교는 선택 사항이며, 07의 judge는 **GPT-5.5 / 2026-04-24**입니다. IQ Chat의 별도 `gpt-5.6-luna`와 Optimizer는 해당 장에서만 준비합니다.

같은 배포 이름으로 다른 모델을 이미 사용하고 있다면 **그 모델을 바꾸거나 삭제하지 않습니다**. 실제 Sol 배포의 기존 이름을 명시적으로 재사용하거나 새 고유 이름을 선택합니다. 설정 도구는 실제 모델/버전을 확인합니다. 기존 agent·평가를 새 모델의 결과로 재사용하지 마세요.

## 7. 데이터 접근 역할 확인

Azure 포털의 **실제 Foundry 리소스 → IAM → Role assignments**를 봅니다.

| 주체 | 역할 | 범위 |
|---|---|---|
| 내 로그인 사용자 | **Foundry User** | 이 실습 Foundry 리소스 |
| 이 프로젝트의 관리 ID | **Foundry User** | 같은 Foundry 리소스 |

포털이 이미 부여했다면 중복 생성하지 않습니다. 없으면 **Add role assignment → Foundry User → Members**에서 해당 주체를 선택해 부여합니다. 이전 이름 **Azure AI User**가 보일 수 있으며 역할 ID는 `53ca6127-db72-4b80-b1b0-d745d6d5456d`입니다.

관리 ID는 내 계정이나 프로젝트 이름 문자열이 아닙니다. 프로젝트 리소스 **JSON View → identity.principalId**로 구분합니다. Identity가 없다면 프로젝트의 관리 ID 설정을 확인한 뒤 계속합니다.

구독 Owner의 리소스 관리 권한이 데이터 작업 권한을 대신하지 않습니다. 앱 등록이나 client secret은 만들지 않습니다.

## 8. 실제 값으로 설정 자동 수집

따옴표 안 세 곳과 접두사를 본인의 값으로 바꿉니다.

```bash
python scripts/selfstudy.py configure --project-id "실제-프로젝트-ARM-ID" --endpoint "실제-프로젝트-Endpoint" --deployment "workshop-chat" --expected-model gpt-6-sol --prefix "lab-jw-0927"
```

**기존 실습을 이어 할 때:** `workshop-compare`가 이미 Sol이라면 위 새 환경 명령 대신 **같은 프로젝트·Endpoint·prefix**로 다음처럼 실제 별칭을 선택합니다. 기존 `workshop-chat`의 모델은 변경하지 않습니다.

```bash
python scripts/selfstudy.py configure --project-id "실제-프로젝트-ARM-ID" --endpoint "실제-프로젝트-Endpoint" --deployment workshop-compare --expected-model gpt-6-sol --prefix "기존-lab-접두사"
```

예전에 사용한 결과 label·파일·agent 버전은 그대로 보관합니다. 새로운 모델/평가 조건에는 새 이름과 label을 사용합니다. [기존 별칭 안내](model-selection.md#기존-배포를-그대로-재사용하기).

이 도구는 Azure CLI로 **구독·프로젝트·계정·배포를 읽기만** 합니다. ID/Endpoint 일치와 배포 상태를 확인한 뒤 다음을 기록합니다.

- `.env`: SDK가 사용할 설정 한 벌.
- `.selfstudy/azure.json`: 실제 리소스 ID, 관리 ID, 리전, 확인 시점.

토큰·비밀번호·API key는 저장하지 않습니다. 기존 다른 프로젝트의 설정은 덮어쓰지 않습니다. `management_metadata_read: true`, `model_invoked: false`를 구분하세요.

새 설정은 **reasoning `low`, 출력 상한 `32768`**을 사용합니다. 값에는 reasoning 토큰도 포함됩니다. 예전 개인 설정을 재사용한다면 값을 직접 확인하고 다음과 같이 맞춘 뒤 새 agent·실험 label을 사용합니다.

```bash
python scripts/selfstudy.py set WORKSHOP_REASONING_EFFORT low
python scripts/selfstudy.py set WORKSHOP_MAX_OUTPUT_TOKENS 32768
```

```bash
python scripts/selfstudy.py values
python scripts/workshop.py doctor --cloud
```

올바른 구독·테넌트·배포가 표시되는지 확인합니다. `doctor --cloud`도 추론 시험이 아니라 메타데이터/인증 확인입니다.

**다음 장에서 Sol의 첫 실제 요청을 통과한 뒤 agent를 만듭니다.** 모델 배포의 `Succeeded`만으로 모든 도구와 API 경로가 지원된다고 판단하지 않습니다. 오류는 [문제 해결](troubleshooting.md)에서 원래 응답과 함께 확인합니다.

## 9. 역할의 실제 명령이 필요할 때

Azure 포털에서 본인 사용자 Object ID를 확인하거나 다음 읽기 명령을 사용합니다.

```bash
az ad signed-in-user show --query id --output tsv
python scripts/selfstudy.py roles --user-object-id "내-사용자-Object-ID"
```

`roles`는 **필요 역할의 명령을 출력할 뿐 실행하지 않습니다.** Portal IAM과 비교하고 없는 역할만 직접 실행하세요. 기존 Owner를 다른 계정에 주거나 권한을 구독 전체로 넓히지 않습니다.

## 완료 확인

- [ ] 내 전용 그룹·Foundry 프로젝트·모델을 만들었다.
- [ ] 내 사용자와 프로젝트 관리 ID의 데이터 역할을 확인했다.
- [ ] 설정을 한 곳에 저장했고 실제 값을 다시 읽었다.
- [ ] 비용과 추가 권한의 경계를 안다.

막히면 [문제 해결](troubleshooting.md)의 해당 오류부터 해결합니다. 중단한다면 지금 [정리](15-capstone-cleanup.md)를 확인합니다.

**다음 → [01. Foundry와 첫 모델 응답](01-foundry.md)**
