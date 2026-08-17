[CmdletBinding()]
param(
  [string]$TenantId = "EL ID DE TU TENANT",
  [string]$Resource = "https://api.fabric.microsoft.com",
  [int]$Port = 39397,
  [switch]$UseDeviceCode,
  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]]$CodexArguments
)

$ErrorActionPreference = "Stop"

$ProxyScript = Join-Path $HOME ".codex\mcp-powerbi-remote-proxy\powerbi-remote-http-proxy.mjs"
$ProxyUrl = "http://127.0.0.1:$Port/mcp"
$HealthUrl = "http://127.0.0.1:$Port/health"
$ReadyUrl = "http://127.0.0.1:$Port/ready"

function Assert-Command($Name) {
  if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
    throw "Required command '$Name' was not found in PATH."
  }
}

function Get-FabricToken {
  $token = & az account get-access-token `
    --resource $Resource `
    --query accessToken `
    --output tsv 2>$null

  if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($token)) {
    return $null
  }

  return $token.Trim()
}

function Test-HttpOk($Url) {
  try {
    $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 2
    return $response.StatusCode -ge 200 -and $response.StatusCode -lt 300
  } catch {
    return $false
  }
}

function Wait-HttpOk($Url, $Seconds) {
  $deadline = (Get-Date).AddSeconds($Seconds)
  while ((Get-Date) -lt $deadline) {
    if (Test-HttpOk $Url) {
      return $true
    }
    Start-Sleep -Milliseconds 500
  }
  return $false
}

Assert-Command "az"
Assert-Command "node"
Assert-Command "codex"

if (-not (Test-Path -LiteralPath $ProxyScript)) {
  throw "Power BI MCP proxy script was not found: $ProxyScript"
}

if (-not (Get-FabricToken)) {
  $loginArgs = @("login", "--tenant", $TenantId, "--allow-no-subscriptions")
  if ($UseDeviceCode) {
    $loginArgs += "--use-device-code"
  }

  Write-Host "Azure CLI has no usable Fabric token. Starting user sign-in..."
  & az @loginArgs

  if ($LASTEXITCODE -ne 0 -or -not (Get-FabricToken)) {
    throw "Azure CLI sign-in finished, but no Fabric token was available."
  }
}

$env:POWERBI_MCP_PROXY_PORT = [string]$Port
$env:POWERBI_MCP_RESOURCE = $Resource
$env:POWERBI_MCP_URL = "https://api.fabric.microsoft.com/v1/mcp/powerbi"

if (-not (Test-HttpOk $HealthUrl)) {
  Start-Process `
    -FilePath "node" `
    -ArgumentList @($ProxyScript) `
    -WindowStyle Hidden | Out-Null
}

if (-not (Wait-HttpOk $HealthUrl 15)) {
  throw "Power BI MCP HTTP proxy did not start on $ProxyUrl."
}

if (-not (Wait-HttpOk $ReadyUrl 15)) {
  Write-Warning "The proxy is running, but token readiness could not be verified. Continuing because Azure CLI token preflight succeeded."
}

$codexConfig = @(
  "--config", "mcp_servers.powerbi_remote.enabled=true",
  "--config", "mcp_servers.powerbi_remote.url=`"$ProxyUrl`"",
  "--config", "mcp_servers.powerbi_remote_stdio_fallback.enabled=false",
  "--config", "mcp_servers.powerbi_remote_http_practice.enabled=false"
)

& codex @codexConfig @CodexArguments
exit $LASTEXITCODE
