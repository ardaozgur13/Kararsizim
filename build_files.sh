#!/bin/bash
set -e

echo "=== Vercel Build Başlıyor ==="

# Statik klasörünün varlığını garantiye al
mkdir -p staticfiles_build/static

# Python sürümünü belirle
if command -v python3.11 &>/dev/null; then
    PYTHON_BIN="python3.11"
elif command -v python3 &>/dev/null; then
    PYTHON_BIN="python3"
elif command -v python &>/dev/null; then
    PYTHON_BIN="python"
else
    PYTHON_BIN="python3"
fi

echo "Python komutu: $PYTHON_BIN"

# PEP 668 (externally-managed-environment) için izole sanal ortam oluştur ve aktif et
echo "Derleme sanal ortamı hazırlanıyor..."
$PYTHON_BIN -m venv .build_venv
source .build_venv/bin/activate

echo "Bağımlılıklar yükleniyor..."
pip install -r requirements.txt

echo "Statik dosyalar derleniyor (collectstatic)..."
python manage.py collectstatic --noinput --clear

echo "=== Vercel Build Başarıyla Tamamlandı ==="
