#Requires -Version 5.1
<#
.SYNOPSIS
    Build + push 2 image SmartLMS len GHCR tu may dev (Windows).

.DESCRIPTION
    Buoc 1 cua luong deploy image-only: server khong build, chi pull.
    Sau khi push xong, chay deploy/scripts/deploy-remote.ps1 de deploy.

    Ten image GHCR phai VIET THUONG - script tu lowercase owner lay tu git remote.

.PARAMETER Owner
    GitHub owner (mac dinh: parse tu `git remote get-url origin`).

.PARAMETER Tag
    Tag cho image (mac dinh: `git rev-parse --short HEAD`).

.PARAMETER ApiBase
    VITE_API_BASE_URL baked vao bundle frontend (mac dinh: /api, dung khi co nginx).

.PARAMETER Platform
    vd: linux/amd64 - can khi may dev khac kien truc voi server (Mac ARM -> VPS amd64).

.PARAMETER NoPush
    Chi build, khong push (kiem tra image local).

.PARAMETER SkipFrontend
    Chi build backend.

.PARAMETER SkipBackend
    Chi build frontend.

.EXAMPLE
    pwsh deploy/scripts/build-push.ps1

.EXAMPLE
    pwsh deploy/scripts/build-push.ps1 -Tag v1.2.0 -Platform linux/amd64
#>
[CmdletBinding()]
param(
    [string]$Owner = "",
    [string]$Tag = "",
    [string]$ApiBase = "/api",
    [string]$Platform = "",
    [switch]$NoPush,
    [switch]$SkipFrontend,
    [switch]$SkipBackend
)

$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $RepoRoot

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Khong tim thay docker CLI. Bat Docker Desktop roi chay lai."
}

if (-not $Owner) {
    $remote = (& git remote get-url origin 2>$null)
    if (-not $remote) { throw "Khong doc duoc git remote 'origin'. Truyen -Owner <github-user>." }
    $remote = $remote.Trim()
    if ($remote -match '[:/]([^/:]+)/([^/]+?)(\.git)?$') {
        $Owner = $Matches[1]
    }
    else {
        throw "Khong parse duoc owner tu remote: $remote. Truyen -Owner <github-user>."
    }
}
# GHCR: repository name phai lowercase, neu khong docker bao
# "invalid reference format: repository name must be lowercase"
$Owner = $Owner.ToLower()

if (-not $Tag) {
    $Tag = (& git rev-parse --short HEAD 2>$null)
    if (-not $Tag) { $Tag = "dev" }
    $Tag = $Tag.Trim()
}

$BackendImage = "ghcr.io/$Owner/smartlms-backend"
$FrontendImage = "ghcr.io/$Owner/smartlms-frontend"
$PlatformArg = @()
if ($Platform) { $PlatformArg = @("--platform", $Platform) }

Write-Host "==> owner=$Owner tag=$Tag" -ForegroundColor Cyan
Write-Host "    backend : ${BackendImage}:$Tag" -ForegroundColor DarkGray
Write-Host "    frontend: ${FrontendImage}:$Tag (VITE_API_BASE_URL=$ApiBase)" -ForegroundColor DarkGray

if (-not $SkipBackend) {
    Write-Host "==> build backend" -ForegroundColor Cyan
    & docker build @PlatformArg -t "${BackendImage}:$Tag" -t "${BackendImage}:latest" ./backend
    if ($LASTEXITCODE -ne 0) { throw "docker build backend that bai." }
}

if (-not $SkipFrontend) {
    Write-Host "==> build frontend" -ForegroundColor Cyan
    & docker build @PlatformArg `
        -f deploy/docker/Dockerfile.frontend.prod `
        --build-arg "VITE_API_BASE_URL=$ApiBase" `
        -t "${FrontendImage}:$Tag" -t "${FrontendImage}:latest" ./frontend
    if ($LASTEXITCODE -ne 0) { throw "docker build frontend that bai." }
}

if ($NoPush) {
    Write-Host "==> -NoPush: bo qua push" -ForegroundColor Yellow
}
else {
    Write-Host "==> push len GHCR" -ForegroundColor Cyan
    if (-not $SkipBackend) {
        & docker push "${BackendImage}:$Tag"
        if ($LASTEXITCODE -ne 0) { throw "docker push backend that bai (da docker login ghcr.io chua?)." }
        & docker push "${BackendImage}:latest"
    }
    if (-not $SkipFrontend) {
        & docker push "${FrontendImage}:$Tag"
        if ($LASTEXITCODE -ne 0) { throw "docker push frontend that bai (da docker login ghcr.io chua?)." }
        & docker push "${FrontendImage}:latest"
    }
}

Write-Host ""
Write-Host "Xong. Deploy:" -ForegroundColor Green
Write-Host "  pwsh deploy/scripts/deploy-remote.ps1 -Server <ip> -User <user> -Tag $Tag -Proxy"
if (-not $NoPush) {
    Write-Host "  (nho dien BACKEND_IMAGE=$BackendImage va FRONTEND_IMAGE=$FrontendImage vao deploy/.env.prod tren server)"
}
