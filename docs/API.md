# KahveCell API Dokümantasyonu

Aktif API sözleşmesi `http://localhost:8000/docs` adresindeki Swagger UI ve
`http://localhost:8000/openapi.json` adresindeki OpenAPI şemasıdır.

## Ortak Kurallar

- API yolu: `/api/v1`
- Başarılı kimlikli isteklerde header: `Authorization: Bearer <access_token>`
- JSON alanları Pydantic modelleri ile doğrulanır
- JWT tokenları oturum yönetimi için kullanılır
- Sipariş ve abonelik işlemleri aktif kullanıcı oturumu gerektirir

## Kimlik

| İşlem | Metot | Endpoint |
|---|---|---|
| Kayıt | POST | `/auth/register` |
| OTP isteme | POST | `/auth/request-otp` |
| OTP doğrulama | POST | `/auth/verify-otp` |
| Giriş | POST | `/auth/login` |
| Token yenileme | POST | `/auth/refresh` |
| Kullanıcı bilgisi | GET | `/auth/me` |
| Profil güncelleme | PATCH | `/auth/me` |

Simülasyon OTP değeri `1234` olarak sabitlenmiştir.

## Abonelik ve Ödeme

| İşlem | Metot | Endpoint |
|---|---|---|
| Paketler | GET | `/subscriptions/plans` |
| Aktif abonelik | GET | `/subscriptions/me` |
| Paket başlatma/değiştirme | POST/PATCH | `/subscriptions`, `/subscriptions/me` |
| İptal | DELETE | `/subscriptions/me` |
| Mock ödeme | POST | `/payments/process` |
| Ödeme geçmişi | GET | `/payments/history` |

Başarılı test kartı: `4242-4242-4242-4242`

Başarısız test kartı: `4000-0000-0000-0002`

## Dükkân ve Konum

| İşlem | Metot | Endpoint |
|---|---|---|
| Dükkânları listele | GET | `/shops` |
| Konum sıralaması | GET | `/shops?lat=X&lng=Y&radius=Z` |
| İsim/adres arama | GET | `/shops?search=anahtar` |
| Dükkân detay | GET | `/shops/{shop_id}` |
| Menü | GET | `/shops/{shop_id}/menu` |

## Sipariş

| İşlem | Metot | Endpoint |
|---|---|---|
| Sipariş oluştur | POST | `/orders` |
| Kullanıcı geçmişi | GET | `/orders/history` |
| Sipariş detayı | GET | `/orders/{order_id}` |
| Dükkân siparişleri | GET | `/orders/shop/pending` |
| Durum güncelle | PATCH | `/orders/{order_id}/status` |
| QR doğrulama | POST | `/orders/{order_id}/verify-qr` |
| Canlı durum akışı | GET | `/orders/{order_id}/stream?access_token=<token>` |
