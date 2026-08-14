# resetall.ps1 — Limpa todos os dados gerados pelo pipeline para reiniciar do zero

Write-Host ""
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "   RESET COMPLETO DO PIPELINE DE EXAMES" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Os seguintes dados serao removidos:" -ForegroundColor Yellow
Write-Host "  - PDFs baixados         (data\exames\*.pdf)"
Write-Host "  - Markdowns gerados     (data\exames\exames_md\)"
Write-Host "  - CSVs de resultados    (data\exames\results\)"
Write-Host "  - Relatorios de audit.  (data\exames\auditoria\)"
Write-Host "  - Screenshots de erro   (data\exames\output\)"
Write-Host "  - Log do pipeline       (_temp\pipeline.log)"
Write-Host ""

$confirm = Read-Host "Tem certeza? Digite 'sim' para confirmar"

if ($confirm -ne "sim") {
    Write-Host ""
    Write-Host "Operacao cancelada." -ForegroundColor Red
    exit 0
}

Write-Host ""

# PDFs baixados
$count = (Get-ChildItem "data\exames\*.pdf" -ErrorAction SilentlyContinue).Count
Remove-Item "data\exames\*.pdf" -Force -ErrorAction SilentlyContinue
Write-Host "  [OK] PDFs removidos: $count" -ForegroundColor Green

# Markdowns
$count = (Get-ChildItem "data\exames\exames_md\*" -ErrorAction SilentlyContinue).Count
Remove-Item "data\exames\exames_md\*" -Force -Recurse -ErrorAction SilentlyContinue
Write-Host "  [OK] Markdowns removidos: $count" -ForegroundColor Green

# CSVs e backups
$count = (Get-ChildItem "data\exames\results\*" -ErrorAction SilentlyContinue).Count
Remove-Item "data\exames\results\*" -Force -Recurse -ErrorAction SilentlyContinue
Write-Host "  [OK] CSVs/Backups removidos: $count" -ForegroundColor Green

# Relatorios de auditoria
$count = (Get-ChildItem "data\exames\auditoria\*" -ErrorAction SilentlyContinue).Count
Remove-Item "data\exames\auditoria\*" -Force -Recurse -ErrorAction SilentlyContinue
Write-Host "  [OK] Relatorios de auditoria removidos: $count" -ForegroundColor Green

# Screenshots de erro do crawler
$count = (Get-ChildItem "data\exames\output\*" -ErrorAction SilentlyContinue).Count
Remove-Item "data\exames\output\*" -Force -Recurse -ErrorAction SilentlyContinue
Write-Host "  [OK] Screenshots de erro removidos: $count" -ForegroundColor Green

# Log do pipeline
if (Test-Path "_temp\pipeline.log") {
    Remove-Item "_temp\pipeline.log" -Force -ErrorAction SilentlyContinue
    Write-Host "  [OK] Log do pipeline removido" -ForegroundColor Green
} else {
    Write-Host "  [--] Nenhum log encontrado (ja estava limpo)" -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "  Reset concluido! Pronto para rodar de zero." -ForegroundColor Cyan
Write-Host "  Execute: ./run.ps1" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""
