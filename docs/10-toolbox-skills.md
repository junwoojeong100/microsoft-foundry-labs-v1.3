# 10. Toolbox·Tool Search·Skills·OpenAPI

[English](en/10-toolbox-skills.md) | **한국어** · [전체 과정](../README.ko.md#진행-순서) · [진행 도움말](checkpoints.md)

**완료 목표:** 내가 만든 Search에 keyless 연결을 만들고, 버전 있는 도구와 절차를 실제로 사용합니다.

**시작 조건:** 06의 원래 Search index/조회, 00의 프로젝트 관리 ID, **08의 azd Foundry 확장과 `prepare-hosted`로 만든 실제 준비 폴더**입니다. 확장 설치만으로 `--cwd`에 넣을 폴더가 생기지는 않습니다.

08의 원격 배포를 수행하지 못했어도 **1~3절의 폴더 준비가 성공했다면 이 장의 1~7절은 진행**할 수 있습니다. 폴더가 없다면 [08의 준비 절차](08-hosted.md#3-기존-프로젝트에-연결하는-독립-폴더)부터 마칩니다. 8절 Hosted Toolbox의 원격 배포는 별도로 지원 여부를 확인합니다.

**실행 위치:** 포털에서 역할·연결 확인, 터미널에서 도구·Skill·Hosted 실행. 8절은 터미널 A·B를 사용합니다.

> **버전 구분:** Skill 버전, Toolbox 버전, Hosted agent 버전은 서로 다른 값입니다. 매번 해당 명령이 반환한 버전을 사용합니다.

**진행 지도**

| 단계 | 확인할 결과 |
|---|---|
| [1. 프로젝트 권한](#1-프로젝트--search-권한) | 프로젝트 관리 ID의 Search 역할 |
| [2. keyless 연결](#2-keyless-프로젝트-연결-직접-생성) | 실제 대상과 인증 방식 |
| [3. 일반 Toolbox](#3-일반-toolbox부터) | 목록 → 실제 검색 → 모델 답변 |
| [4. 도구 발견](#4-tool-search와-도구-고정) | 새 버전의 발견·고정 도구 목록 |
| [5. Skill 업로드](#5-skill-준비업로드readback) | 다운로드한 내용과 원본의 일치 |
| [6. Skill 연결](#6-정확한-skill-버전을-연결) | 실제 Skill load와 도구 결과 |
| [7. OpenAPI](#7-openapi도-같은-search로) | 별도 호출 주체의 실제 검색 |
| [8. Hosted Toolbox](#8-같은-toolbox를-hosted로) | 로컬·원격 응답과 보존된 원시 증거 |
| [9. 기본 버전 선택 — 선택](#9-버전-운영) | 검토한 버전의 명시적 선택 |
| [완료 확인](#완료-확인) | 버전별 실행·소유권·세션 중지 |

## 1. 프로젝트 → Search 권한

06의 **원래 index 이름**이 현재 설정인지 확인합니다.

```bash
python scripts/selfstudy.py status
python scripts/selfstudy.py roles --user-object-id "내-사용자-Object-ID"
```

이 Toolbox의 호출 주체는 **프로젝트 관리 ID**입니다. 이 ID에 **내 실습 Search 범위의 Search Index Data Reader와 Search Service Contributor**를 부여합니다.

Search Service Contributor는 읽기 전용 역할이 아닙니다. 도구가 스키마를 읽는 데 필요한 범위이며 **실습 전용 Search에만** 부여합니다. 다른 연결 방식의 계정 관리 ID와 혼동하지 않습니다.

## 2. keyless 프로젝트 연결 직접 생성

실제 Search/프로젝트 Endpoint와 본인의 고유 연결 이름으로 바꿉니다. `--cwd`에는 **08의 `prepare-hosted`가 출력한 폴더**를 넣어 같은 프로젝트의 ARM 설정을 사용합니다. 저장소 루트나 `.build` 패키지 경로가 아닙니다.

```bash
azd ai connection create "내-prefix-search" --kind cognitive-search --target "실제-Search-Endpoint" --auth-type project-managed-identity --audience https://search.azure.com --project-endpoint "실제-프로젝트-Endpoint" --cwd "실제-08-Hosted-절대경로"
python scripts/selfstudy.py set TOOLBOX_SEARCH_CONNECTION_NAME "내-prefix-search"
```

**확인:** Foundry **Project details → Connected resources**에서 같은 연결, 대상, 인증 방식을 읽어 확인합니다. `--force`, API key, 다른 프로젝트 연결을 사용하지 않습니다.

현재 SDK의 프로젝트 관리 ID 인증 enum은 `ProjectManagedIdentity`로 반환될 수 있습니다. 이전 표현인 `AAD`만 기대해 정상 연결을 거부하지 않습니다. CLI의 `--auth-type project-managed-identity`는 그대로 사용하며, enum 차이를 API key나 다른 ID로 우회하지 않습니다.

## 3. 일반 Toolbox부터

```bash
python scripts/workshop.py toolbox plan
python scripts/workshop.py toolbox create --confirm-create
```

실제 `selected_version`을 기록한 뒤 아래 자리에 넣습니다.

```bash
python scripts/workshop.py toolbox probe --version "실제-버전" --label toolbox-list
python scripts/workshop.py toolbox query --version "실제-버전" --label toolbox-query --confirm-cost
python scripts/workshop.py toolbox ask --version "실제-버전" --label toolbox-answer --confirm-cost
```

| 단계 | 확인한 것 |
|---|---|
| probe | 인증·MCP 연결·도구 목록 |
| query | Toolbox에서 Search로 실제 조회 |
| ask | 모델이 그 도구 결과를 사용해 답변 |

목록 조회가 성공해도 Search의 downstream 권한이 맞는 것은 아닙니다. query가 403이면 원래 실패와 실제 호출 ID를 확인하고 그 ID의 Search 역할만 수정합니다.

## 4. Tool Search와 도구 고정

일반 Toolbox의 성공은 Tool Search·Skill의 실행 증거가 아닙니다. 이번에는 새 Toolbox 버전을 만들어 추가 기능을 따로 확인합니다.

이 기능의 Preview/제공 상태와 CLI 명령을 먼저 확인합니다.

```bash
azd ai skill create --help
azd ai skill download --help
python scripts/workshop.py toolbox plan --discovery --pin-policy
```

지원되는 것을 확인한 뒤:

```bash
python scripts/workshop.py toolbox add-version --discovery --pin-policy --confirm-create
python scripts/workshop.py toolbox probe --version "새-selected_version" --label discovery-list
```

실제 목록의 `tool_search`, `call_tool`, `policy_search`를 확인합니다. Tool Search는 **도구 발견**, File Search/Search는 **정책 정보 검색**입니다.

## 5. Skill 준비·업로드·readback

### 입력 준비·업로드

```bash
python scripts/workshop.py prepare-extensions --label extensions-ko
```

이미 같은 prefix/언어로 준비했다면 선택한 지침의 prompt/source hash까지 맞는지 확인해 재사용합니다. v2 내용이 바뀌었다면 아래 갱신 절차에서 새 입력 label을 사용합니다. `policy-review/SKILL.md`, `manifest.json`, 원본 hash를 읽습니다. **상위 폴더에는 평가 참조도 있으므로 `policy-review/`만 업로드**합니다.

```bash
azd ai skill create "manifest의-skill_name" --file outputs/extensions-ko/policy-review --project-endpoint "실제-프로젝트-Endpoint"
azd ai skill show "manifest의-skill_name" --project-endpoint "실제-프로젝트-Endpoint" --output json
```

### 같은 버전을 내려받아 원본과 비교

반환된 default_version을 명시해 **아직 없는 새 readback 폴더**로 다운로드합니다.

```bash
azd ai skill download "manifest의-skill_name" --version "실제-skill-version" --output-dir .selfstudy/skill-readback --project-endpoint "실제-프로젝트-Endpoint"
python scripts/selfstudy.py compare-files outputs/extensions-ko/policy-review/SKILL.md .selfstudy/skill-readback/SKILL.md
```

**확인:** bytes가 다르면 맞추려고 다운로드 파일을 편집하지 않습니다. 실패 원인을 확인합니다.

**처음 만든 Skill의 readback이 일치했다면 바로 6절로 갑니다.** 아래는 이전 Skill의 지침을 실제로 바꿀 때만 사용하는 절차입니다.

<details>
<summary>기존 지침을 변경할 때만: Skill 새 버전 만들기</summary>

### 기존 Skill을 새 버전으로 갱신하기

강화된 v2는 **인용 ID뿐 아니라 답변의 사실 자체도 실제 근거로 제한**합니다. 기존 입력 폴더를 수정하지 말고 새 label로 준비한 `SKILL.md`에서 이 지침을 확인합니다.

```bash
python scripts/workshop.py prepare-extensions --label skill-update-inputs-ko
```

새 manifest의 `skill_name`이 기존 소유 Skill과 같고 지침이 원하는 v2인지 확인한 뒤 update합니다.

```bash
azd ai skill update "기존-소유-Skill-이름" --file outputs/skill-update-inputs-ko/policy-review --project-endpoint "실제-프로젝트-Endpoint"
azd ai skill show "기존-소유-Skill-이름" --project-endpoint "실제-프로젝트-Endpoint" --output json
```

이전 버전은 보존하며, 버전 번호를 추측하지 말고 실제 새 반환 버전을 사용합니다.

```bash
azd ai skill download "기존-소유-Skill-이름" --version "반환된-새-Skill-버전" --output-dir .selfstudy/skill-readback-v2-ko --project-endpoint "실제-프로젝트-Endpoint"
python scripts/selfstudy.py compare-files outputs/skill-update-inputs-ko/policy-review/SKILL.md .selfstudy/skill-readback-v2-ko/SKILL.md
```

이미 사용한 label/readback 폴더는 덮어쓰지 않습니다. 새 Skill 버전은 6절의 **새 Toolbox 버전**에 명시적으로 연결하고 새 호출 결과로 확인합니다. 이전 Toolbox의 고정된 Skill 버전이나 기존 성공 기록이 자동 변경되는 것은 아닙니다.

</details>

## 6. 정확한 Skill 버전을 연결

```bash
python scripts/workshop.py toolbox plan --discovery --pin-policy --skill-version "실제-skill-version"
python scripts/workshop.py toolbox add-version --discovery --pin-policy --skill-version "실제-skill-version" --confirm-create
python scripts/workshop.py toolbox probe --version "새-Toolbox-version" --label skilled-list
python scripts/workshop.py toolbox ask --version "새-Toolbox-version" --label skilled-answer --with-skill --confirm-cost
```

**확인:** `skill_load_verified`, 실제 호출과 정책 결과를 봅니다. 등록했다는 사실만으로 Skill을 읽었다고 하지 않습니다. 이 예제는 Skill의 임의 스크립트를 실행하지 않습니다.

## 7. OpenAPI도 같은 Search로

새 회사 API를 만들지 않고, 본인이 만든 합성 Search index의 읽기 API를 사용합니다. 먼저 계획과 실제 연결 주체·대상을 확인합니다.

```bash
python scripts/workshop.py openapi plan
```

이 경로의 주체는 **Foundry 계정의 system-assigned identity**입니다. Toolbox의 프로젝트 ID가 아닙니다. 계정의 Identity를 켜고 00에서 선택한 **같은 실제 Sol 별칭**과 `--expected-model gpt-6-sol`로 `configure`를 실행해 ID를 새로 읽습니다. 이 ID에 **해당 Search의 Search Index Data Reader**를 부여합니다. `selfstudy.py roles`에서도 구분해 출력합니다.

```bash
python scripts/workshop.py openapi invoke --label openapi-policy --confirm-cost
```

실제 OpenAPI tool call과 반환 원문을 확인합니다. `lookup_policy`, MCP, OpenAPI, Code Interpreter가 서로 같은 실행이 아니라는 점을 설명합니다.

## 8. 같은 Toolbox를 Hosted로

### 패키지·배포 폴더 준비

검증된 **일반 Toolbox 버전**부터 패키징합니다. Skill 포함 버전을 선택했다면 패키징과 serve 양쪽에 `--with-skill`을 추가하고 같은 선택을 유지합니다.

```bash
python scripts/workshop.py --script package-toolbox --language ko --version "검증한-Toolbox-version"
python scripts/selfstudy.py prepare-hosted --kind toolbox --package "방금-반환한-패키지-경로" --name toolbox-hosted
```

08과 같이 생성된 manifest와 실제 프로젝트를 확인합니다.

### 터미널 A: 로컬 서버 시작

이전 로컬 서버를 중지한 뒤, 루트의 터미널 A에서 실행한 채 둡니다.

```bash
python scripts/workshop.py toolbox serve --version "검증한-Toolbox-version"
```

### 터미널 B: 실제 도구 호출

새 터미널 B도 같은 루트에서 `.venv`를 활성화합니다.

```bash
python -c "from urllib.request import urlopen; print(urlopen('http://127.0.0.1:8088/readiness', timeout=10).read().decode())"
azd ai agent invoke --cwd "실제-Toolbox-Hosted-절대경로" --local --port 8088 --new-session --new-conversation --timeout 210 "2026년 9월 국내 출장에서 170000원 호텔의 사전 승인 조건은?"
```

**확인·중지:** 실제 도구·모델·원문을 확인하고 A를 `Ctrl+C`로 중지합니다.

### 원격 배포·원시 응답 검증

그 다음 원격 배포를 직접 결정합니다.

```bash
azd deploy "내-prefix-toolbox-hosted" --cwd "실제-Toolbox-Hosted-절대경로"
azd ai agent show "내-prefix-toolbox-hosted" --cwd "실제-Toolbox-Hosted-절대경로" --output json
```

새 실제 런타임 ID에 필요한 프로젝트 Foundry User를 08처럼 확인/부여합니다. 원격 응답은 재호출 없이 검증할 수 있도록 raw bytes를 보존합니다.

```bash
python scripts/selfstudy.py capture --directory "실제-.selfstudy-하위-Hosted-절대경로" --service "내-prefix-toolbox-hosted" --version "실제-agent-version" --output .selfstudy/toolbox-remote/response.raw --confirm-cost
python scripts/workshop.py --script verify-toolbox-response --file "capture가-출력한-raw-절대경로" --package "실제-패키지-절대경로" --agent-name "내-prefix-toolbox-hosted" --agent-version "실제-agent-version" --output "새-검증결과-절대경로"
```

`capture`는 성공 여부를 꾸미지 않고 stdout/stderr를 보관합니다. 실제 SSE completed·버전·패키지·도구/Skill 근거는 다음 검증기가 판정합니다. 실패하면 같은 세션의 원본 로그부터 확인합니다.

검증 후 08의 세션 조회/중지 절차를 사용합니다. 원격 근거는 세션 home의 `workshop-evidence/toolbox-runs/`에 있습니다. 실제 stopped session에서도 회수와 도구 결과 hash 대조를 확인했습니다. 삭제를 하지 않더라도 **서비스 만료 전**에 [절대 `--target-path`로 파일 회수](advanced/session-files.md)를 진행하고 원래 패키지·응답·session/버전을 함께 보관합니다.

## 9. 버전 운영

**선택 사항:** 실제 호출을 검토한 버전을 이후 기본값으로 선택할 때만 실행합니다. 새 버전을 만드는 명령은 아닙니다.

```bash
python scripts/workshop.py toolbox select --version "검토한-버전" --confirm-update
```

이전 버전도 보관해 같은 방법으로 되돌릴 수 있습니다.

## 완료 확인

- [ ] 목록 조회·실제 검색·모델 답변을 따로 확인했다.
- [ ] Skill 원본 비교와 실제 load를 확인하고 세 종류의 버전을 구분했다.
- [ ] OpenAPI·Hosted의 실제 결과 또는 차단 상태를 보관했다.
- [ ] 로컬 서버와 원격 세션을 중지하고 원시 응답·소유권 기록을 유지했다.

뒤의 실습을 위해 자산과 ledger를 유지합니다. 최종 정리에서 삭제를 선택한 경우에만 참조 순서대로 제거합니다.

---

[← 09. 운영](09-operations.md) · [전체 과정](../README.ko.md#진행-순서) · [11. 기억·위임·예약 →](11-memory-a2a-routines.md)
