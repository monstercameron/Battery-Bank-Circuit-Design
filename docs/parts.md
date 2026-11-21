---
layout: default
title: Parts
nav_order: 6
---

# Main parts

Snapshot from JLCPCB, single unit, 2026-11-21. Pin details and sources: [chip-metadata.md](chip-metadata.html). Datasheet PDFs: [datasheets/INDEX.md](datasheets/INDEX.html).

| Part | Function | JLCPCB | Stock / price |
|---|---|---|---|
| TI BQ25756 | Bidirectional buck-boost controller (one per USB-C port) | C19272232 | 5,684 / $5.11 |
| TI TPS26750 | USB PD 3.x EPR controller (one per port) | C42166327 | 66 / $3.38 (low stock) |
| TI TPS26750A | Newer variant | C54891596 | 74 / $3.57 |
| TI TPD4S480 | 48 V EPR CC/SBU protector | C43131250 | 2,377 / $1.72 |
| TI LM74502H | Reverse-polarity and OV protection (DC jack) | C5219202 | 7,076 / $1.59 |
| TI TPS2373-4 | PoE powered-device interface | C470963 | 3,425 / $4.65 |
| TI TPS62933 | 3 A aux buck | C3200405 | 12,869 / $0.47 |
| TI BQ34Z100-G1 | Fuel gauge | C91302 | 4,591 / $2.92 |
| TI BQ77915 | 3-5S battery protector | C2876946 (-00) | 460 |
| Realtek RTL8156BG | USB to 2.5GbE (one per port) | C41376388 | 2,784 / $3.24 |
| Realtek RTL8372N | 4x2.5G + 2x10G switch | C46546780 | 1,294 / $9.38 |
| Realtek RTL8221B | 2.5G PHY for the RJ45 | C5155988 | 3,140 / $2.61 |
| TI HD3SS3212 | USB-C SuperSpeed mux | C544517 | 2,798 / $1.74 |
| Espressif ESP32-WROOM-32UE | Control MCU, Bluetooth, Wi-Fi | C701344 | not listed in source |
| Ebyte E73-2G4M08S1CX | nRF52840 module | C2764963 | 713 / $6.37 |
| Ebyte E22-900M22S | SX1262 LoRa | C411293 | 1,293 / $7.36 |
| MAX98357A | I2S audio amp | C910544 | 24,129 / $1.25 |
| MMICT390200012 | PDM microphone | C3171752 | 6,049 / $1.56 |
| AL8860QMP-13 | LED driver | C2678649 | 6,082 / $0.84 |
| SK6812MINI-E | RGB LED | C5149201 | 157,421 / $0.08 |
| IP6826 | Qi transmitter | C2921390 | 277 / $1.03 |
| NT3H2111 | NFC tag | C710403 | 38,028 / $0.56 |

| ST M24512 | 64 KB I2C EEPROM, PD config (one per port; TPS26750 needs 36 KB or more) | see [chip-metadata](chip-metadata.html) | not looked up here |
| TI TPS56A37 | 10 A buck for the switch core rail | see [chip-metadata](chip-metadata.html) | not looked up here |
| TI TCA9548A | I2C mux (BQ25756s all use 0x6B) | see [chip-metadata](chip-metadata.html) | not looked up here |

Router module (not a JLCPCB-stocked part): Acelink SM81 (MT7981 + MT7976CN), about $39.
