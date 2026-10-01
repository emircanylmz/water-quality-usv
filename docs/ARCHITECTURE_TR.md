# Mimari ve kod ayrımı

[English](ARCHITECTURE_EN.md) | [Ana README](../README.md)

Bu düzenleme, çalışan saha giriş noktalarını korurken donanımdan bağımsız mantığı küçük modüllere ayırır. `DualControl.py`, `xslx_logger.py`, `telemetry.py`, `keyboard.py` ve `xslx_to_kml.py` komutları aynı adlarla kalmıştır.

## Ayrılan sınıflar ve fonksiyonlar

| Parça | Yeni konum | Neden ayrı olmalı? |
| --- | --- | --- |
| `DualControlConfig`, `GroundStationConfig` | `usv_monitoring/config.py` | Port, baud, eşik ve dosya yollarını koddan ayırır; saha varsayılanlarını korur. |
| `SensorRecord` | `usv_monitoring/protocol.py` | Bir ölçümün tek ve açık veri sözleşmesidir. |
| `parse_measurement_line()` | `usv_monitoring/protocol.py` | Raporun `KEY=VALUE` ve eski `DATA,...` formatlarını tek yerde yönetir. |
| `select_control_mode()` | `usv_monitoring/control.py` | Histerezis davranışını seri donanım olmadan test eder. |
| `command_from_channels()` | `usv_monitoring/control.py` | RC kanal değerlerini hareket komutuna dönüştüren saf fonksiyondur. |
| `decode_sbus_frame()` ve `SBusFrame` | `usv_monitoring/sbus.py` | Bit çözümleme ile failsafe/frame-loss kararını ayırır. |
| `ExcelMeasurementStore` | `usv_monitoring/storage.py` | Eski kayıtları yükler, yeni kayıtları ekler ve atomik XLSX değişimi yapar. |
| `KeyboardCommandController` | `usv_monitoring/keyboard_control.py` | `pynput` yaşam döngüsünü logger ve yalnız-kontrol uygulamalarında tekrar kullanır. |
| `generate_kml_maps()` | `usv_monitoring/kml.py` | Renk, coğrafi kare ve XML üretimini komut satırı betiğinden ayırır. |
| `DualControlSystem` | `DualControl.py` | Donanım bağlantıları, iş parçacıkları ve sistem yaşam döngüsünün orkestratörüdür. |

Bu ayrımın sınırı bilinçlidir: beş ayrı çalıştırma betiği bir anda yeni bir framework'e dönüştürülmedi. Saha komutları ve varsayılanlar değişmeden, yalnız test edilmesi gereken karar mantığı ayrıldı.

## 1. Donanım mimarisi

```mermaid
flowchart LR
    subgraph Vehicle["İnsansız su aracı"]
        X8R["FrSky X8R"] --> LEVEL["SBUS tersleyici<br/>5 V - 3.3 V dönüştürücü"]
        LEVEL -->|"UART / SBUS"| RPI["Raspberry Pi 4"]

        PH["pH sensörü"] -->|"A0"| ARD["Arduino Mega 2560"]
        TURB["Bulanıklık sensörü"] -->|"A1"| ARD
        TEMP["DS18B20"] -->|"Depo taslağında D1"| ARD
        GPS["NEO-6M GPS<br/>rapordaki saha sürümü"] -.-> ARD

        RPI <-->|"USB seri / 9600"| ARD
        ARD --> MOTORIF["Motor arayüzü"]
        MOTORIF --> LEFT["Sol motor"]
        MOTORIF --> RIGHT["Sağ motor"]
        RPI <-->|"USB seri / 57600"| RADIO1["Araç telemetri modülü"]
        BAT["Li-Po batarya"] --> ARD
        BAT --> RPI
        BAT --> MOTORIF
    end

    RADIO1 <-->|"433/915 MHz"| RADIO2["Yer telemetri modülü"]
    RADIO2 <--> PC["Yer bilgisayarı"]
```

### Depodaki Arduino pinleri

| İşlev | Pin |
| --- | --- |
| pH analog giriş | `A0` |
| Bulanıklık analog giriş | `A1` |
| DS18B20 OneWire | `D1` |
| Motor A enable | `D9` |
| Motor B enable | `D3` |
| Motor A yön | `D7`, `D6` |
| Motor B yön | `D5`, `D4` |

**Doğrulanması gereken kritik nokta:** Arduino Mega'da `D1`, `Serial` TX0 işlevidir. Mevcut taslak hem `Serial` hem OneWire için `D1` kullanıyor. Çalışan saha düzeninde farklı seri port, farklı kart veya farklı sensör pini kullanılıyorsa kaynak kod ve kablolama birlikte güncellenmelidir. Bu düzenleme gerçek kablo bilgisi olmadan pini değiştirmedi.

Rapor SimonK ESC ve `Servo` kütüphanesini anlatırken depo taslağı `ENA/ENB` ve `IN1..IN4` pinleriyle bir motor sürücü arayüzü kullanıyor. `sketch_sep15a.ino` yüklenmeden önce hangi motor elektroniğinin bağlı olduğu kesinleştirilmelidir.

## 2. Yazılım dağıtımı

```mermaid
flowchart TB
    subgraph ArduinoLayer["Arduino katmanı"]
        Sketch["sketch_sep15a.ino"]
        SensorRead["Sensör örnekleme ve kalibrasyon"]
        MotorDrive["Motor komutları ve watchdog"]
        Sketch --> SensorRead
        Sketch --> MotorDrive
    end

    subgraph PiLayer["Raspberry Pi katmanı"]
        Dual["DualControlSystem"]
        SBus["decode_sbus_frame"]
        Decision["select_control_mode<br/>command_from_channels"]
        Dual --> SBus
        Dual --> Decision
    end

    subgraph GroundLayer["Yer bilgisayarı katmanı"]
        Logger["xslx_logger.py"]
        Protocol["parse_measurement_line"]
        Store["ExcelMeasurementStore"]
        Maps["generate_kml_maps"]
        Logger --> Protocol --> Store --> Maps
    end

    ArduinoLayer <-->|"komut ve sensör seri hattı"| PiLayer
    PiLayer <-->|"telemetri radyo hattı"| GroundLayer
```

## 3. Kontrol modu durum makinesi

```mermaid
stateDiagram-v2
    [*] --> COMPUTER
    COMPUTER --> RC: CH1 > RC eşiği
    RC --> COMPUTER: CH1 < bilgisayar eşiği
    COMPUTER --> COMPUTER: CH1 histerezis bandında
    RC --> RC: CH1 histerezis bandında
    COMPUTER --> COMPUTER: Telemetri komutunu Arduino'ya ilet
    RC --> RC: SBUS güncelse kanal komutu üret
    RC --> RC: SBUS kayıp/failsafe ise x gönder
    COMPUTER --> RC: Geçişte zorunlu x
    RC --> COMPUTER: Geçişte zorunlu x
```

`1300..1700` bandında önceki mod korunur. Geçişteki `x`, tekrar eden komut önbelleğinden bağımsız gönderilir.

## 4. Komut ve telemetri sıralaması

```mermaid
sequenceDiagram
    actor Operator as Operatör
    participant PC as Yer bilgisayarı
    participant Radio as Telemetri çifti
    participant Pi as Raspberry Pi
    participant Arduino
    participant Sensors as Sensörler ve GPS

    Operator->>PC: w/a/s/d tuşu
    PC->>Radio: Tek bayt hareket komutu
    Radio->>Pi: Komut
    alt Bilgisayar modu
        Pi->>Arduino: Komutu ilet
    else RC modu
        Pi-->>PC: Bilgisayar komutu yok sayılır
    end
    Arduino->>Sensors: Ölçüm al
    Sensors-->>Arduino: pH, bulanıklık, sıcaklık ve saha sürümünde GPS
    Arduino->>Pi: Telemetri satırı
    Pi->>Radio: Satırı ilet
    Radio->>PC: Telemetri satırı
    PC->>PC: Ayrıştır, uyarıları üret, XLSX'e atomik yaz
```

## 5. Arduino ana döngüsü ve güvenlik

```mermaid
flowchart TD
    START(["Başlat"]) --> INIT["Pinleri ve sensörleri başlat<br/>motorları durdur"]
    INIT --> LOOP{"Ana döngü"}
    LOOP --> RX{"Seri komut var mı?"}
    RX -->|Evet| DRAIN["Tampondaki tüm komutları işle"]
    RX -->|Hayır| WATCH
    DRAIN --> WATCH{"Aktif hareket komutu<br/>2 saniyeyi aştı mı?"}
    WATCH -->|Evet| STOP["Motorları durdur"]
    WATCH -->|Hayır| DUE
    STOP --> DUE{"1 saniyelik ölçüm zamanı geldi mi?"}
    DUE -->|Hayır| LOOP
    DUE -->|Evet| SAMPLE["pH örnekle<br/>bulanıklığı oku<br/>DS18B20 sıcaklığını iste"]
    SAMPLE --> SEND["Makine ve tanılama satırlarını gönder"]
    SEND --> LOOP
```

Watchdog, seri bağlantı kesildiğinde son hareketin sonsuza kadar sürmesini önler. DS18B20 sıcaklık isteği senkron çalışıyorsa ana döngüyü yüzlerce milisaniye engelleyebilir; gerçek durma gecikmesi saha testinde ölçülmelidir.

## 6. Yer istasyonu kayıt akışı

```mermaid
flowchart TD
    OPEN["Seri portu ve mevcut XLSX'i aç"] --> READ["Satır oku"]
    READ --> FORMAT{"Desteklenen paket mi?"}
    FORMAT -->|Hayır| READ
    FORMAT -->|Bozuk aday| WARN1["Format uyarısı ve satırı atla"] --> READ
    FORMAT -->|Evet| VALIDATE["Aralık uyarılarını hesapla"]
    VALIDATE --> APPEND["Mevcut ve yeni kayıtları birleştir"]
    APPEND --> TEMP["Geçici XLSX yaz"]
    TEMP --> REPLACE["Orijinali atomik olarak değiştir"]
    REPLACE --> READ
```

Aralık dışı pH gibi veriler bilimsel inceleme için korunur; sessizce sıfırlanmaz veya silinmez. Logger operatöre uyarı verir.

## 7. Haritalandırma akışı

```mermaid
flowchart LR
    XLSX["all_sensors.xlsx"] --> SCHEMA["temp/temperature şemasını normalize et"]
    SCHEMA --> FILTER["GPS ve ilgili sensör değeri eksik kayıtları filtrele"]
    FILTER --> PHKML["ph.kml"]
    FILTER --> TURBKML["turbidity.kml"]
    FILTER --> TEMPKML["temperature.kml"]
    PHKML --> EARTH["Google Earth veya KML görüntüleyici"]
    TURBKML --> EARTH
    TEMPKML --> EARTH
```

Kareler enleme göre boylam ölçeğini düzeltir. Varsayılan `--half-size-m 4`, merkezden her kenara yaklaşık 4 metre; tam kenar yaklaşık 8 metredir.

## 8. Sınıf ve modül ilişkileri

```mermaid
classDiagram
    class DualControlSystem {
        +detect_usb_ports()
        +connect_all()
        +parse_sbus_channels(data)
        +determine_control_mode()
        +calculate_rc_command()
        +send_to_arduino_safe(command, force)
        +start_system()
    }
    class DualControlConfig
    class GroundStationConfig
    class SBusFrame {
        +channels
        +frame_lost
        +failsafe
        +signal_ok
    }
    class SensorRecord {
        +time
        +lat
        +lon
        +ph
        +turbidity
        +status
        +temp
        +warnings()
    }
    class ExcelMeasurementStore {
        +append(record)
        +flush()
        +close()
    }
    class KeyboardCommandController {
        +on_press(key)
        +on_release(key)
        +run()
    }

    DualControlSystem --> DualControlConfig
    DualControlSystem --> SBusFrame
    GroundStationConfig --> ExcelMeasurementStore
    KeyboardCommandController --> DualControlSystem : komut hattı
    ExcelMeasurementStore --> SensorRecord
```

## Güvenlik değişmezleri

1. Her kontrol modu değişimi fiziksel hatta zorunlu `x` gönderir.
2. SBUS failsafe, frame-loss veya zaman aşımı RC hareketini `x` yapar.
3. Arduino iki saniye yeni hareket komutu almazsa motorları durdurur.
4. Başarısız kısmi bağlantıda açılmış seri portlar kapatılır.
5. USB portu yalnız okunabilir Arduino telemetri işareti bulunursa otomatik atanır.
6. Ham ölçüm doğrulama uyarıları veriyi sessizce değiştirmez.

Bu kurallar fiziksel acil durdurma, sigorta, uygun ESC arming süreci ve operatör gözetiminin yerine geçmez.
