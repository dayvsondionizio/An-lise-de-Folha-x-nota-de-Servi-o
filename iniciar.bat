@echo off
title Painel de Folha eSocial
echo ========================================
echo   Painel de Folha de Pagamento eSocial
echo ========================================
echo.
echo Iniciando... o navegador abrira automaticamente.
echo Para FECHAR o app, feche esta janela preta.
echo.
cd /d "%~dp0"
python -m streamlit run app.py --server.port 8501 --browser.gatherUsageStats false
pause
