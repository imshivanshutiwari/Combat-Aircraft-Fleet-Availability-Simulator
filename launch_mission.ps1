
# 🚀 MISSION-READY OPS CENTER LAUNCH SCRIPT (Windows PowerShell)

Write-Host "--- FLEET OPS CENTER: UNIVERSAL MASTER DEPLOYMENT ---" -ForegroundColor Cyan
Write-Host "Initializing containerized environment..." -ForegroundColor White

# Check for Docker
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "❌ ERROR: Docker is not installed or not in PATH." -ForegroundColor Red
    Write-Host "Please install Docker Desktop and try again."
    exit
}

# Build and Start
Write-Host "Building Mission-Ready Image (this may take a few minutes)..." -ForegroundColor Yellow
docker-compose up --build -d

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ DEPLOYMENT SUCCESSFUL!" -ForegroundColor Green
    Write-Host "Dashboard available at: http://localhost:8501" -ForegroundColor Cyan
    Write-Host "ZMQ Bridge active at: tcp://localhost:5555" -ForegroundColor White
    Write-Host "Use 'docker-compose down' to terminate mission."
} else {
    Write-Host "❌ DEPLOYMENT FAILED. Check Docker logs for details." -ForegroundColor Red
}
