param([switch]$FinalizeTransferred)
$ErrorActionPreference = 'Stop'
$workspaceRoot = [System.IO.Path]::GetFullPath('D:\projects')
$projectRoot = [System.IO.Path]::GetFullPath('D:\projects\claire')
$mappings = [System.Collections.Generic.List[object]]::new()
if ($FinalizeTransferred) {
    foreach ($name in @('assets','checks','node_modules','src','tools','app.js','app.js.map','claire.html','desktop-initial.png','export.log','index.html','package-lock.json','package.json','README.md','server.cjs','start-preview.cmd','style.css','THREE-LICENSE.txt')) {
        $mappings.Add([pscustomobject]@{ Source=Join-Path 'D:\projects\claire-html-v03' $name; Destination=Join-Path $projectRoot $name })
    }
} else {
    foreach ($item in Get-ChildItem -LiteralPath 'D:\projects\claire-html-v03' -Force) {
        $mappings.Add([pscustomobject]@{ Source = $item.FullName; Destination = Join-Path $projectRoot $item.Name })
    }
}
$mappings.Add([pscustomobject]@{ Source='D:\projects\claire-vinyl-preview'; Destination=Join-Path $projectRoot 'models' })
$mappings.Add([pscustomobject]@{ Source='D:\projects\claire-homepage-handoff'; Destination=Join-Path $projectRoot 'docs\handoff' })
$mappings.Add([pscustomobject]@{ Source='D:\projects\review-20261006-claire'; Destination=Join-Path $projectRoot 'reviews\2026-10-06' })
$mappings.Add([pscustomobject]@{ Source='D:\projects\generated-images'; Destination=Join-Path $projectRoot 'references\legacy-generated' })
foreach ($name in @('唱片机封面-3D化设计规范.md','个人简历网站-设计语言拆解与提示词.md')) {
    $mappings.Add([pscustomobject]@{ Source=Join-Path $workspaceRoot $name; Destination=Join-Path $projectRoot ('docs\'+$name) })
}
$inventory = [System.Collections.Generic.List[object]]::new()
foreach ($mapping in $mappings) {
    $sourcePath = [System.IO.Path]::GetFullPath($mapping.Source)
    $targetPath = [System.IO.Path]::GetFullPath($mapping.Destination)
    if (-not $sourcePath.StartsWith($workspaceRoot+'\', [System.StringComparison]::OrdinalIgnoreCase)) { throw 'Source outside workspace' }
    if (-not $targetPath.StartsWith($projectRoot+'\', [System.StringComparison]::OrdinalIgnoreCase)) { throw 'Target outside Claire project' }
    if ($sourcePath.StartsWith($projectRoot+'\', [System.StringComparison]::OrdinalIgnoreCase)) { throw 'Source is already in target project' }
    if (-not $FinalizeTransferred -and (Test-Path -LiteralPath $targetPath)) { throw "Destination already exists: $targetPath" }
    $actualPath = if ($FinalizeTransferred) { $targetPath } else { $sourcePath }
    $item = Get-Item -LiteralPath $actualPath -Force
    $files = if ($item.PSIsContainer) { @(Get-ChildItem -LiteralPath $actualPath -File -Recurse -Force) } else { @($item) }
    foreach ($file in $files) {
        $relative = if ($item.PSIsContainer) { [System.IO.Path]::GetRelativePath($actualPath,$file.FullName) } else { '' }
        $destination = if ($relative) { Join-Path $targetPath $relative } else { $targetPath }
        $inventory.Add([pscustomobject]@{
            OldPath= $(if ($relative) { Join-Path $sourcePath $relative } else { $sourcePath })
            NewPath=$destination
            Bytes=$file.Length
            SHA256=(Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash
        })
    }
}
foreach ($mapping in $mappings) {
    if ($FinalizeTransferred) { continue }
    $parent = [System.IO.Path]::GetDirectoryName($mapping.Destination)
    if (-not (Test-Path -LiteralPath $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
    Move-Item -LiteralPath $mapping.Source -Destination $mapping.Destination
}
foreach ($entry in $inventory) {
    $file = Get-Item -LiteralPath $entry.NewPath
    if ($file.Length -ne $entry.Bytes) { throw "Size mismatch: $($entry.NewPath)" }
    if ((Get-FileHash -LiteralPath $entry.NewPath -Algorithm SHA256).Hash -ne $entry.SHA256) { throw "Hash mismatch: $($entry.NewPath)" }
}
$oldWebsite = [System.IO.Path]::GetFullPath('D:\projects\claire-html-v03')
if ((Test-Path -LiteralPath $oldWebsite) -and $oldWebsite.StartsWith($workspaceRoot+'\',[System.StringComparison]::OrdinalIgnoreCase) -and @(Get-ChildItem -LiteralPath $oldWebsite -Force).Count -eq 0) {
    try { Remove-Item -LiteralPath $oldWebsite } catch { Write-Output 'Old empty website directory is held open; all project files are already transferred.' }
}
$report = [ordered]@{
    Date='2026-10-06'
    Root=$projectRoot
    FileCount=$inventory.Count
    Bytes=($inventory | Measure-Object -Property Bytes -Sum).Sum
    TransferIntegrity='All moved files matched SHA-256 before and after transfer'
    Mappings=$mappings
    Files=$inventory
}
$report | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $projectRoot 'docs\project-migration-2026-10-06.json') -Encoding utf8
Write-Output "MOVED_AND_SHA256_VERIFIED $($inventory.Count) files"
