param([int]$OwnedPid = 0)
$rows = Get-CimInstance Win32_Process -Filter "Name = 'nvda.exe' OR Name = 'python.exe'" |
    Select-Object ProcessId, Name, CommandLine
if ($OwnedPid -gt 0) {
    $rows | Where-Object { $_.ProcessId -eq $OwnedPid -or ($_.Name -eq 'python.exe' -and $_.CommandLine -match 'runtimeWorker.py') }
} else {
    $rows
}
