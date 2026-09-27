# Hosted 세션의 파일 가져오기

08 또는 10의 **실제 Hosted 폴더와 세션 ID**를 사용합니다. 다른 세션을 추측하지 않습니다.

## 1. 같은 세션인지 확인

```bash
azd ai agent sessions list --cwd "실제-Hosted-절대경로" --limit 10
azd ai agent files list --cwd "실제-Hosted-절대경로" --session-id "실제-session-id"
```

작업 결과는 세션의 home 아래에 저장됩니다. Toolbox 결과라면 `workshop-evidence/toolbox-runs/`를 확인합니다.

```bash
azd ai agent files list "workshop-evidence/toolbox-runs" --cwd "실제-Hosted-절대경로" --session-id "실제-session-id"
```

목록에서 실제 반환된 경로를 사용합니다. 임의로 경로를 조합하지 않습니다.

## 2. 필요한 파일만 다운로드

```bash
azd ai agent files download "목록에서-확인한-원격-파일" --target-path "아직-없는-로컬-파일" --cwd "실제-Hosted-절대경로" --session-id "실제-session-id"
```

request·response·tool result·summary 또는 failure를 보관합니다. 다운로드 파일이 해당 요청/버전의 결과인지 확인합니다. 이 명령은 모델을 다시 호출하는 것이 아닙니다.

## 3. 비용 자원 정리

```bash
azd ai agent sessions stop "실제-session-id" --cwd "실제-Hosted-절대경로"
```

stop은 실행 compute를 중지하지만 persistent volume은 보존합니다. 파일 회수가 끝나고 더 보관할 필요가 없을 때만 세션 삭제를 결정합니다. 세션 삭제는 파일도 제거합니다.

[08 배포](../08-hosted.md) · [10 공유 도구](../10-toolbox-skills.md) · [15 정리](../15-capstone-cleanup.md)
