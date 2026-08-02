$ErrorActionPreference = "Stop"

$EvidenceDir = "audit-evidence"
$OutputFile = "audit-evidence.sha256"

if (Test-Path $OutputFile) {
    Remove-Item $OutputFile
}

Get-ChildItem -Path $EvidenceDir -File | ForEach-Object {
    $hash = (Get-FileHash -Path $_.FullName -Algorithm SHA256).Hash
    $line = "$hash  $($_.Name)"
    Add-Content -Path $OutputFile -Value $line
}

Write-Host "Evidence pack signed and saved to $OutputFile"
