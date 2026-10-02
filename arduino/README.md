# Arduino firmware

## Türkçe

Arduino IDE ile `arduino/water_quality_usv/water_quality_usv.ino` dosyasını açın. Gerekli `OneWire`, `DallasTemperature` ve `TinyGPSPlus` kütüphaneleri `libraries.txt` içinde listelenmiştir.

Mevcut taslak şu pinleri kullanır:

| İşlev | Pin |
| --- | --- |
| pH | `A0` |
| Bulanıklık | `A1` |
| DS18B20 | `D1` |
| NEO-6M GPS TX | `D19/RX1` (`Serial1`, 9600 baud) |
| Motor enable | `D9`, `D3` |
| Motor yön | `D7`, `D6`, `D5`, `D4` |

Arduino Mega üzerinde `D1`, TX0 pinidir. Çalışan saha kablosunu doğrulamadan firmware yüklemeyin. Rapor ESC/Servo tabanlı farklı bir motor varyantı tarif ediyor olabilir.

NEO-6M modülünün `TX` çıkışını Mega `D19/RX1` pinine ve GND hattını ortak GND'ye bağlayın. Firmware GPS'e komut göndermediği için `D18/TX1` bağlantısı gerekmez. Modülün besleme gerilimini kullandığınız NEO-6M kartının veri sayfasından doğrulayın; çıplak modül ile regülatörlü breakout kart aynı besleme sınırlarına sahip olmayabilir. GPS fix alınana kadar Arduino `GPS_NO_FIX`, fix sonrasında `LAT/LON/PH/TURB/STATUS/TEMP` paketini gönderir.

## English

Open `arduino/water_quality_usv/water_quality_usv.ino` with Arduino IDE. The required `OneWire`, `DallasTemperature`, and `TinyGPSPlus` libraries are listed in `libraries.txt`.

The sketch uses pH on `A0`, turbidity on `A1`, DS18B20 on `D1`, NEO-6M TX on `D19/RX1` (`Serial1` at 9600 baud), motor enables on `D9`/`D3`, and direction pins `D7`/`D6`/`D5`/`D4`.

`D1` is TX0 on an Arduino Mega. Do not flash the firmware before checking the proven field wiring. The report may describe a different ESC/Servo-based motor variant.

Connect NEO-6M `TX` to Mega `D19/RX1` and share GND. `D18/TX1` is unnecessary because the firmware does not configure the GPS. Verify the supply rating of the exact NEO-6M board; bare modules and regulated breakout boards do not necessarily accept the same input voltage. Arduino emits `GPS_NO_FIX` until a fix is available, then sends `LAT/LON/PH/TURB/STATUS/TEMP` packets.
