# Raspberry Pi

## Türkçe

Bu klasör araç üzerindeki Raspberry Pi çalışma zamanını içerir. `dual_control.py`; X8R/SBUS verisini okur, RC ve bilgisayar modu arasında seçim yapar, yer telemetri komutlarını Arduino'ya iletir ve Arduino sensör satırlarını yer istasyonuna geri gönderir.

```bash
python -m pip install -r raspberry/requirements.txt
python -m raspberry.dual_control
```

Port ve güvenlik eşikleri kökteki `.env.example` üzerinden yapılandırılır. Linux'ta mümkünse `/dev/serial/by-id/...` aygıt adları kullanılmalıdır.

## English

This directory contains the on-vehicle Raspberry Pi runtime. `dual_control.py` reads X8R/SBUS data, selects RC or computer control, forwards ground commands to Arduino, and returns Arduino sensor lines to the ground station.

```bash
python -m pip install -r raspberry/requirements.txt
python -m raspberry.dual_control
```

Configure ports and safety thresholds through the root `.env.example`. Prefer stable `/dev/serial/by-id/...` device paths on Linux.
