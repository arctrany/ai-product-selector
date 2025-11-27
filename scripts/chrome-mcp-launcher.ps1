# Chrome MCP Launcher Script for PowerShell (Cross-platform)
# 启动Chrome浏览器，配置用户目录和调试端口，供Chrome DevTools MCP连接
# 
# 使用方法:
# .\chrome-mcp-launcher.ps1 [options]
#
# 选项:
#   -Port PORT          设置调试端口 (默认: 9222)
#   -Profile PATH       设置用户目录路径 (默认: 自动检测)
#   -Headless          无头模式启动
#   -Help              显示帮助信息

param(
    [int]$Port = 9222,
    [string]$Profile = "",
    [switch]$Headless,
    [switch]$Help
)

# 脚本配置
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$LogFile = Join-Path $ScriptDir "chrome-mcp.log"

# 帮助信息
if ($Help) {
    Write-Host @"
Chrome MCP Launcher - 为Chrome DevTools MCP启动Chrome浏览器

用法: .\chrome-mcp-launcher.ps1 [选项]

选项:
    -Port PORT          设置调试端口 (默认: 9222)
    -Profile PATH       设置用户目录路径 (默认: 自动检测)
    -Headless          启用无头模式
    -Help              显示此帮助信息

示例:
    .\chrome-mcp-launcher.ps1                                    # 使用默认配置启动
    .\chrome-mcp-launcher.ps1 -Port 9223 -Headless              # 无头模式，自定义端口
    .\chrome-mcp-launcher.ps1 -Profile "C:\my-chrome-profile"    # 指定用户目录

连接方法:
    npx chrome-devtools-mcp@latest --browserUrl http://127.0.0.1:9222

"@
    exit
}

# 日志函数
function Write-Log {
    param([string]$Level, [string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    Write-Host $logEntry
    Add-Content -Path $LogFile -Value $logEntry
}

function Write-LogInfo { param([string]$Message) Write-Log "INFO" $Message }
function Write-LogWarn { param([string]$Message) Write-Log "WARN" $Message }
function Write-LogError { param([string]$Message) Write-Log "ERROR" $Message }

# 检测操作系统
function Get-OperatingSystem {
    if ($PSVersionTable.Platform -eq "Unix") {
        $uname = uname
        if ($uname -eq "Darwin") {
            return "macOS"
        } elseif ($uname -eq "Linux") {
            return "Linux"
        }
    }
    return "Windows"
}

# 查找Chrome可执行文件
function Find-ChromeExecutable {
    $os = Get-OperatingSystem
    $chromePaths = @()
    
    switch ($os) {
        "Windows" {
            $chromePaths = @(
                "${env:ProgramFiles}\Google\Chrome\Application\chrome.exe",
                "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
                "${env:LOCALAPPDATA}\Google\Chrome\Application\chrome.exe",
                "${env:ProgramFiles}\Chromium\Application\chrome.exe",
                "${env:ProgramFiles(x86)}\Chromium\Application\chrome.exe"
            )
        }
        "macOS" {
            $chromePaths = @(
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "/Applications/Chromium.app/Contents/MacOS/Chromium",
                "/opt/homebrew/bin/google-chrome",
                "/usr/local/bin/google-chrome"
            )
        }
        "Linux" {
            $chromePaths = @(
                "/usr/bin/google-chrome",
                "/usr/bin/google-chrome-stable",
                "/usr/bin/chromium-browser",
                "/usr/bin/chromium",
                "/snap/bin/chromium",
                "/opt/google/chrome/chrome"
            )
        }
    }
    
    foreach ($path in $chromePaths) {
        if (Test-Path $path) {
            return $path
        }
    }
    
    throw "未找到Chrome可执行文件"
}

# 获取默认用户目录
function Get-DefaultProfile {
    $os = Get-OperatingSystem
    
    switch ($os) {
        "Windows" {
            $defaultProfile = "$env:LOCALAPPDATA\Google\Chrome\User Data\Default"
        }
        "macOS" {
            $defaultProfile = "$env:HOME/Library/Application Support/Google/Chrome/Default"
        }
        "Linux" {
            $defaultProfile = "$env:HOME/.config/google-chrome/Default"
        }
    }
    
    if (-not (Test-Path $defaultProfile)) {
        $defaultProfile = Join-Path $env:HOME ".chrome-mcp-profile"
        Write-LogWarn "默认Chrome目录不存在，将使用: $defaultProfile"
    }
    
    return $defaultProfile
}

# 检查端口是否被占用
function Test-Port {
    param([int]$PortNumber)
    
    try {
        $listener = [System.Net.NetworkInformation.IPGlobalProperties]::GetIPGlobalProperties()
        $tcpEndpoints = $listener.GetActiveTcpListeners()
        foreach ($endpoint in $tcpEndpoints) {
            if ($endpoint.Port -eq $PortNumber) {
                return $false
            }
        }
        return $true
    } catch {
        Write-LogWarn "无法检查端口状态: $_"
        return $true
    }
}

# 构建Chrome启动参数
function Build-ChromeArgs {
    param([string]$ProfileDir)
    
    $args = @(
        "--remote-debugging-port=$Port",
        "--user-data-dir=`"$ProfileDir`"",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-extensions-file-access-check",
        "--disable-extensions-except",
        "--disable-sync",
        "--disable-translate",
        "--disable-background-timer-throttling",
        "--disable-backgrounding-occluded-windows",
        "--disable-renderer-backgrounding",
        "--disable-field-trial-config",
        "--disable-ipc-flooding-protection",
        "--disable-hang-monitor",
        "--disable-prompt-on-repost",
        "--disable-client-side-phishing-detection",
        "--disable-component-extensions-with-background-pages",
        "--disable-default-apps",
        "--disable-dev-shm-usage",
        "--disable-features=TranslateUI",
        "--disable-blink-features=AutomationControlled",
        "--exclude-switches=enable-automation",
        "--no-sandbox"
    )
    
    if ($Headless) {
        $args += @("--headless", "--disable-gpu", "--virtual-time-budget=5000")
        Write-LogInfo "启用无头模式"
    }
    
    return $args
}

# 测试调试端口连接
function Test-DebugConnection {
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:$Port/json/version" -TimeoutSec 5 -ErrorAction Stop
        return $response.StatusCode -eq 200
    } catch {
        return $false
    }
}

# 主函数
function Main {
    Write-LogInfo "Chrome MCP Launcher 启动中..."
    
    # 检查端口
    if (-not (Test-Port $Port)) {
        Write-LogError "端口 $Port 已被占用，请使用 -Port 指定其他端口"
        exit 1
    }
    
    # 查找Chrome可执行文件
    try {
        $chromeExecutable = Find-ChromeExecutable
        Write-LogInfo "Chrome可执行文件: $chromeExecutable"
    } catch {
        Write-LogError $_
        exit 1
    }
    
    # 确定用户目录
    if ($Profile) {
        $profileDir = $Profile
    } else {
        $profileDir = Get-DefaultProfile
    }
    
    # 确保用户目录存在
    if (-not (Test-Path $profileDir)) {
        New-Item -Path $profileDir -ItemType Directory -Force | Out-Null
    }
    
    Write-LogInfo "用户数据目录: $profileDir"
    Write-LogInfo "调试端口: $Port"
    
    # 构建启动参数
    $chromeArgs = Build-ChromeArgs $profileDir
    
    Write-LogInfo "正在启动Chrome浏览器..."
    Write-LogInfo "日志文件: $LogFile"
    
    # 启动Chrome
    try {
        $process = Start-Process -FilePath $chromeExecutable -ArgumentList $chromeArgs -PassThru -NoNewWindow
        Write-LogInfo "Chrome已启动 (PID: $($process.Id))"
        
        # 等待Chrome启动
        Start-Sleep -Seconds 3
        
        # 测试调试端口连接
        if (Test-DebugConnection) {
            Write-LogInfo "调试端口连接测试成功"
            Write-Host ""
            Write-Host "🎉 Chrome MCP连接就绪！" -ForegroundColor Green
            Write-Host ""
            Write-LogInfo "连接命令:"
            Write-Host "npx chrome-devtools-mcp@latest --browserUrl http://127.0.0.1:$Port" -ForegroundColor Blue
            Write-Host ""
            Write-LogInfo "或者在IDE中配置MCP连接到: http://127.0.0.1:$Port"
            Write-Host ""
        } else {
            Write-LogWarn "调试端口连接测试失败，请稍后重试"
        }
        
        # 保存PID用于后续管理
        $pidFile = Join-Path $ScriptDir "chrome-mcp.pid"
        $process.Id | Out-File -FilePath $pidFile -Encoding utf8
        Write-LogInfo "进程ID已保存到: $pidFile"
        
    } catch {
        Write-LogError "Chrome启动失败: $_"
        exit 1
    }
}

# 运行主函数
Main
