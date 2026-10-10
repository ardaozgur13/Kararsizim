# kararsızım — Proje Spesifikasyonu (Antigravity için)

> **Agent'a not:** Bu dosya projenin tek doğruluk kaynağıdır. Her aşamaya başlamadan önce bu dosyanın tamamını oku. Yalnızca benden istenen **aşamayı** yap, sonraki aşamalara kendiliğinden geçme. Bu bir **prototiptir**: basit tut, gereksiz karmaşıklık ekleme (Celery, Redis, DRF, React, Docker vb. YOK). Kod yorumları ve arayüz metinleri **Türkçe** olsun; değişken/fonksiyon/model isimleri **İngilizce** olsun.

---

## 1. Proje Özeti

**Ad:** kararsızım

**Amaç:** Kullanıcıların kararsız kaldıkları konularda (ör. "Bugün sinemaya mı gitsem, restorana mı?") 2 ila 5 seçenekli bir anket açıp diğer kullanıcılardan oy toplayabildiği basit bir topluluk platformu.

**Temel kurallar:**
- Takip (follow) mekanizması **yok**. Her kullanıcı platformdaki **tüm anketleri** görebilir ve oy verebilir.
- **Üye olmayan ziyaretçiler** anketleri görüntüleyebilir ve oy verebilir; ancak **anket oluşturamaz**.
- Anket oluşturmak için **giriş yapmış** olmak gerekir.
- Kayıt sırasında **e-posta, kullanıcı adı ve parola** istenir.
- Anketlerde **kullanıcı adı** görünür, **e-posta asla** görünmez (ne arayüzde ne de herhangi bir public çıktıda).
- Bir anketin **en az 2, en fazla 5** seçeneği olabilir.

---

## 2. Teknoloji Yığını

| Katman | Teknoloji |
|---|---|
| Backend | Python 3.11+, Django 5.x |
| Veritabanı | Supabase (PostgreSQL) — Django ORM ile bağlanılacak |
| Frontend | Django template'leri + saf HTML, CSS, JavaScript (aynı repo, ayrı framework YOK) |
| Deployment | Vercel (Python/WSGI serverless) |
| Statik dosyalar | WhiteNoise |
| Ortam değişkenleri | `python-decouple` veya `os.environ` |

**Önemli mimari kararlar:**
- Supabase'i yalnızca **yönetilen PostgreSQL** olarak kullan. Supabase Auth / Supabase JS client **kullanma**; kimlik doğrulama Django'nun kendi auth sistemiyle yapılacak.
- Bağlantı için Supabase'in **connection pooler** (transaction mode) adresini kullan. Vercel serverless olduğu için `CONN_MAX_AGE = 0` ve `DISABLE_SERVER_SIDE_CURSORS = True` ayarla.
- Oturumlar (session) **veritabanında** tutulacak (Django varsayılanı `django.contrib.sessions.backends.db`). Serverless ortamda dosya/bellek tabanlı session kullanma.
- Oy verme gibi anlık etkileşimler için sayfa yenilemeden çalışan **fetch (AJAX)** kullan, ama JS'e bağımlı kalmadan da çalışsın (progressive enhancement; form POST yedeği olsun).

---

## 3. Kullanıcı Rolleri

| Rol | Anket görme | Oy verme | Anket oluşturma | Kendi anketini silme |
|---|---|---|---|---|
| Ziyaretçi (üye değil) | ✅ | ✅ | ❌ | ❌ |
| Üye (giriş yapmış) | ✅ | ✅ | ✅ | ✅ |

---

## 4. Veri Modeli

Django'nun varsayılan `User` modelini **özelleştirmeden** kullan ama şu kuralları uygula:
- `username` zorunlu ve benzersiz (büyük/küçük harf duyarsız benzersizlik tercih edilir).
- `email` zorunlu ve benzersiz (form seviyesinde kontrol et).
- Kullanıcı adı: 3–20 karakter, harf/rakam/alt çizgi.

### `Poll`
| Alan | Tip | Not |
|---|---|---|
| `id` | AutoField | |
| `question` | CharField(200) | Zorunlu |
| `author` | FK → User (CASCADE) | |
| `created_at` | DateTimeField(auto_now_add) | |

### `Option`
| Alan | Tip | Not |
|---|---|---|
| `id` | AutoField | |
| `poll` | FK → Poll (CASCADE, related_name="options") | |
| `text` | CharField(100) | Zorunlu |
| `position` | PositiveSmallIntegerField | Sıralama için (0–4) |

### `Vote`
| Alan | Tip | Not |
|---|---|---|
| `id` | AutoField | |
| `poll` | FK → Poll (CASCADE) | |
| `option` | FK → Option (CASCADE) | |
| `user` | FK → User (null=True, blank=True) | Üyeyse dolu |
| `session_key` | CharField(40, null=True, blank=True) | Ziyaretçiyse dolu |
| `created_at` | DateTimeField(auto_now_add) | |

**Kısıtlar (constraints):**
- Bir üye bir ankete **en fazla 1 oy** verebilir: `UniqueConstraint(fields=["poll","user"], condition=Q(user__isnull=False))`
- Bir ziyaretçi (session) bir ankete **en fazla 1 oy** verebilir: `UniqueConstraint(fields=["poll","session_key"], condition=Q(session_key__isnull=False))`
- `Vote.option.poll == Vote.poll` olmalı (view/serializer seviyesinde doğrula).

**Doğrulama kuralları:**
- Bir anketin seçenek sayısı 2–5 arasında olmalı (hem backend'de hem frontend'de kontrol et; backend asıl otoritedir).
- Aynı ankette birebir aynı iki seçenek metni olmasın (boşluk/büyük-küçük harf farkı yok sayılarak).
- Seçenek ve soru metinlerinin başındaki/sonundaki boşluklar temizlensin; boş olamaz.

---

## 5. Oy Verme Mantığı

1. Her oy isteği `POST` ile gelir (CSRF korumalı).
2. Kullanıcı **giriş yapmışsa** `Vote.user` doldurulur.
3. Ziyaretçiyse Django session'ı kullanılır: session yoksa oluştur (`request.session.save()`), `Vote.session_key` olarak `request.session.session_key` kaydedilir.
4. Aynı kişi aynı ankete ikinci kez oy veremez → anlamlı bir Türkçe hata mesajı dön ("Bu ankete zaten oy verdin.").
5. **Oy değiştirme prototipte YOK** (sonraki aşamalarda eklenebilir).
6. Sonuçlar (yüzdeler ve toplam oy), kişi oy verdikten sonra gösterilir. Henüz oy vermemiş kişi "Sonuçları gör" bağlantısıyla oy vermeden de sonuçlara bakabilir.
7. Sonuç yüzdesi: `round(option_votes / total_votes * 100)`; toplam 0 ise tüm yüzdeler 0.

> **Bilinen kısıtlama (kabul edilmiş):** Ziyaretçi oyları tarayıcı oturumuna bağlıdır; çerezleri silen biri tekrar oy verebilir. Prototip için bu kabul edilebilir. Sonraki aşamada IP/rate-limit eklenebilir.
>
> **Ziyaretçi giriş yaptığında:** Önceden session ile verdiği oylar olduğu gibi kalır, hesaba taşınmaz (prototip basitliği).

---

## 6. Sayfalar ve URL'ler

| URL | Sayfa | Erişim |
|---|---|---|
| `/` | Anasayfa — anket akışı (en yeni üstte, sayfa başına 10, sayfalama) | Herkes |
| `/anket/<id>/` | Anket detay + oy verme + sonuçlar | Herkes |
| `/anket/yeni/` | Anket oluşturma formu | Sadece giriş yapmış |
| `/anket/<id>/sil/` | Anket silme (POST) | Sadece anket sahibi |
| `/anket/<id>/oy/` | Oy verme endpoint'i (POST, JSON + form destekli) | Herkes |
| `/kayit/` | Kayıt ol | Giriş yapmamış |
| `/giris/` | Giriş yap | Giriş yapmamış |
| `/cikis/` | Çıkış (POST) | Giriş yapmış |
| `/profilim/` | Kendi anketlerim listesi | Sadece giriş yapmış |

**Davranışlar:**
- Giriş yapmamış biri `/anket/yeni/` adresine giderse `/giris/?next=/anket/yeni/` adresine yönlendirilsin; giriş sonrası geri dönsün.
- Anasayfada ve navbar'da giriş yapmamışlara "Anket oluştur" yerine "Anket oluşturmak için giriş yap" yönlendirmesi gösterilsin.
- Anket kartında: soru, "@kullaniciadi tarafından", göreli/okunabilir tarih ("3 saat önce"), toplam oy sayısı.
- Anket oluşturma formunda: soru alanı + başlangıçta 2 seçenek alanı; JS ile "+ Seçenek ekle" (en fazla 5'e kadar) ve "–" ile kaldırma (en az 2). Sunucu tarafı doğrulama her zaman çalışsın.
- Hata ve başarı mesajları Django `messages` framework'ü ile gösterilsin.
- Özel 404 sayfası (tasarıma uygun).

---

## 7. Arayüz ve Tasarım Rehberi

**Duygu:** Soft, tatlış, güven veren, temiz, ferah. Aşırı süs yok.

**Renk paleti (CSS değişkenleri olarak `:root` içinde tanımla):**

```css
:root {
  --blue-900: #1E3A5F;   /* başlıklar, güçlü vurgu */
  --blue-600: #3B6EA8;   /* ana buton, linkler */
  --blue-400: #6FA0D8;   /* hover, ikincil vurgu */
  --blue-100: #E3EEF9;   /* açık mavi arka plan alanları, progress bar zemini */
  --cream-50:  #FFFDF7;  /* kartlar */
  --cream-100: #FBF6EA;  /* sayfa arka planı */
  --cream-200: #F2EAD3;  /* kenarlık, ayırıcı */
  --text:      #2B3440;  /* ana metin */
  --muted:     #6B7686;  /* ikincil metin */
  --success:   #4E9F7D;
  --danger:    #D96C6C;
}
```

**Stil kuralları:**
- Sayfa arka planı `--cream-100`, kartlar `--cream-50` + ince `--cream-200` kenarlık + yumuşak gölge.
- Köşeler yuvarlak (kartlarda `16px`, butonlarda `12px`).
- Ana butonlar `--blue-600` zemin, beyaz yazı; hover'da `--blue-400`.
- Sonuç çubukları (progress bar): zemin `--blue-100`, dolgu `--blue-600`; kullanıcının seçtiği seçenek ayrıca işaretlensin (✓ ve daha koyu ton).
- Font: Google Fonts'tan **Nunito** (yuvarlak, sıcak) — yedek olarak `system-ui, sans-serif`.
- Tamamen **responsive** (mobil öncelikli); kart akışı mobilde tek sütun, geniş ekranda ortalanmış `max-width: 720px` sütun.
- Erişilebilirlik: yeterli kontrast, `focus` görünür, butonlarda anlamlı `aria-label`.
- Küçük mikro animasyonlar (çubuk dolma geçişi `transition`) yeterli; ağır animasyon yok.
- Logo: metin tabanlı "kararsızım" yazısı (mavi), yanında küçük bir "?" / "⚖" benzeri basit ikon (emoji veya inline SVG).

**Boş durumlar:** Hiç anket yoksa dostça bir mesaj ("Henüz kimse kararsız kalmamış 🙂 İlk anketi sen aç!").

---

## 8. Proje Yapısı (önerilen)

```
kararsizim/
├── manage.py
├── requirements.txt
├── vercel.json
├── .env.example
├── .gitignore
├── README.md
├── config/                  # Django proje ayarları
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── accounts/                # kayıt/giriş/çıkış
│   ├── forms.py
│   ├── views.py
│   └── urls.py
├── polls/                   # anket, seçenek, oy
│   ├── models.py
│   ├── forms.py
│   ├── views.py
│   ├── urls.py
│   └── tests.py
├── templates/
│   ├── base.html
│   ├── 404.html
│   ├── accounts/ (register.html, login.html)
│   └── polls/ (home.html, detail.html, create.html, my_polls.html, _poll_card.html)
└── static/
    ├── css/style.css
    └── js/ (poll.js, create_poll.js)
```

---

## 9. Ortam Değişkenleri (`.env.example`)

```
DJANGO_SECRET_KEY=change-me
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,.vercel.app
DATABASE_URL=postgresql://USER:PASSWORD@HOST:6543/postgres
CSRF_TRUSTED_ORIGINS=https://*.vercel.app
```

- `DATABASE_URL` Supabase panelinden **Connection pooling (transaction mode)** adresi olarak alınır.
- Gerçek `.env` dosyası **asla** repoya eklenmesin (`.gitignore`).
- `DEBUG` production'da `False` olmalı.

---

## 10. Güvenlik (prototip için asgari)

- Django CSRF koruması her POST'ta aktif (fetch isteklerinde `X-CSRFToken` başlığı gönderilsin).
- Şablonlarda otomatik escape'i **bozma** (`|safe` kullanma) — XSS'e karşı.
- Parolalar Django'nun varsayılan hashleme sistemiyle saklanır; Django parola doğrulayıcıları açık kalsın.
- Hiçbir public yanıtta/şablonda kullanıcı e-postası gösterilmesin.
- Anket silme yalnızca sahibine açık; backend'de yetki kontrolü yap (sadece UI'da gizlemek yetmez).
- Secret'lar koda gömülmesin.

---

## 11. Aşamalı Geliştirme Planı

Her aşamayı **ayrı bir görev** olarak ver. Bir aşama bitip test edilmeden sonrakine geçme.

### ✅ Aşama 0 — Proje İskeleti ve Veritabanı Bağlantısı
**Prompt:**
> Bu dosyayı (KARARSIZIM_PROJE.md) baştan sona oku. **Sadece Aşama 0'ı** uygula: Django projesini `config` adıyla oluştur, `accounts` ve `polls` uygulamalarını ekle, `requirements.txt` hazırla (django, psycopg[binary], dj-database-url, whitenoise, python-decouple, gunicorn gerekmez). `settings.py`'yi bölüm 2 ve 9'a göre ayarla: DATABASE_URL ile Supabase PostgreSQL bağlantısı, `CONN_MAX_AGE=0`, `DISABLE_SERVER_SIDE_CURSORS=True`, WhiteNoise, Türkçe dil (`tr`) ve `Europe/Istanbul` saat dilimi, templates/static klasörleri, DB tabanlı session. `.env.example`, `.gitignore` ve kısa bir `README.md` oluştur. `base.html` iskeletini (navbar + footer + messages alanı) ve bölüm 7'deki CSS değişkenlerini içeren `style.css` temelini yaz. Yerelde `python manage.py runserver` çalışmalı ve boş bir anasayfa görünmeli. Migration'ları çalıştır ve Supabase'e bağlandığını doğrula.

**Kabul kriteri:** Sunucu açılıyor, anasayfa krem/mavi temayla boş şekilde görünüyor, `migrate` Supabase'e başarıyla uygulanıyor.

---

### ✅ Aşama 1 — Üyelik Sistemi (Kayıt / Giriş / Çıkış)
**Prompt:**
> **Sadece Aşama 1'i** uygula. `accounts` uygulamasında bölüm 4, 6 ve 10'a uygun kayıt (e-posta + kullanıcı adı + parola + parola tekrar), giriş ve çıkış sayfalarını yaz. E-posta ve kullanıcı adı benzersiz olmalı; kullanıcı adı 3–20 karakter, harf/rakam/alt çizgi. Hata mesajları Türkçe ve form altında net görünsün. Kayıttan sonra otomatik giriş yapılsın ve anasayfaya yönlendirilsin. Giriş sayfası `next` parametresini desteklesin. Navbar'da giriş yapmışsa `@kullaniciadi` + "Çıkış", yapmamışsa "Giriş yap" + "Kayıt ol" görünsün. Tasarım bölüm 7'ye uygun, mobil uyumlu olsun. Basit birkaç test yaz (kayıt, tekrar eden e-posta/kullanıcı adı, giriş, çıkış).

**Kabul kriteri:** Kayıt → otomatik giriş → çıkış → tekrar giriş akışı çalışıyor; e-posta hiçbir yerde görünmüyor.

---

### ✅ Aşama 2 — Anket Oluşturma ve Listeleme
**Prompt:**
> **Sadece Aşama 2'yi** uygula. `polls` uygulamasında `Poll` ve `Option` modellerini (bölüm 4) yaz, migration üret ve uygula. `/anket/yeni/` sayfasını yaz: giriş zorunlu, soru + 2–5 seçenek, backend'de tüm doğrulamalar (en az 2 / en fazla 5 seçenek, boşluk temizleme, tekrar eden seçenek engeli, uzunluk sınırları). `create_poll.js` ile "+ Seçenek ekle / kaldır" davranışı (min 2, max 5) ekle. Anasayfada anketleri en yeni üstte olacak şekilde 10'arlık sayfalama ile listele; her kart `_poll_card.html` partial'ı ile soru, "@kullaniciadi tarafından", okunabilir tarih ve seçenek metinlerini göstersin. `/anket/<id>/` detay sayfasını (şimdilik oy vermeden, sadece anketi gösteren) ve `/profilim/` sayfasını (kullanıcının kendi anketleri) ekle. Anket sahibi kendi anketini silebilsin (POST, yetki kontrollü). Boş durum mesajları ve özel 404 sayfası ekle. Testler yaz (oluşturma doğrulamaları, giriş zorunluluğu, silme yetkisi).

**Kabul kriteri:** Giriş yapmış kullanıcı anket açabiliyor; ziyaretçi açamıyor ama listeyi görebiliyor; yetkisiz silme engelleniyor.

---

### ✅ Aşama 3 — Oy Verme ve Sonuçlar
**Prompt:**
> **Sadece Aşama 3'ü** uygula. `Vote` modelini bölüm 4'teki kısıtlarla yaz, migration üret ve uygula. Bölüm 5'teki oy verme mantığını uygula: üyeler `user` ile, ziyaretçiler Django session anahtarı ile oy versin; aynı kişi aynı ankete ikinci kez oy veremesin (Türkçe hata mesajı). Oy endpoint'i hem JSON (fetch) hem klasik form POST ile çalışsın. `poll.js` ile oy verince sayfa yenilenmeden sonuçlar (yüzde çubukları + toplam oy) gösterilsin; kullanıcının seçtiği seçenek işaretlensin. Detay sayfasında oy vermemiş kişi "Sonuçları gör" ile oy vermeden sonuçlara bakabilsin. Anasayfa kartlarında toplam oy sayısı görünsün. Sonuç hesaplamasında N+1 sorgu olmasın (`annotate`/`Count` kullan). Testler yaz: üye oyu, ziyaretçi oyu, çift oy engeli, başka anketin seçeneğiyle oy verme engeli, yüzde hesabı (0 oy dahil).

**Kabul kriteri:** Hem giriş yapmış hem yapmamış kullanıcı oy verebiliyor; çift oy engelleniyor; sonuçlar anında güncelleniyor.

---

### ✅ Aşama 4 — Arayüz Cilası ve Kalite
**Prompt:**
> **Sadece Aşama 4'ü** uygula. Bölüm 7'deki tasarım rehberine göre tüm sayfaları gözden geçirip cilala: tutarlı boşluklar, hover/focus durumları, çubuk dolma animasyonu, mobil görünüm, Nunito fontu, erişilebilirlik (kontrast, aria-label, klavye ile gezinme). Mesajlar (başarı/hata) sade ve tatlı bir tonda olsun. Gereksiz CSS/JS'i temizle. README'yi yerel kurulum adımlarıyla güncelle. Yeni özellik ekleme.

**Kabul kriteri:** Mobil ve masaüstünde tutarlı, temiz, mavi-krem temalı arayüz.

---

### ✅ Aşama 5 — Vercel'e Deployment
**Prompt:**
> **Sadece Aşama 5'i** uygula. Projeyi Vercel'de çalışacak şekilde hazırla: `vercel.json` (Python runtime, tüm istekleri `config/wsgi.py` içindeki `app`/`application` nesnesine yönlendir), `config/wsgi.py`'de Vercel'in beklediği `app` değişkenini tanımla, WhiteNoise ile statik dosyaların sunulması (`collectstatic` build adımı), `ALLOWED_HOSTS` ve `CSRF_TRUSTED_ORIGINS` ayarlarını ortam değişkenlerinden oku, production'da `DEBUG=False` ve güvenli çerez ayarları (`SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`) uygula. Vercel panelinde girilmesi gereken ortam değişkenlerini ve adım adım deployment talimatını README'ye yaz. Supabase connection pooler (transaction mode) kullanıldığını doğrula. Deploy sonrası kontrol listesi hazırla (kayıt, giriş, anket açma, ziyaretçi oyu).

**Kabul kriteri:** Canlı Vercel adresinde tüm temel akışlar çalışıyor.

---

## 12. Prototipte KAPSAM DIŞI (sonraya bırakıldı)

Şunları **ekleme**, istenmedikçe konuşma bile:
- Takip / arkadaşlık sistemi
- Yorumlar, beğeniler, bildirimler
- Oy değiştirme / oyu geri çekme
- Anket süresi (bitiş tarihi), kategori/etiket, arama, filtreleme
- E-posta doğrulama, parola sıfırlama
- Sosyal medya ile giriş
- Admin dışı moderasyon, raporlama, spam koruması / rate limiting
- Çoklu dil desteği
- REST API / mobil uygulama

> Bu liste sonraki iterasyonlar için yol haritası olabilir: önce **parola sıfırlama + e-posta doğrulama**, sonra **anket bitiş süresi + kategori**, sonra **rate limiting**.

---

## 13. Genel Çalışma Kuralları (Agent için)

1. Her aşamanın sonunda: yapılanların kısa özetini, çalıştırılması gereken komutları ve test sonuçlarını raporla.
2. Emin olmadığın bir karar varsa varsayım yap, bu varsayımı özetinde açıkça belirt; küçük şeyler için durup sorma.
3. Mevcut çalışan kodu gereksiz yere yeniden yazma; değişiklikleri küçük ve odaklı tut.
4. Secret/anahtarları asla koda veya loglara yazma.
5. Her aşamada `python manage.py check` ve testler hatasız geçmeli.
6. Kod okunabilir ve basit olsun; prototip için fazla soyutlama yapma.
