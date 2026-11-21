---
layout: default
title: Features
nav_order: 3
---

# Features and derated limits

Limits follow the [3:1 policy](safety.html): current, power and thermal capacity are derated to one third. Full tables are in [design-rules.md](design-rules.html).

| Feature | Limit | Why |
|---|---|---|
| Battery cartridge | 5S1P Samsung 50S, 90 Wh; 8.0 A firmware limit (8.3 A max) | 3:1 on the cell's 25 A rating. Under 100 Wh flies without airline approval |
| Battery-only output | 125 W guaranteed | 8.3 A x 15 V at empty |
| USB-C ports (x4) | 100 W each; 28 V EPR at reduced current | Policy cap per port; USB-C contacts are 5 A, an exception to 3:1 |
| USB-A | 1.5 A (7.5 W at 5 V); QC up to 12 V | 2 A connector; VOOC dropped; OnePlus phones use PPS on USB-C |
| 2.5G Ethernet | All four USB-C ports plus RJ45 | RTL8156BG per port, RTL8372N switch, RTL8221B for the RJ45 |
| DC barrel jack in/out | 40 W at 24 V, 20 W at 12 V | 5 A jack derated to 1.67 A |
| DC 12-24 V output | Default off, explicit selection | Wrong voltage can damage gear |
| PoE input | 802.3bt Type 3, about 51 W | IEEE class; bt-rated magnetics |
| Solar | Via the DC barrel jack | Same 40 W jack limit |
| Qi pad | 5 W | 3:1 on the 15 W IP6826 |
| Speakerphone | About 1 W average speaker | 3:1 on the MAX98357A's 3.2 W |
| Flashlight | 0.5 A (about 1.5 W) | 3:1 on the AL8860's 1.5 A |
| Glow LEDs | 8 x SK6812MINI-E | Attention glow; needs a 5 V level shifter |
| Meshtastic LoRa | nRF52840 + SX1262, phones via Bluetooth | 22 dBm TX about 119 mA |
| NFC | NT3H2111 tap-to-pair | Field detect; I2C 0x55 on its own bus |
| Alarm / sunrise | Firmware, RTC-backed | RV-3028-C7 preferred |
| Cooling | Fan above 45 C board temperature; aluminum case | About 12-15 W dissipated inside at "everything on" |
| Slow-charge toggles | Firmware setting per port | Gentler charging |
| Open firmware | Hardware limits cannot be exceeded | ICHG / ILIM_HIZ resistors, BQ77915, eFuses |

Everything runs at once from the battery (125 W budget) or from pass-through input. The battery-only profile totals about 125 W; see [power-budget.md](power-budget.html).
