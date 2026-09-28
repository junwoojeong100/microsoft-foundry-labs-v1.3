# 08. Hosted 로컬 실행과 Azure 배포

[English](en/08-hosted.md) | **한국어** · [전체 과정](../README.ko.md#진행-순서) · [진행 도움말](checkpoints.md)

**완료 목표:** 코드를 패키징하고, 로컬과 Azure에서 각각 실제 답변을 받습니다.

**시작 조건:** 00장의 프로젝트·Owner·Sol 설정, 04장의 MAF 함수 실행 성공.

**실행 위치:** 터미널에서 준비·배포·호출, 편집기에서 설정 확인, 포털에서 역할 확인. 로컬 호출은 터미널 A·B를 사용합니다.

**Hosted Agent**는 내 코드를 Foundry에 배포해 실행하는 에이전트입니다. 로컬 확인도 Azure 모델을 호출하며, 원격 실행에는 세션 비용이 추가될 수 있습니다.

<a id="chapter-map"></a>

**진행 지도**

| 단계 | 확인할 결과 |
|---|---|
| [1. azd 준비](#1-azd-foundry-명령-준비) | Foundry 확장과 명령 |
| [2. 패키징](#2-안전한-패키지) | 비밀·평가 정답을 제외한 패키지 |
| [3. 배포 폴더](#3-기존-프로젝트에-연결하는-독립-폴더) | 서비스 이름·폴더·프로젝트 |
| [4. 로컬 호출](#4-로컬-실제-호출) | 준비 상태와 실제 답변 |
| [5. 원격 배포](#5-원격-배포) | 새 버전과 런타임 관리 ID |
| [6. 원격 호출·중지](#6-정확한-원격-버전-호출) | 같은 버전의 답변과 세션 중지 |
| [7. 워크플로 배포](#7-같은-방식을-workflow로) | 다른 실행 프로필의 결과 |
| [완료 확인](#완료-확인) | 로컬·원격 결과 구분 |

## 1. azd Foundry 명령 준비

**azd 버전 확인**

```bash
azd version
```

**설치된 확장 확인**

```bash
azd extension list --installed
```

**`microsoft.foundry`가 없을 때만 설치**

```bash
azd extension install microsoft.foundry
```

**00장과 같은 계정·테넌트로 로그인**

```bash
azd auth login
```

**명령 확인**

```bash
azd ai agent show --help
```

도움말이 표시되어야 합니다. 현재 구독·리전의 Hosted 지원과 용량도 확인합니다. 이 코드 배포 경로에는 Docker·ACR 로컬 설치가 필수는 아닙니다.

원격 배포가 미지원이어도 1~3절의 폴더 준비가 성공하면 이후 연결 실습에 사용할 수 있습니다. **폴더 준비와 원격 배포 성공은 별개**입니다.

## 2. 안전한 패키지

```bash
python scripts/workshop.py --script package-hosted
```

출력된 폴더를 엽니다. 기본은 `.build/hosted/`입니다.

| 확인할 파일 | 확인할 내용 |
|---|---|
| `package-manifest.json` | 코드·가상 규정·지침 포함. `.env`·인증정보·평가 정답·실행 결과 제외 |
| `runtime-profile.json` | 배포할 실행 방식 |
| `requirements.txt` | 패키지의 의존성 |

`cloud_deployed: false`는 정상입니다. **아직 로컬 패키지만 만들었습니다.**

이미 폴더가 있다면 먼저 기존 패키지를 확인합니다. 재생성이 필요할 때만 이전 패키지를 비공개로 보관하고 새로 만듭니다.

## 3. 기존 프로젝트에 연결하는 독립 폴더

**저장된 프로젝트 확인**

```bash
python scripts/selfstudy.py status
```

**2절이 출력한 패키지 경로로 준비**

```bash
python scripts/selfstudy.py prepare-hosted --kind runtime --package "실제-패키지-경로" --name hosted
```

이 명령은 **로컬 배포 설정만** 만듭니다. 기존 Foundry 프로젝트를 사용하므로 새 프로젝트를 생성할 필요가 없습니다.

생성된 `azure.yaml`을 열어 프로젝트 주소, 서비스 하나, `main.py`, Python 3.13, Responses 프로토콜, 모델, 원격 인증 `managed-identity`를 확인합니다.

### 준비 결과에서 복사할 값

| 다음 명령의 값 | 복사할 곳 |
|---|---|
| `--package` | 2절의 `.build/...` 패키지 경로 |
| `azd deploy` / `show` 뒤 서비스 이름 | 준비 출력의 **`서비스:` 전체 이름**. 짧은 `hosted`만 넣지 않음 |
| `--cwd` | 준비 출력의 **`폴더:` 절대 경로**. 패키지나 파일 경로가 아님 |
| `--version` | 5절 `show` 결과의 실제 `version` |
| 역할을 받을 ID | 같은 결과의 `instance_identity.principal_id` |

**출력된 배포 명령은 아직 실행하지 않습니다.** 먼저 4절의 로컬 호출을 확인합니다. `--cwd`는 해당 명령의 작업 폴더만 지정하므로 터미널은 계속 README가 있는 폴더에 둡니다.

### 출력을 닫았을 때 다시 찾기

`.selfstudy/` 아래 해당 `azure.yaml`의 `services`에서 서비스 이름을 확인합니다. 그 파일이 있는 폴더의 절대 경로를 `--cwd`에 넣습니다.

같은 준비 폴더는 덮어쓰지 않고 재사용합니다. 새 준비가 필요할 때만 `--run second`처럼 새 이름을 사용합니다. 영문 패키지는 준비 명령에도 `--language en`을 지정합니다.

## 4. 로컬 실제 호출

### 터미널 A: 서버 시작

```bash
python scripts/workshop.py serve
```

A는 실행한 채 둡니다. [새 터미널 B](checkpoints.md#두-터미널을-사용하는-장)를 열어 같은 폴더에서 `.venv`를 활성화합니다.

### 터미널 B: 준비 상태 확인 후 요청

```bash
python -c "from urllib.request import urlopen; print(urlopen('http://127.0.0.1:8088/readiness', timeout=10).read().decode())"
```

**확인:** `healthy`여야 합니다. 아니면 A의 로그를 확인하고, 아래 요청은 보내지 않습니다.

```bash
azd ai agent invoke --cwd "실제-Hosted-절대경로" --local --port 8088 --new-session --new-conversation --timeout 120 "2026년 9월 국내 출장 숙박비 한도와 근거를 알려주세요."
```

**기대 결과:** 150,000원 한도와 현행 규정 근거. `healthy`만 확인한 것은 모델 호출 성공이 아닙니다.

**중지:** 성공·실패와 관계없이 A에서 `Ctrl+C`를 누르고 프롬프트가 돌아오는지 확인합니다.

## 5. 원격 배포

로컬 답변을 확인한 뒤, **3절이 출력한 서비스 하나만** 배포합니다.

```bash
azd deploy "실제-agent-서비스-이름" --cwd "실제-Hosted-절대경로"
```

**배포 결과 조회**

```bash
azd ai agent show "실제-agent-서비스-이름" --cwd "실제-Hosted-절대경로" --output json
```

**확인:** 새 `name`, `version`, `status`, 엔드포인트를 확인합니다. 배포가 실패했다면 이전 활성 버전을 이번 결과로 쓰지 않습니다.

### 런타임에 필요한 역할

원격 코드는 내 로그인 계정이 아니라 **배포된 런타임의 관리 ID**로 실행합니다.

```bash
python scripts/selfstudy.py roles --user-object-id "내-사용자-Object-ID" --hosted-principal-id "실제-instance_identity.principal_id"
```

이 명령은 역할 계획만 출력합니다. 포털 IAM과 대조해 **그 버전의 런타임 ID에 없는 역할만** 지정된 자원 범위에 부여합니다. 로컬 로그인 성공이 원격 권한을 보장하지 않습니다.

## 6. 정확한 원격 버전 호출

5절의 실제 버전을 넣습니다. `v2` 같은 지침 이름이나 `latest`를 추측해 넣지 않습니다.

```bash
azd ai agent invoke --cwd "실제-Hosted-절대경로" --version "방금-확인한-버전" --new-session --new-conversation --timeout 270 "2026년 9월 국내 출장에서 170000원 호텔의 사전 승인 조건은?"
```

**확인:** 150,000원 한도 초과와 예약 전 팀장 승인 안내를 확인합니다. 반환된 세션·대화·추적 ID를 보관합니다. 한 답변의 성공은 전체 품질 평가가 아닙니다.

**내 세션 조회**

```bash
azd ai agent sessions list --cwd "실제-Hosted-절대경로" --limit 10
```

**방금 만든 세션 중지**

```bash
azd ai agent sessions stop "실제-내-session-id" --cwd "실제-Hosted-절대경로"
```

같은 목록 명령으로 그 ID가 실행 중이 아닌지 확인합니다. 호출 실패 시에도 생성된 세션이 있는지 확인합니다.

> [!WARNING]
> **stop은 실행만 중지합니다. 저장 볼륨은 삭제하지 않습니다.** 보관 비용과 삭제 여부는 [15장](15-capstone-cleanup.md)에서 확인합니다.

## 7. 같은 방식을 workflow로

05장의 `workflow-agent`가 성공한 경우 진행합니다. 프로필은 **실행 방식·검색·지침·API·통신 방식의 조합**입니다.

**워크플로 프로필 패키징**

```bash
python scripts/workshop.py --script package-hosted --kind workflow --pattern sequential --retrieval local --prompt v2 --api project-responses --protocol responses
```

**별도 서비스·폴더 준비**

```bash
python scripts/selfstudy.py prepare-hosted --kind runtime --package "실제-workflow-패키지-경로" --name workflow
```

**터미널 A도 같은 프로필로 실행**

```bash
python scripts/workshop.py serve --kind workflow --pattern sequential --retrieval local --prompt v2 --api project-responses --protocol responses
```

이제 **4~6절을 반복**합니다. 이전 서버는 먼저 중지하고, 다음 값만 이번 출력으로 바꿉니다.

| 항목 | 사용할 값 |
|---|---|
| 로컬 요청의 `--cwd` | 새 workflow 준비 폴더 |
| 배포·조회 서비스와 `--cwd` | 새 workflow 서비스·폴더 |
| 원격 요청의 `--version` | 이번 배포에서 조회한 버전 |

기본 `serve`의 단일 에이전트 결과를 워크플로 검증으로 대신하지 않습니다. 마지막에는 로컬 서버와 원격 세션을 모두 중지합니다.

## 완료 확인

- [ ] 패키지 경로·배포 폴더·서비스·버전을 구분했다.
- [ ] 로컬 준비 상태와 실제 답변을 각각 확인했다.
- [ ] 원격 새 버전의 답변 또는 차단 상태를 확인했다.
- [ ] 워크플로 프로필을 맞추고, 실행한 서버·세션을 중지했다.

---

[← 07. 평가](07-evaluation.md) · [전체 과정](../README.ko.md#진행-순서) · [09. 운영 →](09-operations.md) · [진행 지도 ↑](#chapter-map)
