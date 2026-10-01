# Saha çalıştırma ve güvenlik rehberi

[English](OPERATIONS_EN.md) | [Ana README](../README.md)

Bu belge yazılım kullanımını açıklar; elektrik, batarya, teknecilik veya laboratuvar güvenliği eğitiminin yerine geçmez.

## İlk kurulumdan önce

- Pervaneleri sökün veya aracı güvenli bir test sehpasına sabitleyin.
- Fiziksel güç kesme anahtarının operatörün erişiminde olduğunu doğrulayın.
- Li-Po batarya, sigorta, ESC/motor sürücü akım sınırı ve kablo kesitini kontrol edin.
- Arduino modelini ve motor arayüzünü doğrulayın. Rapor ESC/Servo, depo taslağı yön/enable pinleri kullanıyor.
- Arduino Mega kullanılıyorsa `D1` üzerindeki DS18B20 ile `Serial` TX0 çakışmasını fiziksel kablo üzerinden kontrol edin.
- Raspberry Pi UART girişine doğrudan 5 V SBUS bağlamayın; rapordaki tersleyici ve seviye dönüştürücüyü doğrulayın.
- Kuru testte `w`, `a`, `s`, `d`, tuş bırakma ve güç/telemetri kesintisi davranışlarını deneyin.

## Seri hatlar

| Hat | Varsayılan port | Baud | İçerik |
| --- | --- | --- | --- |
| X8R - Raspberry Pi | `/dev/ttyAMA0` | 100000 | SBUS |
| Yer telemetri - Raspberry Pi | `/dev/ttyUSB0` | 57600 | Bilgisayar komutları ve sensör geri dönüşü |
| Arduino - Raspberry Pi | `/dev/ttyUSB1` | 9600 | Motor komutları ve sensör satırları |
| Yer bilgisayarı telemetri | `/dev/tty.usbserial-0001` | 57600 | Kontrol ve veri kaydı |

Varsayılan X8R seri biçimi, çalışan eski kodu korumak için `8N1` bırakılmıştır. Standart SBUS dönüştürücünüz `8E2` gerektiriyorsa:

```bash
export USV_X8R_PARITY=E
export USV_X8R_STOPBITS=2
```

Linux üzerinde değişken `/dev/ttyUSB*` adları yerine mümkünse `/dev/serial/by-id/...` yolunu kullanın.

## Önerilen başlatma sırası

1. Arduino ve motor gücü kapalıyken yer bilgisayarı ile telemetri portunu doğrulayın.
2. Raspberry Pi'de yapılandırmayı yükleyin.
3. `python -m raspberry.dual_control` komutunu çalıştırın.
4. Üç seri bağlantının doğru port adıyla açıldığını kontrol edin.
5. Yer bilgisayarında `python -m pc.xlsx_logger` komutunu çalıştırın.
6. Arduino gücünü verin; ilk telemetri satırını ve Excel satır sayısını doğrulayın.
7. Araç sabitken bilgisayar modu durdurma davranışını test edin.
8. RC moduna geçin; mod değişiminde motorların durduğunu doğrulayın.
9. RC alıcısını kapatın; en geç SBUS zaman aşımı ve Arduino watchdog süresi içinde motorların durduğunu doğrulayın.
10. Ancak bu kontrollerden sonra düşük güçte su testi yapın.

## Acil durumda

Öncelik sırası:

1. Klavye kontrolündeyseniz tuşu bırakın veya `x` gönderin.
2. RC kumandada güvenli/dur konumuna geçin.
3. Fiziksel motor gücünü kesin.
4. Yazılımı `Ctrl+C` ile durdurun.

Yazılım acil durdurması tek güvenlik katmanı olmamalıdır.

## Veri kaydı ve kalite kontrolü

Logger iki paket biçimini kabul eder:

```text
DATA,38.743804,35.468315,7.29,32,CLOUDY,19.87
LAT=38.743804,LON=35.468315,PH=7.29,TURB=32,STATUS=CLOUDY,TEMP=19.87
```

Her saha oturumundan önce:

- Bilinen pH tamponlarıyla kalibrasyon kaydı oluşturun.
- Bulanıklığın ham ADC mi yoksa NTU mu olduğunu oturum notunda belirtin.
- GPS fix durumunu doğrulayın.
- Saat, tarih ve saat dilimini doğrulayın.
- Sensörleri aynı noktada en az birkaç tekrar ölçümüyle kontrol edin.

Her saha oturumundan sonra:

- XLSX dosyasını salt okunur bir yedeğe kopyalayın.
- Negatif pH, DS18B20 hata değerleri (`-127`, bazı durumlarda `85`) ve koordinat sıçramalarını inceleyin.
- Paket sayısı, atlanan bozuk paketler ve çalışma süresini saha günlüğüne yazın.
- KML'i ayrı bir çıktı dizininde üretin.

```bash
python -m pc.xlsx_to_kml --input all_sensors.xlsx --output-dir maps/session-001
```

## Donanım bağlamadan test

```bash
python -m pytest
ruff check .
```

Otomatik testler telemetri ayrıştırma, kontrol modu, SBUS bayrakları, Excel devamlılığı ve KML XML/geometri davranışını kapsar. Gerçek seri zamanlaması, radyo menzili, motor durma süresi ve su üzerindeki davranış yine saha testi gerektirir.
