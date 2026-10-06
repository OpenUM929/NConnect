param([Parameter(Mandatory=$true)][string]$OutputPath)
$ErrorActionPreference = 'Stop'
# Read-only elevated inspection: no process termination, setting change or deletion.
$ids = @(21840, 5780, 2588, 11776, 22380)
$all = @(Get-CimInstance Win32_Process)
$rows = foreach ($p in $all) {
    if ($p.ProcessId -notin $ids -and $p.ParentProcessId -ne 2588) { continue }
    $owner = Invoke-CimMethod -InputObject $p -MethodName GetOwner
    $signature = $null
    if ($p.ExecutablePath -and (Test-Path -LiteralPath $p.ExecutablePath)) {
        $s = Get-AuthenticodeSignature -LiteralPath $p.ExecutablePath
        $signature = @{ Status = [string]$s.Status; Signer = [string]$s.SignerCertificate.Subject }
    }
    [pscustomobject]@{
        Id = $p.ProcessId; ParentId = $p.ParentProcessId; Name = $p.Name
        Path = $p.ExecutablePath; CommandLine = $p.CommandLine
        Created = $p.CreationDate; Owner = "$($owner.Domain)\$($owner.User)"
        Signature = $signature
    }
}
@{ CapturedAt = (Get-Date).ToString('o'); Processes = @($rows) } |
    ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $OutputPath -Encoding UTF8
