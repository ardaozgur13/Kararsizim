# kararsızım ⚖️

Kararsız kalınan konularda 2 ila 5 seçenekli mini anketler açıp diğer kullanıcılardan anlık fikir ve oy toplamayı sağlayan sade, tatlış ve ferah bir topluluk web uygulaması.

---

## 🚀 Teknoloji Yığını

- **Backend:** Python 3.12+, Django 5.x
- **Veritabanı:** Supabase (PostgreSQL) — Django ORM ile bağlantı (yerelde SQLite fallback)
- **Frontend:** Django Templates + Saf HTML5, Modern Vanilla CSS (`Nunito` fontu, yumuşak mikro animasyonlar) ve Vanilla JavaScript
- **Statik Dosyalar:** WhiteNoise
- **Deployment:** Vercel (Python/WSGI Serverless)

---

## 🌟 Temel Özellikler

- **Herkes Görüntüleyebilir ve Oy Verebilir:** Üye olanlar kendi kullanıcı hesaplarıyla, ziyaretçiler ise tarayıcı oturumlarıyla (session) oy kullanabilir.
- **Tek Oy İlkesi:** Hem üyeler hem ziyaretçiler için anket başına tek oy kısıtı (backend unique constraints ile güvence altında).
- **Anlık Etkileşim:** `fetch` (AJAX) ile sayfa yenilenmeden canlı oy verme ve yumuşak çubuk animasyonlarıyla anlık sonuç görüntüleme (JS kapalıyken form fallback desteği).
- **Gizlilik:** Kullanıcıların e-posta adresleri hiçbir public çıktıda veya şablonda yer almaz; yalnızca `@kullaniciadi` gösterilir.
- **Performans:** N+1 veritabanı sorgularını önleyen optimize ORM mimarisi (`select_related`, `prefetch_related`, `annotate`/`Count`).
- **Erişilebilirlik ve Mobil Uyumluluk:** Mobil öncelikli (mobile-first), klavye ile gezinilebilir, ekran okuyucu dostu (A11y) temiz krem/mavi tasarım.

---

## 🛠️ Yerel Kurulum ve Çalıştırma

### 1. Depoyu klonlayın ve klasöre girin
```bash
git clone https://github.com/ardaozgur13/Kararsizim.git
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
# Windows:
copy .env.example .env

# Linux / macOS:
cp .env.example .env
```
*(Eğer Supabase kullanıyorsanız `DATABASE_URL` değişkenine Supabase Connection Pooler adresinizi yazın. Boş bırakırsanız yerel `db.sqlite3` veritabanı otomatik olarak devreye girer.)*

### 5. Veritabanı tablolarını oluşturun (Migration)
```bash
python manage.py migrate
```

### 6. Geliştirme sunucusunu başlatın
```bash
python manage.py runserver
```
Tarayıcınızda [http://127.0.0.1:8000](http://127.0.0.1:8000) adresine giderek uygulamayı kullanmaya başlayabilirsiniz.

---

## 🧪 Testleri Çalıştırma

Projede üyelik akışı, form doğrulamaları, yetkilendirme, anket oluşturma, oy verme ve yüzde hesaplamalarını kapsayan 32 adet birim/entegrasyon testi bulunmaktadır:

```bash
python manage.py test
```

Sistem bütünlüğü kontrolü için:
```bash
python manage.py check
```
