# Wrapper fino (Windows/PowerShell): localiza o Python 3 e executa o núcleo menu-reversa-openclaude.py.
# Não contém lógica de negócio; toda a lógica vive em menu-reversa-openclaude.py.
# Uso: powershell -ExecutionPolicy Bypass -File bin\install.ps1 --yes
# Dica: no Windows sem privilegio de symlink, use --copy.

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Core = Join-Path $ScriptDir ".." "menu-reversa-openclaude.py"

if (-not (Test-Path $Core)) {
    Write-Error "ERRO: menu-reversa-openclaude.py não encontrado em $Core"
    exit 1
}

function Test-Python3 {
    param([string]$Exe, [string[]]$Prefix)
    try {
        & $Exe @Prefix -c "import sys; sys.exit(0 if sys.version_info[0] == 3 else 1)" *> $null
        return ($LASTEXITCODE -eq 0)
    } catch {
        return $false
    }
}

$pyExe = $null
$pyPrefix = @()
foreach ($exe in @("python3", "python")) {
    if (Get-Command $exe -ErrorAction SilentlyContinue) {
        if (Test-Python3 -Exe $exe -Prefix @()) {
            $pyExe = $exe
            $pyPrefix = @()
            break
        }
    }
}
if (-not $pyExe -and (Get-Command "py" -ErrorAction SilentlyContinue)) {
    if (Test-Python3 -Exe "py" -Prefix @("-3")) {
        $pyExe = "py"
        $pyPrefix = @("-3")
    }
}

if (-not $pyExe) {
    Write-Error "ERRO: Python 3 não encontrado. Instale Python 3 e tente novamente."
    exit 1
}

& $pyExe @pyPrefix $Core "install" @args
exit $LASTEXITCODE
