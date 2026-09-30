# 03-fetch-isaaclab-assets.ps1 — 스크립트 본문 (md 전달용)

`.ps1` 파일이 전송되지 않아 본문을 이 문서에 담았다. 받는 쪽(사람 또는 AI)은 아래 순서로 복원한 뒤
`03-fetch-isaaclab-assets.AI_TASK.md`의 지시사항대로 실행한다.

## 1. 복원 방법

1. 아래 `## 2. 스크립트 본문`의 코드 블록 **안쪽 내용만** (첫 줄 `# Mirror the IsaacLab ...`부터
   마지막 줄 `Write-Host ("DONE: ...`까지) 그대로 복사한다. 한 글자도 고치지 않는다.
2. 같은 폴더에 `03-fetch-isaaclab-assets.ps1` 이름으로 저장한다. 본문은 영문(ASCII)뿐이라 인코딩은 상관없다.
3. 복원이 정확한지 대조한다. 아래 명령은 줄바꿈(LF/CRLF)과 파일 끝 공백 차이는 무시하고 **내용만** 비교한다:
   ```powershell
   $t = ([IO.File]::ReadAllText((Get-Item 03-fetch-isaaclab-assets.ps1).FullName) -replace "`r`n", "`n").TrimEnd() + "`n"
   $h = [BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash([Text.Encoding]::UTF8.GetBytes($t))).Replace("-", "").ToLower()
   if ($h -eq "54a9e4169f5257859b29c5b43ffd53831b95c6d06295e75ceabb8545e05afdcc") { "RESTORE OK" } else { "RESTORE MISMATCH: $h" }
   ```
   `RESTORE OK`가 나와야 한다. `RESTORE MISMATCH`면 복사 중 내용이 바뀐 것이다
   (줄 누락, 따옴표 자동 변환, 들여쓰기 변경 등). **이 경우 실행하지 말고 그 사실을 보고한다.**
4. 실행:
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\03-fetch-isaaclab-assets.ps1
   ```

기준 해시(정규화 내용, SHA-256): `54a9e4169f5257859b29c5b43ffd53831b95c6d06295e75ceabb8545e05afdcc`

## 2. 스크립트 본문

```powershell
# Mirror the IsaacLab assets needed by Go2 training (Go2 robot, terrain material, sky HDR).
# Run on a network where Amazon S3 is NOT blocked (phone hotspot, home PC, cloud server).
# Works on stock Windows 10/11 PowerShell 5.1 and PowerShell 7. ASCII only on purpose.
#
#   powershell -ExecutionPolicy Bypass -File .\03-fetch-isaaclab-assets.ps1
#
# Output: .\isaac_assets\Assets\Isaac\5.1\...  (next to this script, or -Dest <dir>)
# Then copy the whole isaac_assets folder to D:\dev\Nconnect\isaac_assets on the training PC.
param([string]$Dest = (Join-Path (Get-Location) "isaac_assets"),
      [string]$Bucket = "https://omniverse-content-production.s3-us-west-2.amazonaws.com")
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"   # PS 5.1 progress bar makes downloads 10x slower
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$Prefixes = @(
  "Assets/Isaac/5.1/Isaac/IsaacLab/Robots/Unitree/Go2/",
  "Assets/Isaac/5.1/Isaac/IsaacLab/Materials/TilesMarbleSpiderWhiteBrickBondHoned/",
  "Assets/Isaac/5.1/Isaac/Materials/Textures/Skies/PolyHaven/kloofendal_43d_clear_puresky_4k.hdr"
)

function Get-Text([string]$url) {
  try { $r = Invoke-WebRequest -UseBasicParsing -Uri $url }
  catch {
    throw (("Cannot reach S3 from this network ({0}). If this is an office network, a web filter " +
            "is probably blocking Amazon S3 - use another network.") -f $_.Exception.Message)
  }
  $t = [string]$r.Content
  if ($t -match "deny_new\.html|<iframe") {
    throw "Blocked by a web filter on this network (got a block page instead of S3). Use another network."
  }
  return $t
}

$n = 0
foreach ($p in $Prefixes) {
  $token = $null
  do {
    $q = "$Bucket/?list-type=2&prefix=" + [uri]::EscapeDataString($p)
    if ($token) { $q += "&continuation-token=" + [uri]::EscapeDataString($token) }
    [xml]$x = Get-Text $q
    $items = @($x.ListBucketResult.Contents)
    if ($items.Count -eq 0 -or -not $items[0]) { throw "No objects listed under $p" }
    foreach ($c in $items) {
      $key = [string]$c.Key
      if ($key.EndsWith("/")) { continue }
      $out = Join-Path $Dest ($key -replace "/", "\")
      New-Item -ItemType Directory -Force -Path (Split-Path $out) | Out-Null
      if ((Test-Path $out) -and ((Get-Item $out).Length -eq [int64]$c.Size)) { continue }
      Write-Host ("GET {0} ({1} bytes)" -f $key, $c.Size)
      Invoke-WebRequest -UseBasicParsing -Uri "$Bucket/$key" -OutFile $out
      if ((Get-Item $out).Length -ne [int64]$c.Size) { throw "Size mismatch: $key" }
      $n++
    }
    $token = [string]$x.ListBucketResult.NextContinuationToken
  } while ($token)
}

$go2 = Join-Path $Dest "Assets\Isaac\5.1\Isaac\IsaacLab\Robots\Unitree\Go2\go2.usd"
# Validate by content, not size: the IsaacLab go2.usd can be a small root layer that references other files.
if (-not (Test-Path $go2)) { throw "go2.usd missing" }
$fs = [IO.File]::OpenRead($go2); $buf = New-Object byte[] 8; $got = $fs.Read($buf, 0, 8); $fs.Close()
$hdr = [Text.Encoding]::ASCII.GetString($buf, 0, $got)
if (-not ($hdr -eq "PXR-USDC" -or $hdr.StartsWith("#usda"))) {
  throw ("go2.usd is not a USD file (first bytes: '{0}') - probably a web filter block page" -f $hdr)
}
# SHA-256 manifest (LF line endings, sha256sum -c compatible) for integrity check on the training PC
$root = (Get-Item -LiteralPath $Dest).FullName.TrimEnd("\")   # same form as FullName of children (8.3-safe)
$lines = Get-ChildItem $root -Recurse -File | Where-Object Name -ne "MANIFEST.sha256" | Sort-Object FullName |
  ForEach-Object { "{0}  {1}" -f (Get-FileHash $_.FullName -Algorithm SHA256).Hash.ToLower(),
                   ($_.FullName.Substring($root.Length + 1) -replace "\\", "/") }
[IO.File]::WriteAllText((Join-Path $root "MANIFEST.sha256"), (($lines -join "`n") + "`n"))
Write-Host ("MANIFEST: {0} entries -> {1}" -f @($lines).Count, (Join-Path $root "MANIFEST.sha256"))
Write-Host ("DONE: {0} files downloaded to {1}  (go2.usd = {2} bytes)" -f $n, $Dest, (Get-Item $go2).Length)
```
