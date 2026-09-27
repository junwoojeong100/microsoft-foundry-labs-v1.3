# 01. Foundry와 첫 모델 응답

**완료 목표:** Foundry를 설명하고, 내가 배포한 모델에서 실제 응답을 받습니다.

**시작 조건:** [00](00-setup.md)의 프로젝트·모델·권한·설정. 이 장에서 새 리소스를 추가할 필요는 없습니다.

## 무엇을 왜 배우는가

직원이 “출장 호텔을 예약해도 되는가?”라고 묻습니다. 답변이 빠르기만 해서는 부족합니다. 우리 규정을 알고, 날짜를 구분하고, 근거를 보여 주며, 실제 승인 권한이 없다는 경계를 지켜야 합니다.

| 말 | 이 과정의 뜻 |
|---|---|
| 모델 | 문장을 이해하고 생성하는 엔진 |
| 배포 이름 | 내 코드가 그 모델을 호출할 이름. 예: `workshop-chat` |
| 에이전트 | 모델에 업무 지침과 사용할 도구를 연결한 도우미 |
| 프로젝트 | 에이전트·평가·연결·파일 작업을 묶는 공간 |
| Foundry | 모델·에이전트·지식·도구·평가·운영을 함께 다루는 플랫폼 |

Azure OpenAI 모델 호출은 이 플랫폼에서 사용할 수 있는 기능 중 하나입니다. Microsoft 365 Copilot은 제공된 업무 경험, Copilot Studio는 로우코드 제작 환경, **Microsoft Agent Framework(MAF)는 코드 프레임워크**입니다. 서로 모두 같은 제품은 아닙니다.

## 1. 포털에서 한 번

1. Foundry에서 내 프로젝트를 선택합니다.
2. **Build → Models / Deployments → workshop-chat → Playground**를 엽니다.
3. 다음 질문을 보냅니다.

**Tools에 Web search가 기본 추가되어 있으면 이번 요청 전에 제거**합니다. 이 단계는 검색 없는 모델 호출이며, 불필요한 Bing 호출·추가 비용·데이터 이동을 포함하지 않습니다. 새 탭이나 새 대화에서도 도구 설정을 다시 확인합니다.

```text
처음 국내 출장을 가는 직원의 준비 체크리스트를 한국어 3줄로 써 주세요.
```

일정·목적·준비물 같은 일반 답변이 나오면 첫 모델 호출 성공입니다. **아직 한빛기술 규정을 검색하거나 업무 시스템에 연결한 것은 아닙니다.**

## 2. 같은 배포를 코드에서

v1.5 루트의 실습 터미널에서 실행합니다.

```bash
python scripts/workshop.py model --question "처음 국내 출장을 가는 직원의 준비 체크리스트를 한국어 3줄로 써 주세요." --output outputs/learner-notes-ko/01-model.json
```

실제 파일은 `outputs/learner-notes-ko/01-model.json`에 있습니다. 실행기가 출력한 위치를 사용하세요.

답변, 실제 모델/배포 정보, 응답 ID와 사용량을 읽습니다. 같은 질문도 문장이 매번 같을 필요는 없습니다. 빈 응답·오류는 성공이 아닙니다.

코드의 핵심은 `AIProjectClient → get_openai_client → responses.create`입니다. 이번에는 라이브러리 내부를 전부 외우지 않고 **내 프로젝트의 실제 배포를 호출했다**는 연결을 이해합니다.

### 프로젝트 API와 계정 API를 구분하기

포털 성공과 프로젝트 API 성공은 별개입니다. 프로젝트 호출에서 `Unsupported parameter: reasoning.effort`가 나거나 설정을 제거했는데도 500이 계속되면 원래 오류를 보관합니다. 모델을 재생성하거나 reasoning을 자동으로 제거하지 않습니다.

같은 Foundry 홈의 **Azure OpenAI endpoint**를 확인해 서비스 루트만 설정합니다. 화면 값이 `/openai/v1`으로 끝나면 그 경로 부분만 제외하고 아래에 넣습니다.

```bash
python scripts/selfstudy.py set AZURE_OPENAI_ENDPOINT "https://실제-foundry-domain.openai.azure.com"
python scripts/workshop.py model --api account-responses --question "처음 국내 출장을 가는 직원의 준비 체크리스트를 한국어 3줄로 써 주세요." --output outputs/learner-notes-ko/01-model-account.json
```

이 선택은 **같은 배포에 대한 명시적 계정 Responses 호출**입니다. 결과의 `inference_api: account-responses`를 기록합니다. File Search·Prompt Agent 같은 프로젝트 자산의 성공을 대신하지 않습니다. `model`, `answer`, `collect`만 이 옵션을 받으며 오류 후 자동 전환은 없습니다.

**Sweden Central에서 같은 증상이 재현되면:** 02의 `workshop-compare`(GPT-6 Sol / 2026-09-22)를 먼저 준비하고 프로젝트 API로 한 번 확인합니다.

```bash
python scripts/workshop.py --model-deployment workshop-compare model --question "한국어 한 문장으로 인사해 주세요." --output outputs/learner-notes-ko/01-sol-project-check.json
```

성공을 확인한 뒤, 03 이후의 **기본 실행 배포를 Sol로 명시적으로 선택**합니다. 00과 동일한 ID·Endpoint·prefix를 사용합니다.

```bash
python scripts/selfstudy.py configure --project-id "실제-프로젝트-ARM-ID" --endpoint "실제-프로젝트-Endpoint" --deployment workshop-compare --expected-model gpt-6-sol --prefix "내-lab-접두사"
```

기존 Luna 배포는 그대로 둡니다. 이후 “기본 모델”은 실제 설정값을 뜻하며, Luna의 에이전트 경로를 검증했다고 쓰지 않습니다. 이미 agent나 결과를 만들었다면 새 소유 이름·label을 사용하고 `--name`을 생성과 호출에 동일하게 지정합니다. Sol을 기본 답변으로 선택했다면 07에서 **별도 `workshop-judge` 배포**를 준비합니다. 같은 모델 계열이라는 자기 평가 편향은 별도 배포로도 사라지지 않습니다.

## 3. 세 가지 구현을 미리 구분

| 구현 | 정의/실행 위치 | 이후 실습 |
|---|---|---|
| Prompt Agent | Foundry에 지침·도구·버전을 저장 | 03 |
| 로컬 MAF/워크플로 | 내 Python에서 작업을 구성, 모델은 Azure 호출 | 04~05 |
| Hosted Agent | 내 코드를 Foundry 런타임에 배포 | 08 |

모두 같은 합성 업무를 다루지만 같은 객체는 아닙니다. 로컬 결과를 원격 배포의 성공 증거로 옮기지 않습니다.

## 기록과 확인

워크북에 프로젝트, 기반 모델/버전, 배포 이름, 응답 ID, 결과 파일을 기록합니다.

**스스로 설명:** “Foundry는 ______이고, 모델 호출만으로 부족한 ______를 함께 다룬다.”

**막히면:** 401/403은 사용자·테넌트·데이터 역할, 404는 프로젝트 Endpoint와 **배포 이름**, 429는 할당량부터 확인합니다. [문제 해결](troubleshooting.md).

**다음 → [02. 모델·프롬프트·비교·Router](02-models-prompts.md)**
