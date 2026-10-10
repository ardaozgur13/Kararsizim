#!/bin/bash
set -e

echo "=== Vercel Build Başlıyor ==="

# Klasörün her halükarda var olmasını garantiye al
mkdir -p staticfiles

# Python komutunu tespit et
if command -v python3.11 &>/dev/null; then
    PYTHON_BIN="python3.11"
elif command -v python3 &>/dev/null; then
    PYTHON_BIN="python3"
elif command -v python &>/dev/null; then
    PYTHON_BIN="python"
else
    PYTHON_BIN="python3"
fi

echo "Kullanılan Python: $PYTHON_BIN"

# Bağımlılıkları yükle
echo "Bağımlılıklar yükleniyor..."
$PYTHON_BIN -m pip install -r requirements.txt

# Statik dosyaları derle
echo "Statik dosyalar derleniyor (collectstatic)..."
$PYTHON_BIN manage.py collectstatic --noinput --clear

echo "=== Vercel Build Başarıyla Tamamlandı ==="
