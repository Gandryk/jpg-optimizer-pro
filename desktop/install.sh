#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# JPG Optimizer Pro - Скрипт встановлення
# Версія: 1.0
# ═══════════════════════════════════════════════════════════════════════════

set -e

echo ""
echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║           🖼  JPG Optimizer Pro - Встановлення                    ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo ""

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_NAME="JPG Optimizer Pro"
APP_PATH="$SCRIPT_DIR/$APP_NAME.app"

# ─────────────────────────────────────────────────────────────────────────────
# Перевірка Python 3
# ─────────────────────────────────────────────────────────────────────────────
echo "🔍 Перевірка Python 3..."

if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1)
    echo "   ✅ $PYTHON_VERSION"
else
    echo "   ❌ Python 3 не знайдено!"
    echo ""
    echo "   Встановіть Python 3 одним із способів:"
    echo "   • Завантажте з https://python.org/downloads/"
    echo "   • Або через Homebrew: brew install python3"
    echo ""
    exit 1
fi

# ─────────────────────────────────────────────────────────────────────────────
# Встановлення Python залежностей
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "📦 Встановлення Python бібліотек..."

python3 -m pip install --upgrade pip -q 2>/dev/null || true
python3 -m pip install Pillow piexif -q 2>/dev/null

if python3 -c "from PIL import Image; import piexif" 2>/dev/null; then
    echo "   ✅ Pillow та piexif встановлено"
else
    echo "   ❌ Помилка встановлення бібліотек"
    echo "   Спробуйте вручну: pip3 install Pillow piexif"
    exit 1
fi

# ─────────────────────────────────────────────────────────────────────────────
# Перевірка MozJPEG (опціонально)
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "🔧 Перевірка MozJPEG (опціонально)..."

MOZJPEG_FOUND=false
if [ -f "/opt/homebrew/opt/mozjpeg/bin/cjpeg" ] || [ -f "/usr/local/opt/mozjpeg/bin/cjpeg" ]; then
    echo "   ✅ MozJPEG встановлено - оптимальне стиснення активне"
    MOZJPEG_FOUND=true
else
    echo "   ⚠️  MozJPEG не знайдено"
    echo ""
    echo "   MozJPEG дає на 10-15% краще стиснення."
    echo "   Хочете встановити? (потрібен Homebrew)"
    echo ""
    read -p "   Встановити MozJPEG? (y/n): " -n 1 -r
    echo ""

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if command -v brew &> /dev/null; then
            echo "   📥 Встановлення MozJPEG..."
            brew install mozjpeg
            echo "   ✅ MozJPEG встановлено"
            MOZJPEG_FOUND=true
        else
            echo "   ⚠️  Homebrew не знайдено. Пропускаємо MozJPEG."
            echo "   Встановіть Homebrew: https://brew.sh"
        fi
    else
        echo "   ℹ️  Пропускаємо MozJPEG. Додаток буде використовувати Pillow."
    fi
fi

# ─────────────────────────────────────────────────────────────────────────────
# Перевірка .app пакету
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "📱 Перевірка додатку..."

if [ -d "$APP_PATH" ]; then
    echo "   ✅ $APP_NAME.app знайдено"
else
    echo "   ❌ $APP_NAME.app не знайдено в папці встановлення"
    exit 1
fi

# ─────────────────────────────────────────────────────────────────────────────
# Копіювання в /Applications
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "📂 Встановлення в /Applications..."
echo ""
read -p "   Скопіювати додаток в /Applications? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Видалення старої версії
    if [ -d "/Applications/$APP_NAME.app" ]; then
        echo "   🗑  Видалення старої версії..."
        rm -rf "/Applications/$APP_NAME.app"
    fi

    # Копіювання
    echo "   📋 Копіювання..."
    cp -R "$APP_PATH" /Applications/

    # Видалення карантину (щоб macOS не блокував)
    xattr -rd com.apple.quarantine "/Applications/$APP_NAME.app" 2>/dev/null || true

    echo "   ✅ Додаток встановлено в /Applications"
    INSTALLED_PATH="/Applications/$APP_NAME.app"
else
    echo "   ℹ️  Пропускаємо копіювання. Можете запустити з поточної папки."
    INSTALLED_PATH="$APP_PATH"
fi

# ─────────────────────────────────────────────────────────────────────────────
# Готово
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║                    ✨ Встановлення завершено!                     ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo ""
echo "   📍 Шлях: $INSTALLED_PATH"
echo ""
echo "   🚀 Способи запуску:"
echo "      • Знайдіть 'JPG Optimizer Pro' в Launchpad"
echo "      • Відкрийте через Finder → Програми"
echo "      • Або запустіть: open \"$INSTALLED_PATH\""
echo ""

if [ "$MOZJPEG_FOUND" = true ]; then
    echo "   ⚡ MozJPEG активний - максимальна якість стиснення!"
else
    echo "   💡 Порада: встановіть MozJPEG для кращих результатів:"
    echo "      brew install mozjpeg"
fi

echo ""
echo "───────────────────────────────────────────────────────────────────────"
echo ""

# Запитати чи запустити
read -p "   Запустити додаток зараз? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "   🚀 Запуск..."
    open "$INSTALLED_PATH"
fi

echo ""
echo "   Дякуємо за використання JPG Optimizer Pro! 🎉"
echo ""
