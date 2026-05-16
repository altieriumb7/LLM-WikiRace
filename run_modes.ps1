Set-Location 'C:\Users\Umberto\Desktop\LLM-WikiRace'
$env:PYTHONPATH = 'C:\Users\Umberto\Desktop\LLM-WikiRace\src'
$wikigraphPath = 'C:\Users\Umberto\Desktop\LLM-WikiRace-Benchmark\data\wikidata'

foreach ($mode in @('baseline','state_only','stratified','full')) {
    Write-Host "`nMode: $mode" -ForegroundColor Cyan

    & '.\.venv\Scripts\python.exe' scripts\run_benchmark_batch_eval.py `
        --mode-config "configs/modes/$mode.yaml" `
        --difficulty easy --limit 10 --batch-size 4 `
        --wikigraph-path $wikigraphPath `
        --log-save-path "game_logs\official_${mode}_easy_10"

    $files = Get-ChildItem "game_logs\official_${mode}_easy_10" -Recurse -Filter *.jsonl -ErrorAction SilentlyContinue
    if ($files) {
        $rows = foreach ($f in $files) {
            $last = Get-Content $f.FullName | Select-Object -Last 1 | ConvertFrom-Json
            [PSCustomObject]@{
                Status = $last.status
                Steps  = if ($last.path) { $last.path.Count - 1 } else { 0 }
            }
        }
        $rows | Group-Object Status | Select-Object Name, Count | Format-Table
        $done = $rows | Where-Object Status -eq 'completed'
        if ($done) {
            $avg = ($done.Steps | Measure-Object -Average).Average
            Write-Host "Avg steps (completed): $avg"
        }
    }
}
