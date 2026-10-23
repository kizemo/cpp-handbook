<#
  Deploy the skill-c++ skill into the MiniMax Code skills directory.

  ASCII-only on purpose: Windows PowerShell 5.1 parses .ps1 files as ANSI
  (GBK on this machine) when there is no BOM, so any non-ASCII character in
  a script body corrupts the parse and the script never runs.

  Usage:
    powershell -NoProfile -ExecutionPolicy Bypass -File install.ps1
    powershell -NoProfile -ExecutionPolicy Bypass -File install.ps1 -Target <dir> -Kb <dir>

  -SkillName installs under a different slug and rewrites the frontmatter name
  to match. The default slug "skill-c++" is what the owner asked for and the
  MiniMax Code runtime resolves it by name, but the Agent Skills spec only
  allows lowercase letters/digits/hyphens -- every host lens (amp, claude,
  copilot, hermes, openclaw, opencode) rejects "+". Use a compliant slug such
  as "skill-cpp" when publishing to other hosts.
#>
param(
    [string]$Target = "",
    [string]$Kb = "",
    [string]$SkillName = "skill-c++"
)

$ErrorActionPreference = 'Stop'

$SkillDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$KbDir = if ($Kb) { $Kb } else { Join-Path (Split-Path -Parent $SkillDir) 'knowlege' }

function Resolve-SkillsRoot {
    param([string]$Preferred)

    # An explicitly requested target must win outright. The "most subdirectories
    # wins" scoring below must never override it, or -Target silently installs
    # somewhere else.
    if ($Preferred) {
        if (-not (Test-Path -LiteralPath $Preferred -PathType Container)) {
            throw "Target does not exist: $Preferred"
        }
        return $Preferred
    }

    $candidates = New-Object System.Collections.Generic.List[string]
    if ($env:MINIMAX_DATA_DIR) { $candidates.Add((Join-Path $env:MINIMAX_DATA_DIR 'skills')) }

    foreach ($base in @($env:USERPROFILE, 'E:\Users\Duanyi', 'C:\Users\Duanyi')) {
        if (-not $base) { continue }
        $candidates.Add((Join-Path $base '.minimax\.minimax\skills'))
    }

    $best = $null
    $bestScore = -1
    foreach ($c in $candidates) {
        if (-not (Test-Path -LiteralPath $c -PathType Container)) { continue }
        $count = @(Get-ChildItem -LiteralPath $c -Directory -ErrorAction SilentlyContinue).Count
        if ($count -gt $bestScore) { $bestScore = $count; $best = $c }
    }
    if (-not $best) { throw "Cannot locate a skills directory. Pass -Target explicitly." }
    return $best
}

$SkillsRoot = Resolve-SkillsRoot -Preferred $Target
$Dest = Join-Path $SkillsRoot $SkillName

Write-Host "skill source : $SkillDir"
Write-Host "knowledge base: $KbDir"
Write-Host "install target: $Dest"

if (-not (Test-Path -LiteralPath (Join-Path $KbDir 'index\knowledge-map.md'))) {
    Write-Warning "Knowledge base not found at: $KbDir"
    Write-Warning "The skill still works: chapters, rule index and cheatsheets ship with it."
    Write-Warning "Only the knowledge-base text lookup (kb_lookup.py) will be unavailable."
    Write-Warning "To enable it later, set CPP_KB_ROOT or write kb_root.txt inside the skill dir."
    $KbDir = ''
}

# Build a fresh directory, then move it into place. Never delete the
# user's existing install before the new one is ready.
$Staging = Join-Path $SkillsRoot ('.' + $SkillName + '.staging-' + [Guid]::NewGuid().ToString('N').Substring(0, 8))
New-Item -ItemType Directory -Path $Staging -Force | Out-Null

Get-ChildItem -LiteralPath $SkillDir -Force | ForEach-Object {
    if ($_.PSIsContainer) {
        if ($_.Name -eq '__pycache__') { return }
        Copy-Item -LiteralPath $_.FullName -Destination $Staging -Recurse -Force
    } else {
        if ($_.Extension -eq '.pyc') { return }
        Copy-Item -LiteralPath $_.FullName -Destination $Staging -Force
    }
}

# Belt and braces: no bytecode cache may survive in the deployed copy.
Get-ChildItem -LiteralPath $Staging -Recurse -Directory -Force -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -eq '__pycache__' } |
    ForEach-Object { Remove-Item -LiteralPath $_.FullName -Recurse -Force }
Get-ChildItem -LiteralPath $Staging -Recurse -File -Force -Filter '*.pyc' -ErrorAction SilentlyContinue |
    ForEach-Object { Remove-Item -LiteralPath $_.FullName -Force }

# The skill must be able to find the knowledge base from anywhere.
# kb_root.txt is the first thing _kbpath.py looks at.
# The knowledge base is optional: without it, only kb_lookup.py degrades.
if ($KbDir) {
    [System.IO.File]::WriteAllText(
        (Join-Path $Staging 'kb_root.txt'),
        (Resolve-Path -LiteralPath $KbDir).Path,
        (New-Object System.Text.UTF8Encoding($false)))
}

# Keep the frontmatter name in sync with the installed slug.
$SkillMd = Join-Path $Staging 'SKILL.md'
if (Test-Path -LiteralPath $SkillMd) {
    $skillText = [System.IO.File]::ReadAllText($SkillMd, [System.Text.Encoding]::UTF8)
    $skillText = [regex]::Replace($skillText, '(?m)^name:\s*.*$', "name: $SkillName", 1)
    [System.IO.File]::WriteAllText($SkillMd, $skillText, (New-Object System.Text.UTF8Encoding($false)))
}

if (Test-Path -LiteralPath $Dest) {
    $Backup = Join-Path $SkillsRoot ('.' + $SkillName + '.backup-' + [Guid]::NewGuid().ToString('N').Substring(0, 8))
    Move-Item -LiteralPath $Dest -Destination $Backup
    # The runtime resolves a skill by the `name:` in its SKILL.md, NOT by the
    # directory name -- a dot-prefixed backup directory is still discovered and
    # can shadow the real install. Retire the copy's manifest so the backup
    # stays recoverable but is no longer a loadable skill.
    $OldManifest = Join-Path $Backup 'SKILL.md'
    if (Test-Path -LiteralPath $OldManifest) {
        Move-Item -LiteralPath $OldManifest -Destination ($OldManifest + '.retired') -Force
    }
    Write-Host "previous install kept (manifest retired) at: $Backup"
}
Move-Item -LiteralPath $Staging -Destination $Dest

Write-Host ""
Write-Host "Verifying installed copy..."
Push-Location $Dest
try {
    python (Join-Path $Dest 'scripts\verify_bundle.py')
    $code = $LASTEXITCODE
} finally {
    Pop-Location
}

if ($code -ne 0) {
    Write-Host "Verification FAILED (exit $code)."
    exit $code
}

Write-Host ""
Write-Host "Installed OK: $Dest"
Write-Host "Restart the session for the skill to become visible."
exit 0
