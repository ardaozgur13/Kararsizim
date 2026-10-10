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
- **Anlık Etkileşim:** `fetch` (AJAX) ile sayfa yenilenmeden canlı oy verme ve yumuşak çubuk animasyonlarıyla anlık sonuç görüntüleme (JS kapalıyken klasik form fallback desteği).
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

## 🚢 Vercel Deployment Kılavuzu

Proje, Vercel üzerinde Python Serverless WSGI çalışma zamanıyla sorunsuz çalışacak şekilde yapılandırılmıştır (`vercel.json`, `build_files.sh`, `config/wsgi.py`).

### 1. Supabase Veritabanını Hazırlama
1. [supabase.com](https://supabase.com) üzerinde yeni bir proje açın.
2. **Project Settings -> Database -> Connection string** sekmesine gidin.
3. **Connection Pooling** sekmesini seçin:
   - **Mode:** `Transaction` (Serverless için şarttır)
   - **Port:** `6543`
   - Bağlantı URI formatı: `postgresql://postgres.[PROJECT-REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres`
4. Canlı veritabanı tablolarını oluşturmak için yerel terminalinizde Supabase `DATABASE_URL` bilginizi `.env` dosyasına yazıp şu komutu bir kez çalıştırın:
   ```bash
   python manage.py migrate
   ```

### 2. Vercel'de Projeyi İçe Aktarma
1. [vercel.com](https://vercel.com) paneline giriş yapın ve **"Add New... -> Project"** seçeneğine tıklayın.
2. GitHub deponuzu (`ardaozgur13/Kararsizim`) seçip **Import** deyin.
3. **Framework Preset:** `Other` olarak bırakın.
4. **Root Directory:** `./` olarak seçin.

### 3. Vercel Ortam Değişkenleri (Environment Variables)
Vercel proje ayarlarında **Environment Variables** bölümüne aşağıdaki değişkenleri ekleyin:

| Değişken Adı | Değer / Açıklama |
|---|---|
| `DJANGO_SECRET_KEY` | Üretim için en az 50 karakterlik rastgele gizli anahtar |
| `DJANGO_DEBUG` | `False` |
| `DJANGO_ALLOWED_HOSTS` | `.vercel.app,127.0.0.1,localhost` |
| `DATABASE_URL` | Supabase Transaction Mode Pooler URL (`postgresql://...:6543/postgres`) |
| `CSRF_TRUSTED_ORIGINS` | `https://*.vercel.app` (veya özel alan adınız: `https://alanadiniz.com`) |

### 4. Deploy Etme
* **"Deploy"** butonuna tıklayın. Vercel `build_files.sh` betiğini çalıştıracak, statik dosyaları derleyecek (`collectstatic`) ve sitenizi yayına alacaktır.

---

## ✅ Deploy Sonrası Kontrol Listesi (Checklist)

Canlıya aldıktan sonra aşağıdaki akışları test edin:

- [ ] **Anasayfa:** Canlı Vercel URL'sinde sayfanın krem/mavi temayla hatasız açıldığını doğrulayın.
- [ ] **Kayıt Olma:** `/kayit/` sayfasına gidip yeni bir hesap oluşturun; otomatik giriş yapılıp anasayfaya yönlendirildiğinizi ve e-postanın hiçbir yerde görünmediğini kontrol edin.
- [ ] **Anket Oluşturma:** `/anket/yeni/` sayfasına gidin, dinamik butonla 3. bir seçenek ekleyip anketi yayınlayın.
- [ ] **Üye Oyu:** Kendi oluşturduğunuz veya başka bir ankete oy verin; sayfa yenilenmeden çubuk animasyonunun dolduğunu ve *"✓ Senin Oyun"* rozetini görün.
- [ ] **Ziyaretçi Oyu:** Gizli bir sekme açarak oturum açmadan aynı ankete oy verin; ziyaretçi oyunun sayıldığını ve sonuçların güncellendiğini doğrulayın.
- [ ] **Çift Oy Engeli:** Aynı sekmede tekrar oy vermeyi deneyin; *"Bu ankete zaten oy verdin."* uyarısını teyit edin.
- [ ] **Anket Silme:** Anket sahibi olarak oturum açıp anketi silmeyi test edin; başkasının anketinde silme butonunun çıkmadığını ve URL ile silinmeye çalışıldığında engellendiğini kontrol edin.

---

## 🧪 Testleri Çalıştırma

Projede üyelik akışı, form doğrulamaları, yetkilendirme, anket oluşturma, oy verme ve yüzde hesaplamalarını kapsayan **32 adet** birim/entegrasyon testi bulunmaktadır:

```bash
python manage.py test
```

Sistem kontrolü:
```bash
python manage.py check
```
