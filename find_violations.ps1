# find_violations.ps1
# PowerShell script to find configuration violations
# Run: .\find_violations.ps1

Write-Host "==============================================================" -ForegroundColor Cyan
Write-Host "CONFIGURATION VIOLATION SCANNER" -ForegroundColor Cyan
Write-Host "==============================================================" -ForegroundColor Cyan

$srcPath = "src\agents"

# 1. Find all Config classes
Write-Host "`n🔴 CRITICAL: Config Classes (should be in config.py)" -ForegroundColor Red
Write-Host "--------------------------------------------------------------"
Get-ChildItem -Path $srcPath -Filter "*.py" -Recurse | ForEach-Object {
    $matches = Select-String -Path $_.FullName -Pattern "class\s+\w+Config\(" -AllMatches
    if ($matches) {
        foreach ($match in $matches) {
            $fileName = $_.Name
            $lineNum = $match.LineNumber
            $line = $match.Line.Trim()
            Write-Host "  $fileName (Line $lineNum): $line" -ForegroundColor Yellow
        }
    }
}

# 2. Find duplicate constants
Write-Host "`n🟠 HIGH: Module-level Constants" -ForegroundColor Yellow
Write-Host "--------------------------------------------------------------"
Get-ChildItem -Path $srcPath -Filter "*.py" -Recurse | ForEach-Object {
    $matches = Select-String -Path $_.FullName -Pattern "^[A-Z_]+ = " -AllMatches
    if ($matches) {
        foreach ($match in $matches) {
            $fileName = $_.Name
            $lineNum = $match.LineNumber
            $line = $match.Line.Trim()
            Write-Host "  $fileName (Line $lineNum): $line" -ForegroundColor Yellow
        }
    }
}

# 3. Find hardcoded periods
Write-Host "`n🟡 MEDIUM: Hardcoded Time Periods" -ForegroundColor DarkYellow
Write-Host "--------------------------------------------------------------"
Get-ChildItem -Path $srcPath -Filter "*.py" -Recurse | ForEach-Object {
    $matches = Select-String -Path $_.FullName -Pattern "(default_)?period["\s:=]+["\']?\d+[YMD]" -AllMatches
    if ($matches) {
        foreach ($match in $matches) {
            $fileName = $_.Name
            $lineNum = $match.LineNumber
            $line = $match.Line.Trim()
            if ($line.Length -gt 70) { $line = $line.Substring(0, 70) + "..." }
            Write-Host "  $fileName (Line $lineNum): $line" -ForegroundColor DarkYellow
        }
    }
}

# 4. Find hardcoded thresholds/rates
Write-Host "`n🟡 MEDIUM: Hardcoded Rates/Thresholds" -ForegroundColor DarkYellow
Write-Host "--------------------------------------------------------------"
Get-ChildItem -Path $srcPath -Filter "*.py" -Recurse | ForEach-Object {
    $matches = Select-String -Path $_.FullName -Pattern "(threshold|rate)[:\s=]+0\.\d+" -AllMatches
    if ($matches) {
        foreach ($match in $matches) {
            $fileName = $_.Name
            $lineNum = $match.LineNumber
            $line = $match.Line.Trim()
            if ($line.Length -gt 70) { $line = $line.Substring(0, 70) + "..." }
            Write-Host "  $fileName (Line $lineNum): $line" -ForegroundColor DarkYellow
        }
    }
}

# 5. Find uses of old constants
Write-Host "`n⚪ INFO: Uses of TRADING_DAYS_PER_YEAR" -ForegroundColor Gray
Write-Host "--------------------------------------------------------------"
$tdpy = Get-ChildItem -Path $srcPath -Filter "*.py" -Recurse | Select-String -Pattern "TRADING_DAYS_PER_YEAR"
if ($tdpy) {
    foreach ($match in $tdpy) {
        $fileName = Split-Path $match.Path -Leaf
        $lineNum = $match.LineNumber
        Write-Host "  $fileName (Line $lineNum)" -ForegroundColor Gray
    }
} else {
    Write-Host "  ✅ None found (good!)" -ForegroundColor Green
}

Write-Host "`n==============================================================" -ForegroundColor Cyan
Write-Host "SUMMARY" -ForegroundColor Cyan
Write-Host "==============================================================" -ForegroundColor Cyan
Write-Host "Review the violations above and consolidate into config.py"
Write-Host ""
Write-Host "RECOMMENDED ACTIONS:"
Write-Host "1. Move all XxxConfig classes to config.py"
Write-Host "2. Move all CONSTANTS to config.py"
Write-Host "3. Replace hardcoded values with config.data.X"
Write-Host "4. Run this script again to verify"
Write-Host ""