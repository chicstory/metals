# ThePathLab 일일 자동 브리핑 작업 스케줄러 등록 스크립트 (평일 월~금 09:30)
$TaskName = "ThePathLab_Daily_Briefing"
$ActionScript = "c:\Users\chics\OneDrive\문서\gemini\thepathlab\auto_daily_briefing.bat"

# 1. 트리거: 매주 월, 화, 수, 목, 금 오전 9시 30분
$Trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday, Tuesday, Wednesday, Thursday, Friday -At 9:30AM

# 2. 실행 동작: cmd.exe를 통해 배치 파일 실행
$Action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$ActionScript`"" -WorkingDirectory "c:\Users\chics\OneDrive\문서\gemini\thepathlab"

# 3. 설정: PC가 절전 모드여도 깨워서 실행 (WakeToRun), 배터리/전원 무관 실행
$Settings = New-ScheduledTaskSettingsSet -WakeToRun -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

# 4. 등록 (기존 작업이 있으면 덮어쓰기)
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
Register-ScheduledTask -TaskName $TaskName -Trigger $Trigger -Action $Action -Settings $Settings -Description "ThePathLab 7대 금속원자재 일일 자동 브리핑 및 배포 (월-금 09:30)"

Write-Host "✅ 작업 스케줄러 등록 완료: $TaskName" -ForegroundColor Green
Write-Host "📅 실행 일정: 매주 월~금 오전 09:30" -ForegroundColor Cyan
Write-Host "⚡ 절전 모드 깨우기(WakeToRun): 활성화됨" -ForegroundColor Cyan
