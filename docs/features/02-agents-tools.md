# F02. MAF, 함수, MCP와 추가 도구

**목표:** 같은 Foundry 모델에 도구를 붙이는 방법을 구분하고, 실제 실행을 확인합니다.

준비: [기능 환경](README.md), 모델 호출 비용. v1.2의 **합성 정책 조회 도구**를 사용합니다. 기본 과정의 다온테크 계산 함수와 다른 실행입니다. 시간: 첫 세 단계 30~45분.

## 1. MAF 에이전트 호출

```bash
python scripts/v12.py maf --question "Foundry와 Agent Framework의 차이를 세 문장으로 설명해 주세요." --output outputs/learner-notes-ko/f02-agent.json
```

`orchestration: local`, `tools: none`과 실제 답변을 봅니다. **MAF는 코드 프레임워크이고 Foundry는 모델·에이전트 플랫폼**입니다.

## 2. 읽기 전용 함수 도구

```bash
python scripts/v12.py maf --tools --question "2026년 9월 국내 출장 호텔이 170000원인데 예약해도 되나요? 한도와 절차를 알려주세요." --output outputs/learner-notes-ko/f02-function.json
```

`lookup_policy`가 동봉한 합성 문서를 조회합니다. `tools: function`, 실제 도구 이력, `answer`의 금액·인용·승인 조건을 봅니다. 실제 예약은 하지 않습니다.

## 3. 같은 업무를 로컬 MCP로

```bash
python scripts/v12.py maf --mcp --question "2026년 5월 국내 출장 숙박비의 1박 한도는 얼마인가요?" --output outputs/learner-notes-ko/f02-mcp.json
```

클라이언트가 같은 가상 환경으로 로컬 MCP 서버를 실행하고 stdio로 통신합니다. 공개 URL이나 API key를 만들지 않습니다. 도구 목록을 보는 것과 모델이 실제로 도구를 호출하는 것을 구분하세요.

| 방식 | 핵심 차이 |
|---|---|
| Python 함수 | 앱 내부 함수를 도구로 노출 |
| MCP | 도구를 표준 프로토콜로 제공/호출 |
| OpenAPI | HTTP API의 계약을 설명 |
| Code Interpreter | 관리되는 실행 환경에서 데이터/파일 작업 |

## 4. 추가 도구도 유지

첫 추가 도구는 **합성 정책의 CSV를 만드는 Code Interpreter**입니다. 지원 모델/도구 권한, 생성·세션 비용과 정리 범위를 먼저 확인합니다.

```bash
python scripts/v12.py code-interpreter run --label f02-code-table --confirm-create --confirm-cost
```

반환 파일의 ID·다운로드 결과·CSV 내용을 원본 정책과 대조합니다. “파일을 만들었다”는 텍스트만으로 완료 처리하지 않습니다.

필요한 결과를 보관한 뒤 **해당 실행의 임시 자산을 삭제하기로 결정한 경우에만** 실행합니다.

```bash
python scripts/v12.py code-interpreter cleanup --label f02-code-table --confirm-delete
```

OpenAPI는 본인 소유의 준비된 Search API에 대한 읽기 전용 경로로 유지합니다. [추가 도구 절차](https://github.com/junwoojeong100/microsoft-foundry-v1.2-labs/blob/c2065477baf8210bbba4b845ab741ecd527b9559/docs/ko/labs/extensions/additional-tools.md)의 연결·identity 확인부터 진행합니다. Toolkit은 [개발 도구 준비](https://github.com/junwoojeong100/microsoft-foundry-v1.2-labs/blob/c2065477baf8210bbba4b845ab741ecd527b9559/docs/ko/labs/extensions/developer-toolkit.md)에 유지합니다.

**완료:** 함수와 MCP의 실제 호출/결과, Code Interpreter는 실제 파일 또는 미실행 상태. **정리:** 로컬 프로세스 종료와 각 도구의 소유 자산 정리는 별개입니다.

세부 계약과 도구 평가: [v1.2 MAF·도구](https://github.com/junwoojeong100/microsoft-foundry-v1.2-labs/blob/c2065477baf8210bbba4b845ab741ecd527b9559/docs/ko/labs/04-agents-tools.md).

[기본 Lab 04](../04-tools.md) · [기능 목록](README.md)
