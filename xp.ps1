# 选评自动化CLI应用可执行入口 (PowerShell版本)
# 使用方法: .\xp.ps1 [命令] [选项]

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$xpScript = Join-Path $scriptDir "xp"

# 尝试使用 python3，如果不存在则使用 python
try {
    & python3 $xpScript $args
} catch {
    & python $xpScript $args
}

