# Ground computer / Yer bilgisayarı

## Türkçe

Bu klasör yer bilgisayarında çalışan uygulamaları içerir:

- `xlsx_logger.py`: telemetri okuma, klavye kontrolü ve Excel kaydı
- `telemetry.py`: yalnız klavye kontrolü
- `keyboard.py`: klavye kontrolü ve Arduino tanılama izleme
- `xlsx_to_kml.py`: Excel ölçümlerinden KML üretimi

```bash
python -m pip install -r pc/requirements.txt
python -m pc.xlsx_logger --port /dev/tty.usbserial-0001
python -m pc.xlsx_to_kml --input all_sensors.xlsx --output-dir maps
```

## English

This directory contains ground-computer applications:

- `xlsx_logger.py`: telemetry reading, keyboard control, and Excel logging
- `telemetry.py`: keyboard-only control
- `keyboard.py`: keyboard control with Arduino diagnostics
- `xlsx_to_kml.py`: KML generation from measurement workbooks

```bash
python -m pip install -r pc/requirements.txt
python -m pc.xlsx_logger --port /dev/tty.usbserial-0001
python -m pc.xlsx_to_kml --input all_sensors.xlsx --output-dir maps
```
