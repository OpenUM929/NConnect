# 작업 요청서 — IsaacLab Go2 에셋 다운로드 및 검증

> 이 문서를 받은 AI 에이전트에게: 아래 **지시사항**을 순서대로 수행하고,
> **확인사항**을 모두 점검한 뒤 **보고 양식**대로 결과를 돌려주세요.
> 추측으로 채우지 말고, 실제로 실행한 명령과 출력만 근거로 쓰세요.

## 1. 배경 (왜 이 작업이 필요한가)

- 학습 PC(Windows 10, Isaac Sim 5.1 + IsaacLab 2.3.2)에서 Unitree Go2 강화학습을 돌려야 한다.
- IsaacLab은 로봇 모델(USD)을 NVIDIA의 Amazon S3 버킷
  `https://omniverse-content-production.s3-us-west-2.amazonaws.com`에서 실행 중에 받아온다.
- 그런데 학습 PC가 있는 사내망의 웹 필터(ePrism)가 **Amazon S3 전체를 차단**한다.
  SSL 검증을 꺼도 필터의 차단 페이지(HTML 416 bytes)만 돌아온다.
- 그래서 **S3가 열린 네트워크(이 PC)** 에서 필요한 파일을 미리 받아 학습 PC로 옮긴다.

필요한 파일 (전부 Isaac Sim **5.1** 경로):

| 용도 | S3 키 prefix |
|---|---|
| Go2 로봇 모델 (**필수**) | `Assets/Isaac/5.1/Isaac/IsaacLab/Robots/Unitree/Go2/` |
| 지형 재질 (시각용) | `Assets/Isaac/5.1/Isaac/IsaacLab/Materials/TilesMarbleSpiderWhiteBrickBondHoned/` |
| 하늘 조명 (시각용) | `Assets/Isaac/5.1/Isaac/Materials/Textures/Skies/PolyHaven/kloofendal_43d_clear_puresky_4k.hdr` |

## 2. 지시사항

### 2-0. 사전 점검 — S3가 실제로 열려 있는지

```bash
curl -sS -I https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/5.1/Isaac/IsaacLab/Robots/Unitree/Go2/go2.usd
```
- 정상: `Server: AmazonS3`, `Content-Type`이 `text/html`이 아님.
  (`go2.usd`는 다른 파일을 참조하는 **작은 루트 파일일 수 있으므로 크기로 판단하지 않는다.**)
- 실패: `Server: ePrism` 등 다른 서버이거나 `Content-Type: text/html`이면
  **이 네트워크도 막힌 것**이다. 여기서 멈추고 그 출력을 그대로 보고한다.
  (Windows에서 curl이 `CRYPT_E_NO_REVOCATION_CHECK`로 실패하면 `--ssl-no-revoke`를 붙여 다시 시도한다.)

### 2-1. 다운로드 스크립트 실행 (환경에 맞는 것 하나)

스크립트는 이 문서와 함께 전달된다. **스크립트를 수정하지 말고** 그대로 실행한다.

> `.ps1` 파일 대신 `03-fetch-isaaclab-assets.ps1.md`를 받았다면, 먼저 그 문서의 「1. 복원 방법」대로
> `.ps1`을 복원하고 `RESTORE OK`를 확인한 뒤 진행한다. `RESTORE MISMATCH`면 실행하지 말고 보고한다.
> (보고서 특이사항에 복원 여부와 결과를 적는다.)

- Windows (PowerShell 5.1 이상):
  ```powershell
  powershell -ExecutionPolicy Bypass -File .\03-fetch-isaaclab-assets.ps1
  ```
- Linux / Git Bash:
  ```bash
  bash 03-fetch-isaaclab-assets.sh
  ```

결과는 현재 폴더 아래 `isaac_assets/`에 생긴다. 마지막 줄이
`DONE: N files downloaded to ... (go2.usd = XXXX bytes)` 이면 스크립트 단계는 성공이다.
실패하면 에러 전문을 보고하고, 원인이 명확하고 스크립트 밖의 문제(네트워크·권한)일 때만 조치 후 재실행한다.

### 2-2. 무결성 목록 확인 (스크립트가 자동 생성)

스크립트가 끝날 때 `isaac_assets/MANIFEST.sha256`(SHA-256, LF 줄바꿈, `sha256sum -c` 호환)을 자동으로 만들고
`MANIFEST: N entries -> ...` 줄을 출력한다. **따로 만들지 않는다.** 스스로 한 번 검증만 한다:

- Linux / Git Bash: `(cd isaac_assets && sha256sum -c --quiet MANIFEST.sha256 && echo OK)`
- Windows PowerShell:
  ```powershell
  Get-Content isaac_assets\MANIFEST.sha256 | ForEach-Object { $h,$f = $_ -split '  ',2
    if ((Get-FileHash (Join-Path isaac_assets $f) -Algorithm SHA256).Hash.ToLower() -ne $h) { "MISMATCH $f" } }
  ```
  (출력이 없으면 전부 일치)

### 2-3. 전달용 압축

- Linux: `tar czf isaac_assets.tgz isaac_assets`
- Windows: `Compress-Archive -Path isaac_assets -DestinationPath isaac_assets.zip`

학습 PC에서는 이 압축을 풀어 `D:\dev\Nconnect\isaac_assets\Assets\Isaac\5.1\...` 구조가 되게 둔다.

## 3. 확인사항 (모두 점검하고 결과를 표로 보고)

| # | 확인 항목 | 방법 | 통과 기준 |
|---|---|---|---|
| C1 | S3가 진짜 S3 응답인가 | 2-0의 헤더 | `Server: AmazonS3` |
| C2 | 스크립트가 정상 종료했는가 | 종료 코드, 마지막 줄 | rc=0, `DONE:` 출력 |
| C3 | `go2.usd`가 차단 페이지가 아닌 진짜 USD인가 | 파일 앞 8바이트 확인 (`head -c 8 .../go2.usd` 또는 `Format-Hex`) | `PXR-USDC` (바이너리 USD) 또는 `#usda` (텍스트 USD). `<!DOCTYPE`, `<html`이면 **실패** |
| C4 | `go2.usd` 크기와 Go2 폴더 전체 | 파일 크기, Go2 폴더의 파일 목록과 합계 크기 | **크기는 판정 기준이 아니다**(루트 파일은 수 KB일 수 있음). 값만 기록한다. 루트 파일이 작으면 실제 메시·물리 데이터는 참조 파일에 있으므로 **C7이 필수**가 된다 |
| C5 | 세 prefix 모두 파일이 받아졌는가 | 폴더별 파일 수 | 각 prefix 아래 파일 1개 이상 |
| C6 | 받아진 파일 중 HTML이 섞였는가 | `grep -rl "deny_new\|<html" isaac_assets` (바이너리 경고 무시) | 결과 없음 |
| C7 | **Go2 USD가 폴더 밖 파일을 참조하는가** (중요) | 아래 3-1 | 참조 경로 목록을 그대로 보고. 폴더 밖(`../` 로 Go2 폴더를 벗어나거나 `http(s)://`, `omniverse://`) 참조가 있으면 **그 경로를 추가로 받아야 하므로 반드시 명시** |
| C8 | MANIFEST 자체 검증 | 2-2의 검증 명령 | 불일치 0건, 줄 수 = 파일 수(MANIFEST 제외) |
| C9 | 압축 파일 | 크기, SHA-256 | 보고서에 기재 |

### 3-1. C7 참조 확인 방법

pxr(USD 파이썬)이 있으면 가장 정확하다:
```python
from pxr import UsdUtils, Sdf
layers, assets, unresolved = UsdUtils.ComputeAllDependencies(
    "isaac_assets/Assets/Isaac/5.1/Isaac/IsaacLab/Robots/Unitree/Go2/go2.usd")
print("layers:", [l.identifier for l in layers]); print("assets:", assets); print("unresolved:", unresolved)
```
pxr이 없으면(`pip install usd-core`로 설치 가능) 설치해서 위를 실행한다. 설치도 불가하면 차선책으로
바이너리 안의 경로 문자열을 뽑는다:
```bash
grep -aoE '[A-Za-z0-9_./:@-]+\.(usd|usda|usdc|mdl|png|jpg|hdr|exr)' isaac_assets/Assets/Isaac/5.1/Isaac/IsaacLab/Robots/Unitree/Go2/go2.usd | sort -u
```
`unresolved`가 비어 있지 않거나 폴더 밖 경로가 나오면, 그 경로에 해당하는 S3 키를 같은 방식으로 추가 다운로드하고
**무엇을 추가로 받았는지** 보고한다.

## 4. 하지 말 것

- 스크립트 내용, 다운로드 경로(5.1)를 바꾸지 않는다. 다른 버전(4.5 등) 에셋으로 대체하지 않는다.
- 차단 페이지나 에러 HTML을 파일로 저장한 채 성공으로 보고하지 않는다.
- HuggingFace, GitHub 등 **제3자 사본**을 대신 쓰지 않는다 (공식 파일과 같다는 보장이 없음).
- 확인하지 않은 항목을 "통과"로 쓰지 않는다. 못 한 항목은 `미확인`과 이유를 쓴다.

## 5. 보고 양식 (이대로 채워서 돌려줄 것)

```markdown
## 에셋 다운로드 결과
- 실행 환경: (OS / 셸 / 네트워크 종류)
- 사용 스크립트: (.ps1 / .sh), 종료 코드:
- 마지막 출력 줄:

## 확인사항
| # | 결과 (통과/실패/미확인) | 근거 (명령 출력 요약) |
|---|---|---|
| C1 | | |
| C2 | | |
| C3 | | |
| C4 | | |
| C5 | | |
| C6 | | |
| C7 | | (참조 경로 목록 전체) |
| C8 | | |
| C9 | | (파일명, 크기, SHA-256) |

## 추가로 받은 파일 (C7 때문에)
- (없으면 "없음")

## 파일 목록
(isaac_assets 아래 전체 파일 경로와 크기)

## 특이사항 / 실패 내용
```
