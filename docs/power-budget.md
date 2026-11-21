# Power budget: everything on at once

## Sources
| Source | Max power available | Limited by |
|---|---|---|
| Battery cartridge, 5S1P Samsung 50S, 90 Wh | **125 W** guaranteed (8.3 A × 15 V at empty), ~175 W when full | 3:1 on the cell's 25 A rating, so 8.0 A firmware limit |
| USB-C input (any of C1–C4, through that port's BQ25756 in forward mode) | up to **100 W** per port (20 V × 5 A, or 28 V EPR × 3.57 A) | per-port 100 W cap (3:1 on the stage inductor/FETs) |
| PoE input (802.3bt Type 3, Class 6) | **51 W** at the PD, about 46 W after the isolated converter | IEEE 802.3bt class |
| DC barrel input (12–24 V) | **40 W** at 24 V (1.67 A) | 3:1 on the 5 A jack |

Several inputs can be connected at once:
- **USB-C:** each USB-C port has its own bidirectional stage, so a charger on any USB-C port charges the bank directly.
- **PoE and the DC jack** share one forward-only charger stage through ideal-diode ORing. The higher-voltage source wins; firmware can force a choice.
- **Pass-through:** all stages share the battery node, so input power serves the loads first and the surplus charges the pack.

## "Everything on" profile, battery only (must fit in 125 W)
| Load | Allocation | Notes |
|---|---|---|
| USB-C C1–C4 | 4 × 18 W = 72 W | e.g., 9 V/2 A or PPS; firmware power allocator re-advertises PDOs |
| USB-A | 7.5 W | 5 V / 1.5 A (connector exception + 3:1 on IP6525S) |
| DC output | 12 W | 12 V / 1 A (jack 3:1 limit 1.67 A) |
| Qi pad | 5 W out ≈ 7 W in | 3:1 on the 15 W IP6826 |
| Router module (MT7981 + Wi-Fi 6) | 8 W | Acelink SM81 typical |
| Ethernet: 4 × RTL8156BG + RTL8372N + RTL8221B | 7 W | ~0.65 W per NIC, 3.3 W switch, ~1 W PHY |
| ESP32 + LoRa node + RTC + NFC + gauge + logic | 2 W | radio peaks are averaged |
| Audio | 1 W average | 3:1 on MAX98357A's 3.2 W |
| Flashlight | 1.5 W | 3:1 on AL8860's 1.5 A (0.5 A drive) |
| Glow LEDs (8 × SK6812) + fan | 2 W | |
| **Subtotal (loads)** | **118 W** | |
| Conversion losses (~6% average across stages) | ~7 W | |
| **Total from battery** | **~125 W ≤ 125 W ✓ (at the limit)** | runtime ~40 min from 90 Wh at this load |

Every per-block number above is that block's **3:1-derated** maximum, not a share of a larger part. "Everything on" therefore keeps every part at or below ⅓ of its current/power rating.

## With pass-through
| Input present | Extra power | What it unlocks |
|---|---|---|
| USB-C 100 W charger (any port) | +100 W | Other USB-C ports up to 60 W each (or one at 100 W) while still charging; two chargers on two ports add up |
| PoE 51 W | +46 W | Run router + Ethernet + phones on PoE indefinitely (desk / van) |
| DC jack 40 W | +40 W | Solar top-up while everything runs |

## Firmware power allocator (required)
- **Hard ceiling:** battery discharge current ≤ 8.0 A, enforced by firmware and backed by the BQ77915 OCD in hardware (set above 8.3 A, below the cell rating).
- **Priority order when over budget:**
  1. Safety and thermal limits.
  2. USB-C ports (fair share).
  3. USB-A.
  4. DC out.
  5. Router + Ethernet.
  6. Qi.
  7. Audio volume.
  8. Lighting.
  9. Charging.
- **When over budget:** lower the USB-C offers first, by re-advertising PDOs. Turn nothing off without a user-visible notice.

## Thermal at "everything on"
- **Internal dissipation:** about 7 W conversion losses + ~3 W Ethernet + router SoC heat, so roughly **12–15 W** inside the case.
- **Cooling:** fan on above 45 °C board temperature; the aluminum case is the heatsink.
- **Throttle points:**
  - Cells: above 50 °C (stays clear of the cell discharge limit).
  - Any FET or IC: above Tj(max) − 40 °C.
