# 00. 내 실습 환경 만들기

[English](en/00-setup.md) | **한국어** · [전체 과정](../README.ko.md#진행-순서) · [진행 도움말](checkpoints.md)

**완료 목표:** 내 Azure 구독에 Foundry 프로젝트와 모델 배포를 만들고, 데이터 작업 권한과 로컬 실행 환경을 직접 준비합니다.

**시작 조건:** Microsoft Entra ID 계정 + Azure 구독 + 활성 구독 Owner. 다른 사람이 준비한 Endpoint나 Search는 필요하지 않습니다.

**실행 위치:** Azure·Foundry 포털, 편집기, 실습 폴더의 터미널.

> [!IMPORTANT]
> Azure 자원은 **North Central US**(`northcentralus`)에 준비합니다. 처음에는 **포털 경로만** 따라가고, 접힌 CLI 대안은 생략하세요. 새 자원과 모델 호출에는 비용이 발생할 수 있습니다.

<a id="chapter-map"></a>

**진행 지도**

| 단계 | 확인할 결과 |
|---|---|
| [1. 권한 확인](#1-내-권한-확인) | 사용할 구독의 활성 Owner |
| [2. 파일·도구 설치](#2-실습-파일과-개발-도구) | Python 3.13 환경, 로컬 doctor `PASS` |
| [3. 로그인·이름 계획](#3-로그인과-이름-계획) | 같은 테넌트, 내 고유 접두사 |
| [4. 전용 그룹 생성](#4-실습-전용-리소스-그룹-만들기) | 실습 자원만 넣을 그룹 |
| [5. 프로젝트 생성](#5-foundry-프로젝트-만들기) | Project endpoint와 전체 프로젝트 ID |
| [6. Sol 배포](#6-첫-모델-배포) | 실제 모델·버전과 `Succeeded` |
| [7. 데이터 역할 확인](#7-데이터-접근-역할-확인) | 사용자·프로젝트 관리 ID의 역할 |
| [8. 설정 수집](#8-실제-값으로-설정-자동-수집) | 저장된 내 설정과 인증·메타데이터 확인 |
| [9. 역할 명령 생성 — 필요할 때만](#9-역할의-실제-명령이-필요할-때) | 미부여 역할의 명령 계획 |
| [완료 확인](#완료-확인) | 01장의 첫 모델 호출을 시작할 준비 |

문서의 이름은 예시입니다. 검증 보고서의 리소스 그룹·ID를 내 설정으로 복사하지 않습니다. 기존 환경을 재개한다면 [재개 방법](checkpoints.md#다음-날-재개하기)부터 확인합니다.

## 1. 내 권한 확인

1. [Azure 포털](https://portal.azure.com)에 로그인합니다.
2. **Subscriptions → 사용할 구독 → Access control (IAM) → View my access**에서 Owner를 확인합니다.
3. PIM의 “할당 가능” 상태라면 조직의 정상 절차로 활성화합니다. 활성 역할과 자격만 있는 상태는 다릅니다.
4. 같은 구독의 **Overview → Subscription ID**, **Properties → Directory/Tenant ID** 위치를 확인합니다. 필요한 값은 해당 화면에서 명령에 직접 복사하며, 8절의 설정 도구가 다시 수집·저장합니다.
5. 조직의 허용 리전·서비스·네트워크 정책을 확인합니다. Owner도 관리 그룹의 거부 정책을 우회할 수 없습니다.

**중요:** 구독 Owner와 Entra Global Administrator는 다릅니다. 이 과정의 Azure 리소스 준비에는 디렉터리 전체 관리자나 새 client secret이 필요하지 않습니다. GitHub OIDC workflow의 실습 권한은 14장에서 다룹니다.

## 2. 실습 파일과 개발 도구

### 실습 폴더 열기

1. 받은 **실습 ZIP**을 압축 해제합니다. ZIP이 없다면 [이 저장소](https://github.com/junwoojeong100/microsoft-foundry-labs-v1.5)의 **Code → Download ZIP**을 사용합니다. 비공개 저장소라면 접근 권한이 필요합니다.
2. 압축을 푼 폴더 중 **`README.md`, `scripts/`, `curriculum.json`이 함께 있는 폴더**를 찾습니다. 압축파일 안이나 그 상위 폴더에서 실행하지 않습니다.
3. 편집기가 없다면 [VS Code](https://code.visualstudio.com/download)를 먼저 설치합니다. **File → Open Folder**로 그 폴더 전체를 열고, **Terminal → New Terminal**로 명령 입력 창을 엽니다.

**가이드 읽기:** 브라우저에서 읽거나 VS Code의 **Open Preview**로 엽니다. 단축키는 macOS `Cmd+Shift+V`, Windows/Linux `Ctrl+Shift+V`입니다. 표·링크·접힌 선택 절이 보이는 상태로 읽으세요.

**명령 실행:** 미리보기 화면이 아니라 **터미널**에 붙여 넣습니다.

코드와 데이터가 모두 포함되어 있으므로 추가 저장소는 필요하지 않습니다. 전달받은 ZIP으로 시작하면 GitHub 계정과 Git도 필요하지 않습니다.

<details>
<summary>선택: Git이 이미 설치되어 있다면 ZIP 대신 복제</summary>

```bash
git clone https://github.com/junwoojeong100/microsoft-foundry-labs-v1.5.git
```

**복제한 폴더로 이동**

```bash
cd microsoft-foundry-labs-v1.5
```

복제한 폴더를 편집기에서 엽니다. ZIP 경로와 둘 다 수행할 필요는 없습니다.

</details>

### 필수 도구 설치

PC에는 다음이 필요합니다. 회사 단말의 설치 제한은 Azure Owner로 해결되지 않으므로 승인된 개발 환경을 사용하세요.

| 도구 | 설치와 확인 |
|---|---|
| Python **3.13** | [Python](https://www.python.org/downloads/)에서 **3.13.x 버전**을 선택해 설치. macOS/Linux `python3.13 --version`, Windows `py -3.13 --version` |
| Azure CLI | [공식 설치](https://learn.microsoft.com/cli/azure/install-azure-cli) 후 `az version` |
| Azure Developer CLI | [azd 설치](https://learn.microsoft.com/azure/developer/azure-developer-cli/install-azd) 후 `azd version` |
| 편집기 | VS Code 등으로 **v1.5 폴더 전체** 열기 |

설치 후 편집기를 다시 열고 새 터미널에서 위 버전 명령을 확인합니다. `command not found` 또는 “인식되지 않는 명령”이 나오면 다음 단계로 가지 않습니다.

Python의 최신 버전이 아니라 **이 실습의 3.13 환경**이 필요합니다.

> [!NOTE]
> **Windows에서는 PowerShell로 준비할 수 있습니다.** 다만 05장 5절의 로컬 SDK 중단·재개와 추가 실험은 macOS/Linux(승인된 WSL 포함) 전용입니다. 실행기가 POSIX `fcntl` 잠금을 사용하므로 Windows Python에서는 동작하지 않습니다.

해당 절도 수행하려면 승인된 WSL/Linux의 **별도 소스 사본**에서 Linux Python 설치와 doctor까지만 준비합니다. 그 로컬 실험에는 Azure 설정·로그인이 필요하지 않습니다.

Windows의 `.venv`나 개인 Azure 상태를 WSL/Linux로 복사하지 않습니다.

현재 폴더와 파일은 macOS/Linux의 `pwd`·`ls`, PowerShell의 `Get-Location`·`Get-ChildItem`으로 확인합니다.

코드 상자의 `bash`/`powershell` 표시는 입력할 명령이 아닙니다. **한 줄씩 실행하고 오류가 나면 다음 줄로 넘어가지 않습니다.**

이미 다른 Python으로 만든 `.venv`나 개인 실습 상태가 있다면 덮어쓰지 않습니다. 기존 폴더를 보관하고 **새 폴더에 ZIP을 풀어 시작**하세요.

**처음 시작한다면 다음 접힌 절은 건너뛰고, 본인 OS의 설치 명령 한 묶음만 실행합니다.** `python --version`에서 **Python 3.13.x**를 확인한 뒤에만 다음 설치 명령으로 갑니다.

**내 OS로 이동:** [macOS / Linux](#macos--linux) · [Windows PowerShell](#windows-powershell) → [모든 OS 공통 확인](#모든-os-설치-결과-확인)

<details>
<summary>이전 환경이 있을 때만: 다른 프로젝트로 새로 시작하기</summary>

### 새 프로젝트에서 이전 상태를 인수하지 않기

1. 이전 환경은 [15의 중지·보관 절차](15-capstone-cleanup.md#4-먼저-실행-중인-것을-멈추기)를 적용합니다. `.env`, `.selfstudy`, `outputs/`, `.build/`와 소유 기록은 비공개로 보존합니다.
2. **새 폴더에 소스만** 압축 해제하거나 복제하고 새 터미널을 엽니다. 이전 설정·결과·azd 환경을 새 프로젝트의 활성 상태로 복사하지 않습니다.
3. 새 프로젝트·접두사와 사용하지 않은 결과 label을 정합니다. label을 바꾸면 collect/evaluate/compare/verify의 참조도 모두 맞춥니다.
4. 기존 자원 삭제는 별도의 결정입니다. 보고서의 삭제 이력을 따라 다른 그룹을 삭제하거나, 소유권 파일을 편집해 프로젝트 혼합 검사를 우회하지 않습니다.

**같은 checkout의 `configure`, `set`, `models`, `resource`, `bind-matrix`는 한 번에 하나씩 실행합니다.** 동시에 쓰면 설정 파일 갱신이 충돌할 수 있습니다. 병렬 실험은 별도 workspace와 소유권 기록을 사용하세요.

</details>

### macOS / Linux

**1. 새 가상 환경 만들기**

```bash
python3.13 -m venv .venv
```

**2. 가상 환경 활성화**

```bash
source .venv/bin/activate
```

**3. Python 3.13 확인**

```bash
python --version
```

**`Python 3.13.x`가 보여야 다음으로 갑니다.** 다른 버전이 나오면 지금 설치하지 말고 가상 환경부터 확인합니다.

**4. 필수 패키지 설치**

```bash
python -m pip install -r requirements.txt
```

**5. 설치된 패키지 검사**

```bash
python -m pip check
```

### Windows PowerShell

**1. 새 가상 환경 만들기**

```powershell
py -3.13 -m venv .venv
```

**2. 가상 환경 활성화**

활성화가 차단되면 시스템 정책을 낮추지 않습니다. 아래 활성화 대신, 이후 모든 `python ...`을 `.\.venv\Scripts\python.exe ...`로 실행할 수 있습니다.

```powershell
.\.venv\Scripts\Activate.ps1
```

**3. Python 3.13 확인**

```powershell
python --version
```

**`Python 3.13.x`가 보여야 다음으로 갑니다.** 다른 버전이 나오면 지금 설치하지 말고 가상 환경부터 확인합니다.

**4. 필수 패키지 설치**

```powershell
python -m pip install -r requirements.txt
```

**5. 설치된 패키지 검사**

```powershell
python -m pip check
```

### 모든 OS: 설치 결과 확인

이 단계는 로컬 패키지만 설치합니다. **Azure 리소스 생성·로그인·구독 변경은 하지 않습니다.** 이미 개인 설정이나 실행 결과가 있는 폴더를 덮어쓰지 말고 보관하세요.

```bash
python scripts/workshop.py doctor
```

**확인:** 다음 출력이 맞아야 합니다. 아직 Azure 연결 시험은 아닙니다.

| 출력 | 기대 값 |
|---|---|
| 패키지 검사 | `No broken requirements found.` |
| `documents` / `dev_cases` / `holdout_cases` | `6` / `6` / `4` |
| `azure_tested` / `result` | `false` / `PASS` |

holdout은 개수만 확인하며 문항·정답 파일은 15장까지 열지 않습니다.

**새 터미널마다 `.venv`를 활성화**합니다. 이후 모든 명령은 README.md가 있는 폴더에서 실행합니다.

별도 기록 파일을 만들지 않고 다음 절로 진행합니다. 설정은 8절에서 `.env`와 `.selfstudy/azure.json`에 저장되고, 이후 결과는 각 명령에 표시된 파일에서 확인합니다. 필요한 폴더도 도구가 생성합니다.

`.selfstudy`, `.env`, `.build`처럼 점으로 시작하는 이름은 숨김 파일/폴더일 수 있습니다. 편집기의 파일 탐색기에서 확인하고 앞의 점을 빼지 않습니다.

> [!NOTE]
> **`.env`는 8절의 `configure`가 만듭니다.** 지금 `.env.example`을 복사하거나 key를 채울 필요가 없습니다.

## 3. 로그인과 이름 계획

```bash
az login
```

**접근 가능한 구독 확인**

```bash
az account list --output table
```

**같은 테넌트로 azd 로그인**

```bash
azd auth login
```

조직의 정상 MFA 절차를 따릅니다. 브라우저·CLI·azd의 테넌트가 같은지 확인하세요. 이 가이드의 설정 수집기는 구독 ID를 명시하므로 기본 구독을 자동 변경하지 않습니다.

본인의 고유 접두사를 정합니다. 예시는 그대로 공유하지 마세요.

| 용도 | 이름 예시 |
|---|---|
| 내 자산을 구분할 접두사 | `lab-yourname-nc-0928` |
| 리소스 그룹 | `rg-mf15-yourname-nc-0928` |
| Foundry 프로젝트 | `mf15-nc-project` |
| Foundry 리소스 | 포털이 생성한 실제 이름을 기록 |
| 처음 배포할 모델의 별칭 | `workshop-chat` |

접두사는 `lab-`로 시작하는 소문자·숫자·하이픈, 최대 32자로 정합니다. 모든 자산을 내 것과 구분하는 이름이므로 실습 도중 바꾸지 않습니다.

| 내 값으로 바꾸기 | 처음에는 그대로 사용하기 |
|---|---|
| `yourname`이 들어간 자원 이름, `YOUR-...`/`실제-...` 자리표시자 | `workshop-chat`, 결과 label `baseline`/`candidate`, 파일 경로 |

모델·버전·리전도 이 가이드의 선택을 유지합니다. 이미 같은 이름이 사용 중이면 기존 자원을 바꾸지 말고 해당 절의 새 이름/재개 안내를 따릅니다.

## 4. 실습 전용 리소스 그룹 만들기

1. Azure 포털 **Resource groups → Create**.
2. 내 Owner 구독과 새 그룹 이름을 선택합니다.
3. **North Central US**를 선택합니다. 프로젝트 생성 가능 여부와 모든 모델·도구의 실제 성공은 별개입니다.
4. [Foundry 리전](https://learn.microsoft.com/azure/foundry/reference/region-support)과 [Search 리전](https://learn.microsoft.com/azure/search/search-region-support)을 확인합니다. 뒤의 관리형 AI red teaming에 관한 두 공식 목록에도 North Central US가 공통으로 포함됩니다. [목록 차이와 해석은 13장](13-governance.md#5-관리형-ai-red-teaming--기본-검증-대상)에서 다룹니다.
5. `workshop=foundry-v1.5` 같은 비밀 아닌 태그를 달고 생성합니다.

이 그룹에는 실습 자원만 넣습니다. 기존 업무용 그룹을 사용하면 마지막에 그룹 전체를 삭제할 수 없습니다.

<details>
<summary>선택: 포털 대신 CLI로 그룹 만들기 — 둘 중 하나만 실행</summary>

구독 ID와 이름을 본인 값으로 바꿉니다. 포털에서 이미 만든 그룹은 다시 만들지 않습니다.

```bash
az group create --subscription "내-구독-ID" --name "rg-mf15-yourname-nc-0928" --location northcentralus --tags workshop=foundry-v1.5 lifecycle=retain
```

</details>

`lifecycle=retain`은 보존 의사를 기록하는 태그이지 삭제 방지 잠금은 아닙니다. 자원을 남길 경우 [보존 모드](15-capstone-cleanup.md#보존-모드로-진행할-때)를 적용합니다.

구독/그룹의 **Cost Management → Budgets**에서 본인의 실습 예산 알림을 설정할 수 있습니다. 금액은 현재 가격과 자신의 예산으로 정합니다. **알림은 자동 사용 중지나 환불 보장이 아닙니다.**

## 5. Foundry 프로젝트 만들기

1. [Foundry](https://ai.azure.com)를 엽니다. **New Foundry** 전환이 보이면 현재 포털을 선택합니다.
2. 왼쪽 위 프로젝트 선택 영역 → **Create new project**.
3. 프로젝트 이름을 입력하고 **Advanced options**를 엽니다.
4. 사용할 구독, **방금 만든 실습 그룹**, 확인한 리전을 지정하고 생성합니다.
5. Foundry 리소스 이름은 자동 생성될 수 있습니다. 예시 이름을 추측하지 말고 실제 이름을 확인합니다.
6. 프로젝트 홈에서 **Project endpoint**를 복사합니다.

**복사할 값 1 — Project endpoint**

형식은 `https://<실제-domain>.services.ai.azure.com/api/projects/<실제-project>`입니다. 모델의 `.openai.azure.com` Endpoint와 다릅니다.

고정 실행 코드가 받는 형식과 다른 URL만 보이면 Libraries/API 영역에서 프로젝트 Endpoint를 다시 확인합니다. 도메인을 임의로 바꾸지 않습니다.

**복사할 값 2 — 프로젝트 ARM ID**

Azure 포털에서 **프로젝트 리소스 → JSON View**를 열고 `id`도 복사합니다.

```text
/subscriptions/.../resourceGroups/.../providers/Microsoft.CognitiveServices/accounts/.../projects/...
```

부모 Foundry 계정 ID가 아니라 **`/projects/...`까지 포함한 ID**입니다.

<details>
<summary>선택: 포털 대신 CLI로 Foundry 프로젝트 만들기</summary>

### 같은 준비를 CLI로 할 때

포털 경로 대신 사용할 수 있습니다. `--assign-identity`와 `--allow-project-management true`를 빠뜨리지 않습니다. 이름은 전역에서 고유해야 하며 모든 명령에 같은 구독·그룹·리전을 지정합니다.

```bash
az cognitiveservices account create --subscription "내-구독-ID" --resource-group "rg-mf15-yourname-nc-0928" --name "내-고유-foundry-이름" --custom-domain "내-고유-foundry-이름" --kind AIServices --sku S0 --location northcentralus --assign-identity --allow-project-management true
```

**생성한 Foundry 계정에 프로젝트 생성**

```bash
az cognitiveservices account project create --subscription "내-구독-ID" --resource-group "rg-mf15-yourname-nc-0928" --name "내-고유-foundry-이름" --project-name "mf15-nc-project" --location northcentralus
```

CLI 생성은 사용자·프로젝트의 **Foundry User 역할을 자동으로 보장하지 않습니다.** 7절에서 두 주체의 역할을 반드시 확인합니다.

</details>

## 6. 첫 모델 배포

1. Foundry **Discover → Models**에서 `gpt-6-sol`을 찾습니다.
2. 버전 **`2026-09-22`**, 지원 기능·리전·할당량을 확인합니다. 첫 응답부터 에이전트·도구 실습까지 Sol로 직접 진행합니다. [모델 역할과 기준](model-selection.md).
3. **Deploy / Use this model**에서 배포 이름을 `workshop-chat`으로 지정합니다.
4. 본인 정책에 맞는 종량제 Standard 계열을 고릅니다. Global Standard는 글로벌 처리 정책이 허용할 때만 선택합니다. PTU 계약은 필요하지 않습니다.
5. 상태가 **Succeeded**가 될 때까지 기다립니다. 실제 기반 모델·버전·유형·리전을 확인합니다.

> [!WARNING]
> 할당량이 없거나 모델이 제공되지 않으면 **Create를 반복하지 않습니다**. 고정 리전과 Sol 선택을 유지하며, 다른 모델로 바꿔 성공처럼 표시하지 않습니다.

모델 배포 화면/Quota 메뉴에서 현재 가용성을 확인합니다. 필요한 증가를 요청하거나 준비될 때까지 멈춥니다.

기본 답변 모델은 Sol입니다. 02의 GPT-6 Luna 비교는 선택 사항이며, 07의 judge는 **GPT-5.5 / 2026-04-24**입니다. IQ Chat의 별도 `gpt-5.6-luna`와 Optimizer는 해당 장에서만 준비합니다.

같은 배포 이름으로 다른 모델을 이미 사용하고 있다면 **그 모델을 바꾸거나 삭제하지 않습니다**. 실제 Sol 배포의 기존 이름을 명시적으로 재사용하거나 새 고유 이름을 선택합니다.

설정 도구는 실제 모델/버전을 확인합니다. 기존 agent·평가를 새 모델의 결과로 재사용하지 마세요.

## 7. 데이터 접근 역할 확인

Azure 포털의 **실제 Foundry 리소스 → IAM → Role assignments**를 봅니다.

| 주체 | 역할 | 범위 |
|---|---|---|
| 내 로그인 사용자 | **Foundry User** | 이 실습 Foundry 리소스 |
| 이 프로젝트의 관리 ID | **Foundry User** | 같은 Foundry 리소스 |

포털이 이미 부여했다면 중복 생성하지 않습니다. 없으면 **Add role assignment → Foundry User → Members**에서 해당 주체를 선택해 부여합니다.

이전 이름 **Azure AI User**가 보일 수 있습니다. 역할 ID는 `53ca6127-db72-4b80-b1b0-d745d6d5456d`입니다.

관리 ID는 내 계정이나 프로젝트 이름 문자열이 아닙니다. 프로젝트 리소스 **JSON View → identity.principalId**로 구분합니다. Identity가 없다면 프로젝트의 관리 ID 설정을 확인한 뒤 계속합니다.

구독 Owner의 리소스 관리 권한이 데이터 작업 권한을 대신하지 않습니다. 앱 등록이나 client secret은 만들지 않습니다.

역할을 방금 추가했다면 반영에 몇 분 걸릴 수 있습니다. 바로 403이 나도 새 프로젝트를 만들거나 같은 역할을 중복 추가하지 말고, 주체·범위를 확인한 뒤 잠시 기다려 같은 작업을 다시 확인합니다.

## 8. 실제 값으로 설정 자동 수집

아래 값의 출처를 먼저 확인하고 따옴표 안 자리표시자를 바꿉니다. 따옴표는 남깁니다.

| 명령 인자 | 넣을 값 |
|---|---|
| `--project-id` | 5절 JSON View에서 복사한 `/projects/...`까지의 ID |
| `--endpoint` | 5절 프로젝트 홈의 Project endpoint |
| `--deployment` | 6절에서 만든 Sol의 배포 이름. 기본은 `workshop-chat` |
| `--prefix` | 3절에서 정한 내 `lab-` 접두사 |

```bash
python scripts/selfstudy.py configure --project-id "실제-새-NC-프로젝트-ARM-ID" --endpoint "실제-새-NC-프로젝트-Endpoint" --deployment "workshop-chat" --expected-model gpt-6-sol --prefix "lab-yourname-nc-0928"
```

<details>
<summary>이전 환경이 있을 때만: 다른 이름의 기존 Sol 배포 사용</summary>

삭제되지 않은 같은 프로젝트에서 `workshop-compare`가 실제 Sol인지 확인했다면 같은 프로젝트·Endpoint·prefix로 아래 별칭을 사용할 수 있습니다. 새 환경의 기본 명령과 둘 다 실행하지 않습니다.

```bash
python scripts/selfstudy.py configure --project-id "실제-프로젝트-ARM-ID" --endpoint "실제-프로젝트-Endpoint" --deployment workshop-compare --expected-model gpt-6-sol --prefix "기존-lab-접두사"
```

예전에 사용한 결과 label·파일·agent 버전은 그대로 보관합니다. 새로운 모델/평가 조건에는 새 이름과 label을 사용합니다. [기존 별칭 안내](model-selection.md#기존-배포를-그대로-재사용하기).

</details>

이 도구는 Azure CLI로 **구독·프로젝트·계정·배포를 읽기만** 합니다. ID/Endpoint 일치와 배포 상태를 확인한 뒤 다음을 기록합니다.

- `.env`: SDK가 사용할 설정 한 벌.
- `.selfstudy/azure.json`: 실제 리소스 ID, 관리 ID, 리전, 확인 시점.

토큰·비밀번호·API key는 저장하지 않습니다. 기존 다른 프로젝트의 설정은 덮어쓰지 않습니다.

| 출력 | 뜻 |
|---|---|
| `management_metadata_read: true` | Azure 관리 정보를 읽었습니다. |
| `model_invoked: false` | 아직 모델에 질문하지 않았습니다. |

새 설정은 reasoning `low`, 출력 상한 `32768`을 사용합니다. 출력 상한에는 reasoning 토큰도 포함됩니다.

<details>
<summary>이전 개인 설정을 재사용할 때만: 생성 설정 맞추기</summary>

저장된 값을 확인한 뒤 다음과 같이 맞춥니다. 바뀐 조건에는 새 agent·실험 label을 사용합니다.

```bash
python scripts/selfstudy.py set WORKSHOP_REASONING_EFFORT low
```

**출력 토큰 상한 설정**

```bash
python scripts/selfstudy.py set WORKSHOP_MAX_OUTPUT_TOKENS 32768
```

</details>

**저장한 값 다시 읽기**

```bash
python scripts/selfstudy.py values
```

**준비 상태 확인**

```bash
python scripts/workshop.py doctor --cloud
```

올바른 구독·테넌트·배포가 표시되는지 확인합니다. `doctor --cloud`도 추론 시험이 아니라 메타데이터/인증 확인입니다.

> [!IMPORTANT]
> **다음 장에서 Sol의 첫 실제 요청을 통과한 뒤 agent를 만듭니다.** 배포의 `Succeeded`는 모든 도구·API 경로의 성공을 보장하지 않습니다.

오류는 [문제 해결](troubleshooting.md)에서 원래 응답과 함께 확인합니다.

**처음에는 장을 건너뛰지 않아도 됩니다.** MAF는 04장, 로그는 09장에서 준비합니다. 최초 요청부터 trace가 꼭 필요한 별도 검증에만 [09의 로그 연결](09-operations.md#1-로그-환경-생성연결)을 먼저 적용합니다. 연결 전 응답이 소급 수집되지는 않습니다.

## 9. 역할의 실제 명령이 필요할 때

**7절에서 IAM의 두 역할을 확인했다면 이 절은 생략하고 완료 확인으로 갑니다.** CLI로 부여할 명령이 필요한 경우에만 사용합니다.

Azure 포털에서 본인 사용자 Object ID를 확인하거나 다음 읽기 명령을 사용합니다.

```bash
az ad signed-in-user show --query id --output tsv
```

**필요한 역할의 계획 조회**

```bash
python scripts/selfstudy.py roles --user-object-id "내-사용자-Object-ID"
```

`roles`는 **필요 역할의 명령을 출력할 뿐 실행하지 않습니다.** Portal IAM과 비교하고 없는 역할만 직접 실행하세요. 기존 Owner를 다른 계정에 주거나 권한을 구독 전체로 넓히지 않습니다.

## 완료 확인

- [ ] 내 전용 그룹·Foundry 프로젝트·모델을 만들었다.
- [ ] 내 사용자와 프로젝트 관리 ID의 데이터 역할을 확인했다.
- [ ] 설정을 한 곳에 저장했고 실제 값을 다시 읽었다.
- [ ] 비용과 추가 권한의 경계를 안다.

막히면 [문제 해결](troubleshooting.md)의 해당 오류부터 해결합니다. 중단한다면 지금 [정리](15-capstone-cleanup.md)를 확인합니다.

---

[전체 과정](../README.ko.md#진행-순서) · [다음: 01. 첫 모델 응답 →](01-foundry.md) · [진행 지도 ↑](#chapter-map)
