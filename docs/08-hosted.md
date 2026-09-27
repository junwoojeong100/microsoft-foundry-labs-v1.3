# 08. Hosted 로컬 실행과 Azure 배포

**완료 목표:** 내 코드를 패키지로 만들고, 로컬 실제 호출 후 Foundry에 배포해 원격 버전을 호출합니다.

**시작 조건:** 04의 MAF 함수 실행, 00의 프로젝트·ARM ID·location, 실제 모델. **배포 권한은 내 구독 Owner로 준비**하며, 런타임 데이터 접근은 별도로 부여합니다.

## 1. azd Foundry 명령 준비

```bash
azd version
azd extension list --installed
```

`microsoft.foundry`가 없다면 설치합니다. 이미 있다면 재설치하지 않습니다.

```bash
azd extension install microsoft.foundry
azd auth login
azd ai agent show --help
```

현재 구독·리전의 Hosted 지원과 용량을 확인합니다. 지원되지 않으면 이 장은 차단으로 기록하고 **기존 프로젝트를 임의로 재생성하지 않습니다**. 코드 배포에는 Docker/ACR 로컬 설치가 필수는 아닙니다.

## 2. 안전한 패키지

```bash
python scripts/workshop.py --script package-hosted
```

출력 경로의 `package-manifest.json`, `runtime-profile.json`, `requirements.txt`를 엽니다. 기본 경로는 `.build/hosted/`입니다.

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

명령이 **서비스 이름, 폴더, 다음 배포/조회 명령**을 출력합니다. 이후의 서비스 이름과 Hosted 경로에는 이 값을 사용합니다.

서비스 이름, `main.py`, Python 3.13, Responses protocol, 실제 Endpoint와 모델, 원격 인증 `managed-identity`를 확인합니다.

## 4. 로컬 실제 호출

터미널 A, v1.5 루트:

```bash
python scripts/workshop.py serve
```

터미널 B:

```bash
curl --fail http://127.0.0.1:8088/readiness
azd ai agent invoke --cwd "실제-Hosted-절대경로" --local --port 8088 --new-session --new-conversation --timeout 120 "2026년 9월 국내 출장 숙박비 한도와 근거를 알려주세요."
```

readiness가 실패하면 invoke를 실행하지 않습니다. 상태 `healthy`는 서버 준비, 실제 답변·근거는 추론 성공입니다. 로컬 서버도 Azure 모델 비용이 있습니다.

확인 후 A에서 `Ctrl+C`로 내 서버를 종료합니다.

## 5. 원격 배포

구독·프로젝트·서비스 이름과 코드/세션 비용을 직접 확인한 뒤 **해당 서비스만** 배포합니다.

```bash
azd deploy "실제-agent-서비스-이름" --cwd "실제-Hosted-절대경로"
azd ai agent show "실제-agent-서비스-이름" --cwd "실제-Hosted-절대경로" --output json
```

배포 실패 후 과거 active 버전을 이번 성공으로 쓰지 않습니다. 실제 새 `name`, `version`, `status`, endpoint를 기록합니다.

### 런타임에 필요한 역할

`show`가 반환한 **`instance_identity.principal_id`**는 내 사용자, agent 이름, client ID와 다릅니다.

```bash
python scripts/selfstudy.py roles --user-object-id "내-사용자-Object-ID" --hosted-principal-id "실제-instance_identity.principal_id"
```

이 출력은 계획입니다. **실제 배포한 이름·버전의 ID**인지 대조한 뒤 런타임의 Foundry User 등 필요한 역할만 그 리소스 범위에 부여합니다. 로컬 `az login` 성공이 원격 런타임 권한을 주지는 않습니다.

## 6. 정확한 원격 버전 호출

```bash
azd ai agent invoke --cwd "실제-Hosted-절대경로" --version "방금-확인한-버전" --new-session --new-conversation --timeout 270 "2026년 9월 국내 출장에서 170000원 호텔의 사전 승인 조건은?"
```

실제 응답·근거·Session·Conversation·Trace ID를 기록합니다. 한 번의 성공은 07의 전체 품질 평가를 대신하지 않습니다.

세션을 계속 쓸 계획이 없으면 **내가 방금 만든 세션**만 중지합니다.

```bash
azd ai agent sessions list --cwd "실제-Hosted-절대경로" --limit 10
azd ai agent sessions stop "실제-내-session-id" --cwd "실제-Hosted-절대경로"
```

stop은 실행 compute를 중지하지만 persistent volume까지 삭제하지 않습니다. 이후 삭제와 보관 비용도 마지막 장에서 확인합니다.

## 7. 같은 방식을 workflow로

05의 `workflow-agent`가 성공한 뒤:

```bash
python scripts/workshop.py --script package-hosted --kind workflow --pattern sequential --retrieval local --prompt v2 --api project-responses --protocol responses
```

출력된 **새 프로필의 패키지 경로**를 사용해 3~6절을 반복합니다. 이름은 `<prefix>-workflow`, 폴더도 별도로 만듭니다. 단일-agent 패키지나 과거 버전을 대신 사용하지 않습니다.

**완료:** 패키지 생성 / 로컬 추론 / 원격 배포·응답을 각각 확인했습니다. 새 Hosted 폴더·정확한 버전·세션 정리 상태를 보관합니다.

**다음 → [09. Trace·Insights·운영](09-operations.md)**
