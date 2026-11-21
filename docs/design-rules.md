# Design rules: safety margins, debuggability, quality

These rules are enforced by `hardware/checks/` where the check can be automated, and by the adversarial design review otherwise.

## 1. The 3:1 safety buffer (current, power and thermal capacity)

**Rule (clarified by the user 2026-11-21):** every part that carries current or dissipates power is rated for at least **3×** its worst-case operating current or power. **3:1 does not apply to voltage**; voltage uses the standard derating in §1.3. Where an interface standard makes 3:1 impossible, the exceptions table (§1.4) records what we do instead.

### 1.1 What 3:1 applies to
| Part type | Rated parameter | Rule |
|---|---|---|
| Battery cells | Continuous discharge current | Design discharge ≤ ⅓ of rating: Samsung 50S 25 A → **8.3 A max**, firmware limit 8.0 A |
| Inductors (power stages, bucks) | Rated (thermal) current and saturation current | I_rated ≥ 3 × worst-case RMS; I_sat ≥ 3 × worst-case peak is the goal, ≥ 2 × peak is the hard minimum |
| MOSFETs | I_D at Tc = 100 °C, and power dissipation | I_D(100 °C) ≥ 3 × worst-case RMS; conduction + switching loss ≤ ⅓ of the package's rated dissipation on our copper |
| Diodes (rectifiers, Schottky, ORing body paths) | I_F(AV) | ≥ 3 × average current |
| Resistors (incl. current-sense) | Power | Dissipation ≤ ⅓ of rated power |
| Load switches / eFuses | Continuous current | Current limit set ≤ ⅓ of rated continuous current where the part allows; otherwise the part is sized 3× over the load |
| Connectors: DC jacks, battery, fan, LED-board, router mezzanine | Contact current rating | Operating current ≤ ⅓ of the contact rating |
| Copper: traces, planes, vias | IPC-2152 current for a 10 °C rise | Copper sized for **3 ×** design current; vias in parallel so each via carries ≤ ⅓ of its rating |
| Fuses | Interrupt rating | Interrupt rating ≥ 3 × available fault current; fuse current rating above normal current per its derating curve |
| Regulators / converters (aux bucks, LED driver, Qi, amp) | Output current / power | Load ≤ ⅓ of the IC's rated output current, or several in parallel |
| Thermal | Junction temperature | Tj ≤ Tj(max) − 40 °C at the "everything on" profile |

### 1.2 How 3:1 changes the product
| Item | Rating | 3:1 limit | Consequence |
|---|---|---|---|
| Cell current | 25 A | 8.3 A | Battery-only output **125 W** guaranteed (8.3 A × 15 V at empty) |
| DC barrel jack (input / output) | 5 A | 1.67 A | **40 W at 24 V** in or out; 20 W at 12 V |
| XT60 battery connector | about 30 A | 10 A | ≥ 8.3 A ✓ |
| Per-port power stage (BQ25756) | Inductor 22 A rated (TMPA1707SP-6R8MN-D), FETs ≫ 21 A | ~7.0 A worst-case RMS (100 W boost from 15 V) | **USB-C ports capped at 100 W each** (20 V/5 A, or 28 V EPR at 3.57 A). 140 W would need ≥ 30 A inductors |
| TPS62933 aux bucks | 3 A each | 1 A each | **Several bucks or a larger regulator** per rail: 5 V up to 3 A load needs a ≥ 9 A-capable converter, 0.95 V Ethernet core (~4.5 A) needs ≥ 13.5 A |
| TPS22965 load switch | 6 A | 2 A | Fine for 3.3 V Ethernet gating (~1 A) |
| TPS26631 eFuse (DC out) | 6 A | 2 A | Sets DC output to ≤ 1.67 A anyway (jack-limited) |
| AL8860 LED driver | 1.5 A | 0.5 A | **Flashlight runs at ≤ 0.5 A** (~1.5 W) unless a bigger driver is used. Reviewer to decide |
| MAX98357A amp | 3.2 W into 4 Ω (10% THD) | ~1 W | **Speaker limited to about 1 W average** (peaks allowed within the datasheet) |
| IP6826 Qi (15 W) | 15 W | 5 W | **Qi pad limited to 5 W** (BPP), unless a bigger transmitter is used |
| IP6525S USB-A (22.5 W) | 22.5 W | 7.5 W | USB-A ≤ 7.5 W (5 V/1.5 A), which matches the connector exception |

### 1.3 Voltage derating (standard, not 3:1)
| Part type | Rule |
|---|---|
| Ceramic capacitors | DC rating ≥ **2 ×** net max (DC-bias capacitance loss); effective capacitance at bias ≥ 50% of nominal |
| Polymer / electrolytic | ≥ 1.25 × net max |
| MOSFETs V_DS | ≥ **1.5 ×** drain-net max, plus ringing: 21 V bus → ≥ 40 V; 28 V VBUS → ≥ 60 V (TI's own EPR designs use 80 V) |
| Diodes V_R | ≥ 1.5 × working voltage |
| TVS | Standoff ≥ working max + 10%; clamp < protected part's abs-max |
| Resistors | Voltage across ≤ the rated working voltage of the package (0402 = 50 V, 0603 = 75 V, 0805 = 150 V) |
| ICs | Every pin inside its *recommended operating* range in the worst case |

Worst-case net voltages:
- VBAT 21.0 V
- VBUS 28.0 V (EPR capped by policy)
- PoE input 57 V
- VPOE 22 V
- VDCIN 24 V
- VDCOUT 24 V
- V12 12 V
- V5 5.5 V
- V3V3 3.6 V
- V0V95 1.0 V

### 1.4 Exceptions (3:1 on current not achievable)
| Item | Why | What we do instead |
|---|---|---|
| USB-C contacts (VBUS 5 A) | USB PD defines 5 A with e-marked cables; no 15 A USB-C exists | Use 5 A-rated receptacles; firmware never exceeds the negotiated contract; NTC at each connector with thermal foldback |
| USB-A contacts (2 A part) | No high-current USB-A on LCSC | Limit USB-A to 1.5 A (QC up to 12 V); **VOOC dropped** (needs 4–6.5 A special receptacles); OnePlus phones use PPS on USB-C |
| PoE pairs / magnetics | 802.3bt defines per-pair current | bt-rated magnetics; Type 3 Class 6 |
| IC internal power switches (e.g., TPS26750 PP5V 3 A, TPS2373 hot-swap FET) | Set by the silicon | Use only as specified; never pass high power through internal switches when an external path exists |

## 2. Debuggability rules
1. **Test points:**
   - A labelled test point on every power rail, next to its regulator.
   - On every power stage: switch nodes (probe pad), sense-resistor ends, STAT/PG/INT.
2. **Isolation links:**
   - Each power stage and functional block is fed through a **solder jumper or 0 Ω link**, so it can be cut off and its current measured.
   - High-current links (≥ 2 A) are solder-bridge copper jumpers (no part), so they carry 3× current.
3. **Bus access:**
   - Every I²C branch (behind the TCA9548A mux) has SDA/SCL/GND test pads.
   - Main I²C has a Qwiic/STEMMA-QT footprint (DNP).
4. **Programming / consoles** on Tag-Connect TC2030 or 1.27 mm pad footprints:
   - ESP32: UART0 + EN + IO0, plus EN and BOOT buttons.
   - nRF52840: SWD + RESET + UART.
   - Router module: UART console.
   - RTL8372N: UART0 + SPI-flash ISP pads.
5. **Status LEDs** (each behind a solder jumper so it can be cut for standby current):
   - One per power stage (PG/STAT).
   - One per aux rail.
   - One fault LED driven by the ESP32.
6. **Built-in measurement:**
   - BQ25756 ADC on every stage (VAC, IAC, VBAT, IBAT).
   - BQ34Z100 pack gauge.
   - NTCs at each USB-C connector, each power stage, the cells, the LED and the router.
7. **Fault containment:**
   - Hardware current limits on every stage (ICHG / ILIM_HIZ resistors cap register values).
   - eFuse or load switch with PG on every gated block.
   - Open firmware can't exceed the hardware limits.
8. **Silkscreen:** refdes on every part (≥ 1.0 mm), rail names at test points, pin-1 marks, a connector legend, and the revision/date.
9. **Schematic structure:** one sheet per block; nets named by function (`VBUS_C2`, `I2C3_SDA`).

## 3. "Everything on" reference profile
See `docs/power-budget.md`. Every block must stay within its 3:1 limits and thermal limits at the same time, from the battery alone and with pass-through power from USB-C, the DC barrel jack, or PoE.

## 4. Quality rules
- **Parts:** JLCPCB stock ≥ 5× the build quantity at order time. Every critical part has a second source or a noted alternative.
- **Datasheets:** every IC follows its datasheet "typical application" values unless the review records why not.
- **Review gate:** the adversarial review must pass with **no open critical or major findings** before layout starts.
