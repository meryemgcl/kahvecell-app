# KahveCell Mimari Kararlar

## Genel Mimari

KahveCell, FastAPI tabanlı REST backend ve React/Vite tabanlı istemciden oluşan
ayrı iki uygulama olarak tasarlanmıştır. SQLite ilişkisel veritabanı tek dosya
yaklaşımı ile yerel geliştirmeyi basitleştirir.

## Backend Katmanları

- **API/Controller:** İstek doğrulama, HTTP kodları ve endpoint orkestrasyonu
- **Schema:** Pydantic ile giriş ve çıkış sözleşmeleri
- **Service:** Abonelik, ödeme, sipariş ve güvenlik iş kuralları
- **Repository/DB:** SQLAlchemy model ve session yönetimi
- **Core:** JWT, OTP, HMAC QR ve SSE yardımcıları

## Frontend Katmanları

- **Pages:** Kullanıcı akışına ait ekranlar
- **Components:** Ortak kart, toast ve yükleme durumları
- **API:** Axios istemcisi ve yetkilendirme interceptor'ı
- **Store:** Oturum ve bildirim state'i

## Güvenlik ve Saklama

JWT access ve refresh tokenları istemci tarafında saklanır. OTP kaydı süre ve
deneme sayısı ile sınırlıdır. QR yükü HMAC-SHA256 imzasıyla doğrulanır.
Gizli anahtarlar üretim ortamında ortam değişkenlerinden sağlanmalıdır.

## Konum Hesaplama

Haversine formülü, enlem ve boylam farklarını dünya yüzeyi üzerinde yaklaşık
mesafeye dönüştürür. Sonuçlar kilometre cinsinden hesaplanır ve yakınlığa göre
sıralanır.

## Sipariş Durum Geçişleri

```text
PENDING -> ACCEPTED -> PREPARING -> READY -> DELIVERED
```

Her geçiş backend tarafından sıralı olarak kontrol edilir. `READY` durumundan
sonra sadece yetkili dükkân sahibi QR doğrulaması ile `DELIVERED` yapabilir.

## Gerçek Zamanlı Bildirim

Server-Sent Events, sipariş durumunu tek yönlü ve düşük gecikmeyle istemciye
iletir. Tarayıcı bağlantısı kesildiğinde EventSource otomatik yeniden bağlanma
denemesi yapabilir.
