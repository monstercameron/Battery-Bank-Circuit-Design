---
layout: default
title: Dev log
nav_order: 12
---

# Dev log

Newest entries first. Each entry records what changed, why, and what is still open. Datasheet-derived values cite the datasheet in `docs/datasheets/`.

---

## 2026-11-21 — Entry 11: review round 1, high-speed fixes
The high-speed reviewer found **3 critical, 11 major and 19 minor** issues (`hardware/review/round1_highspeed.md`), all checked against the generated netlist. It also decrypted the RC4-protected Realtek datasheets so their text can be searched (`hardware/tools/flatpdf.py`).

**Fixed**
- **H-1 (critical) — SPI flash data lines swapped.** RTL8372N `SPF_SDI`/`SPF_SDO` are named from the *flash's* side (`SPF_SDO` is a switch input). The switch could never have loaded its firmware.
- **H-2 (critical) — crystal strap wrong.** The `SEL_XTAL` pull-down selected a 50 MHz reference with a 25 MHz crystal fitted. Now left on its internal pull-up (25 MHz).
- **H-4 / H-5 — switch straps.**
  - `REG_IF_SEL` = 11 (slave MDC/MDIO, PHY ID 29) for the router's DSA driver.
  - `EN_PHY` = 1. Its default pull-down would have **disabled all four embedded 2.5G PHYs**.
- **H-6 — USB-C mux power.** The HD3SS3212 moved to always-on V3V3, with a 1k in series on SEL. Its control pin was being driven while its gated supply was off.
- **H-9 — RTL8221B straps.** CFG_OPT0/1 get explicit 4.7k pull-downs: no MDI swap, CLKOUT off.
- **H-13 — router interface.**
  - AC coupling in both SerDes directions.
  - Switch INT routed to the router.
  - I/O-reference pin, boot/recovery button, and 6 ground pins.
- **H-11 / H-12 — net classes.**
  - New `SERDES_100R` and `USB2_90R` classes; `RJ_TD*` added to `ETH_100R`.
  - Pair widths ≥ 0.15 mm (2 oz outer minimum), routed as inner stripline. Final geometry comes from JLCPCB's 6-layer impedance calculator.
- **Repo hygiene.**
  - Added `.gitignore` for build outputs, KiCad local state, vendor PDFs (copyright), extracted text, 3D models (157 MB) and caches.
  - The folder had been inside a Desktop-wide Git repository that saw 15,817 files from unrelated projects. It now has its **own repository** (`main`, no commits yet) that tracks 161 files / 5.2 MB.

**Architecture changes queued** (after the other three reviews land)
- **H-3 — board partition.** The switch moves onto the power board (A) beside the four NICs, so only 4 SerDes pairs (plus MDIO/reset/INT) cross to board B, on a differential-rated mezzanine. Board-to-board connector symbols will go into the schematic so each net has a board.
- **H-10 — 0.95 V supplies.** Realtek requires ≤ 15 mVpp ripple and forced-PWM above 1 MHz on the analog 0.95 V, which is impossible directly from 21 V. Plan: VBAT → 5 V intermediate, then fast point-of-load bucks.
  - Candidates in stock: TLV62585 (1.5 MHz, 3 A) and TPS62827A (2.2 MHz, 4 A, 4,546 in stock) per NIC.
  - The switch core needs ≥ 8.7 A for 3:1; that part is still to find.
- **H-7 — PHY-to-PHY coupling.** Capacitive 2.5GBASE-T coupling needs Realtek confirmation. Plan: add footprints for common-mode chokes (0 Ω fitted), with magnetics as the fallback.
- **H-8 — USB data role.** TPS26750 configuration: "Initiate Swap to UFP" = 1. NIC enumeration depends on the partner accepting DR_Swap; this is documented as a limitation.
- **H-14 — MAC addresses.** Unique MACs need a production eFUSE programming step.

---

## 2026-11-21 — Entry 10: battery cartridge PCB, review round 1 started
**Changed**
- **New cartridge project** (`python hardware/gen/build.py --project cartridge` → `hardware/kicad_cartridge/`): 60 parts, 0 checker errors.
  - BQ7791500 protector (4.20 V OV / 2.90 V UV).
  - 5 mΩ shunt: OCD1 = 60 mV → **12 A**, SCD = 120 mV → **24 A**. Both trip above the 8.3 A design current and below the 25 A cell rating.
  - 2 + 2 back-to-back NTMFS5C628NL discharge/charge FETs.
  - STS2250 fuse: 25 A, 72 V, 500 A interrupt.
  - BQ34Z100-G1 gauge, powered from a TLV70433 regulator off the pack. It keeps each pack's Qmax and cycle count.
  - XT60PW-F connector and five pogo landing pads.
- **Presence loop.** The cartridge's PRES pin is pulled to the pack voltage only through a loop the main board closes (pogo PRES_A–PRES_B shorted on the main board).
  - A cartridge that is out of the device sits in HIBERNATE with its FETs off, so a spare in a bag has dead contacts.
  - The main board's old CART_PRES_N logic input is removed; the loop carries pack voltage, so it can't drive a logic pin. Presence is detected through the gauge on I²C mux channel 7.
- **Review round 1 launched:**
  - Three Claude adversarial reviewers: power/safety, high-speed/networking, control/radios/DFM.
  - **Plus an independent Codex `gpt-6.2-astra` reviewer**, run read-only through the Codex CLI at the user's request. Reports land in `hardware/review/`.

---

## 2026-11-21 — Entry 9: full first-pass schematic, 0 checker errors
**Changed**
- **All 13 blocks written:**
  - USB-C port ×4
  - power input
  - PoE PD + isolated flyback
  - battery interface
  - aux rails
  - Ethernet switch + PHY + router connector
  - MCU (ESP32 + mux + expander + RTC + NFC + microSD + fan)
  - LoRa
  - audio
  - lighting
  - DC out
  - USB-A
  - Qi
- **Size:** 16 sheets, 1,114 parts, 159 BOM lines (957 placements).
- **Fixes from the checker:**
  - **DC input over-voltage cutoff lowered from 26.1 V to 24.3 V.** That's the jack's own rating, and it lets 50 V MLCCs meet the 2× rule. Divider 178k / 14.3k / 10k.
  - **Logic-level pins** (BQ25756 REGN/TS/ICHG, eFuse dVdT/ILIM, Qi VCC, router SerDes) no longer inherit their power rail's voltage.
  - **PoE primary side** is referenced to its own isolated return (POE_RTN). The primary FET's drain stress is set by an RCD clamp to ≤ 125 V, so the 200 V FET meets 1.5×.
  - **USB-A output caps** moved to 50 V parts: QC up to 12.6 V needs ≥ 25.2 V.
  - **LED board harness** is now a JST PH 6-pin (C131342): 2 A contacts for 0.5 A, 4:1.
- **Documented 3:1 exceptions:**
  - USB-C 5 A contacts
  - USB-A 2 A connector
  - 802.3bt per-pair current
  - TPS2373 internal hot-swap FET
- **Checker update:** listed exceptions are recorded instead of failing the build.
- **Build:** missing passives are now collected in one pass instead of stopping the build.

**Status**
- Design check: **0 errors**, 3 warnings (consigned parts with no LCSC number: RJ45 PoE MagJack, router module, PoE transformer).
- KiCad ERC: 21 warnings, all library-copy mismatches on 2-pin EasyEDA inductor/jack symbols (cosmetic, still investigating).

**Open (VERIFY items in the code)**
- PoE flyback compensation, turns ratio and snubber values.
- IP6826 crystal frequency and demodulation network.
- IP6525S enable pin behaviour.
- TPS56A37 FB/MODE.
- RTL8156BG RSET.
- Router module pinout.
- Cartridge PCB (separate project).

---

## 2026-11-21 — Entry 8: mechanical spec, custom site, 3D model
**Changed**
- **Mechanical spec.** Added `hardware/mechanical/mech_spec.json`, the single source of truth for mechanics:
  - Enclosure: 150 × 94 × 70 mm, extruded aluminium with PC/ABS end caps.
  - Battery cartridge: 112 × 82 × 25 mm, 5 × 21700, slides in from the right end.
  - Two stacked 124 × 86 mm 6-layer boards: power (A) at z = 28 and logic/network (B) at z = 48, joined by a 2×20 1.27 mm stacking header.
  - An aluminium-core LED board facing out of the left cap.
  - Every connector's edge position.
  - The PCB layout and the website's 3D model both read this file, so they stay aligned.
- **Why two boards.** Six 100 W-class power stages with 17 × 17 mm inductors fill most of one 124 × 86 mm board. Networking, the router module, radios and logic move to a second board above it.
- **Website.**
  - The landing page is being redone as a custom HTML page (`docs/index.html`). The old markdown index moves to `overview.md`.
  - An interactive three.js model (`docs/assets/device3d.js`, `docs/device3d.html`) is built from the spec.
- **Power input block** (`blocks/power_input.py`):
  - DC jack path: TVS → TPS26631 eFuse with a back-to-back blocking FET (OV 26.1 V / UV 9.95 V, I_LIM 11k = 1.65 A) → LM74700 ideal diode → VIN_AUX.
  - PoE path: VPOE → LM74700 → VIN_AUX.
  - VIN_AUX feeds a forward-only BQ25756 stage: ICHG 3.33 A, ILIM 2.67 A.

**Open**
- The router module form factor (edge-card vs castellated) affects the logic board's height. Revisit after the vendor confirms its 2.5G link.

---

## 2026-11-21 — Entry 7: schematic pipeline online, USB-C port sheets generated
**Changed**
- **Schematic generator.**
  - Added the generator in `hardware/gen/`:
    - `sexp.py`: KiCad S-expression reader/writer.
    - `symlib.py`: loads LCSC symbols and their pins.
    - `generics.py`: R/C/L/D/FET/test-point symbols.
    - `kicad_writer.py`: hierarchical schematic, one global label per pin.
    - `bb.py`: design helpers that attach JLCPCB numbers and ratings.
    - `build.py`: build entry point.
  - First block: `blocks/usbc_port.py`, instantiated ×4. It produced 494 parts and 51 BOM lines.
- **Design checker.** Added `hardware/checks/check.py`. It covers voltage derating, the 3:1 current/power rule, open pins, single-pin nets and missing LCSC numbers.
- **KiCad project.**
  - `hardware/kicad/battery-bank.kicad_pro` holds JLCPCB design rules plus net classes: Power_10A, Power_3A, USB3_90R, ETH_100R.
  - Project library tables point at `hardware/lib/lcsc.*` and `hardware/lib/bb.kicad_sym`.
  - Installed KiCad 10.0.8's default global library tables on first run.
- **KiCad ERC.**
  - The first run showed 1,872 violations. 844 were "unspecified pin type" warnings from EasyEDA symbols, fixed by marking LCSC pins `passive`. 988 were missing library tables, fixed by adding the project file and tables.
  - Now 48 remain: 40 labels whose other end is on a sheet not written yet, and 8 inductor library-copy mismatches (still investigating).
- **Build outputs.** Every build now writes `hardware/kicad/erc.rpt`, `design_check.txt`, `bom_jlcpcb.csv` and `battery-bank-schematic.pdf`.

**Datasheet-driven corrections found while wiring the port**
- **TPS26750 config EEPROM.** It must be **≥ 36 KB** (TPS26750 datasheet §7.3.9.2). The planned 24C256 (32 KB) is too small. Switched to **ST M24512-RMN6TP** (64 KB, JLCPCB C79991, 150 k in stock).
- **TPS26750 VBUS pin.** It is rated 4–22 V, so it reads VBUS through the TPD4S480's VBUS_LV divider for 28 V EPR.
- **TPS26750 I²C straps.** The four ports use the SafeMode straps from Table 7-6:
  - #1 = ADCIN1 LDO_3V3, ADCIN2 GND → 0x20
  - #2 = GND, GND → 0x21
  - #3 = 0.806 divider (24k/100k), GND → 0x22
  - #4 = LDO_1V5, LDO_3V3 → 0x23
- **BQ25756 programming values:**
  - VFB is 1.536 V. R_TOP 249k / R_BOT 20k gives 20.66 V (4.13 V/cell, gentle on the cells).
  - K_ICHG and K_ILIM are 50 A·kΩ (ILIM is specified at 2 mΩ, so 20 A·kΩ with our 5 mΩ sense).
  - ICHG 7.5k gives a 6.7 A stage-output ceiling. ILIM 4.02k gives a 4.97 A input ceiling.
  - TS uses RT1 5.23k / RT2 30.1k with a 10k NTC at the connector.
  - R_FSW 80.6k gives ≈ 347 kHz.
- **NIC core buck (TPS62933).** Minimum on-time is 70 ns, so 21 V → 0.95 V can't run at the default 500 kHz. Set RT = 71.5k (310 kHz).
- **TPD4S480.** The VBIAS capacitor must be rated ≥ 63 V (100 V used). Its SBU channels protect the USB2 D+/D− lines (datasheet pin note).
- **TPS2373 (PoE).** Class 6 = RCLSA 63.4 Ω (class 4 for events 1–2) + RCLSB 249 Ω (class 1). Also DEN 24.9k and REF 49.9k.
- **Ethernet-switch 0.95 V core.** It needs a 3:1-sized converter, so added **TPS56A37** (10 A, 4.5–28 V in, C22392669) for the switch and PHY cores.

**Open**
- Remaining blocks to write: power input, PoE, battery, aux rails, Ethernet/router, MCU, LoRa, audio, lighting, DC out, USB-A, Qi.
- The 8 inductor library-mismatch warnings.
- RTL8156BG RSET value: 2.49k assumed, still to verify.

---

## 2026-11-21 — Entry 6: 3:1 rule clarified (current/power, not voltage)
**Changed**
- **3:1 scope.** Per the user, the 3:1 buffer applies to **current, power and thermal capacity**, not voltage. Voltage uses standard derating: MLCC ≥ 2×, FET/diode ≥ 1.5×, resistors within the package working voltage. Rewrote `docs/design-rules.md` §1.
- **Consequences:**
  - USB-C ports capped at **100 W each**, with 28 V EPR at 3.57 A. The stage inductor is 22 A-rated against 7 A RMS.
  - Qi pad limited to 5 W, flashlight to about 1.5 W, speaker to about 1 W average, USB-A to 1.5 A.
  - DC jack in/out limited to 40 W (5 A jack ÷ 3).
  - Battery-only budget is 125 W (25 A cell ÷ 3 × 15 V).
- **Supply rails.** Split into separate converters so each runs at ≤ ⅓ of its rating:
  - 3V3 main, 3V3_ETH, 5V_PD, 5V_AUX, 12V_QI, 12V_RTR.
  - One 0.95 V buck per Ethernet NIC.
  - TPS56A37 for the switch core.
- **Part picker.** Re-ran it with the new voltage rule. Almost every passive is now a JLCPCB **Basic** part.

---

## 2026-11-21 — Entry 5: research consolidated into docs
**Changed**
- Added `docs/chip-metadata.md` (pin metadata for every IC), `docs/jlcpcb-rules.md` (rules from JLCPCB's capability pages), `docs/design-rules.md`, and `docs/power-budget.md` (the "everything on" profile).
- Downloaded 38 datasheets and app notes into `docs/datasheets/` (index in `INDEX.md`).
- Missing datasheets:
  - nRF52840 product specification: blocked with HTTP 403.
  - SX1262: no direct link found.
  - MAX98357A: download timed out.
  - Würth 750320237: blocked with HTTP 403.
  - USB-IF specifications: not downloaded because of their licence terms.
- Added tools in `hardware/tools/`:
  - `jlc.py`: JLCPCB parts-library search with a cache.
  - `pick_passives.py`: picks passives to the derating rules and prefers Basic parts.
  - `pdftxt.py` + `dsgrep.py`: datasheet text extraction and search.

**Research corrections**
- **RTL8372N** has its four 2.5GBASE-T PHYs integrated, so four RTL8221B PHYs were removed from the plan.
- **RTL8156BG** has no USB-C orientation mux (added an HD3SS3212 per port) and needs an external 0.95 V supply (up to 650 mA).
- **LM74502H** is reverse-polarity/OVP only, with no reverse-current blocking. ORing uses **LM74700** ideal-diode controllers instead.
- **BQ77915** variants -04 and -13 disable the current and temperature protections. Use -00 or -02.
- **BQ25756** I²C address is fixed at 0x6B, so a **TCA9548A** I²C mux gives each stage its own branch.
- **ESP32-WROOM-32UE** (U.FL antenna) replaces the 32E, because the metal case would detune its PCB antenna.
- **Microphone:** the MMICT390200012 is made by TDK InvenSense, and one distributor shows a last-time-buy date, so plan an alternate. ST25DV04K is not recommended for new designs, so NFC uses **NT3H2111**.
- **USB-A:** no stocked high-current USB-A receptacle exists, so VOOC was dropped.
- **PoE:** TPS23730 is out of stock at JLCPCB, so PoE uses TPS2373-4 + an LM5155 flyback, following TIDA-050023.

---

## 2026-11-21 — Entry 4: features locked
- **Features:**
  - Travel router: a real OpenWrt Wi-Fi 6 module.
  - 2.5G Ethernet on all four USB-C ports.
  - Meshtastic LoRa node, which phones reach over Bluetooth.
  - Swappable battery cartridge.
  - Alarm firmware and open firmware.
  - PoE input on the RJ45.
  - Port meter / cable tester, NFC, solar input, DC 12–24 V output, red night light + SOS + siren, Qi pad, microSD, tripod mount + lantern.
  - Slow-charge toggles, plus a physical SLOW switch.
- **Battery:** under 100 Wh so it flies without airline approval, giving a 5S1P Samsung 50S cartridge at 90 Wh.

## 2026-11-21 — Entry 3: cells and Ethernet
- **Cells:** compared on live retail price, capacity and current. EVE 50E has the best $/Wh. After the under-100 Wh cap, the Samsung 50S (25 A) was chosen for power headroom.
- **Ethernet:** 2.5G picked over 5G. The RTL8156BG is stocked and cheaper than the 1G chip; the RTL8157 isn't stocked and needs 10 Gbps routing.

## 2026-11-21 — Entry 2: requirements
- **Tools and manufacturing:** KiCad, JLCPCB build.
- **Ports and power:** latest USB PD (Revision 3.3, posted 2026-11-05); pass-through; 4 × USB-C + 1 × USB-A.
- **Phones:** OnePlus support (PPS; VOOC was explored).
- **Extras:** flashlight + attention glow, fan + metal heat sinking, Wi-Fi + Bluetooth/IP speakerphone.

## 2026-11-21 — Entry 1: project created
- Created the project folder and `plan.md`.
