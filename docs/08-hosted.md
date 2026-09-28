# 08. Hosted 로컬 실행과 Azure 배포

[English](en/08-hosted.md) | **한국어** · [전체 과정](../README.ko.md#진행-순서) · [진행 도움말](checkpoints.md)

**완료 목표:** 내 코드를 패키지로 만들고, 로컬 실제 호출 후 Foundry에 배포해 원격 버전을 호출합니다.

**시작 조건:** 04의 MAF 함수 실행, 00의 프로젝트·ARM ID·location, 실제 모델. **배포 권한은 내 구독 Owner로 준비**하며, 런타임 데이터 접근은 별도로 부여합니다.

**실행 위치:** 터미널에서 패키징·배포·호출, 편집기에서 설정 확인, Azure 포털에서 역할 확인. 로컬 호출은 터미널 A·B를 사용합니다.

<a id="chapter-map"></a>

**진행 지도**

| 단계 | 확인할 결과 |
|---|---|
| [1. azd 준비](#1-azd-foundry-명령-준비) | Foundry 확장과 Hosted 지원 |
| [2. 패키징](#2-안전한-패키지) | 비밀·평가 정답을 제외한 패키지 |
| [3. 별도 배포 폴더](#3-기존-프로젝트에-연결하는-독립-폴더) | 실제 서비스·폴더·프로젝트 값 |
| [4. 로컬 호출](#4-로컬-실제-호출) | 서버 준비와 실제 응답을 각각 확인 |
| [5. 원격 배포·역할](#5-원격-배포) | 새 버전과 그 런타임 ID |
| [6. 원격 호출·중지](#6-정확한-원격-버전-호출) | 같은 버전의 응답과 세션 중지 |
| [7. workflow로 반복](#7-같은-방식을-workflow로) | workflow 프로필의 로컬·원격 결과 |
| [완료 확인](#완료-확인) | 패키징·로컬·원격 성공을 구분 |

패키지 경로, 배포 폴더, 서비스 이름은 서로 다릅니다. [3절의 값 복사 표](#3-기존-프로젝트에-연결하는-독립-폴더)에서 출처를 확인하고 해당 출력값을 다음 명령에 직접 사용합니다.

## 1. azd Foundry 명령 준비

```bash
azd version
```

**설치된 Foundry 확장 확인**

```bash
azd extension list --installed
```

`microsoft.foundry`가 없다면 설치합니다. 이미 있다면 재설치하지 않습니다.

```bash
azd extension install microsoft.foundry
```

**같은 테넌트로 azd 로그인**

```bash
azd auth login
```

**Foundry 명령 사용 가능 여부 확인**

```bash
azd ai agent show --help
```

현재 구독·리전의 Hosted 지원과 용량을 확인합니다. 지원되지 않으면 이 장은 차단으로 기록하고 **기존 프로젝트를 임의로 재생성하지 않습니다**. 코드 배포에는 Docker/ACR 로컬 설치가 필수는 아닙니다.

원격 배포만 막힌 경우에도 1~3절의 **로컬 준비 폴더**는 뒤의 프로젝트 연결에 사용할 수 있습니다. 준비가 성공했다면 그 폴더를 보관하고, 원격 배포/호출은 미실행으로 구분합니다. 폴더 준비 자체가 실패했다면 준비된 것으로 기록하지 않습니다.

## 2. 안전한 패키지

```bash
python scripts/workshop.py --script package-hosted
```

**확인:** 출력 경로의 `package-manifest.json`, `runtime-profile.json`, `requirements.txt`를 엽니다. 기본 경로는 `.build/hosted/`입니다.

코드·합성 정책·지침은 있고, `.env`·인증정보·평가 정답·실행 결과는 없어야 합니다. `cloud_deployed: false`는 **패키징 결과**이며 Azure 조회 결과가 아닙니다.

이미 패키지가 있으면 내용을 먼저 읽습니다. 다시 만들 필요가 있을 때만 이전 패키지를 다른 개인 경로에 보관한 후 재생성합니다.

## 3. 기존 프로젝트에 연결하는 독립 폴더

```bash
python scripts/selfstudy.py status
```

프로젝트 ID·리전·접두사는 저장한 설정을 재사용합니다. 앞 명령이 출력한 **패키지 경로 하나만** 넣습니다.

```bash
python scripts/selfstudy.py prepare-hosted --kind runtime --package "실제-패키지-경로" --name hosted
```

생성된 `azure.yaml`에는 기존 프로젝트 연결과 의도한 Hosted 서비스 하나만 있어야 합니다. 모델 배포 목록을 새로 추가하거나 소스 전체를 서비스로 만들지 않습니다. 별도 Foundry 프로젝트를 또 provision할 필요가 없는 경로입니다.

`prepare-hosted`는 로컬 manifest/azd 환경만 준비하며 아직 배포하거나 모델을 호출하지 않습니다. 같은 준비 폴더가 이미 있으면 덮어쓰지 말고 기존 경로를 재사용합니다. 새 준비가 필요한 경우만 `--run second`처럼 새 이름을 지정합니다.

영문 패키지를 준비할 때는 `prepare-hosted`에도 `--language en`을 명시합니다. 패키지의 언어와 준비 단계의 언어가 다르면 중단하며 한국어 프로필로 자동 변경하지 않습니다.

명령이 **서비스 이름, 폴더, 다음 배포/조회 명령**을 출력합니다. 이후의 서비스 이름과 Hosted 경로에는 이 값을 사용합니다.

**출력된 배포 명령을 지금 바로 실행하지 않습니다.** 아래 표에서 값의 출처만 확인하고, 4절의 로컬 확인을 마친 뒤 5절에서 실행합니다.

| 다음 명령에 넣을 값 | 복사할 곳 | 넣으면 안 되는 값 |
|---|---|---|
| `--package` | 2절 package 명령이 반환한 `.build/...` 경로 | 저장소 루트나 `.selfstudy` 폴더 |
| `azd deploy`/`show` 뒤의 서비스 이름 | `prepare-hosted` 출력의 **`서비스:`** 전체 값 | `--name`에 넣은 짧은 `hosted`만 |
| `--cwd` | 같은 출력의 **`폴더:`** 절대 경로 | 패키지 폴더, `azure.yaml` 파일 경로 |
| 원격 `--version` | 5절 `show` 결과의 **`version` 값** | prompt 이름 `v2`, 패키지명, 추측한 `latest` |
| 역할 부여 대상 | 같은 `show`의 **`instance_identity.principal_id`** | 내 사용자 ID나 Client ID |

따옴표 안 자리표시자만 바꾸고 따옴표는 남깁니다. `--cwd`를 사용해도 터미널은 계속 실습 루트에 둡니다. 7절 workflow와 10·12장에서는 **그 배포가 출력한 값**을 사용합니다.

터미널 출력을 닫았더라도 `.selfstudy/` 아래의 해당 `azure.yaml`을 열면 `name`과 `services`에서 서비스 이름을 확인할 수 있습니다. 그 파일이 있는 **폴더의 절대 경로**가 `--cwd`이며, 버전은 아래 `show`로 다시 조회합니다. 별도 기록 파일을 만들 필요는 없습니다.

서비스 이름, `main.py`, Python 3.13, Responses protocol, 실제 Endpoint와 모델, 원격 인증 `managed-identity`를 확인합니다.

## 4. 로컬 실제 호출

### 터미널 A: 서버 시작

터미널 A, v1.5 루트에서 실행한 채 둡니다. [두 터미널 사용법](checkpoints.md#두-터미널을-사용하는-장).

```bash
python scripts/workshop.py serve
```

### 터미널 B: 준비 상태 확인 후 요청

새 터미널 B도 같은 루트에서 `.venv`를 활성화합니다. 아래 Python 상태 확인은 macOS/Linux와 PowerShell 모두 사용할 수 있습니다.

```bash
python -c "from urllib.request import urlopen; print(urlopen('http://127.0.0.1:8088/readiness', timeout=10).read().decode())"
```

**확인:** 상태가 `healthy`여야 합니다. 실패하면 아래 요청을 실행하지 말고 터미널 A의 서버 로그부터 확인합니다.

**준비 상태를 확인한 뒤 모델에 요청**

```bash
azd ai agent invoke --cwd "실제-Hosted-절대경로" --local --port 8088 --new-session --new-conversation --timeout 120 "2026년 9월 국내 출장 숙박비 한도와 근거를 알려주세요."
```

**확인:** 실제 답변·근거가 있어야 추론 성공입니다. 앞의 `healthy`는 서버 준비만 뜻합니다. 로컬 서버도 Azure 모델 비용이 있습니다.

**중지:** 확인 후 A에서 `Ctrl+C`로 내 서버를 종료합니다.

## 5. 원격 배포

구독·프로젝트·서비스 이름과 코드/세션 비용을 직접 확인한 뒤 **해당 서비스만** 배포합니다.

```bash
azd deploy "실제-agent-서비스-이름" --cwd "실제-Hosted-절대경로"
```

**배포된 실제 버전과 런타임 ID 조회**

```bash
azd ai agent show "실제-agent-서비스-이름" --cwd "실제-Hosted-절대경로" --output json
```

배포 실패 후 과거 active 버전을 이번 성공으로 쓰지 않습니다. 실제 새 `name`, `version`, `status`, endpoint를 기록합니다.

### 런타임에 필요한 역할

`show`가 반환한 `instance_identity.principal_id`는 내 사용자, agent 이름, client ID와 다릅니다.

```bash
python scripts/selfstudy.py roles --user-object-id "내-사용자-Object-ID" --hosted-principal-id "실제-instance_identity.principal_id"
```

이 출력은 계획입니다. **실제 배포한 이름·버전의 ID**인지 대조한 뒤 런타임의 Foundry User 등 필요한 역할만 그 리소스 범위에 부여합니다. 로컬 `az login` 성공이 원격 런타임 권한을 주지는 않습니다.

## 6. 정확한 원격 버전 호출

```bash
azd ai agent invoke --cwd "실제-Hosted-절대경로" --version "방금-확인한-버전" --new-session --new-conversation --timeout 270 "2026년 9월 국내 출장에서 170000원 호텔의 사전 승인 조건은?"
```

**확인:** 실제 응답·근거·Session·Conversation·Trace ID를 기록합니다. 한 번의 성공은 07의 전체 품질 평가를 대신하지 않습니다.

세션을 계속 쓸 계획이 없으면 **내가 방금 만든 세션**만 중지합니다.

```bash
azd ai agent sessions list --cwd "실제-Hosted-절대경로" --limit 10
```

**목록에서 확인한 내 세션만 중지**

```bash
azd ai agent sessions stop "실제-내-session-id" --cwd "실제-Hosted-절대경로"
```

stop은 실행 compute를 중지하지만 persistent volume까지 삭제하지 않습니다. 이후 삭제와 보관 비용도 마지막 장에서 확인합니다.

## 7. 같은 방식을 workflow로

05의 `workflow-agent`가 성공한 뒤:

```bash
python scripts/workshop.py --script package-hosted --kind workflow --pattern sequential --retrieval local --prompt v2 --api project-responses --protocol responses
```

출력된 **새 프로필의 패키지 경로**로 별도 서비스/폴더를 준비합니다.

```bash
python scripts/selfstudy.py prepare-hosted --kind runtime --package "실제-workflow-패키지-경로" --name workflow
```

4~6절을 반복하되 **터미널 A의 로컬 서버도 workflow 프로필로** 실행합니다. 기본 `serve`는 단일-agent이므로 이 요청의 검증을 대신하지 않습니다.

```bash
python scripts/workshop.py serve --kind workflow --pattern sequential --retrieval local --prompt v2 --api project-responses --protocol responses
```

터미널 B의 상태 확인·로컬 호출·배포에는 방금 출력된 **workflow 서비스 이름과 폴더**를 사용합니다. 이전 서버는 먼저 `Ctrl+C`로 중지하며, 단일-agent 패키지나 과거 버전을 대신 사용하지 않습니다.

## 완료 확인

- [ ] 패키지·배포 폴더·서비스 이름을 구분하고 실제 출력값을 사용했다.
- [ ] 로컬 준비 상태와 실제 모델 응답을 각각 확인했다.
- [ ] 원격 새 버전의 응답 또는 차단 상태를 확인하고, 내가 만든 세션을 중지했다.
- [ ] workflow를 단일-agent 프로필과 섞지 않았다.

새 Hosted 폴더·정확한 버전·세션 정리 상태를 보관합니다.

---

[← 07. 평가](07-evaluation.md) · [전체 과정](../README.ko.md#진행-순서) · [09. 운영 →](09-operations.md) · [진행 지도 ↑](#chapter-map)
