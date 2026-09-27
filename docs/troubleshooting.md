# 문제 해결 — 같은 오류에 재생성부터 하지 않기

**현재 장, 마지막 성공, 실제 대상/버전, 오류 원문을 기록합니다.** 비밀번호·토큰·API key·회사 데이터는 기록하거나 공유하지 않습니다.

| 증상 | 먼저 확인할 것 | 다음 행동 |
|---|---|---|
| Python/패키지 오류 | `.reference/v1.2/.venv`의 Python 3.13인가 | 00의 환경 활성화/설치. 루트 축약 예제 SDK와 혼합 금지 |
| `az`/`azd`/Foundry 명령 없음 | 도구와 `microsoft.foundry` 확장 | 00/08의 설치. 기존 동작 환경을 무조건 업그레이드하지 않음 |
| configure에 계정 ARM ID 입력 | `/projects/...`까지 있는가 | 프로젝트 JSON View의 실제 id 복사 |
| Endpoint 불일치 | 모델 URL, 다른 계정/프로젝트 URL인가 | 같은 프로젝트 홈의 Endpoint와 실제 customSubDomainName 대조 |
| `.env`/셸 설정 충돌 | 과거 export가 우선하는가 | 해당 변수 해제 또는 새 터미널. 다른 프로젝트로 자동 전환하지 않음 |
| 401/로그인 만료 | 사용자·tenant·구독 일치 | 정상 로그인/MFA. 토큰 복사나 client secret 생성으로 우회 금지 |
| Owner인데 모델/agent 403 | Foundry 데이터 역할 | 본인/실제 서비스 ID의 Foundry User와 범위 확인 |
| Search 403 | RBAC/Both 인증, 실제 caller, 데이터 역할 | 내 사용자·프로젝트 MI·계정 MI·Search MI를 구분 |
| Toolbox 목록은 되는데 query 실패 | downstream Search 접근 | 프로젝트 MI의 Index Data Reader와 필요한 Service Contributor 확인 |
| OpenAPI만 실패 | 계정 MI인가, API 버전 인자인가 | `openapi plan`의 주체와 내부 오류 확인. Toolbox ID와 다름 |
| Hosted만 403 | `instance_identity.principal_id` 역할 | 로컬 로그인 반복 대신 실제 원격 ID에 필요한 역할 |
| 모델/버전/지역 제공 안 됨 | 실제 가용성·quota | 정식 quota 요청 또는 명시적 새 계획. 실행 중 몰래 모델 교체 금지 |
| 429 | 공유 한도·동시 요청 | 중단/대기 후 제한적 재시도. 전후 평가 조건을 유지 |
| Provider 등록/Policy 거부 | Subscription의 provider와 조직 정책 | Owner로 가능한 등록은 Portal 절차 사용. 상위 정책 우회 금지 |
| Public access disabled/timeout | Private Link·DNS·client 위치 | 승인된 네트워크 경로 사용. 공유 방화벽/인증서 보호 해제 금지 |
| File Search 버튼/인용 없음 | 모델·지역·도구 설정·인덱싱 | 인라인 답변을 검색 성공으로 바꾸지 않음 |
| 과거/현행 혼동 | 질문 날짜와 적용 기간 | 원문 120,000/150,000원 구분, 실제 실패 기록 |
| Search 기능 과금 오류 | Semantic/Knowledge retrieval 각각의 플랜 | Free 기능과 Basic 서비스 비용을 구분하고 추가 지출을 결정 |
| Hybrid schema/차원 오류 | 실제 embedding 차원과 새 index | 0 벡터/잘라낸 벡터 금지. 기존 index를 덮어쓰지 않음 |
| IQ Chat check 실패 | 고정 모델/버전·Search MI·역할 | 지원 조건을 해결하거나 해당 preset 차단으로 기록 |
| label/파일/패키지가 이미 존재 | 이전 실제 결과인가 | 먼저 읽고, 새 요청/패키지에는 새 이름/경로. 실패 삭제 금지 |
| benchmark 고정 조건 오류 | 모델 map·코드·원문·API·버전·동시성 | 비교 가능 조건을 맞춘 새 실험. 원시 hash 편집 금지 |
| judge/Optimizer 결과 누락 | evaluator 목록·전체 행·실제 입력 | 부분 결과로 통과 처리하지 않음 |
| trace가 없음 | 연결 이후 요청인가, 로그 권한/시간 범위인가 | 몇 분 대기 후 본인 요청 재조회. 로컬 JSON을 trace로 대신하지 않음 |
| Memory 조회 지연 | 같은 store/ID·TTL·scope인가 | write 반복 대신 같은 항목을 제한적으로 읽기 |
| Routine 전달 후 답변 없음 | dispatch/run과 response 보관 상태 | 전달·실행·답변을 구분. 직접 agent 호출로 대체 금지 |
| Skill readback 차이 | 원래 package·실제 버전·다운로드 bytes | 내려받은 파일을 정답에 맞춰 수정하지 않음 |
| Hosted raw capture 실패 | 실제 폴더/Endpoint/활성 버전인가 | 보관한 stdout/stderr로 진단. 실패 stream을 성공으로 취급하지 않음 |
| Entra 앱/Fabric/M365 거부 | Azure Owner 외의 제품/디렉터리 권한 | 14의 추가 조건 확인. Owner로 강제 활성화하지 않음 |

## 오류와 품질 실패를 구분

`collect`/`evaluate`/`benchmark`가 비정상 종료해도 **오답을 제대로 발견한 결과**일 수 있습니다. 응답 6개가 모두 있는지, 요청 오류가 있는지, 업무 기준이 실패했는지 각각 읽습니다.

“6개 요청 중 5개 성공”은 “5/5 통과”가 아닙니다. 모델/평가자가 제공하지 않은 값을 0이나 성공으로 채우지 않습니다.

## 안전하게 재개

프로젝트·prefix·언어·소스·소유권 ledger를 유지합니다. 이미 생성한 ID를 다시 조회하고, 이전 결과를 읽은 뒤 **실제로 필요한 다음 단계만** 진행합니다.

완전히 다른 프로젝트/접두사로 바꾸려면 기존 자산을 정리/기록하고 새 실습 폴더에서 시작합니다. `.selfstudy`, `.reference/v1.2/outputs`, `.env`를 삭제해 보호 조건을 우회하지 않습니다.

## 오류 보고 양식

```text
장/단계:
마지막 성공:
실제 프로젝트/agent/버전:
명령 (비밀 값 제외):
오류/원래 응답 상태:
응답/실행 ID와 로컬 파일:
현재 남아 있는 자산/과금:
다음 확인:
```

중단할 때도 [15의 정리](15-capstone-cleanup.md)를 수행합니다.
