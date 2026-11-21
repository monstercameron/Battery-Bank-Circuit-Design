# Review round 1: finding tracker

**Sources**
- [round1_power.md](round1_power.md): P-1 … P-49, 6 critical / 23 major / 20 minor
- [round1_highspeed.md](round1_highspeed.md): H-1 … H-33, 3 critical / 11 major / 19 minor
- [round1_control_dfm.md](round1_control_dfm.md): C-1 … C-46, 5 critical / 17 major / 24 minor
- [round1_codex.md](round1_codex.md): independent Codex `gpt-6.2-astra` review; still running when this tracker was started

**Status key**
- **FIXED:** in the generated design.
- **AGENT:** a repair agent is working on it (it owns that file).
- **OPEN:** needs an outside answer or a later stage.
- **ACCEPTED:** documented exception.

## Critical
| ID | Finding | Status | Where / how |
|---|---|---|---|
| H-1 | RTL8372N SPI flash data lines swapped | FIXED | `ethernet.py`: SPF_SDI→flash DI, SPF_SDO←flash DO (names are from the flash's side) |
| H-2 | SEL_XTAL pull-down selected 50 MHz with a 25 MHz crystal | FIXED | pull-down removed; internal pull-up = 25 MHz |
| H-3 / C-4 | Board split pushed 16 MDI pairs through a 40-pin header; no B2B connector in the schematic | FIXED | Switch moved to board A with the NICs. Generated `interconnect` sheet: 2×24 2.54 mm low-speed/power + G-S-S-G SerDes mezzanine (4 pairs). New checker rule: a net crossing boards must pass a B2B connector on each board. mech spec rev B |
| C-1 | TCA9555 internal pull-ups would switch every gated rail on at power-up | FIXED | TCA9535 (no pull-ups) ×2 |
| C-2 / P-1 | Always-on TPS62933 EN pins pulled to 21 V (6 V abs-max) | FIXED | EN left floating (datasheet allows it); new PIN_ABS_MAX checker would now flag it |
| C-3 | IP6525S inductor 6.8 µH vs 22 µH reference | FIXED | 22 µH / 6 A (SLO1365H220MTT) + 100 µF polymer + 2.2 Ω / 1 nF snubber |
| C-5 | TPS26631PWPR out of stock | FIXED | TPS26631RGER (VQFN, 292 in stock) |
| P-2 | No hardware VBUS switch or discharge; VBUS depended on firmware | AGENT | `usbc_port.py`, TI EPR architecture |
| P-3 / P-4 / P-5 | PoE: floating LM5155 UVLO; 0.2 Ω CS limits ~8 W; 100 V snubber diode at ~125 V | AGENT | `poe.py` |
| P-6 | Unidirectional TVS ahead of the reverse-polarity FET | AGENT | `power_input.py` (bidirectional TVS) |

## Major (summary)
| ID | Finding | Status |
|---|---|---|
| H-4 / H-5 | REG_IF_SEL defaulted to slave I²C; EN_PHY defaulted to disabling the 4 PHYs | FIXED (4.7k pull-ups) |
| H-6 | HD3SS3212 SEL driven while its gated VCC was off | FIXED (mux on always-on V3V3, 1k series) |
| H-7 | Capacitive PHY-to-PHY 2.5GBASE-T not documented by Realtek | OPEN: needs Realtek FAE confirmation; CM-choke DNP footprints and magnetics fallback planned for layout |
| H-8 | NIC only enumerates if the partner accepts DR_Swap | OPEN: TPS26750 EEPROM config ("Initiate Swap to UFP" = 1); documented limitation |
| H-9 | RTL8221B CFG_OPT floating | FIXED (4.7k pull-downs) |
| H-10 | 0.95 V analog rails need ≤ 15 mVpp and PWM > 1 MHz | FIXED: V5_ETH rail → TPS62933F FCCM at 1.2 MHz per NIC and PHY; switch core on TPS56A37 + ferrite filter (MODE strap VERIFY) |
| H-11 / H-12 | Missing SerDes/USB2/RJ net classes; pair widths below the 2 oz minimum | FIXED (new classes, ≥ 0.15 mm, inner stripline) |
| H-13 | Router interface under-specified | FIXED (caps both ways, SW_INT, VIO, boot/recovery, more GND); module choice still OPEN |
| H-14 | Four NICs need unique MACs | OPEN: production eFUSE step (docs/manufacturing) |
| C-6 / C-7 | No ADC pin for the LED NTC; mux reset not drivable | FIXED (IO36 → LED_NTC, IO2 → mux reset held low until firmware; SLOW + red LED moved to a 2nd expander) |
| C-8 | Expander level INT mixed with BQ25756 pulse INTs | FIXED (expander INTs on PD_INT_N) |
| C-9 / C-10 | Back-powering of gated LoRa/router/ETH domains | FIXED (1k series on the UART, pull-ups moved into their own domains) |
| C-11 | Glow data floating at boot / driving an unpowered strip | FIXED (pull-down + OE from the expander, default Hi-Z) |
| C-12 | Fan ground switching could back-feed GPIO39 | FIXED (high-side TPS22965) |
| C-13 / C-14 | IP6525S output cap/snubber; enable must be open-drain | FIXED |
| C-15 | IP6826 demod/FOD network incomplete | PARTIAL: 2.2 nF on VDET added; rest AGENT (`qi.py`) |
| C-16 | IP6826 needs a firmware burn | FIXED (pre-programmed via the LCSC/JLC service; DEBUG test point) |
| C-17 | No isolation link per block | AGENT (power files); remaining blocks at layout |
| C-18 | Tact-switch pin pairing unverified | FIXED: diagonal pads (1 & 4), correct whatever the internal pairing |
| C-19 / C-20 | Checker had no IC pin abs-max check and no stock check | FIXED: PIN_ABS_MAX table from the datasheets; `build.py --stock` |
| C-21 | TPS26750 stock (66 + 74) | ACCEPTED for prototypes (5 boards × 4 = 20); global sourcing for volume |
| C-22 | Speaker stock 2; blank off-board footprints | FIXED (speaker off the JLC BOM, fitted at final assembly) |
| P-7 … P-49 | Dead-battery paths, bulk capacitance, 0.1 % FB, 100 W EPR cap, eFuse OV nuisance, input ILIM vs sources, bus TVS clamp vs 32 V abs-max, main fuse, cartridge inrush, USB-A/Qi hardware limits, PoE converter gaps, safety timer, budget | AGENT (3 repair agents) |

Minor items are tracked in each review file. They get fixed alongside the major items in the same block, or in round 2.
