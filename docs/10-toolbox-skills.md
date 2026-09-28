# 10. Toolbox·Tool Search·Skills·OpenAPI

[English](en/10-toolbox-skills.md) | **한국어** · [전체 과정](../README.ko.md#진행-순서) · [진행 도움말](checkpoints.md)

**완료 목표:** 공유 도구와 업무 지침을 연결하고 실제 사용을 확인합니다.

**시작 조건:** 06장의 **원래 Search 인덱스** 조회 성공, 프로젝트 관리 ID, 08장의 Foundry 확장과 **`prepare-hosted` 준비 폴더**.

**실행 위치:** 포털에서 권한 확인, 터미널에서 생성·호출, 편집기에서 결과 확인. 8절은 터미널 A·B를 사용합니다.

08장의 원격 배포가 막혔어도 준비 폴더가 있으면 1~7절은 진행할 수 있습니다. 폴더가 없다면 [08장 3절](08-hosted.md#3-기존-프로젝트에-연결하는-독립-폴더)을 먼저 마칩니다.

<a id="chapter-map"></a>

**진행 지도**

| 단계 | 확인할 결과 |
|---|---|
| [1. Search 권한](#1-프로젝트--search-권한) | 프로젝트 관리 ID의 역할 |
| [2. 연결 생성](#2-keyless-프로젝트-연결-직접-생성) | API key 없는 실제 연결 |
| [3. Toolbox](#3-일반-toolbox부터) | 목록 → 조회 → 답변 |
| [4. 도구 발견](#4-tool-search와-도구-고정) | 도구를 찾는 기능 |
| [5. Skill 업로드](#5-skill-준비업로드readback) | 원본과 다운로드 파일 일치 |
| [6. Skill 사용](#6-정확한-skill-버전을-연결) | 실제 Skill 읽기 |
| [7. OpenAPI](#7-openapi도-같은-search로) | 다른 호출 주체의 검색 |
| [8. Hosted Toolbox](#8-같은-toolbox를-hosted로) | 로컬·원격 도구 결과 |
| [9. 기본 버전 — 선택](#9-버전-운영) | 검토한 버전 선택 |
| [완료 확인](#완료-확인) | 버전별 결과와 세션 중지 |

**Toolbox는 공유 도구 묶음**, **Skill은 재사용할 업무 지침 묶음**입니다. Toolbox·Skill·Hosted 에이전트의 버전 번호는 서로 다릅니다.

## 1. 프로젝트 → Search 권한

```bash
python scripts/selfstudy.py status
```

`sdk_settings.AZURE_SEARCH_INDEX_NAME`이 06장 4절의 원래 인덱스인지 확인합니다.

**역할 계획 조회**

```bash
python scripts/selfstudy.py roles --user-object-id "내-사용자-Object-ID"
```

포털의 Search IAM에서 **프로젝트 관리 ID**에 다음 역할이 있는지 확인하고, 없는 것만 부여합니다.

| 역할 | 용도 |
|---|---|
| Search Index Data Reader | 문서 조회 |
| Search Service Contributor | 도구의 스키마 접근 |

두 역할의 범위는 **내 실습 Search**입니다. Service Contributor는 읽기 전용이 아니므로 공유 서비스에 부여하지 않습니다.

## 2. keyless 프로젝트 연결 직접 생성

keyless는 API key 대신 관리 ID로 인증한다는 뜻입니다. `--cwd`에는 08장이 출력한 준비 폴더를 넣습니다.

```bash
azd ai connection create "내-prefix-search" --kind cognitive-search --target "실제-Search-Endpoint" --auth-type project-managed-identity --audience https://search.azure.com --project-endpoint "실제-프로젝트-Endpoint" --cwd "실제-08-Hosted-절대경로"
```

**확인:** Foundry **Project details → Connected resources**에서 연결 이름·Search 주소·프로젝트 관리 ID 인증을 확인합니다.

**확인한 이름 저장**

```bash
python scripts/selfstudy.py set TOOLBOX_SEARCH_CONNECTION_NAME "내-prefix-search"
```

같은 이름의 연결을 `--force`로 덮어쓰지 않습니다. SDK에서 인증 형식이 `ProjectManagedIdentity`로 보여도 정상입니다.

## 3. 일반 Toolbox부터

**계획 확인**

```bash
python scripts/workshop.py toolbox plan
```

프로젝트·Search 연결·인덱스가 맞아야 생성합니다.

```bash
python scripts/workshop.py toolbox create --confirm-create
```

반환된 **`selected_version`을 아래 세 명령에 동일하게** 넣습니다.

**도구 목록 확인**

```bash
python scripts/workshop.py toolbox probe --version "실제-버전" --label toolbox-list
```

**실제 Search 조회**

```bash
python scripts/workshop.py toolbox query --version "실제-버전" --label toolbox-query --confirm-cost
```

**조회 성공 후 모델 호출**

```bash
python scripts/workshop.py toolbox ask --version "실제-버전" --label toolbox-answer --confirm-cost
```

**확인:** `probe`는 목록, `query`는 원문 조회, `ask`는 도구 결과를 사용한 답변입니다. **목록만 성공하면 다음 단계의 성공이 아닙니다.**

query가 403이면 멈추고 프로젝트 관리 ID의 Search 역할을 확인합니다. 실패 결과와 실제 호출 ID를 보관합니다.

## 4. Tool Search와 도구 고정

Tool Search는 **사용할 도구를 찾는 기능**입니다. 규정 문서를 찾는 File Search와 다릅니다.

**새 버전 계획**

```bash
python scripts/workshop.py toolbox plan --discovery --pin-policy
```

**새 Toolbox 버전 생성**

```bash
python scripts/workshop.py toolbox add-version --discovery --pin-policy --confirm-create
```

**새 `selected_version`으로 목록 확인**

```bash
python scripts/workshop.py toolbox probe --version "새-selected_version" --label discovery-list
```

**확인:** `tool_search`, `call_tool`, `policy_search`가 표시되어야 합니다. 미지원이면 이 기능만 차단으로 남기고 일반 Toolbox 성공과 구분합니다.

## 5. Skill 준비·업로드·readback

readback은 **업로드한 내용을 다시 읽어 확인**하는 작업입니다.

**CLI 지원 확인**

```bash
azd ai skill create --help
```

**다운로드 명령 확인**

```bash
azd ai skill download --help
```

**입력 준비**

```bash
python scripts/workshop.py prepare-extensions --label extensions-ko
```

`outputs/extensions-ko/manifest.json`의 `skill_name`과 `policy-review/SKILL.md`를 확인합니다. 이미 준비했다면 언어·접두사·지침·원문 hash가 같은지 확인해 재사용합니다.

**Skill 폴더만 업로드**

```bash
azd ai skill create "manifest의-skill_name" --file outputs/extensions-ko/policy-review --project-endpoint "실제-프로젝트-Endpoint"
```

상위 폴더에는 평가 참조가 있으므로 **`policy-review/`만** 업로드합니다.

**버전 조회**

```bash
azd ai skill show "manifest의-skill_name" --project-endpoint "실제-프로젝트-Endpoint" --output json
```

**반환된 `default_version`을 새 폴더로 다운로드**

```bash
azd ai skill download "manifest의-skill_name" --version "실제-skill-version" --output-dir .selfstudy/skill-readback --project-endpoint "실제-프로젝트-Endpoint"
```

**원본과 비교**

```bash
python scripts/selfstudy.py compare-files outputs/extensions-ko/policy-review/SKILL.md .selfstudy/skill-readback/SKILL.md
```

**확인:** 파일 내용이 바이트 단위로 같아야 합니다. 다르면 이름·버전·원본을 확인합니다. 다운로드 파일을 편집해 일치시키지 않습니다.

<details>
<summary>기존 지침을 바꿀 때만: 새 Skill 버전</summary>

새 입력을 만들고 지침을 검토합니다.

```bash
python scripts/workshop.py prepare-extensions --label skill-update-inputs-ko
```

**기존 소유 Skill에 새 버전 추가**

```bash
azd ai skill update "기존-소유-Skill-이름" --file outputs/skill-update-inputs-ko/policy-review --project-endpoint "실제-프로젝트-Endpoint"
```

**실제 버전 조회**

```bash
azd ai skill show "기존-소유-Skill-이름" --project-endpoint "실제-프로젝트-Endpoint" --output json
```

**새 버전 다운로드**

```bash
azd ai skill download "기존-소유-Skill-이름" --version "반환된-새-Skill-버전" --output-dir .selfstudy/skill-readback-v2-ko --project-endpoint "실제-프로젝트-Endpoint"
```

**원본 비교**

```bash
python scripts/selfstudy.py compare-files outputs/skill-update-inputs-ko/policy-review/SKILL.md .selfstudy/skill-readback-v2-ko/SKILL.md
```

새 Skill은 6절의 새 Toolbox 버전에 명시적으로 연결합니다. 이전 버전·결과는 자동 변경되지 않습니다.

</details>

## 6. 정확한 Skill 버전을 연결

**5절의 Skill 버전으로 계획**

```bash
python scripts/workshop.py toolbox plan --discovery --pin-policy --skill-version "실제-skill-version"
```

**새 Toolbox 버전 생성**

```bash
python scripts/workshop.py toolbox add-version --discovery --pin-policy --skill-version "실제-skill-version" --confirm-create
```

**반환된 Toolbox 버전으로 목록 확인**

```bash
python scripts/workshop.py toolbox probe --version "새-Toolbox-version" --label skilled-list
```

**같은 버전으로 Skill 사용**

```bash
python scripts/workshop.py toolbox ask --version "새-Toolbox-version" --label skilled-answer --with-skill --confirm-cost
```

**확인:** `skill_load_verified`와 실제 도구 호출·규정 결과를 확인합니다. 등록만 한 상태와 실제 읽은 상태는 다릅니다. 이 예제는 Skill의 임의 스크립트를 실행하지 않습니다.

## 7. OpenAPI도 같은 Search로

OpenAPI는 HTTP API의 사용법을 기술하는 형식입니다. 이번에는 새 업무 API 대신 **내 Search 인덱스의 읽기 API**를 사용합니다.

```bash
python scripts/workshop.py openapi plan
```

**호출 주체는 Foundry 계정의 관리 ID**입니다. Toolbox의 프로젝트 관리 ID와 다릅니다.

1. Foundry 계정의 **Identity → System assigned**를 확인합니다.
2. 새로 켰다면 [00장의 `configure`](00-setup.md#8-실제-값으로-설정-자동-수집)를 **같은 프로젝트·Sol 배포·접두사**로 다시 실행해 ID를 갱신합니다.
3. 이 계정 관리 ID에 **내 Search 범위의 Search Index Data Reader**를 확인·부여합니다.

```bash
python scripts/workshop.py openapi invoke --label openapi-policy --confirm-cost
```

**확인:** 실제 OpenAPI 도구 호출과 반환 원문을 읽습니다. 함수·MCP의 성공 결과를 이 호출의 증거로 대신하지 않습니다.

## 8. 같은 Toolbox를 Hosted로

### 패키지·배포 폴더 준비

처음에는 **3절에서 조회·답변을 확인한 일반 Toolbox 버전**을 사용합니다. Skill 버전을 사용하려면 패키징과 로컬 `serve` 양쪽에 `--with-skill`을 추가합니다.

```bash
python scripts/workshop.py --script package-toolbox --language ko --version "검증한-Toolbox-version"
```

**출력된 패키지로 준비**

```bash
python scripts/selfstudy.py prepare-hosted --kind toolbox --package "방금-반환한-패키지-경로" --name toolbox-hosted
```

08장처럼 **실제 서비스 이름·준비 폴더·패키지 경로**를 구분합니다.

### 터미널 A: 로컬 서버 시작

이전 서버가 있다면 먼저 중지합니다.

```bash
python scripts/workshop.py toolbox serve --version "검증한-Toolbox-version"
```

### 터미널 B: 실제 도구 호출

같은 폴더에서 가상 환경을 활성화한 뒤 확인합니다.

```bash
python -c "from urllib.request import urlopen; print(urlopen('http://127.0.0.1:8088/readiness', timeout=10).read().decode())"
```

**`healthy`일 때만 호출**

```bash
azd ai agent invoke --cwd "실제-Toolbox-Hosted-절대경로" --local --port 8088 --new-session --new-conversation --timeout 210 "2026년 9월 국내 출장에서 170000원 호텔의 사전 승인 조건은?"
```

실제 도구 결과·답변·인용을 확인합니다. 성공·실패와 관계없이 A에서 `Ctrl+C`로 서버를 중지합니다.

### 원격 배포·원시 응답 검증

**준비 명령이 출력한 서비스 배포**

```bash
azd deploy "실제-Toolbox-서비스-이름" --cwd "실제-Toolbox-Hosted-절대경로"
```

**새 버전·런타임 ID 조회**

```bash
azd ai agent show "실제-Toolbox-서비스-이름" --cwd "실제-Toolbox-Hosted-절대경로" --output json
```

[08장 5절](08-hosted.md#5-원격-배포)처럼 그 런타임 ID의 Foundry User 역할을 확인합니다.

**실제 호출과 원시 응답 저장**

```bash
python scripts/selfstudy.py capture --directory "실제-.selfstudy-하위-Hosted-절대경로" --service "실제-Toolbox-서비스-이름" --version "실제-agent-version" --output .selfstudy/toolbox-remote/response.raw --confirm-cost
```

**저장된 응답 검사 — 재호출 없음**

```bash
python scripts/workshop.py --script verify-toolbox-response --file "capture가-출력한-raw-절대경로" --package "실제-패키지-절대경로" --agent-name "실제-Toolbox-서비스-이름" --agent-version "실제-agent-version" --output "새-검증결과-절대경로"
```

**확인:** 스트리밍 응답 완료, 버전·패키지 일치, 실제 도구 사용을 확인합니다. `capture` 파일이 생겼다는 것만으로 성공은 아닙니다.

실패해도 [08장의 세션 조회·중지](08-hosted.md#6-정확한-원격-버전-호출)를 수행합니다. 세션의 `workshop-evidence/toolbox-runs/`도 [만료 전에 보관](advanced/session-files.md)합니다.

## 9. 버전 운영

**선택:** 검토한 버전을 이후 기본값으로 사용할 때만 실행합니다.

```bash
python scripts/workshop.py toolbox select --version "검토한-버전" --confirm-update
```

새 버전을 만드는 명령이 아닙니다. 이전 버전도 남겨 두면 같은 방법으로 되돌릴 수 있습니다.

## 완료 확인

- [ ] 도구 목록·실제 검색·모델 답변을 각각 확인했다.
- [ ] Skill 원본 일치와 실제 읽기를 확인하고 세 종류의 버전을 구분했다.
- [ ] OpenAPI·Hosted 결과 또는 차단 상태를 보관했다.
- [ ] 서버·세션을 중지하고 원시 응답과 소유 기록을 유지했다.

---

[← 09. 운영](09-operations.md) · [전체 과정](../README.ko.md#진행-순서) · [11. 기억·위임·예약 →](11-memory-a2a-routines.md) · [진행 지도 ↑](#chapter-map)
