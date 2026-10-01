# Arduino firmware

## Türkçe

Arduino IDE ile `arduino/water_quality_usv/water_quality_usv.ino` dosyasını açın. Gerekli kütüphaneler `libraries.txt` içinde listelenmiştir.

Mevcut taslak şu pinleri kullanır:

| İşlev | Pin |
| --- | --- |
| pH | `A0` |
| Bulanıklık | `A1` |
| DS18B20 | `D1` |
| Motor enable | `D9`, `D3` |
| Motor yön | `D7`, `D6`, `D5`, `D4` |

Arduino Mega üzerinde `D1`, TX0 pinidir. Çalışan saha kablosunu doğrulamadan firmware yüklemeyin. Rapor ESC/Servo tabanlı farklı bir motor varyantı tarif ediyor olabilir.

## English

Open `arduino/water_quality_usv/water_quality_usv.ino` with Arduino IDE. Required libraries are listed in `libraries.txt`.

The sketch uses pH on `A0`, turbidity on `A1`, DS18B20 on `D1`, motor enables on `D9`/`D3`, and direction pins `D7`/`D6`/`D5`/`D4`.

`D1` is TX0 on an Arduino Mega. Do not flash the firmware before checking the proven field wiring. The report may describe a different ESC/Servo-based motor variant.
