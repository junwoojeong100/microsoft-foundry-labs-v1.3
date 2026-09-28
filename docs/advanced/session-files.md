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

## 2. 만료 전에 절대 경로로 보관

**중지된 세션에서도 파일이 아직 남아 있으면 다운로드할 수 있습니다.** 실제 원격 stopped session의 증거를 회수하고 도구 결과의 hash와 일치하는 것을 확인했습니다. 파일을 받기 위해 세션을 다시 실행하거나 새 추론을 만들지 않습니다.

필요한 request·response·tool result·summary/failure만 **서비스의 세션/파일 만료 전**에 보관합니다. 리소스를 보존하거나 compute를 stop했다고 파일이 무기한 남는 것은 아닙니다. 실제 보존 조건을 확인하고, 이미 만료된 결과를 다른 응답으로 대신하지 않습니다.

README가 있는 폴더에서 새 개인 보관 폴더를 준비합니다. 이미 있으면 새 이름을 사용합니다.

```bash
python -c "from pathlib import Path; p=Path('.selfstudy/session-archive-ko').resolve(); p.mkdir(parents=True,exist_ok=False); print(p)"
```

출력된 절대 폴더 안의 새 파일 경로를 `--target-path`에 넣습니다. **상대 target 경로는 터미널의 현재 폴더가 아니라 azd의 `--cwd` 기준으로 해석**될 수 있으므로 반드시 절대 경로를 사용합니다.

```bash
azd ai agent files download "목록에서-확인한-원격-파일" --target-path "ABSOLUTE-NEW-LOCAL-FILE-PATH" --cwd "실제-Hosted-절대경로" --session-id "실제-session-id"
```

macOS/Linux는 `/.../session-archive-ko/파일.json`, Windows는 `C:/.../session-archive-ko/파일.json`처럼 실제 절대 경로로 바꿉니다. 세션 ID·agent 버전·원격/로컬 경로·회수 시점을 함께 기록합니다.

로컬 파일의 byte SHA-256을 기록하려면:

```bash
python -c "import hashlib,sys; from pathlib import Path; print(hashlib.sha256(Path(sys.argv[1]).read_bytes()).hexdigest())" "ABSOLUTE-DOWNLOADED-FILE-PATH"
```

기록된 도구 결과의 hash와 **같은 대상·알고리즘**으로 대조합니다. 파일 byte SHA-256과 `tool_results_hash` 같은 canonical JSON digest는 서로 다를 수 있습니다. JSON 전체/내부 payload 중 무엇을 hash했는지 확인하며, 맞추려고 원시 파일을 편집하지 않습니다. 원래 패키지·SSE·검증 결과도 함께 비공개로 보관합니다.

## 3. 비용 자원 정리

```bash
azd ai agent sessions stop "실제-session-id" --cwd "실제-Hosted-절대경로"
```

실행 중인 본인 세션에만 stop을 적용합니다. 이미 stopped라면 위의 파일 회수를 먼저 진행할 수 있습니다. Stop은 compute를 중지하지만 volume 보존과 서비스 만료는 별도입니다. 보존 모드에서는 세션/volume을 삭제하지 않으며, 로컬 보관을 완료해도 공유 자원을 임의로 제거하지 않습니다.

[08 배포](../08-hosted.md) · [10 공유 도구](../10-toolbox-skills.md) · [15 정리](../15-capstone-cleanup.md)
