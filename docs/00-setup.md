# 00. 내 실습 환경 만들기

[English](en/00-setup.md) | **한국어** · [전체 과정](../README.ko.md#진행-순서) · [진행 도움말](checkpoints.md)

**완료 목표:** Python 환경, Foundry 프로젝트, Sol 모델 배포, 접근 권한을 준비합니다.

**시작 조건:** Microsoft Entra ID 계정, Azure 구독, 활성 구독 Owner 역할.

**실행 위치:** Azure·Foundry 포털, 편집기, 실습 폴더의 터미널.

> [!WARNING]
> **유료 자원을 만듭니다.** 리전은 **North Central US**(`northcentralus`)를 사용합니다. 처음에는 포털 경로만 따라가고, 접힌 CLI 대안은 생략하세요.

<a id="chapter-map"></a>

**진행 지도**

| 단계 | 확인할 결과 |
|---|---|
| [1. 권한 확인](#1-내-권한-확인) | 사용할 구독의 활성 Owner |
| [2. 파일·도구 설치](#2-실습-파일과-개발-도구) | Python 3.13, 로컬 검사 `PASS` |
| [3. 로그인·이름 정하기](#3-로그인과-이름-계획) | 같은 테넌트, 내 고유 접두사 |
| [4. 실습 그룹 생성](#4-실습-전용-리소스-그룹-만들기) | 실습 자원만 넣을 그룹 |
| [5. 프로젝트 생성](#5-foundry-프로젝트-만들기) | 프로젝트 주소와 전체 ID |
| [6. Sol 배포](#6-첫-모델-배포) | 지정 모델·버전, `Succeeded` |
| [7. 데이터 역할 확인](#7-데이터-접근-역할-확인) | 사용자·프로젝트 관리 ID의 역할 |
| [8. 설정 저장](#8-실제-값으로-설정-자동-수집) | 실제 연결 설정과 인증 확인 |
| [9. 역할 명령 — 필요할 때만](#9-역할의-실제-명령이-필요할-때) | 역할 부여 계획 |
| [완료 확인](#완료-확인) | 01장의 첫 호출 준비 |

이미 준비한 환경은 [재개 순서](checkpoints.md#다음-날-재개하기)를 사용합니다. 다른 사람의 리소스 이름·ID를 복사하지 않습니다.

## 1. 내 권한 확인

1. [Azure 포털](https://portal.azure.com)에 로그인합니다.
2. **Subscriptions → 사용할 구독 → Access control (IAM) → View my access**에서 활성 **Owner** 역할을 확인합니다.
3. 역할이 “할당 가능” 상태라면 조직의 PIM 절차로 활성화합니다. PIM은 필요한 때에만 역할을 활성화하는 기능입니다.
4. **Overview → Subscription ID**, **Properties → Directory/Tenant ID**를 확인합니다. 테넌트는 로그인 계정을 관리하는 조직 디렉터리입니다.
5. 조직이 North Central US와 이 실습의 서비스 사용을 허용하는지 확인합니다.

**확인:** 사용할 구독에서 Owner가 활성 상태여야 합니다. 없으면 자원 생성 전에 멈춥니다. Owner도 조직의 거부 정책을 우회할 수 없습니다.

구독 Owner와 디렉터리 전체 관리자(Global Administrator)는 다릅니다. 이 준비에는 새 앱 등록이나 client secret이 필요하지 않습니다.

## 2. 실습 파일과 개발 도구

### 실습 폴더 열기

1. 받은 ZIP을 압축 해제합니다. ZIP이 없다면 [저장소](https://github.com/junwoojeong100/microsoft-foundry-labs-v1.3)의 **Code → Download ZIP**을 선택합니다. 비공개 저장소는 접근 권한이 필요합니다.
2. `README.md`, `scripts/`, `curriculum.json`이 함께 있는 폴더를 찾습니다.
3. [VS Code](https://code.visualstudio.com/download)에서 **File → Open Folder**로 그 폴더를 엽니다.
4. **Terminal → New Terminal**을 선택합니다. 이후 명령은 모두 이 터미널에서 실행합니다.

**문서 읽기:** Markdown 파일의 **Open Preview**를 사용합니다. macOS는 `Cmd+Shift+V`, Windows/Linux는 `Ctrl+Shift+V`입니다. 명령은 문서 미리보기가 아니라 **터미널**에 붙여 넣습니다.

<details>
<summary>선택: Git이 있다면 ZIP 대신 복제</summary>

```bash
git clone https://github.com/junwoojeong100/microsoft-foundry-labs-v1.3.git
```

**복제한 폴더로 이동**

```bash
cd microsoft-foundry-labs-v1.3
```

이 폴더를 편집기에서 엽니다. ZIP 다운로드와 둘 다 할 필요는 없습니다.

</details>

### 필수 도구 설치

| 도구 | 설치 | 설치 후 확인 |
|---|---|---|
| Python **3.13.x** | [Python 다운로드](https://www.python.org/downloads/) | macOS/Linux: `python3.13 --version`, Windows: `py -3.13 --version` |
| Azure CLI | [설치 안내](https://learn.microsoft.com/cli/azure/install-azure-cli) | `az version` |
| Azure Developer CLI(azd) | [설치 안내](https://learn.microsoft.com/azure/developer/azure-developer-cli/install-azd) | `azd version` |

설치 후 편집기와 터미널을 다시 엽니다. 확인 명령에 버전이 표시되어야 합니다. “명령을 찾을 수 없음”이 나오면 설치부터 해결합니다.

> [!NOTE]
> 기본 실습은 Windows PowerShell에서도 진행합니다. 단, **05장 5절의 로컬 SDK 중단·재개**는 macOS/Linux 전용입니다. 실행기가 `fcntl`을 사용하므로 Windows Python에서는 동작하지 않습니다.

그 절까지 수행하려면 조직에서 승인한 WSL(Windows의 Linux 환경) 또는 Linux를 사용합니다. **별도 소스 폴더**에서 Python 설치와 로컬 검사까지만 준비하고, Windows의 `.venv`나 Azure 설정을 복사하지 않습니다.

**아래에서 본인 OS의 명령만 실행하세요.** 한 상자씩 실행하고, 오류가 나면 다음 상자로 넘어가지 않습니다.

<details>
<summary>기존 환경이 있을 때만: 다른 프로젝트로 새로 시작</summary>

### 새 프로젝트에서 이전 상태를 인수하지 않기

1. 이전 환경에서 [실행을 중지](15-capstone-cleanup.md#4-먼저-실행-중인-것을-멈추기)합니다.
2. 기존 `.env`, `.selfstudy/`, `.build/`, `outputs/`를 비공개로 보관합니다.
3. **새 폴더에 소스만** 압축 해제합니다. 이전 설정·결과를 복사하지 않습니다.
4. 새 프로젝트와 고유 접두사를 사용합니다. 이전 Azure 자원의 삭제는 별도로 결정합니다.

같은 폴더의 `configure`, `set`, `models`, `resource`, `bind-matrix`는 한 번에 하나씩 실행합니다. 동시에 실행하면 설정 저장이 충돌할 수 있습니다.

</details>

### macOS / Linux

**1. 가상 환경 만들기** — 이 실습의 Python 패키지를 분리하는 폴더입니다.

```bash
python3.13 -m venv .venv
```

**2. 활성화**

```bash
source .venv/bin/activate
```

**3. 버전 확인** — `Python 3.13.x`여야 합니다.

```bash
python --version
```

**4. 실습 패키지 설치**

```bash
python -m pip install -r requirements.txt
```

**5. 패키지 검사**

```bash
python -m pip check
```

### Windows PowerShell

**1. 가상 환경 만들기**

```powershell
py -3.13 -m venv .venv
```

**2. 활성화**

```powershell
.\.venv\Scripts\Activate.ps1
```

**활성화가 차단되면:** 시스템 정책을 낮추지 않습니다. 아래 명령부터 이후 모든 `python`을 `.\.venv\Scripts\python.exe`로 바꿉니다. 예: `.\.venv\Scripts\python.exe --version`.

**3. 버전 확인** — `Python 3.13.x`여야 합니다.

```powershell
python --version
```

**4. 실습 패키지 설치**

```powershell
python -m pip install -r requirements.txt
```

**5. 패키지 검사**

```powershell
python -m pip check
```

### 모든 OS: 설치 결과 확인

`pip check`에서 `No broken requirements found.`를 확인한 뒤 실행합니다.

```bash
python scripts/workshop.py doctor
```

| 필드 | 기대 값 |
|---|---|
| `documents` | `6` |
| `dev_cases` / `holdout_cases` | `6` / `4` |
| `azure_tested` | `false` |
| `result` | `PASS` |

이 검사는 **Python 버전과 로컬 데이터**만 확인합니다. Azure 연결 검사는 아닙니다. holdout은 최종 평가용 데이터이므로 개수만 확인하고 15장까지 파일을 열지 않습니다.

새 터미널마다 가상 환경을 활성화합니다. `.env`는 8절에서 자동 생성하므로 지금 `.env.example`을 복사하지 않습니다. 점으로 시작하는 파일은 숨김 파일일 수 있습니다.

## 3. 로그인과 이름 계획

**Azure CLI 로그인**

```bash
az login
```

**구독 목록 확인**

```bash
az account list --output table
```

1절의 구독 ID가 목록에 있어야 합니다. 없다면 올바른 조직 계정으로 로그인했는지 확인합니다.

**같은 계정·테넌트로 azd 로그인**

```bash
azd auth login
```

브라우저의 다단계 인증(MFA) 안내를 따릅니다. 이후 설정 도구는 구독 ID를 명시하며 기본 구독을 바꾸지 않습니다.

| 이름 | 예시 | 사용 방법 |
|---|---|---|
| 접두사(prefix) | `lab-yourname-nc-0928` | `yourname`을 내 고유 이름으로 변경 |
| 리소스 그룹 | `rg-mf15-yourname-nc-0928` | 내 고유 이름으로 변경 |
| 프로젝트 | `mf15-nc-project` | 새 실습 그룹에서 사용 |
| 기본 모델 배포 | `workshop-chat` | 처음에는 그대로 사용 |

접두사는 내 자원을 구분하는 이름입니다. **`lab-`로 시작하는 소문자·숫자·하이픈, 최대 32자**로 정하고 실습 중 바꾸지 않습니다.

`실제-...`, `YOUR-...`는 내 값으로 바꿀 자리표시자입니다. 따옴표는 남깁니다. [명령 읽기](checkpoints.md#명령과-자리표시자-읽기).

## 4. 실습 전용 리소스 그룹 만들기

1. Azure 포털에서 **Resource groups → Create**를 선택합니다.
2. 1절의 구독, 내 새 그룹 이름, **North Central US**를 지정합니다.
3. `workshop=foundry-v1.3` 태그를 추가하고 생성합니다.
4. 생성된 그룹의 **Overview**에서 구독·이름·리전을 확인합니다.

이 그룹에는 **실습 자원만** 넣습니다. 업무용 자원이 섞이면 마지막에 그룹 전체를 삭제할 수 없습니다.

<details>
<summary>선택: 포털 대신 CLI로 그룹 생성 — 둘 중 하나만 실행</summary>

```bash
az group create --subscription "내-구독-ID" --name "rg-mf15-yourname-nc-0928" --location northcentralus --tags workshop=foundry-v1.3 lifecycle=retain
```

이미 포털에서 만들었다면 실행하지 않습니다. `lifecycle=retain` 태그는 삭제 방지 잠금이 아닙니다.

</details>

**비용 관리:** **Cost Management → Budgets**에서 예산 알림을 설정할 수 있습니다. 알림은 자동 사용 중지가 아닙니다.

## 5. Foundry 프로젝트 만들기

1. [Foundry](https://ai.azure.com)를 엽니다. 전환 메뉴가 보이면 **New Foundry**를 선택합니다.
2. 프로젝트 선택 영역에서 **Create new project → Advanced options**를 엽니다.
3. 내 프로젝트 이름, 구독, **방금 만든 그룹**, **North Central US**를 지정해 생성합니다.
4. 프로젝트 홈과 Azure 포털에서 아래 두 값을 복사합니다.

| 값 | 복사할 곳 | 올바른 형식 |
|---|---|---|
| Project endpoint | Foundry 프로젝트 홈 | `https://<도메인>.services.ai.azure.com/api/projects/<프로젝트>` |
| 프로젝트 ARM ID | Azure 포털의 **프로젝트 리소스 → JSON View → id** | `/subscriptions/.../resourceGroups/.../providers/Microsoft.CognitiveServices/accounts/.../projects/...` |

엔드포인트는 요청을 보내는 주소, ARM ID는 자원의 전체 식별 경로입니다. **부모 Foundry 계정 ID나 `.openai.azure.com` 주소를 대신 넣지 않습니다.**

포털이 생성한 Foundry 리소스 이름도 확인합니다. 주소 형식이 다르면 프로젝트의 Libraries/API 영역을 확인하고, 도메인을 임의로 바꾸지 않습니다.

<details>
<summary>선택: 포털 대신 CLI로 Foundry 프로젝트 생성</summary>

전역에서 고유한 Foundry 이름을 정합니다. 두 명령에 같은 구독·그룹·이름을 사용합니다.

```bash
az cognitiveservices account create --subscription "내-구독-ID" --resource-group "rg-mf15-yourname-nc-0928" --name "내-고유-foundry-이름" --custom-domain "내-고유-foundry-이름" --kind AIServices --sku S0 --location northcentralus --assign-identity --allow-project-management true
```

**계정 생성 후 프로젝트 생성**

```bash
az cognitiveservices account project create --subscription "내-구독-ID" --resource-group "rg-mf15-yourname-nc-0928" --name "내-고유-foundry-이름" --project-name "mf15-nc-project" --location northcentralus
```

이 명령만으로 데이터 접근 역할이 준비되지는 않습니다. 7절을 수행합니다.

</details>

## 6. 첫 모델 배포

1. Foundry **Discover → Models**에서 `gpt-6-sol` / `2026-09-22`를 찾습니다.
2. 리전·지원 기능·할당량을 확인합니다.
3. **Deploy / Use this model**에서 배포 이름을 `workshop-chat`으로 지정합니다.
4. 사용량에 따라 과금하는 Standard 계열을 선택합니다. **Global Standard는 글로벌 처리가 허용될 때만** 사용합니다.
5. 생성 후 실제 모델·버전과 **`Succeeded`** 상태를 확인합니다.

**막히면:** 모델이나 할당량이 없을 때 Create를 반복하거나 다른 모델로 바꾸지 않습니다. 해당 모델의 가용성·할당량을 확인하고, 필요한 증가 요청 후 준비될 때까지 멈춥니다.

같은 이름의 다른 모델이 이미 있다면 변경·삭제하지 않습니다. [기존 배포 이름 사용법](model-selection.md#기존-배포를-그대로-재사용하기)을 따릅니다. 비교·검색·평가용 모델은 해당 장에서 추가합니다.

## 7. 데이터 접근 역할 확인

Azure 포털의 **부모 Foundry 리소스 → Access control (IAM) → Role assignments**를 엽니다.

| 주체 | 필요한 역할 | 범위 |
|---|---|---|
| 내 로그인 사용자 | **Foundry User** | 이 실습 Foundry 리소스 |
| 이 프로젝트의 관리 ID | **Foundry User** | 같은 Foundry 리소스 |

관리 ID는 Azure 서비스가 로그인할 때 쓰는 신원입니다. 프로젝트 리소스의 **JSON View → identity.principalId**로 식별합니다. 내 사용자 ID나 프로젝트 이름과 다릅니다.

1. 위 두 주체의 역할을 확인합니다.
2. 없는 역할만 **Add role assignment → Foundry User → Members**에서 추가합니다.
3. 역할 목록에서 **주체·역할·범위가 모두 맞는지** 다시 확인합니다.

이전 역할 이름 **Azure AI User**가 보일 수 있습니다. 역할 ID는 `53ca6127-db72-4b80-b1b0-d745d6d5456d`입니다.

관리 ID가 없다면 해당 프로젝트의 관리 ID를 먼저 준비합니다. Owner는 자원을 관리하는 역할이며 모델 데이터 접근을 대신하지 않습니다. 역할 반영에는 몇 분 걸릴 수 있으므로 403이 나도 중복 부여하지 않습니다.

## 8. 실제 값으로 설정 자동 수집

| 인자 | 넣을 값 |
|---|---|
| `--project-id` | 5절의 `/projects/...`까지 포함한 ARM ID |
| `--endpoint` | 5절의 Project endpoint |
| `--deployment` | 6절의 배포 이름. 기본 `workshop-chat` |
| `--prefix` | 3절에서 정한 내 `lab-` 접두사 |

```bash
python scripts/selfstudy.py configure --project-id "실제-프로젝트-ARM-ID" --endpoint "실제-프로젝트-Endpoint" --deployment "workshop-chat" --expected-model gpt-6-sol --prefix "lab-yourname-nc-0928"
```

이 명령은 Azure 정보를 **조회**한 뒤 `.env`와 `.selfstudy/azure.json`에 설정을 저장합니다. 자원을 생성하거나 모델을 호출하지 않습니다. 기존의 다른 프로젝트 설정은 덮어쓰지 않습니다.

**확인:** `management_metadata_read: true`, `model_invoked: false`가 표시되고 두 파일이 생겨야 합니다. 토큰·비밀번호·API key는 저장하지 않습니다.

**저장된 값 확인**

```bash
python scripts/selfstudy.py values
```

**인증·배포 상태 확인**

```bash
python scripts/workshop.py doctor --cloud
```

| 출력 필드 | 확인할 값 |
|---|---|
| `subscription.id` / `subscription.tenantId` | 1절의 구독·테넌트 |
| `project_endpoint` | 5절의 프로젝트 주소 |
| `deployment.name` | 6절의 실제 배포 이름 |
| `deployment.model.name` / `deployment.model.version` | `gpt-6-sol` / `2026-09-22` |
| `deployment.state` | `Succeeded` |
| `inference_tested` | `false` |

**아직 모델 호출 성공은 아닙니다.** 이 검사는 인증과 배포 정보를 확인합니다. 실제 호출은 01장에서 수행합니다.

새 설정의 reasoning은 `low`, 출력 토큰 상한은 `32768`입니다. [생성 설정 설명](model-selection.md#생성-설정). 오류가 나면 [문제 해결](troubleshooting.md)에서 해당 증상을 찾습니다.

## 9. 역할의 실제 명령이 필요할 때

**7절을 포털에서 마쳤다면 생략합니다.** CLI 역할 부여 명령이 필요할 때만 실행합니다.

**내 사용자 Object ID 조회**

```bash
az ad signed-in-user show --query id --output tsv
```

**반환된 ID로 역할 계획 생성**

```bash
python scripts/selfstudy.py roles --user-object-id "내-사용자-Object-ID"
```

**확인:** `mode: plan-only`, `role_assignments_executed: false`가 정상입니다. 출력된 명령은 아직 실행되지 않았습니다. IAM과 대조해 **없는 역할만** 해당 자원 범위에 부여합니다.

## 완료 확인

- [ ] 로컬 `doctor`의 `result`가 `PASS`이다.
- [ ] 내 전용 그룹·프로젝트·Sol 배포를 확인했다.
- [ ] 사용자와 프로젝트 관리 ID의 Foundry User 역할을 확인했다.
- [ ] `doctor --cloud`의 구독·테넌트·모델·버전·상태가 위 표와 맞는다.

중단한다면 [15. 중지·비용 확인](15-capstone-cleanup.md#4-먼저-실행-중인-것을-멈추기)으로 갑니다.

---

[전체 과정](../README.ko.md#진행-순서) · [다음: 01. 첫 모델 응답 →](01-foundry.md) · [진행 지도 ↑](#chapter-map)
