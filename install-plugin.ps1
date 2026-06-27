# install-plugin.ps1 — מתקין את crypto-dashboard-manager plugin
$source = "$PSScriptRoot\crypto-dashboard-plugin-extracted"
$dest   = "C:\Users\maksi\Claude\plugins\crypto-dashboard-plugin"

if (-not (Test-Path $source)) {
    Write-Error "לא נמצאה תיקיית המקור: $source"
    exit 1
}

# צור תיקיית יעד
New-Item -ItemType Directory -Force -Path $dest | Out-Null

# העתק הכל
Copy-Item -Path "$source\*" -Destination $dest -Recurse -Force

# ודא מבנה
$pluginJson = Join-Path $dest ".claude-plugin\plugin.json"
if (Test-Path $pluginJson) {
    Write-Host "✅ הפלאגין הותקן בהצלחה ב: $dest"
    Write-Host "✅ plugin.json נמצא במיקום הנכון"
} else {
    Write-Error "❌ שגיאה: plugin.json לא נמצא. בדוק את המבנה."
}
