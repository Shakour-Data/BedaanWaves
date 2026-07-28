$ErrorActionPreference = "Stop"
Set-Location -LiteralPath (Split-Path -Parent $MyInvocation.MyCommand.Path)
$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$resultsRoot = Join-Path -Path (Get-Location) -ChildPath "test_results"
$categoryDir = Join-Path -Path $resultsRoot -ChildPath "backend"
New-Item -ItemType Directory -Path $categoryDir -Force | Out-Null
$summaryFile = Join-Path -Path $categoryDir -ChildPath "test_results_$timestamp.txt"
Write-Host "[1/2] Running test suite..."
$fullOutput = python -m pytest -v --tb=short 2>&1 | Out-String
$fullOutput | Out-File -FilePath $summaryFile -Encoding utf8
Write-Host "Summary saved to: $summaryFile"
$testFiles = @(
    "tests\test_base_service.py",
    "tests\test_brs_api_client.py",
    "tests\test_cache_service.py",
    "tests\test_config_service.py",
    "tests\test_database_service.py",
    "tests\test_dependency_container.py",
    "tests\test_fundamental_service.py",
    "tests\test_health_checker.py",
    "tests\test_history_service.py",
    "tests\test_logger_service.py",
    "tests\test_market_service.py",
    "tests\test_momentum_service.py",
    "tests\test_news_service.py",
    "tests\test_notification_service.py",
    "tests\test_portfolio_service.py",
    "tests\test_preference_service.py",
    "tests\test_risk_service.py",
    "tests\test_scoring_service.py",
    "tests\test_specialized_services.py",
    "tests\test_stock_service.py",
    "tests\test_technical_service.py",
    "tests\test_user_profile_service.py",
    "tests\test_volatility_service.py",
    "tests\test_watchlist_service.py"
)
Write-Host "[2/2] Generating categorized result files..."
foreach ($testFile in $testFiles) {
    $safeName = [System.IO.Path]::GetFileNameWithoutExtension($testFile)
    $categoryFile = Join-Path -Path $categoryDir -ChildPath "${safeName}_$timestamp.txt"
    $filtered = python -m pytest -v --tb=short $testFile 2>&1 | Out-String
    $filtered | Out-File -FilePath $categoryFile -Encoding utf8
    Write-Host "  Saved: $categoryFile"
}
Write-Host "Categorized results saved under: $categoryDir"
Write-Host "Done."
