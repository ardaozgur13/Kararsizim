# kararsızım ⚖️

Kararsız kalınan konularda 2 ila 5 seçenekli mini anketler açıp diğer kullanıcılardan anlık fikir ve oy toplamayı sağlayan sade, tatlış ve ferah bir topluluk web uygulaması.

---

## 🚀 Teknoloji Yığını

- **Backend:** Python 3.12+, Django 5.x
- **Veritabanı:** Supabase (PostgreSQL) — Django ORM ile bağlantı (yerelde SQLite fallback)
- **Frontend:** Django Templates + Saf HTML, Modern CSS ve Vanilla JS
- **Statik Dosyalar:** WhiteNoise
- **Deployment:** Vercel Serverless WSGI

---

## 🛠️ Yerel Kurulum ve Çalıştırma

### 1. Depoyu klonlayın ve klasöre girin
```bash
git clone <repo-url>
cd Kararsizim
```

### 2. Sanal ortamı hazırlayın ve aktif edin
```bash
python -m venv .venv

# Windows PowerShell:
.\.venv\Scripts\Activate.ps1

# Linux / macOS:
source .venv/bin/activate
```

### 3. Bağımlılıkları yükleyin
```bash
pip install -r requirements.txt
```

### 4. Ortam değişkenlerini yapılandırın
`.env.example` dosyasını `.env` olarak kopyalayın:
```bash
cp .env.example .env
```
*(Eğer Supabase kullanıyorsanız `DATABASE_URL` değişkenine Supabase Connection Pooler adresinizi yazın. Boş bırakırsanız yerel `db.sqlite3` veritabanı kullanılır.)*

### 5. Veritabanı tablolarını oluşturun (Migration)
```bash
python manage.py migrate
```

### 6. Geliştirme sunucusunu başlatın
```bash
python manage.py runserver
```
Tarayıcınızda [http://127.0.0.1:8000](http://127.0.0.1:8000) adresine gidin.

---

## 🧪 Testleri Çalıştırma

```bash
python manage.py test
```
