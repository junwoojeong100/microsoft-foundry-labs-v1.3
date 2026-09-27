# F01. 모델 선택과 운영

**목표:** 이미 승인된 모델 두 개를 같은 질문·지침·근거로 비교합니다. 모델 수명 주기와 Router도 기능 범위에 유지합니다.

준비: [기능 환경](README.md), 구조화 응답/Responses를 지원하는 승인 배포 두 개, 각 6문항의 호출 비용. 시간: 30~45분. 이 카드에서 새 모델을 배포하거나 기존 모델을 폐기하지 않습니다.

## 1. 비교 조건 고정

모델 A/B의 실제 모델명, 버전, 배포 이름, 리전·유형을 적습니다. 같은 v1.2 dev 세트, v2 지침, local 검색, 출력 한도를 사용합니다. 모델 외 조건이 다르면 “모델 하나만 바꾼 실험”이 아닙니다.

## 2. 각 모델로 여섯 문항

따옴표 안은 실제 **배포 이름**으로 바꿉니다. `--model-deployment`는 이 실행에만 적용되며 `.env`나 Azure의 active 배포를 바꾸지 않습니다.

```bash
python scripts/v12.py --model-deployment "실제-배포-A" collect --split dev --label model-a --prompt v2 --retrieval local
python scripts/v12.py --model-deployment "실제-배포-B" collect --split dev --label model-b --prompt v2 --retrieval local
python scripts/v12.py evaluate --label model-a
python scripts/v12.py evaluate --label model-b
python scripts/v12.py compare --baseline model-a --candidate model-b --variable model
```

실제 응답, 오류, 근거, 토큰·지연을 함께 봅니다. 실패 행을 빼거나 다른 모델로 자동 대체하지 않습니다. API/schema 미지원은 그 자체로 호환성 결과입니다.

## 3. 선택 이유 한 문장

```text
우리는 ______ 업무에서 ______를 우선하므로 모델 ____를 선택했다.
근거는 ______이고, 아직 확인하지 못한 것은 ______이다.
```

작은 6문항 결과를 모든 작업의 성능 순위로 일반화하지 않습니다. 이전 모델을 유지할 조건과 되돌릴 방법도 적습니다.

## 4. Router는 별도 시스템

Router는 고정 모델 A의 다른 이름이 아니라 **요청을 보고 모델을 고르는 시스템**입니다.

준비된 Router가 있을 때만 포털의 배포·버전·허용 모델 범위를 확인하고 동일 질문 세트를 보냅니다. 품질·지연·비용 외에 실제 선택 모델 분포를 확인합니다. 선택 모델이 노출되지 않으면 “선택 모델 미확인”으로 기록합니다.

직접 Responses 호출도 그 Router가 지원한다고 확인한 경우에만 사용합니다. 직접 모델 실패 시 Router로 몰래 전환하지 않습니다.

**완료:** 두 모델의 전체 행과 선택/보류 이유, Router는 실행 또는 미실행 상태. **정리:** 비교는 배포 삭제가 아닙니다. 공유 모델 변경·폐기는 담당자 승인 범위에서만 수행합니다.

원본의 세부 조건: [모델 운영](https://github.com/junwoojeong100/microsoft-foundry-v1.2-labs/blob/c2065477baf8210bbba4b845ab741ecd527b9559/docs/ko/labs/extensions/model-operations.md) · [모델 Lab](https://github.com/junwoojeong100/microsoft-foundry-v1.2-labs/blob/c2065477baf8210bbba4b845ab741ecd527b9559/docs/ko/labs/02-models.md).

[기본 Lab 02](../02-models-prompts.md) · [기능 목록](README.md)
