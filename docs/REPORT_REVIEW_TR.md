# Bitirme raporu incelemesi

[English](REPORT_REVIEW_EN.md) | [Ana README](../README.md)

İncelenen rapor: **Su Analizi Yapan İnsansız Su Aracı**, 40 PDF sayfası, Ocak 2026. PDF depoya kopyalanmamıştır; son sayfasında kişisel iletişim ve adres bilgileri vardır.

## Güçlü yönler

- Projenin çevresel izleme amacı, üç katmanlı mimarisi ve düşük maliyet hedefi anlaşılır.
- Arduino, Raspberry Pi ve yer bilgisayarı sorumlulukları kavramsal olarak ayrılmış.
- pH, bulanıklık, sıcaklık ve GPS verisinin aynı kayıt içinde ilişkilendirilmesi doğru bir sistem hedefi.
- RC ve bilgisayar kontrolünün birlikte sunulması pratik bir saha ihtiyacını karşılıyor.
- Donanım, mikrodenetleyici, Raspberry Pi ve yer bilgisayarı için ayrı diyagramlar bulunuyor.
- Rapor, veri setinin makine öğrenmesi için yetersiz kaldığını açıkça kabul ediyor.

## Rapor ile depodaki kod arasındaki kritik farklar

| Konu | Raporda | Depodaki kaynakta | Gereken işlem |
| --- | --- | --- | --- |
| GPS | NEO-6M ve `TinyGPSPlus`; Arduino GPS okuyor | `sketch_sep15a.ino` içinde GPS kodu yok | Çalışan saha firmware'ini ayrıca arşivle veya raporu mevcut taslağa göre düzelt. |
| Seri paket | `LAT=...,LON=...,PH=...,TURB=...,STATUS=...,TEMP=...` | Arduino `PH:...,CAL:...,TURB:...,TEMP:...`; eski logger `DATA,...` bekliyordu | Logger iki GPS'li biçimi de destekleyecek şekilde düzeltildi; GPS'siz taslak tam kayıt üretemez. |
| Motor elektroniği | SimonK 30A ESC, `Servo.writeMicroseconds()` | `ENA/ENB`, `IN1..IN4`, `digitalWrite/analogWrite` | Gerçek donanım varyantını belirle; yanlış firmware motor elektroniğine yüklenmemeli. |
| Sıcaklık pini | Şemada/pin açıklamasında net değil | OneWire `D1` | Mega TX0 çakışmasını kablo üzerinde doğrula. |
| Kayıt düzeni | pH, bulanıklık ve sıcaklık ayrı dosyalarda deniyor | Tek `all_sensors.xlsx` kullanılıyor | Raporu birleşik kayıt şemasına göre güncellemek daha tutarlı. |
| KML kütüphanesi | `simplekml` kullanıldığı yazıyor | XML elle üretiliyor | Rapor veya kod tek gerçeği anlatmalı; yeni modül standart XML API kullanıyor. |
| Harita geometrisi | Her ölçüm bir “nokta/yer işareti” | Renkli poligon/kare üretiliyor | Raporda poligon boyutu ve renk eşikleri açıklanmalı. |
| Baud | Algoritmada tek `9600` değeri | Arduino bağlantısı 9600, radyo/yer bağlantısı 57600 | İki ayrı seri hattı raporda tablo halinde ayır. |

## Bilimsel yöntem ve veri kalitesi sorunları

1. **Kalibrasyon tekrarlanabilir değil.** Kullanılan pH tamponlarının değerleri, sıcaklığı, kalibrasyon tarihi, eğim/ofset katsayıları ve referans cihaz belirtilmiyor.
2. **İki pH formülü var.** Depo taslağı hem `7 + ((2.5 - V) / 0.18)` hem `-5.70V + 21.34` hesaplıyor. Hangisinin rapor sonuçlarını ürettiği açıklanmalı.
3. **Bulanıklığın birimi yok.** Rapor ve Excel örneğinde `19`, `32`, `96` gibi değerler var; bunların ham ADC, yüzde veya NTU olduğu belirtilmiyor.
4. **CLEAR/CLOUDY/DIRTY sınıfları tanımsız.** Eşikler, birimler ve bilimsel dayanak verilmemiş.
5. **Testler yalnız nitel anlatılmış.** Referans ölçüm, örnek sayısı, ortalama hata, standart sapma, tekrar edilebilirlik ve güven aralığı tablosu yok.
6. **Negatif pH kayıtları açıklanmıyor.** Depodaki güncel örnek veride negatif pH değerleri bulunuyor; bu durum kalibrasyon/ADC besleme varsayımının doğrulanmasını gerektirir.
7. **Zaman senkronizasyonu belirtilmiyor.** Zaman damgasının Arduino, Raspberry Pi veya yer bilgisayarından geldiği ve saat dilimi açıklanmamış.
8. **GPS kalite ölçütü yok.** Uydu sayısı, HDOP, fix yaşı, koordinat doğruluğu ve fix kaybı davranışı kaydedilmiyor.
9. **İletişim performansı ölçülmemiş.** Paket kaybı, gecikme, menzil ve yeniden bağlantı süresi verilmemiş.
10. **Enerji bütçesi yok.** Batarya kapasitesi, ortalama/tepe akım ve tahmini çalışma süresi bulunmuyor.
11. **Su ve elektrik güvenliği eksik.** Su geçirmezlik, kablo geçişleri, korozyon, sigorta, fiziksel acil durdurma ve Li-Po güvenliği raporda ölçülebilir gereksinim olarak yer almıyor.
12. **Maliyet iddiası sayısallaştırılmamış.** Düşük maliyet vurgulanıyor ancak BOM ve toplam maliyet tablosu yok.

## Yazılım ve güvenlik iddiaları

- Rapor, mod değişiminde dur komutu gönderildiğini doğru biçimde hedefliyor; eski uygulamada komut önbelleği bu dur komutunu atlayabiliyordu. Yeni sürüm geçiş durdurmasını zorunlu yazar.
- Rapor, geçersiz komutun motorları durdurduğunu söylüyor; bu yalnız yeni bir bayt gelirse geçerlidir. Bağlantı tamamen kesildiğinde eski Arduino taslağı son hareketi sürdürüyordu. Watchdog eklendi.
- SBUS çözümünde failsafe ve frame-loss bayrakları raporda ve eski kodda değerlendirilmemiş. Yeni çözümleyici bu bayrakları işler.
- Eski logger her oturumun ilk ölçümünde önceki Excel kayıtlarını silebiliyordu. Yeni depo mevcut veriyi yükleyip atomik biçimde ekler.
- USB algılama koşulundaki `or True`, ilk USB cihazını Arduino sayıyordu. Yeni algılama tanınan telemetri işareti arar.

## Yazım ve görsel düzen sorunları

- İngilizce özet sayfasının başlığı hâlâ “BİTİRME ÖDEVİ BAŞLIĞI İNGİLİZCE”; gerçek İngilizce başlık yazılmalı.
- Birçok yerde kelimeler birleşmiş: örneğin “Buçalışma”, “gölvebenzeri” gibi dizgi hataları var.
- Kısaltmalar listesinde `GPS`, `IMU`, `PC`, `PWM`, `SBUS`, `UART` harfleri gereksiz boşluklarla ayrılmış.
- Algoritma 2.1 kutusu ile alt yazısı görsel olarak çok sıkışık/çakışmalı.
- Donanım “blok diyagramı” gerçekte ayrıntılı bir kablolama görseli; küçük etiketler basılı sayfada zor okunuyor. Ayrı blok diyagramı ve pin bağlantı tablosu daha iyi olur.
- Kod örnekleri PDF üretiminde harf aralıkları açılmış ve okunabilirlik azalmış.
- Şekil 2.1 seri ekran görüntüsü önemli bir protokol kanıtı; metinde paket grameri olarak ayrıca verilmeliydi.
- Kaynakların DOI, sayfa aralığı ve tam bibliyografik bilgileri doğrulanmalı.
- Özgeçmiş sayfasındaki telefon, e-posta ve açık adres herkese açık GitHub deposuna konmamalı.

## Rapor için önerilen ek tablolar

1. Tam BOM, birim fiyat ve toplam maliyet
2. Pin bağlantı tablosu ve elektriksel gerilim seviyeleri
3. Seri hat/protokol tablosu
4. Sensör modeli, birimi, aralığı, çözünürlüğü ve kalibrasyon katsayıları
5. Referans ölçüme karşı hata ve tekrar edilebilirlik sonuçları
6. Telemetri paket kaybı/gecikme/menzil sonuçları
7. Batarya akımı ve çalışma süresi
8. Saha koşulları, tarih, hava, su koşulu ve GPS kalite bilgileri
9. Bilinen sınırlamalar ve güvenlik riskleri

## Önerilen İngilizce başlık

**Unmanned Surface Vehicle for Water-Quality Analysis**

## Sonuç

Rapor projenin amacını ve genel mimarisini anlatıyor; ancak bilimsel doğrulama, güvenlik davranışı ve “hangi kaynak kod hangi saha donanımında çalıştı?” izlenebilirliği yetersiz. En önemli sonraki belge, çalışan Arduino/Raspberry Pi/yer bilgisayarı sürümlerini tek bir sürüm etiketi altında donduran bir saha sürüm kaydıdır.
