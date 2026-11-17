#Requires -Version 5.1
<#
.SYNOPSIS
    Deploy SmartLMS len server tu may dev - KHONG can git clone tren server.

.DESCRIPTION
    Chi copy 4 thu len server roi pull image tu registry:
      deploy/docker-compose.images.yml
      deploy/.env.prod            (neu co o may dev; khong co thi phai co san tren server)
      deploy/nginx/nginx.conf     (bo qua voi -SkipNginx)
      postgres-init/01_extensions.sql
      sgk_data/                   (2.1 GB, bo qua voi -SkipData)

    Sau do chay: docker compose pull && up -d.

.PARAMETER Server
    IP hoac hostname cua server.

.PARAMETER User
    User SSH (mac dinh: root).

.PARAMETER RemotePath
    Thu muc project tren server (mac dinh: /opt/smartlms).

.PARAMETER Tag
    Image tag da push len registry (mac dinh: latest). Dung tag cu de rollback.

.PARAMETER Proxy
    Bat service nginx (profile "proxy") - mo port 80.

.PARAMETER Tunnel
    Bat Cloudflare Tunnel (profile "tunnel", tu bat luon nginx). Can
    CLOUDFLARE_TUNNEL_TOKEN trong deploy/.env.prod tren server.

.PARAMETER Quick
    Bat quick tunnel 0 dong (profile "quick", tu bat luon nginx): khong can domain,
    khong can token. URL *.trycloudflare.com doi moi lan restart - chi de demo.

.PARAMETER SkipData
    Khong upload sgk_data/ (2.1 GB). Dung khi server da co san.

.PARAMETER SkipUpload
    Chi chay compose tren server, khong copy file nao.

.PARAMETER SshKey
    Duong dan private key (mac dinh: dung key/agent cua ssh).

.PARAMETER Port
    SSH port (mac dinh: 22). Bi bo qua khi dung -CloudflareAccess.

.PARAMETER CloudflareAccess
    sshd khong mo ra Internet, di qua Cloudflare Access. Khi bat:
      - -Server la HOSTNAME (vd ssh-staging.vnexus.io.vn), khong phai IP
      - them ProxyCommand "cloudflared access ssh --hostname %h"
      - can TUNNEL_SERVICE_TOKEN_ID / TUNNEL_SERVICE_TOKEN_SECRET trong moi truong

.PARAMETER RegistryUser
    User GHCR de docker login tren server (thuong la GitHub username).

.PARAMETER RegistryToken
    PAT co quyen read:packages. Chi can khi package de private.

.EXAMPLE
    pwsh deploy/scripts/deploy-remote.ps1 -Server 203.0.113.10 -User ubuntu -Proxy -Tag latest

.EXAMPLE
    pwsh deploy/scripts/deploy-remote.ps1 -Server 203.0.113.10 -SkipData -SkipUpload -Tag a1b2c3d
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Server,
    [string]$User = "root",
    [string]$RemotePath = "/opt/smartlms",
    [string]$Tag = "latest",
    [switch]$Proxy,
    [switch]$Tunnel,
    [switch]$Quick,
    [switch]$SkipData,
    [switch]$SkipUpload,
    [switch]$SkipNginx,
    [string]$SshKey = "",
    [int]$Port = 22,
    [switch]$CloudflareAccess,
    [string]$RegistryUser = "",
    [string]$RegistryToken = "",
    [string]$EnvFile = ""
)

$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$ComposeFile = "deploy/docker-compose.images.yml"
$NginxConf = "deploy/nginx/nginx.conf"
$InitSql = "postgres-init/01_extensions.sql"
$DataDir = "sgk_data"
$Target = "$User@$Server"

if (-not $EnvFile) { $EnvFile = Join-Path $RepoRoot "deploy/.env.prod" }

# ssh dung -p, scp dung -P (khac nhau!) - tach rieng de khong lan tham so.
$CommonOpts = @("-o", "ConnectTimeout=10", "-o", "StrictHostKeyChecking=accept-new")
if ($SshKey) { $CommonOpts += @("-i", $SshKey) }

if ($CloudflareAccess) {
    # sshd khong mo ra Internet: di qua Cloudflare Access. -Server la HOSTNAME
    # (vd ssh-staging.vnexus.io.vn), khong phai IP. Khong dung -p/-P.
    # Can 2 bien moi truong cua service token (cloudflared tu doc):
    #   TUNNEL_SERVICE_TOKEN_ID / TUNNEL_SERVICE_TOKEN_SECRET
    $CommonOpts += @("-o", "ProxyCommand=cloudflared access ssh --hostname %h")
    $SshOpts = $CommonOpts
    $ScpOpts = $CommonOpts
} else {
    $SshOpts = $CommonOpts + @("-p", "$Port")
    $ScpOpts = $CommonOpts + @("-P", "$Port")
}

function Invoke-Remote {
    param([string]$Command)
    & ssh @SshOpts $Target $Command
    if ($LASTEXITCODE -ne 0) { throw "Lenh SSH that bai (exit $LASTEXITCODE): $Command" }
}

function Copy-ToRemote {
    param([string]$Source, [string]$Destination)
    & scp @ScpOpts $Source "${Target}:${Destination}"
    if ($LASTEXITCODE -ne 0) { throw "scp that bai (exit $LASTEXITCODE): $Source" }
}

function Test-RemoteFile {
    param([string]$Path)
    $out = & ssh @SshOpts $Target "test -f '$Path' && echo yes || echo no"
    return ($out -join "").Trim() -eq "yes"
}

Write-Host "==> Kiem tra cong cu" -ForegroundColor Cyan
$requiredTools = @("ssh", "scp")
if ($CloudflareAccess) { $requiredTools += "cloudflared" }
foreach ($cmd in $requiredTools) {
    if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) {
        if ($cmd -eq "cloudflared") {
            throw "Thieu 'cloudflared'. Cai bang: winget install --id Cloudflare.cloudflared"
        }
        throw "Thieu '$cmd'. Tren Windows 10+ bat OpenSSH Client trong Settings > Apps > Optional Features."
    }
}
if ($CloudflareAccess) {
    if (-not $env:TUNNEL_SERVICE_TOKEN_ID -or -not $env:TUNNEL_SERVICE_TOKEN_SECRET) {
        throw "Thieu TUNNEL_SERVICE_TOKEN_ID / TUNNEL_SERVICE_TOKEN_SECRET. Tao service token o Zero Trust > Access > Service Auth roi set 2 bien moi truong."
    }
}

Write-Host "==> Kiem tra file local" -ForegroundColor Cyan
foreach ($f in @($ComposeFile, $NginxConf, $InitSql)) {
    if (-not (Test-Path (Join-Path $RepoRoot $f))) { throw "Thieu file: $f" }
}
$HasLocalEnv = Test-Path $EnvFile
if (-not $HasLocalEnv -and -not $SkipUpload) {
    Write-Host "    (!) Khong thay deploy/.env.prod o may dev - se dung file co san tren server." -ForegroundColor Yellow
}

Write-Host "==> Tao thu muc tren server ($Target`:$RemotePath)" -ForegroundColor Cyan
Invoke-Remote ("mkdir -p '{0}/deploy/nginx' '{0}/postgres-init' '{0}/sgk_data'" -f $RemotePath)

if (-not $SkipUpload) {
    Write-Host "==> Copy config" -ForegroundColor Cyan
    Copy-ToRemote (Join-Path $RepoRoot $ComposeFile) "$RemotePath/deploy/"
    Copy-ToRemote (Join-Path $RepoRoot $InitSql) "$RemotePath/postgres-init/"
    if (-not $SkipNginx) {
        Copy-ToRemote (Join-Path $RepoRoot $NginxConf) "$RemotePath/deploy/nginx/"
    }
    if ($HasLocalEnv) {
        Copy-ToRemote $EnvFile "$RemotePath/deploy/"
        Write-Host "    da copy deploy/.env.prod (kiem tra lai secret tren server!)" -ForegroundColor Yellow
    }
}

# Kiem tra .env.prod TRUOC khi upload 2 GB sgk_data - tranh upload xong moi bao loi.
if (-not (Test-RemoteFile "$RemotePath/deploy/.env.prod")) {
    Write-Host ""
    Write-Host "DUNG: server chua co $RemotePath/deploy/.env.prod" -ForegroundColor Red
    Write-Host "Tao file env tren server roi chay lai script:" -ForegroundColor Yellow
    Write-Host "  scp deploy/.env.prod.example ${Target}:${RemotePath}/deploy/.env.prod"
    Write-Host "  ssh ${Target} `"nano ${RemotePath}/deploy/.env.prod`"   # dien DB password, SECRET_KEY, API key, R2_*"
    Write-Host "Hoac dat file that vao deploy/.env.prod o may dev roi chay lai (script se tu copy)."
    exit 1
}

if ($Tunnel) {
    $tok = (& ssh @SshOpts $Target "grep -E '^CLOUDFLARE_TUNNEL_TOKEN=.+' '$RemotePath/deploy/.env.prod' | head -1")
    if (-not (($tok -join "").Trim())) {
        throw "Thieu CLOUDFLARE_TUNNEL_TOKEN trong $RemotePath/deploy/.env.prod. Tao tunnel tren Zero Trust dashboard roi dien token truoc khi dung -Tunnel."
    }
}

if (-not $SkipUpload -and -not $SkipData) {
    if (Test-RemoteFile "$RemotePath/sgk_data/vectors.dump") {
        Write-Host "    sgk_data da co tren server - bo qua (dung -SkipData de tat han)." -ForegroundColor DarkGray
    }
    else {
        $localData = Join-Path $RepoRoot $DataDir
        if (-not (Test-Path $localData)) { throw "Thieu thu muc $DataDir o may dev." }
        $bytes = (Get-ChildItem $localData -File | Measure-Object Length -Sum).Sum
        Write-Host ("    Upload {0} (~{1} GB) - co the mat vai phut..." -f $DataDir, [math]::Round($bytes / 1GB, 2)) -ForegroundColor Yellow
        Copy-ToRemote $localData "$RemotePath/"
    }
}

if ($RegistryToken) {
    if (-not $RegistryUser) { throw "Can -RegistryUser khi dung -RegistryToken." }
    Write-Host "==> docker login ghcr.io tren server" -ForegroundColor Cyan
    $RegistryToken | & ssh @SshOpts $Target "docker login ghcr.io -u '$RegistryUser' --password-stdin"
    if ($LASTEXITCODE -ne 0) { throw "docker login that bai." }
}

$profiles = @()
if ($Proxy) { $profiles += "--profile proxy" }
if ($Tunnel) { $profiles += "--profile tunnel" }
if ($Quick) { $profiles += "--profile quick" }
$profileArg = ($profiles -join " ")
$compose = "docker compose --project-directory . --env-file deploy/.env.prod -f $ComposeFile $profileArg"

$remoteScript = @'
set -e
cd __REMOTE_PATH__
export IMAGE_TAG=__TAG__
echo "==> pull image (tag=$IMAGE_TAG)"
__COMPOSE__ pull
echo "==> up -d"
__COMPOSE__ up -d --remove-orphans
echo "==> ps"
__COMPOSE__ ps
echo "==> doi backend healthy (toi da 90s)"
status="unknown"
for i in $(seq 1 45); do
  status=$(docker inspect -f '{{.State.Health.Status}}' smartlms_backend 2>/dev/null || echo starting)
  [ "$status" = "healthy" ] && break
  sleep 2
done
echo "backend health: $status"
[ "$status" = "healthy" ] || { echo "LOI: backend khong healthy - xem: docker logs --tail 100 smartlms_backend"; exit 1; }
echo "==> OK"
'@

$remoteScript = $remoteScript.Replace("__REMOTE_PATH__", $RemotePath).
    Replace("__TAG__", $Tag).
    Replace("__COMPOSE__", $compose)

Write-Host "==> Deploy (tag=$Tag, proxy=$([bool]$Proxy))" -ForegroundColor Cyan
Invoke-Remote $remoteScript

$quickUrl = ""
if ($Quick) {
    Write-Host "==> Lay URL quick tunnel" -ForegroundColor Cyan
    for ($i = 0; $i -lt 15; $i++) {
        $out = & ssh @SshOpts $Target "docker logs smartlms_cloudflared_quick 2>&1 | grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' | head -1"
        $quickUrl = ($out -join "").Trim()
        if ($quickUrl) { break }
        Start-Sleep -Seconds 2
    }
}

Write-Host ""
Write-Host "Xong." -ForegroundColor Green
if ($Quick) {
    if ($quickUrl) {
        Write-Host "  URL tam thoi: $quickUrl" -ForegroundColor Green
        Write-Host "  (doi moi lan restart container - chi de demo, khong dung cho production)"
    }
    else {
        Write-Host "  Chua lay duoc URL. Xem tren server: docker logs smartlms_cloudflared_quick"
    }
}
elseif ($Tunnel) {
    Write-Host "  Cloudflare Tunnel dang chay. Mo domain da cau hinh tren Zero Trust dashboard."
    Write-Host "  Kiem tra log tunnel tren server: docker logs -f smartlms_cloudflared"
    Write-Host "  Luu y: public hostname phai tro vao http://nginx:80"
}
elseif ($Proxy) {
    Write-Host "  URL phu thuoc NGINX_BIND/NGINX_PORT trong deploy/.env.prod tren server:"
    Write-Host "    NGINX_BIND=0.0.0.0, NGINX_PORT=80     -> http://$Server/"
    Write-Host "    NGINX_BIND=127.0.0.1, NGINX_PORT=8080 -> http://127.0.0.1:8080/ (tren server),"
    Write-Host "                                             host nginx/tunnel tro vao do"
}
else {
    Write-Host "  Khong bat -Proxy/-Tunnel => khong co port nao publish ra ngoai."
    Write-Host "  Kiem tra tren server: docker compose --project-directory . --env-file deploy/.env.prod -f $ComposeFile ps"
}
