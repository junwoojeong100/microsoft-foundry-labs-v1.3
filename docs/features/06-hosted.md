# F06. 로컬 코드를 Hosted Agent로 옮기기

**목표:** 패키지 생성, 로컬 모델 호출, 원격 배포를 구분하면서 같은 코드를 서비스로 옮깁니다.

준비: [기능 환경](README.md), F02의 MAF 함수 실행, Hosted 지원 리전/용량, 정확한 프로젝트 ARM ID와 location, azd와 Foundry 확장, 런타임 identity 권한. **원격 단계는 배포·세션 비용의 별도 승인이 있어야 합니다.** 시간: 준비 후 45~75분.

## 1. 안전한 패키지부터

```bash
python scripts/v12.py --script package-hosted
```

반환된 경로의 `package-manifest.json`을 엽니다. 처음 생성 위치는 `.reference/v1.2/.build/hosted/`입니다.

확인할 것:

- 코드·가상 정책·지침과 파일 해시가 있음.
- `.env`, 자격 증명, 실행 결과, dev/holdout 정답이 없음.
- `cloud_deployed: false`임.

이미 패키지가 있으면 내용을 확인합니다. 재생성이 필요하면 기존 패키지를 다른 개인 경로로 옮겨 보관한 뒤 다시 생성합니다. 기존 폴더를 강제로 덮어쓰지 않습니다. **패키지가 생겼다는 것은 배포했다는 뜻이 아닙니다.**

## 2. 별도 Hosted 프로젝트 준비

담당자에게 다음 다섯 값을 받습니다. Endpoint를 보고 ARM ID를 추측하지 않습니다.

| 값 | 출처 |
|---|---|
| 패키지 절대 경로 | 앞 명령의 실제 출력 |
| 새 빈 Hosted 폴더의 절대 경로 | 이 소스 복사본 밖의 개인 폴더 |
| 프로젝트 ARM resource ID | Azure 프로젝트 리소스의 JSON View `id` |
| 프로젝트 location 코드 | 실제 리소스 location |
| 고유 Hosted agent 이름 | 본인 Prefix의 새 이름 |

자리표시자를 실제 값으로 바꾼 뒤 실행합니다.

```bash
python scripts/v12.py --script prepare-hosted --language ko --kind runtime --package "실제-패키지-절대경로" --directory "새-빈-Hosted-절대경로" --agent-name "실제-고유-이름" --initialize-env --project-id "실제-프로젝트-ARM-ID" --location "실제-location-코드"
```

새 `azure.yaml`에 **기존 프로젝트 연결과 의도한 agent 하나**가 있는지 확인합니다. 준비 도구는 패키지 해시와 범위를 검사합니다. 새 모델·역할·Azure 배포를 자동으로 생성하는 명령이 아닙니다.

원본의 [Hosted 준비·실행 가이드](https://github.com/junwoojeong100/microsoft-foundry-v1.2-labs/blob/c2065477baf8210bbba4b845ab741ecd527b9559/docs/ko/labs/08-hosted.md)에 세부 입력 출처와 현재 manifest 검사가 있습니다.

## 3. 로컬에서 실제 모델 호출

터미널 A, v1.5 루트:

```bash
python scripts/v12.py serve
```

터미널 B에서 이 서버의 준비 상태를 확인합니다.

```bash
curl --fail http://127.0.0.1:8088/readiness
```

준비 상태만 확인하고 끝내지 않습니다. 앞에서 만든 **실제 Hosted 디렉터리**로 호출합니다.

```bash
azd ai agent invoke --cwd "실제-Hosted-절대경로" --local --port 8088 --new-session --new-conversation --timeout 120 "2026년 9월 국내 출장 숙박비 한도와 근거를 알려주세요."
```

실제 답변·근거·Session/Conversation을 기록합니다. 로컬 서버도 모델은 Azure를 호출하므로 비용이 있습니다. A에서 `Ctrl+C`로 서버를 멈춥니다.

## 4. 원격 배포가 승인된 경우

프로젝트가 있어도 런타임 identity·네트워크·용량·지원 리전은 별도입니다. 준비되지 않았다면 여기서 중단하며 `원격 미실행`으로 기록합니다.

승인된 **해당 서비스만** 배포하고 실제 상태를 확인합니다.

```bash
azd deploy "실제-agent-서비스-이름" --cwd "실제-Hosted-절대경로"
azd ai agent show --cwd "실제-Hosted-절대경로" --output json
```

배포 실패 시 이전 active 버전을 성공 증거로 쓰지 않습니다. 새 버전의 active 상태와 실제 번호를 기록한 뒤 호출합니다.

```bash
azd ai agent invoke --cwd "실제-Hosted-절대경로" --version "방금-확인한-버전" --new-session --new-conversation --timeout 270 "2026년 9월 국내 출장에서 170000원 호텔의 사전 승인 조건은?"
```

응답·Session·Conversation·Trace ID를 보관합니다. 이 버전의 실제 품질은 별도의 dev 평가로 확인해야 합니다. 기본 과정의 로컬 앱 점수를 원격 Hosted의 점수로 옮기지 않습니다.

## 5. 워크플로·Toolbox·고정 matrix도 유지

| 확장 | 시작 조건과 실제 절차 |
|---|---|
| MAF workflow를 Responses Hosted로 | [원본 Hosted의 workflow 절](https://github.com/junwoojeong100/microsoft-foundry-v1.2-labs/blob/c2065477baf8210bbba4b845ab741ecd527b9559/docs/ko/labs/08-hosted.md) |
| Toolbox를 같은 코드로 로컬/원격 실행 | [Hosted Toolbox](https://github.com/junwoojeong100/microsoft-foundry-v1.2-labs/blob/c2065477baf8210bbba4b845ab741ecd527b9559/docs/ko/labs/extensions/toolbox-hosted.md) |
| 고정 Invocations/model matrix/회귀/trace | [Hosted 평가 워크북](https://github.com/junwoojeong100/microsoft-foundry-v1.2-labs/blob/c2065477baf8210bbba4b845ab741ecd527b9559/docs/ko/reference/evaluation-workbook.md) |

**완료:** 패키지 / 로컬 추론 / 원격 배포를 각각 실제 상태로 기록합니다. 서비스 GA와 사용 SDK prerelease는 따로 확인합니다.

**정리:** 생성한 Hosted 버전·세션·별도 리소스와 잔여 과금을 담당자와 확인합니다. 고정 원본의 [정리 가이드](https://github.com/junwoojeong100/microsoft-foundry-v1.2-labs/blob/c2065477baf8210bbba4b845ab741ecd527b9559/docs/ko/reference/cleanup.md)를 사용하며 공유 프로젝트 전체를 삭제하지 않습니다.

[기본 Lab 06](../06-app-operations.md) · [기능 목록](README.md)
