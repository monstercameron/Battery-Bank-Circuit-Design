# Chip pin metadata (high level)

Gathered 2026-11-21 by research agents from manufacturer pages, TI HTML datasheet viewers, and LCSC/JLCPCB listings. Pins are grouped by function, not listed in full; the full pinout comes from the LCSC/EasyEDA symbol pulled into `hardware/lib/`. "Not found" means no source confirmed it, so check the PDF in `docs/datasheets/`. Stock and price are JLCPCB, single unit, 2026-11-21.

---

## Power path

### TI TPS26750: USB PD 3.x EPR controller (one per USB-C port)
- **Part / stock:** JLCPCB C42166327 (TPS26750SRSMR, 66 pcs, $3.38) / C54891596 (TPS26750ASRSMR, 74 pcs, $3.57). **Low stock: 4 needed per board.**
- **Package:** VQFN-32 RSM, 4×4 mm + thermal pad.
- **Supplies:**
  - VIN_3V3: 3.0–3.6 V.
  - PP5V ×2: 4.9–5.5 V (internal 5 V/3 A source switch + VCONN supply).
  - VBUS ×2: **4–22 V**, so for 28 V EPR it gets its VBUS from the TPD4S480's VBUS_LV divider output.
  - VSYS: tie to GND.
  - LDO_3V3 out (value not found); LDO_1V5 (core only, no external load).
- **I²C:**
  - Target port I2Ct_SCL/SDA/IRQ: address 0x20–0x23, set by ADCIN1/ADCIN2 dividers. That's 4 addresses, one per port.
  - Controller port I2Cc_SCL/SDA/IRQ: needs pull-ups even if unused. It loads the config EEPROM at 0x50, one EEPROM per controller.
- **Control:**
  - ADCIN1/2: straps for the I²C address and dead-battery mode (AlwaysEnableSink / NegotiateHighVoltage / SafeMode; use SafeMode with an EEPROM).
  - 10 GPIOs: GPIO0–7, GPIO11; the IRQs can become GPIO10/12. GPIO4/5 can serve as BC1.2 D+/D−.
  - POWER_PATH_EN: a 9 V / 10 µA charge-pump output, not logic level.
- **Data role:** DR_Swap is supported (Port Control 0x29 bits 12–15; 4CC tasks SWUF/SWDF; Status 0x1A bit 6 = data role). Source + UFP at the same time isn't explicitly stated, so verify on the EVM.
- **Readback:**
  - Received Source Caps: register 0x30 (13 PDOs + EPR).
  - Partner Discover Identity: register 0x48.
  - Cable e-marker (SOP′) register: not found.
- **Newer TPS26750A exists** (SLVSJE4A / TRM SPMU378, 2026): check register differences.

### TI BQ25756: bidirectional 4-switch buck-boost controller (6 per board)
- **Part / stock:** JLCPCB C19272232 (BQ25756RRVR), 5,684 pcs, $5.11.
- **Package:** VQFN-36 RRV, 6×5 mm, pad = PGND.
- **Supplies:**
  - VAC (pin 32): 4.2–70 V operating, 85 V abs-max. Pin 33 is the bias input, with the ACUV/ACOV dividers referenced to it.
  - VBAT: 0–70 V.
  - DRV_SUP: 4–12 V gate-drive supply (tie to REGN or feed externally).
  - REGN LDO: 4.7 µF.
- **I²C:** SCL/SDA, address **0x6B (fixed)**. Several BQ25756s on one bus clash, so they need separate buses.
- **ADC:** 16-bit, reads IAC 0x2D, IBAT 0x2F, VAC 0x31, VBAT 0x33, TS 0x37, VFB 0x39. This gives a per-port power meter for free.
- **Control / status:**
  - INT (256 µs pulse), STAT1, STAT2, PG: open-drain, 10 kΩ pull-ups.
  - CE: active-low, must not float.
  - TS: NTC divider REGN–TS–GND, 103AT-2.
  - ICHG: R to GND sets the charge-current ceiling.
  - ILIM_HIZ: R to GND sets the input-current ceiling. I = 50 A·kΩ / R at 2 mΩ.
  - ACUV / ACOV: input window comparators.
  - FSW_SYNC: R to GND sets frequency, R = 1/(10·fsw·5 pF − 500 ns); 100 kΩ = 300 kHz, 80 kΩ = 350 kHz.
- **Hardware ceiling (confirmed):** the effective limit is the lower of the pin setting and the register, which suits open firmware. Whether the pins also cap reverse mode isn't confirmed.
- **Reverse (OTG):**
  - EN_REV is REG0x19 bit 0. It resets on watchdog timeout and on adapter plug-in.
  - VAC_REV: 3.3–65 V in 20 mV steps.
  - IAC_REV: 0.4–20 A.
- **Power pins:**
  - HIDRV1/LODRV1/BTST1/SW1 (buck leg), HIDRV2/LODRV2/BTST2/SW2 (boost leg).
  - ACP/ACN: input sense, 5 mΩ recommended for USB PD (20 A max range).
  - SRP/SRN: charge sense, fixed at 5 mΩ.
  - FB/FBG: charge-voltage divider.
- **External parts per stage:** 4 N-FETs + 1 inductor + 2 sense resistors. TI's examples use 6.8–10 µH; its 240 W EPR example runs at 450 kHz with 80 V FETs.

### TI TPD4S480: 48 V EPR CC/SBU protector (one per USB-C port)
- **Part / stock:** JLCPCB C43131250 (TPD4S480RUKR), 2,377 pcs, $1.72.
- **Package:** WQFN-20 RUK, 3×3 mm + pad.
- **Supplies:** VPWR 2.7–4.5 V; VBIAS 0.1 µF.
- **Signals:** EPR_EN in; FLT open-drain out.
- **Protected lines:**
  - Connector side C_CC1/2, C_SBU1/2.
  - System side CC1/2, SBU1/2.
  - CC/SBU withstand a 63 V DC short to VBUS.
- **VBUS sense:** VBUS (0–51 V) in → VBUS_LV out (divided in EPR mode) → TPS26750 VBUS. EPR_BLK_G drives an optional blocking FET. RPD_G1/2 are dead-battery straps.

### Inputs: protection and ORing
- **TI LM74502H** (C5219202, 7,076 pcs, $1.59):
  - **Reverse-polarity + OV protection only, no reverse-current blocking, so it is not an ORing part.** Used on the DC-jack input.
  - SOT-23-8 DDF. Pins: EN/UVLO, GND, VCAP, VS, GATE, OV, SRC.
- **ORing** uses true ideal-diode controllers: TI LM74700-Q1 (3.2–65 V) or LM5050-1 (5–75 V). Stock to confirm.

### PoE powered-device input
- **TI TPS2373-4** (C470963, 3,425 pcs, $4.65):
  - VQFN-20 5×5 mm, 8–57 V. Integrated 100 V hot-swap FET (0.1 Ω, 2.2 A); the family covers Type 3 (60 W) / Type 4 (90 W).
  - Pins: DEN, CLSA, CLSB, REF, APD, AMPS_CTL, MPS_DUTY, RTN×2, PG, VC_OUT, VC_IN, UVLO_SEL, TPH, TPL, BT.
  - Confirmed class-resistor values: RCLSA 63.4 Ω (Class 4), RCLSB 90.9 Ω (Class 3). Read Table 1 for Class 6.
- **TI TPS23730** (PD interface + active-clamp-forward controller, 51 W, VQFN-45): better fit, but **0 stock at JLCPCB** (C3189530).
- **Closest reference designs:**
  - TIDA-050023: TPS2373-3 + LM51551 flyback, 12 V / 51 W.
  - PMP23365: TPS23730 ACF, 24 V / 72 W, Würth 750320237 transformer.
- **Isolated converter:** TPS2373-4 + LM5155x-class flyback controller. Transformer: Würth WE-PoE++ family; design for about 20 V out, 51 W, 1500 V AC isolation.
- **RJ45:** no 2.5G + 802.3bt MagJack stocked at LCSC. Candidates: Daburn 56F-1803DGDZ2NL, YAGEO JXF0 (2.5G/5G, 90 W), Pulse JXK0-2500NL. Central Semicon CTRJPPS2R5GF (C7236648) is 802.3at only (720 mA).

### Battery cartridge
- **TI BQ77915** standalone 3–5S protector:
  - TSSOP-24. Pins: VC0–VC5, SRP/SRN, CHG/DSG low-side NFET drivers (~12 V), LD, TS/VTB, CCFG, OCDP, CTRC/CTRD, CBI/CBO/LPWR/PRES.
  - Protections: OV/UV/OCC/OCD1/OCD2/SCD/OT/UT and open-wire detection. Passive balancing up to 50 mA.
  - **Order -00 / -02 / -08 (4.2 V OV). Avoid -04 and -13: they disable the current and temperature protections.** Stock: BQ7791500PWR C2876946 (460), BQ7791502PWR C2865574 (163).
- **TI BQ34Z100-G1** fuel gauge:
  - C91302 (BQ34Z100PWR-G1), 4,591 pcs, $2.92. TSSOP-14.
  - REGIN 2.7–4.5 V (needs a pre-regulator from the pack); REG25 2.5 V LDO.
  - I²C at **0x55** (fixed) or HDQ.
  - Pins: BAT (divided to about 900 mV), VEN (divider switch), SRP/SRN (coulomb counter), TS, P1–P4.
  - Supports 3–65 V packs via a divider. Learned Qmax, Ra and cycle count live in data flash, so it doubles as the cartridge's "ID/stats chip".
  - Successor: BQ34Z100-R2 (C7220642).

### Aux rails
- **TI TPS62933** (C3200405, 12,869 pcs, $0.47):
  - 3.8–30 V in, 3 A, 0.8–22 V out, 200 kHz–2.2 MHz. SOT-583 DRL-8.
  - Pins: RT, EN, VIN, GND, SW, BST (100 nF), SS/PG, FB.
  - Variants: P/O have a PG output; F is forced continuous-conduction mode.
  - Run at about 500 kHz from the 21 V bus.

---

## Ethernet and router

### Realtek RTL8156BG-CG: USB 3.2 Gen 1 to 2.5GbE (one per USB-C port)
- **Part / stock:** C41376388, 2,784 pcs, $3.24.
- **Package:** QFN-56 6×6 mm, 0.35 mm pitch, EP = GND.
- **Supplies:**
  - 3.3 V: about 88–92 mA.
  - **0.95 V (0.92–0.98 V): 364 mA typ, 650 mA max each, external buck needed.** The BG version has no internal regulator; POW_EXT_SWR is the enable output for the external buck.
  - DVDD09_UPS: internal LDO output, decouple separately.
- **Interfaces:**
  - USB: SS TX±, SS RX±, D+/D−. **No Type-C orientation mux, so it needs an HD3SS3212.**
  - MDI: 4 pairs.
  - 25 MHz crystal; RSET.
- **Control:** LED0–3 (LED0/1 shared with EEPROM/SPI), GPIO1–4 + GPI (GPIO1/2 = I²C slave), LANWAKEB, DOCK_DET, CONFIG_SEQ.
- **MAC address:** OTP eFUSE, so no EEPROM is needed (programmed with Realtek's PG tool).

### Realtek RTL8372N-CG: 4×2.5G + 2×10G switch
- **Part / stock:** C46546780, 1,294 pcs, $9.38.
- **Package:** dual-row QFN-144, 11×11 mm, 0.5 / 0.65 mm pitch, EP about 5.9×6.6 mm.
- **PHYs: the four 2.5GBASE-T PHYs are integrated** (internal 100 Ω termination). The RTL8156BG MDI connects to it directly.
- **SerDes S0/S1:** USXGMII, 10G-R, HSGMII, 2500BASE-X, 1000BASE-X, SGMII, 100BASE-FX. 100 nF AC coupling; unused pins pulled low through 1 kΩ.
- **Supplies:** 0.95 V (DVDDL×21, AVDDL, SVDDL…) and 3.3 V; DVDDIO0 can be 3.3/2.5/1.8 V. Thermal design assumes 3.3 W. Hold nRESET low ≥10.5 ms after the rails settle.
- **Clock:** 25 MHz, ±50 ppm.
- **Interfaces:**
  - SPI-flash master (4 pins).
  - Slave management: SPI, I²C or MDIO via straps.
  - MDC0/MDIO0 and MDC1/MDIO1 masters (manage the RTL8221B).
  - 6 GPIO, UART0 on 2 of them.
  - LED pins; 11 straps on the LED pins.
- **Boot:** INI_MODE[1:0]. The default (internal pull-ups) is 11 = CPU boots from SPI flash, so fit SPI flash with SDK firmware, or let the router manage it.
- **OpenWrt:** out-of-tree drivers only.

### Realtek RTL8221B-VB-CG: 2.5G PHY for the RJ45
- **Part / stock:** C5155988, 3,140 pcs, $2.61.
- **Package:** QFN-48 6×6 mm.
- **Supplies:** 3.3 V and 0.95 V (external; POW_EXT_SWR enable). DVDD3318 sets the MDIO level.
- **Interfaces:**
  - SerDes: SGMII 1.25 Gbaud or HiSGMII/2500BASE-X 3.125 Gbaud, 0.1 µF AC caps.
  - MDIO/MDC Clause 22/45, 1.5 kΩ pull-up. The SerDes mode is set over MDIO (MMD30 0x697A).
- **Control:** PHYRSTB (≥10 ms), INTB, 3 LEDs = PHYAD straps, CFG_OPT0/1, RSET 2.49 kΩ.

### TI HD3SS3212: USB-C SuperSpeed 2:1 mux (one per USB-C port)
- **Part / stock:** C544517 (HD3SS3212IRKSR, 2,798, $1.74); C129320 (about $0.63).
- **Package / rating:** VQFN-20 4.5×2.5 mm, 3.3 V, 10 Gbps.
- **Pins:** A0±/A1± (to the NIC), B0±/B1± and C0±/C1± (to the connector), SEL (orientation, from the PD controller GPIO), OEn.

### Router module (OpenWrt, MT7981B)
- **Acelink SM81** (MT7981 + MT7976CN):
  - Castellated, 50×36 mm, 3.3 V, about 8 W typ / 11 W max.
  - 1 GB DDR4, 2 MB NOR + eMMC. GbE + HSGMII, USB3, UART, 3 IPEX.
  - $39. OpenWrt 23.05.
- **GainStrong Oolite MT7981B V1:** edge connector, 70×58 mm, 5 V or 12 V in, 1× HSGMII 2.5G.
- **Hi-Link HLK-RM65:** 60×90 mm, 3.3 V / 5 A.
- **To confirm:** 2.5G HSGMII to RTL8372N interop and the pinout, with the vendor.

---

## Controllers and radios

### Espressif ESP32-WROOM-32UE (U.FL antenna variant, for the metal case)
- **Part:** C701344 (ESP32-WROOM-32UE-N4). The 32E with PCB antenna is C701342.
- **Package:** 38 pins + EPAD. 3V3 3.0–3.6 V, needs a supply of at least 0.5 A (379 mA TX peak). EN must not float.
- **GPIO:**
  - 26 GPIO; GPIO34/35/36/39 are input-only.
  - GPIO6–11 are flash pins, not available.
  - Straps: GPIO0, 2, 12 (must be low at boot), 15, 5.
  - About 15 fully free bidirectional GPIOs remain.
- **Audio:** **mic on I2S0 (PDM RX)** and **amp on I2S1 (TX)**.
- **ADC:** use ADC1 only (ADC2 is unusable with Wi-Fi).

### Ebyte E73-2G4M08S1CX: nRF52840 module (Meshtastic node)
- **Part / stock:** C2764963, 713 pcs, $6.37.
- **Module:** 13×18 mm, 43 pads, IPEX antenna, +8 dBm.
- **Power pads:** GND 5/21/24, VCC 19, VDDH 23, DCCH 25, VBUS 27.
- **Debug and USB:** SWDIO 37, SWCLK 39, RESET 26, USB D−/D+ 29/31.
- **I/O:** XL1/XL2 pads 11/13 (32 kHz crystal); about 27 GPIO.

### Ebyte E22-900M22S: SX1262 LoRa, 850–930 MHz
- **Part / stock:** C411293, 1,293 pcs, $7.36.
- **Module:** 14×20 mm, 22 pads, TCXO.
- **Power:** VCC pad 9, 1.8–3.7 V. 22 dBm TX about 119 mA.
- **SPI:** MISO 16, MOSI 17, SCK 18, NSS 19.
- **Control:** BUSY 14, DIO1 13, DIO2 8.
- **RF switch:** RXEN 6 (MCU) and TXEN 7 (MCU or DIO2).
- **NRST:** listed as both pad 12 and pad 15, so verify against the PDF.
- **Antenna:** pad 21 (stamp) or IPEX.

---

## Audio, lighting, misc

| Part | JLCPCB | Key pins / facts |
|---|---|---|
| **MAX98357AETE+T** I²S amp | C910544 (24,129, $1.25) | TQFN-16 3×3. DIN 1, GAIN_SLOT 2, SD_MODE 4, VDD 7/8, OUTP 9, OUTN 10, LRCLK 14, BCLK 16. 2.5–5.5 V. 3.2 W into 4 Ω @ 10% THD (2.5 W @ 1%). SD_MODE thresholds: <0.16 V shutdown, >1.4 V left. Budget 650–800 mA peak on 5 V. |
| **MMICT390200012** PDM mic (**TDK InvenSense**, not Knowles) | C3171752 (6,049, $1.56) | LGA-5 3.5×2.65 mm, 1.65–3.63 V, 650 µA. Pin table not found (image-only datasheet), so get it from the EasyEDA symbol and verify. **One distributor shows Last-Time-Buy 2026-06-15**, so plan an alternate. |
| **AL8860QMP-13** LED driver | C2678649 (6,082, $0.84) | MSOP-8EP. SET 1 (Rs to VIN, I = 0.1/Rs), GND 2/3, CTRL 4 (float = on, <0.2 V off, PWM <500 Hz via open-drain), SW 5/6, VIN 8 (4.5–40 V, ≥10 µF). EP is thermal only. |
| **SK6812MINI-E** RGB LED | C5149201 (157,421, $0.08) | VDD 1, DOUT 2, GND 3, DIN 4. 3.7–5.5 V. **VIH ≥ 0.7·VDD, so it needs the 5 V level shifter.** About 1 mA idle per LED. |
| **SN74AHCT1G125DBVR** level shifter | C7484 (37,655, $0.11) | SOT-23-5. OE 1, A 2, GND 3, Y 4, VCC 5. TTL input works from 3.3 V. |
| **IP6826** Qi transmitter (Injoinic) | C2921390 (277, $1.03, **needs firmware burn**) | QFN-32. VIN 26/27 4.5–12 V (16 V abs). 15 W needs a 12 V input, so add a 12 V buck. Integrated full bridge; LX1/LX2, BST1/2, ISENSE/IGND (20 mΩ), V_DECODE/VDET, LED1–3 (status only, no I²C), NTC 11, LOSS_THR 12. **NC 25/31 must float.** EPAD = PGND to the shunt's high side. A11 coil. |
| CPS8100 Qi transmitter (alternative) | C2836806 | QFN-48, 3.9–24 V in, I²C/UART/SWD, external FETs; needs vendor firmware. |
| **IP6525S_EN** USB-A fast charge | C46550236 | ESOP-8, 5.2–32 V in, 22.5 W. BC1.2/QC2/QC3/FCP/SCP/AFC/SFCP/**VOOC**/PE+. **No UFCS, no I²C.** |
| **RV-3028-C7** RTC | TBD | 3.2×1.5 mm, **crystal built in**, 45 nA. I²C **0x52**. VBACKUP (10 kΩ to VSS if unused); EVI must not float. Preferred over PCF85063A (C5151540, I²C 0x51, needs a 32.768 kHz crystal). |
| **NT3H2111W0FHKH** NFC tag | C710403 (38,028, $0.56) | XQFN-8. LA/LB antenna (50 pF input capacitance, tune to 13.56 MHz), VCC 1.67–3.6 V, I²C **0x55** (same address as the BQ34Z100, so they go on separate buses), FD open-drain field detect, VOUT energy harvest. |
| TPS22965DSGR load switch | C122837 | WSON-8, 0.8–5.7 V, 6 A, 16 mΩ (3.3 V / 5 V gating). |
| TPS26631PWPR eFuse | C2866319 | HTSSOP-20, 4.5–60 V, 0.6–6 A limit, PGOOD + current monitor (DC output, and 21 V bus gating). |
| TPD4E05U06DQAR USB ESD | C138714 | USON-10, 4 channels, 0.5 pF. |

## Power-stage parts (each BQ25756 stage)

- **FETs:** TI suggests 60 V AONS66614 (4S) and 80 V SiR880BDP (EPR). The **3:1 rule needs ≥ 84 V** on the 28 V VAC side, so use **100 V** FETs (part TBD).
- **Inductor:** 6.8 µH at 350 kHz. Worst case is boost at 15 V, about 10 A, so Isat ≥ 15 A. Candidate: Changjiang FXL1365-6R8-M (C5359272, Isat 19 A, 13 A rated, 12 mΩ).
- **Sense resistors:** 5 mΩ on both SRP/SRN and ACP/ACN, 2512 3 W (e.g., C500739).
- **Frequency:** 300–350 kHz (R_FSW 100 kΩ / 80 kΩ).
- **Capacitors:** REGN 4.7 µF; DRV_SUP 4.7 µF. Split the bulk capacitance on both sides of each sense resistor.

## Connectors (candidates)

| Function | Part | LCSC | Note |
|---|---|---|---|
| USB-C 24-pin, 5 A, mid-mount | HCTL HC-TYPE-C-24P-MM-1.4-5A-12 | C5307768 | Voltage rating unverified |
| USB-C 24-pin (alt) | HCTL HC-TYPE-C-24P-MM0.8-5A-01 | C5345933 | |
| USB-A | HCTL HC-A-002-4P-DIP10-2A-27 | C5447379 | 2 A max, so USB-A is capped at about 2 A for the 3:1 rule |
| DC barrel | XKB DC-005-5A-2.0 / -2.5 | C381116 / C381115 | 5 A, 24 V rating, so derating is an exception |
| Battery power | Amass XT60PW-M | C98732 | about 30 A |
| U.FL | Hirose U.FL-R-SMT-1(10) | C88373 | |
| microSD | Hroparts TF-01A | C91145 | |
| Fan | JST SM04B-SRSS-TB | C160404 | |

## Antennas, audio, coil, crystal

- **Wi-Fi antenna:** dual-band FPC MyAntenna AIWF010 (C53286278).
- **2.4 GHz antenna:** FPC Kinghelm KH-FPC2.4G-1.13IPEX-100 (C709378).
- **LoRa antenna:** external stub Abracon AEACAC053010-S868 (C6123574) / 915 MHz variant C6123576.
- **Speaker:** XHXDZ 40 mm 4 Ω 3 W (C50387222).
- **Qi coil:** CND-tek YX-A11-R501000-R0806 (C3003211, 6.3 µH).
- **32.768 kHz crystal (7 pF):** SJK 7LC32768F07UC (C252399). Only needed if the PCF85063A is used.
