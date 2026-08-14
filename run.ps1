cls
# Script auxiliar para executar o Dashboard do Projeto no Windows (PowerShell)
$VENV_PATH = ".\venv"

if (-not (Test-Path -Path $VENV_PATH)) {
    Write-Error "Ambiente virtual não encontrado em '$VENV_PATH'. Por favor, execute './setup.ps1' primeiro para criar e configurar o ambiente."
    exit 1
}

Write-Host "Ativando o ambiente virtual Python..." -ForegroundColor Cyan
& "$VENV_PATH\Scripts\Activate.ps1"

Write-Host "Iniciando o Dashboard Streamlit..." -ForegroundColor Green
streamlit run app/dashboard.py
