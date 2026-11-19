# Güvenlik Kontrol Listesi

- `.env` ve SQLite veritabanı dosyaları repository dışında tutulmalıdır.
- Production JWT ve QR gizli anahtarları en az 32 karakterli rastgele değerlerden
  oluşturulmalıdır.
- OTP gerçek entegrasyonda kısa süreli ve deneme sayısı ile sınırlı tutulmalıdır.
- Ödeme bilgilerinde gerçek kart verisi saklanmamalıdır.
- QR imzası HMAC-SHA256 ile hesaplanmalı ve sunucu tarafında tekrar doğrulanmalıdır.
- Dükkân sahipliği kullanıcı rolü ve sipariş dükkânı üzerinden backend tarafında
  doğrulanmalıdır.
- Production dağıtımında HTTPS ve güvenli CORS kaynakları kullanılmalıdır.
