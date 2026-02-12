#!/bin/bash
# JPG Optimizer Pro - Web Version
# Запуск локального сервера

echo "🚀 JPG Optimizer Pro - Web Version"
echo "=================================="

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 не знайдено!"
    exit 1
fi

# Install dependencies if needed
if ! python3 -c "import streamlit" 2>/dev/null; then
    echo "📦 Встановлення залежностей..."
    pip3 install -r requirements.txt
fi

echo ""
echo "🌐 Запуск веб-сервера..."
echo "   Відкрийте в браузері: http://localhost:8501"
echo ""
echo "   Натисніть Ctrl+C для зупинки"
echo ""

streamlit run app.py
