<#
.SYNOPSIS
    MeFrp-GR-Client 宝塔面板部署脚本（Windows 本地侧）
.DESCRIPTION
    一键打包 docs/ 并上传到宝塔服务器，自动解压、设置权限、刷新 Nginx。
    首次运行会要求输入服务器信息，保存到 deploy-bt.config.json。
.PARAMETER Domain
    部署的域名，例如 mefrp.example.com
.PARAMETER Server
    服务器 SSH 地址，例如 root@1.2.3.4 或 user@1.2.3.4:22
.PARAMETER SshKey
    SSH 私钥路径（可选，默认使用密码或 ssh-agent）
.EXAMPLE
    .\deploy-bt.ps1 -Domain mefrp.example.com -Server root@1.2.3.4
.EXAMPLE
    .\deploy-bt.ps1   # 使用上次保存的配置
#>
[CmdletBinding()]
param(
    [string]$Domain = "",
    [string]$Server = "",
    [string]$SshKey = ""
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

# ---------- 路径 ----------
$ScriptDir   = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$DocsDir     = Join-Path $ProjectRoot "docs"
$ConfigFile  = Join-Path $ScriptDir "deploy-bt.config.json"
$TmpZip      = Join-Path $env:TEMP "mefrp-site-$([guid]::NewGuid().ToString('N').Substring(0,8)).zip"
$TmpScript   = Join-Path $env:TEMP "mefrp-deploy-server.sh"

# ---------- 颜色 ----------
function Write-Step($msg)  { Write-Host "[$(Get-Date -Format 'HH:mm:ss')] $msg" -ForegroundColor Cyan }
function Write-OK($msg)    { Write-Host "[OK] $msg" -ForegroundColor Green }
function Write-Warn($msg)  { Write-Host "[!] $msg" -ForegroundColor Yellow }
function Write-Err($msg)   { Write-Host "[X] $msg" -ForegroundColor Red }

# ---------- 加载/创建配置 ----------
function Load-Config {
    if (Test-Path $ConfigFile) {
        try {
            $json = Get-Content $ConfigFile -Raw -Encoding UTF8 | ConvertFrom-Json
            Write-OK "已加载配置：$ConfigFile"
            return $json
        } catch {
            Write-Warn "配置文件解析失败，将重新创建"
        }
    }
    return $null
}

function Save-Config($cfg) {
    $cfg | ConvertTo-Json -Depth 5 | Set-Content $ConfigFile -Encoding UTF8
    Write-OK "配置已保存到 $ConfigFile"
}

# ---------- 1. 收集配置 ----------
Write-Step "=== MeFrp-GR-Client 宝塔部署 ==="
Write-Step "项目根目录：$ProjectRoot"

if (-not (Test-Path $DocsDir)) {
    Write-Err "找不到 $DocsDir"
    exit 1
}

$cfg = Load-Config
if (-not $Domain -and $cfg)      { $Domain = $cfg.domain }
if (-not $Server -and $cfg)      { $Server = $cfg.server }
if (-not $SshKey -and $cfg)     { $SshKey = $cfg.sshKey }

if (-not $Domain) {
    $Domain = Read-Host "请输入部署域名（例如 mefrp.example.com）"
}
if (-not $Server) {
    $Server = Read-Host "请输入 SSH 地址（例如 root@1.2.3.4）"
}
if (-not $SshKey) {
    $ans = Read-Host "SSH 私钥路径？直接回车用密码登录"
    if ($ans) { $SshKey = $ans }
}

# 宝塔 API（可选）
$btPanel = ""
$btKey   = ""
if ($cfg) { $btPanel = $cfg.btPanel; $btKey = $cfg.btKey }
if (-not $btPanel) {
    $ans = Read-Host "宝塔面板地址（可选，例如 https://1.2.3.4:8888；直接回车跳过）"
    if ($ans) { $btPanel = $ans }
}
if ($btPanel -and -not $btKey) {
    $btKey = Read-Host "宝塔 API Key（在面板 → 设置 → API 接口查看）" -AsSecureString
    $ptr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($btKey)
    $btKey = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($ptr)
    [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
}

# 保存配置
$saveObj = @{
    domain = $Domain
    server = $Server
    sshKey = $SshKey
    btPanel = $btPanel
    btKey = $btKey
}
Save-Config $saveObj

# ---------- 2. 打包 docs/ ----------
Write-Step "打包 docs/ → $TmpZip"
if (Test-Path $TmpZip) { Remove-Item $TmpZip -Force }

Add-Type -AssemblyName System.IO.Compression.FileSystem
$docsFull = (Resolve-Path $DocsDir).Path
[System.IO.Compression.ZipFile]::CreateFromDirectory(
    $docsFull, $TmpZip,
    [System.IO.Compression.CompressionLevel]::Optimal,
    $false
)
$size = (Get-Item $TmpZip).Length
Write-OK "打包完成 ($([math]::Round($size/1KB,1)) KB)"

# ---------- 3. 准备服务器侧脚本 ----------
$serverScript = Get-Content (Join-Path $ScriptDir "deploy-bt-server.sh") -Raw -Encoding UTF8
Set-Content $TmpScript -Value $serverScript -Encoding UTF8 -NoNewline

# ---------- 4. 构建 SSH/SCP 参数 ----------
function Get-SshArgs {
    $args = @()
    if ($SshKey) {
        $args += "-i"; $args += $SshKey
    }
    $args += "-o"; $args += "StrictHostKeyChecking=accept-new"
    $args += "-o"; $args += "ServerAliveInterval=30"
    return $args
}

$sshArgs = Get-SshArgs

# ---------- 5. 上传部署包和脚本 ----------
Write-Step "上传部署包 → $Server"
& scp @sshArgs $TmpZip "${Server}:/tmp/mefrp-site.zip"
if ($LASTEXITCODE -ne 0) { Write-Err "scp 上传部署包失败"; exit 1 }
Write-OK "部署包已上传"

Write-Step "上传服务器脚本"
& scp @sshArgs $TmpScript "${Server}:/tmp/deploy-bt-server.sh"
if ($LASTEXITCODE -ne 0) { Write-Err "scp 上传脚本失败"; exit 1 }
& ssh @sshArgs $Server "chmod +x /tmp/deploy-bt-server.sh"
Write-OK "脚本已上传"

# ---------- 6. 远程执行 ----------
Write-Step "远程执行部署..."
$envArgs = @(
    "BT_SITE_DOMAIN='$Domain'",
    "BT_SITE_ROOT='/www/wwwroot/$Domain'",
    "BT_PANEL='$btPanel'",
    "BT_KEY='$btKey'"
)
$remoteCmd = "$($envArgs -join ' ') bash /tmp/deploy-bt-server.sh"

& ssh @sshArgs -t $Server $remoteCmd
$rc = $LASTEXITCODE

# ---------- 7. 清理临时文件 ----------
Remove-Item $TmpZip, $TmpScript -Force -ErrorAction SilentlyContinue
& ssh @sshArgs $Server "rm -f /tmp/mefrp-site.zip /tmp/deploy-bt-server.sh" 2>$null

# ---------- 8. 结果 ----------
if ($rc -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  部署成功！" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  访问地址：https://$Domain" -ForegroundColor Cyan
    Write-Host "  下次更新：.\deploy-bt.ps1 即可" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Green
} else {
    Write-Err "部署失败（远程退出码 $rc）"
    exit $rc
}
