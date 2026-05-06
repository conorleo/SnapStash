# Use the folder this .ps1 file lives in (repo root)
$projectDir = $PSScriptRoot
$scriptPath = Join-Path $projectDir "snap.py"
$startupDir = [Environment]::GetFolderPath("Startup")
$shortcutPath = Join-Path $startupDir "SnapStash.lnk"

if (-not (Test-Path $scriptPath)) {
    throw "snap.py not found at $scriptPath"
}

# Prefer venv pythonw, then system pythonw, then python
$venvPythonw = Join-Path $projectDir ".venv\Scripts\pythonw.exe"
$pythonExe = $null

if (Test-Path $venvPythonw) {
    $pythonExe = $venvPythonw
} else {
    $cmd = Get-Command pythonw.exe -ErrorAction SilentlyContinue
    if ($cmd) {
        $pythonExe = $cmd.Source
    } else {
        $cmd = Get-Command python.exe -ErrorAction SilentlyContinue
        if ($cmd) {
            $pythonExe = $cmd.Source
        }
    }
}

if (-not $pythonExe) {
    throw "Could not find pythonw.exe or python.exe. Install Python or create .venv first."
}

$wsh = New-Object -ComObject WScript.Shell
$shortcut = $wsh.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $pythonExe
$shortcut.Arguments = """$scriptPath"""
$shortcut.WorkingDirectory = $projectDir
$shortcut.WindowStyle = 7   # Minimized
$shortcut.Description = "Start SnapStash on login"
$shortcut.Save()

Write-Host "Created/updated startup shortcut:"
Write-Host "  $shortcutPath"
Write-Host "Target: $pythonExe"
Write-Host "Args:   `"$scriptPath`""
