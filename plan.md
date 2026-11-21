# Battery Bank — Design Plan

Living plan for a multi-port USB-C power bank designed in **KiCad** and built at **JLCPCB** (PCB + assembly).
Research snapshot: **2026-11-21**. Prices are single-unit and change often; re-check before ordering.

---

## 1. Requirements (decided)

| Area | Requirement |
|---|---|
| Tooling | KiCad (v10, native Windows ARM64 build available); design for JLCPCB fab + assembly |
| Outputs | **4 × USB-C + 1 × USB-A** |
| USB PD | Target the latest spec. usb.org lists **USB PD Revision 3.3 Version 1.0** (posted 11/05/2026). Build on certified PD 3.1/3.2 silicon (EPR, AVS, PPS) and move to 3.3 as vendors update firmware |
| Voltages | 5, 9, 12, 16, 20, 24 V (see §5 for how each is delivered) |
| Phone support | OnePlus VOOC / SuperVOOC wherever possible; PPS on every USB-C port as the fallback |
| Pass-through | Must charge plugged-in devices while the bank itself is plugged in and charging |
| Ethernet | Ethernet over USB-C (the bank acts like a USB-C dock); speed: 1 Gbps acceptable, **2.5–5 Gbps preferred** |
| Cell choice | Pick cells on price vs. capacity vs. power (see §6) |
| Lighting | **2 LEDs:** one flashlight, one attention-grabbing glow |
| Thermal | **Active cooling (fan)** plus **metal heat sinking** for stability |
| Wireless + audio (proposed) | Wi-Fi, plus a Bluetooth / IP (network) speaker with microphone. Scope still open (§8b, D9–D10) |

---

## 2. Open decisions

| # | Decision | Options | Recommendation |
|---|---|---|---|
| D1 | How many USB-C ports get Ethernet | One dock port, or all four | **Decided 2026-11-21: all four USB-C ports, 2.5G.** Costs a 2.5G switch + extra chips (~$25–40 more parts, several watts, denser board); see §4 for the topology |
| D2 | Ethernet speed | 1G / 2.5G / 5G | **2.5G (RTL8156BG).** Cheaper than the 1G chip and stocked; 5G chip not stocked at JLCPCB and needs 10 Gbps USB routing |
| D3 | Pack size | See §6 tables | **Decided 2026-11-21: maximum that flies internationally without airline approval, i.e. under 100 Wh.** Chosen pack: **5S1P Samsung 50S, 90 Wh, ~187 W sustained** (§6). Override option: 5S1P Samsung 58E for 96 Wh at less than half the power |
| D4 | Total output budget / max per port | e.g. 140 W one port, shared total | Cap each port at **140 W (28 V EPR)**; on battery the firmware shares ~187 W across everything. With input power plugged in, pass-through raises the budget up to the input's limit |
| D5 | Which port is the input | Bidirectional USB-C1, or add a dedicated input | **USB-C1 bidirectional** (input + output) |
| D6 | Per-port power stage chips | See §9 | Needs sourcing work; leading power-bank SoCs aren't stocked at JLCPCB |
| D7 | SuperVOOC chip | SW6301V (consign) or skip | Try for the **USB-A** port; fall back to QC/UFCS if it can't be sourced |
| D8 | Control MCU | STM32G0 (simple), ESP32-C3/S3 (Wi-Fi + BLE only), or ESP32-WROOM-32E (Wi-Fi + Classic Bluetooth) | **ESP32-WROOM-32E** if the Bluetooth speaker goes ahead: it's the ESP32 here with Classic Bluetooth (needed for A2DP music and HFP calls). Battery safety stays in hardware (BMS + charger limits), so a firmware crash can't make the pack unsafe |
| D9 | What "Wi-Fi adapter" means | (a) Wi-Fi adapter for the plugged-in laptop, (b) travel router / hotspot, (c) the bank's own Wi-Fi for app + network audio | **(c) in v1.** (a) needs host drivers and won't work on phones or Apple devices; (b) needs a Linux router SoC and several watts, so it's a v2 candidate |
| D10 | Audio scope | Bluetooth speaker only, + mic for calls (speakerphone), + network (IP) speaker | **Decided 2026-11-21: speaker + mic are in v1.** Start on the ESP32; add a dedicated Bluetooth audio chip only if call quality isn't good enough |
| D11 | Router level | ESP32 basic hotspot, or a real travel-router module | **Decided 2026-11-21: real travel-router module** (OpenWrt-class, Wi-Fi 6) |
| D12 | Extra travel features | See §8c candidate list | **Decided 2026-11-21**, see "Selected for v1" in §8c |

---

## 3. Architecture (draft)

```
                 ┌──────────────────────────── BATTERY 5S1P (Samsung 50S) ───────────┐
                 │  BMS protector + balancing  ·  fuel gauge  ·  2× cell NTC         │
                 └──────────────┬────────────────────────────────────────────────────┘
                                │  battery node / system bus (15.0–21.0 V)
USB-C1 (IN/OUT, EPR) ─ port protect ─ PD ctrl ─ bidirectional buck-boost charger (BQ25756)
                                │
     ┌──────────────────────────┼──────────────────────────────────────────────┐
     │                          │                                              │
 Port stages C2–C4                                                      USB-A stage
 buck-boost + PD ctrl each (C1's power path is the charger above)       QC / UFCS / (SuperVOOC)
                                                                        → USB-A
 Ethernet on all four USB-C ports:
   USB-C1..C4 ─ RTL8156BG (2.5G USB NIC) ×4 ─ PHY-to-PHY ─ 2.5G switch (RTL8372N)
                                                             ├─ SerDes → router SoC (LAN)
                                                             └─ SerDes → RTL8221B PHY → RJ45
     │
 Aux rails: 3.3 V / 5 V buck → ESP32 (MCU + Wi-Fi + Bluetooth), audio amp + mic, glow LEDs, fan, Ethernet, NFC, microSD
 Router module (power-gated): Wi-Fi 6 OpenWrt SoC ↔ 2.5G switch (LAN side: all four USB-C ports; RJ45 as WAN)
 Solar DC input jack ─ protection ─ ideal-diode OR ─┐ (into charger input, alongside USB-C1)
 PoE in (RJ45) ─ TPS2373-4 ─ isolated flyback ─ ideal-diode OR ─┘
 LoRa node: nRF52840 (Meshtastic, BLE to phones) + SX1262 ─ UART ↔ ESP32; always-on capable
 Battery = swappable cartridge (cells + BMS + fuse + NTC + ID chip) on a keyed connector
 DC barrel output 12–24 V (app-selected, default off) ← dedicated buck-boost from system bus
 Wireless charging pad (Qi) ← system bus, under a non-metal top
 Flashlight + red night LED on aluminum LED board
 Flashlight: AL8860 constant-current buck → XP-G3 LED (on metal)
 Sensors: NTCs on each power stage, charger, cells, LED → MCU (fan + power throttling)
```

**Pass-through behavior:** when C1 has input power, the charger feeds the system bus; outputs are served first and the remainder charges the pack. The loads sit on the battery node, so the charger must not end charging early because load current masks charge current. Either use firmware/gauge-based termination or switch to a charger with a separate system power path. To be decided when the architecture is locked.

**Port map (proposed):**
- **C1:** input/output, up to PD EPR in and out
- **C2, C3, C4:** outputs
- **All four USB-C ports:** 2.5G Ethernet into the internal switch and router
- **A:** output, QC/UFCS, SuperVOOC if sourceable

---

## 4. USB-C ports and Ethernet

**Decided: 2.5G Ethernet on all four USB-C ports (D1).**

**Ethernet over USB-C: how it works.** Each USB-C port supplies power while appearing to the connected device as a USB network adapter, like a USB-C dock. A charger normally starts as USB host, so the port's PD controller has to swap data roles (DR_Swap). Laptops and iPads generally accept the swap; phones vary, so this needs testing. The USB-A port can't do this because USB-A is always the host side.

| Speed | Chip | JLCPCB # | Stock (11/21) | 1 pc | Notes |
|---|---|---|---|---|---|
| 1G | RTL8153B-VB-CG | C2802072 | 2,580 | $3.54 | USB 3.2 Gen 1 |
| **2.5G** | **RTL8156BG-CG** | **C41376388** | **2,784** | **$3.24** | USB 3.2 Gen 1, chosen |
| 5G | RTL8157-CG | C41413892 | 0 (consign) | — | Needs USB 3.2 Gen 2 (10 Gbps) routing; full speed only on 10 Gbps hosts, otherwise drops to a 2.5G mode; Windows needs a driver; Linux r8152 support patched Mar 2026 |
| Switch (1G) | RTL8367S-CG | C2760849 | 2,329 | $2.65 | 5-port GbE, only needed for multi-port Ethernet |
| Switch (2.5G) | RTL8372N-CG | C46546780 | 1,294 | $9.38 | Reportedly needs external RTL8221B PHYs (forum summary, unverified) |

**Ethernet extras:** 2.5GBASE-T-rated RJ45 with magnetics, 25 MHz crystals, MAC address storage. Power-gate the Ethernet block when no host has enumerated to avoid battery drain.

**Four-port topology (proposed, to verify against datasheets):**
- **Per port:** one RTL8156BG per USB-C port (×4). Each has a built-in 2.5G PHY, so it connects PHY-to-PHY (on-board, capacitor-coupled, no magnetics) to a switch port.
- **Switch:** RTL8372N-CG (C46546780, 1,294 in stock, $9.38).
  - Its datasheet title is "4-port 2.5G + 2-port 10G switch controller".
  - A forum comment says the 4 × 2.5G PHYs are integrated, but a forum summary says the chip needs external RTL8221B PHYs. **Unverified; read the datasheet before locking.**
  - One 10G SerDes link goes to the router SoC (LAN). The other goes through an **RTL8221B-VB-CG** 2.5G PHY (C5155988, 3,140 in stock, $2.61) to the RJ45 (WAN).
  - RTL8373N (8-port class) is consign-only at JLCPCB.
- **Cost:** about 8 active 2.5G PHYs in the worst case (4 in the NICs + 4 in the switch).
  - Power-gate each port's NIC when nothing is plugged in.
  - Power-gate the whole Ethernet block when the router is off.
  - Add the switch + NICs to the thermal plan (§8).

---

## 5. USB PD, voltages, and OnePlus charging

- **Fixed PD voltages:** 5 / 9 / 15 / 20 V (SPR), plus 28 / 36 / 48 V (EPR).
- **12 V and 16 V:** via **PPS** (adjustable 3.3–21 V). QC / UFCS also provide 12 V.
- **24 V:** via **AVS** in the EPR range.
- A device only gets one of these voltages if it requests it. A fixed 24 V output for non-USB gear would need a separate DC jack (not planned).
- **OnePlus:**
  - **SuperVOOC:** proprietary; needs a licensed protocol chip and the OnePlus cable. iSmartWare **SW6301V** lists SVOOC, VOOC 4.0, UFCS, PD 3.1, 2–6S cells, up to 100 W (ChargerLAB, Feb 2024); at JLCPCB it's consign-only.
  - **PPS fallback:** reviews report ~45 W for a OnePlus 13 and ~36–55 W for a OnePlus 15 on PPS.
- **PD certification:** TI's TPS26750 page titles it a PD 3.2 controller but states USB-IF certification for PD 3.1. I haven't read what PD 3.3 changes; check before finalizing.

---

## 6. Battery cells

**Live retail prices** (18650batterystore.com product feed, updated 2026-11-21; 3.6 V nominal used for Wh):

| Cell | Capacity | Max cont. | Price | Wh | $/Wh | In stock |
|---|---|---|---|---|---|---|
| **EVE 50E 21700** | 5,000 mAh | 15 A | $5.99 | 18.0 | **$0.33** | yes |
| Samsung 58E 21700 | 5,330 mAh | 10.7 A | $6.99 | 19.2 | $0.36 | yes |
| Samsung 50E 21700 | 5,000 mAh | 9.8 A | $6.99 | 18.0 | $0.39 | yes |
| EVE 35V 18650 | 3,500 mAh | 10 A | $4.99 | 12.6 | $0.40 | yes |
| EVE 40PL 21700 | 4,000 mAh | 70 A | $6.99 | 14.4 | $0.49 | yes |
| Samsung 45T 21700 | 4,500 mAh | 50 A | $7.99 | 16.2 | $0.49 | yes |
| Tenpower 60XG 21700 | 6,000 mAh | 60 A | $11.99 | 21.6 | $0.56 | yes |
| Molicel P50B 21700 | 5,000 mAh | 60 A | $11.99 | 18.0 | $0.67 | yes |

**Best value overall: EVE 50E** (lowest $/Wh). But the pack is now capped **under 100 Wh** (D3), which means one cell string of 5 cells. Every cell then carries the full load, so current rating matters more.

**Under-100 Wh options** (power = max continuous current at the empty voltage of 3.0 V/cell; "derated" = 50% of that, my margin for heat and cell life, before converter losses):

| Config | Cells | Wh | Cell cost | Max / derated power | Notes |
|---|---|---|---|---|---|
| **5S1P Samsung 50S** | 5 × 5,000 mAh, 25 A | **90** | $49.95 | 375 / **~187 W** | **Chosen:** best power at max-ish capacity |
| 5S1P Samsung 58E | 5 × 5,330 mAh, 10.7 A | 96 | $34.95 | 160 / ~80 W | Most energy, but too little power for router + Qi + 4 ports |
| 5S1P EVE 50E | 5 × 5,000 mAh, 15 A | 90 | $29.95 | 225 / ~112 W | Cheapest; limits multi-port output |
| 4S2P Samsung 30Q (18650) | 8 × 3,000 mAh, 15 A | 86 | $55.92 | 360 / ~180 W | Less energy, more cells |
| 4S1P Tenpower 60XG | 4 × 6,000 mAh, 60 A | 86 | $47.96 | 720 / ~360 W | Huge power headroom, less energy, lower voltage |

**5S (15.0–21.0 V) is a good bus voltage:** 20 V USB output is a small buck, and 28 V EPR is a modest boost.

**Airline label:** mark the pack's Wh rating (90 Wh) on the case. Rules vary by airline; check before flying.

**For reference only: larger EVE 50E packs.** Above 100 Wh these need airline approval or can't fly, so they're ruled out by D3. Same power method as above.

| Config | Voltage (nom, range) | Wh | Cells | Cell cost | Max / derated power | Airline carry-on |
|---|---|---|---|---|---|---|
| 5S1P | 18.0 V (15.0–21.0) | 90 | 5 | $29.95 | 225 / ~112 W | OK (<100 Wh) |
| 6S1P | 21.6 V (18.0–25.2) | 108 | 6 | $35.94 | 270 / ~135 W | Needs approval |
| 4S2P | 14.4 V (12.0–16.8) | 144 | 8 | $47.92 | 360 / ~180 W | Needs approval |
| 5S2P | 18.0 V (15.0–21.0) | 180 | 10 | $59.90 | 450 / ~225 W | Not allowed (>160 Wh) |
| 6S2P | 21.6 V (18.0–25.2) | 216 | 12 | $71.88 | 540 / ~270 W | Not allowed |

Airline rule of thumb: ≤100 Wh no approval, 100–160 Wh with airline approval, >160 Wh not allowed in passenger baggage.

**Cell safety:** cell temperature limits (charge/discharge windows) come from the Samsung 50S datasheet; the BMS and firmware enforce them through the cell NTCs.

---

## 7. LEDs

### Flashlight
- **LED:** Cree XLamp **XP-G3** cool white, **XPGDWT-01-0000-00ME2** (5700 K, 2 A max), JLCPCB **C17483992**, 145 in stock, $3.10.
  - Alt: XPGDWT-B1-0000-00ME4 (4500 K), C17183945, 100 in stock, $3.46.
  - Low stock on both: order buffer or allow a substitute.
- **Driver:** Diodes **AL8860QMP-13** constant-current buck (4.5–40 V in, up to 1.5 A, 1 MHz), JLCPCB **C2678649**, 6,082 in stock, $0.84. Runs straight from the 5S pack (15–21 V).
- **Drive level:** ~1 A (~3 W) for high mode, dimmed by MCU PWM on the driver's control pin.
- **Modes:** low / med / high / strobe / SOS on a dedicated button.
- **Mounting:** on a small **aluminum-core PCB** (JLCPCB makes these) bonded to the metal case, behind a 20 mm TIR optic.

### Attention glow
- **LEDs:** **SK6812MINI-E** reverse-mount addressable RGB, JLCPCB **C5149201**, 157,421 in stock, $0.08. Several of them behind a diffuser or light-pipe strip.
- **Behavior:** breathing / pulse / color effects to catch attention.
- **Doubles as status:** battery level, charging, pass-through, overheat warning.
- **Power:** gate the 5 V supply with a FET when the glow is off, since addressable LEDs draw idle current even when dark.

---

## 8. Thermal: active cooling + metal heat sinking

**Heat sources:** per-port buck-boost stages (up to 140 W each), the main charger, the 2.5G Ethernet chip, the flashlight LED, and the cells.

### Active cooling
- **Fan:** 5 V, 4-wire (PWM + tach), 30×30 or 40×40 mm, on a JST connector, powered from the aux 5 V rail.
- **Control:** MCU fan curve driven by the NTCs; off at idle for silence and battery life, ramps with temperature.
- **Airflow path:** cool air enters, passes over the power stages and heatsink, and exhausts away from the cells. Don't blow converter heat across the battery compartment.
- **Fan-failure safety:** tach monitoring detects a stalled fan, and the MCU falls back to throttling, so the bank stays safe without the fan.

### Passive / metal heat sinking
- **Enclosure:** an aluminum shell acting as the main heatsink.
- **Board-to-case path:** power FETs and inductors on top with thermal-via arrays under hot pads to large bottom copper, then silicone thermal pads to the aluminum case.
- **Hot cluster:** an extruded aluminum heatsink over the converter / Ethernet cluster, sitting in the fan's airflow.
- **Flashlight LED:** on its aluminum-core PCB bonded to the case.
- **Battery:** thermally separated from the power electronics, with insulation between the pack and the hot side.

### Thermal sensing and protection
- **NTC locations:** each port stage, the main charger, two on the cells, and the flashlight LED.
- **Throttling:** when hot, the MCU renegotiates lower PD power on the ports, then limits charging, then shuts down.
- **Copper:** 2 oz copper on the power layers to cut I²R heating.

---

## 8b. Wireless + audio (proposed)

### What "Wi-Fi adapter" could mean

| Option | How it would work | Verdict |
|---|---|---|
| (a) Wi-Fi adapter for the plugged-in device | The dock port becomes a USB hub with the 2.5G NIC and a USB Wi-Fi chip behind it | **Skip.** Needs drivers on the host; phones and Apple devices generally won't load third-party USB Wi-Fi drivers; laptops already have Wi-Fi |
| (b) Travel router / hotspot | Shares the RJ45 wired network over Wi-Fi | **v2 candidate.** Needs an OpenWrt-class router SoC with RAM, flash, and antennas, drawing several watts |
| (c) Bank's own Wi-Fi + Bluetooth | One ESP32 module: phone app (battery, port power, temps, LED/glow control), firmware updates, network audio | **Do in v1.** Cheap, stocked, and it doubles as the control MCU (D8) |

### Speaker + microphone

- **Bluetooth speaker (A2DP) and calls (HFP):** both need Classic Bluetooth. The **original ESP32** has it; ESP32-S3, C3, and C6 are BLE-only.
  - The ESP32 can run Wi-Fi and Bluetooth audio at the same time, but radio sharing is its weak spot. Prototype this early.
- **IP / network speaker:** over Wi-Fi on the same ESP32. Open-source ESP32 network-audio players exist; which protocols to support is still open (AirPlay and Spotify Connect involve licensing or certification).
- **Amplifier:** Analog Devices **MAX98357AETE+T** I²S class-D mono amp, JLCPCB **C910544**, 24,129 in stock, $1.25. Pair with a ~40 mm full-range driver in a sealed back chamber.
- **Microphone:** Knowles **MMICT390200012** digital PDM MEMS mic, JLCPCB **C3171752**, 6,049 in stock, $1.56.
  - The ESP32's I²S0 port accepts PDM input.
  - Two mics can share one data line (left/right) for noise reduction.
  - The I²S mics ICS-43434 and SPH0645LM4H are out of stock at JLCPCB.
- **Speakerphone echo cancellation:** the speaker and mic share a box, so calls need echo cancellation. That's limited on the original ESP32. If call quality isn't good enough, add a dedicated Bluetooth audio SoC module that does HFP + echo cancellation in hardware, and keep the ESP32 for Wi-Fi.

### Conflicts with the rest of the design

- **Metal case vs radio:** an aluminum enclosure blocks Wi-Fi and Bluetooth. Put the module at a board edge with an antenna keep-out zone behind a plastic RF window or end cap, or use an external antenna (U.FL).
- **Fan vs microphone:** fan noise reaches the mic. Slow or stop the fan during calls (with thermal throttling as backup), mount the mic far from the fan, and acoustically seal it.
- **Speaker vs airflow and space:** the speaker needs a sealed back volume, which competes with the fan's air path and battery space. The enclosure will grow.
- **Battery drain:** audio at volume and active Wi-Fi each cost watts. Radios sleep when idle.
- **Certification:** use a pre-certified radio module (e.g., ESP32-WROOM-32E) instead of a bare chip, which avoids full intentional-radiator testing. The product still needs its own emissions testing.

---

## 8c. Travel router + cheap extra features (candidates)

### Router level (D11)

| Option | What it does | Cost / power | Notes |
|---|---|---|---|
| **ESP32 hotspot** | Repeats hotel Wi-Fi to your devices (NAT), captive-portal login once | ~$0, already on board | Slow: community ESP32 NAT router projects report roughly 10–20 Mbps (unverified). Can't use the 2.5G port as WAN at speed. Good enough for messaging and email |
| **Real travel-router module** | Wi-Fi 6 router: hotel RJ45 or Wi-Fi as WAN, your own private network, VPN, ad blocking (OpenWrt) | Roughly +$15–30 parts, several watts | OpenWrt-class MediaTek MT7981-family chip (used in popular travel routers). Needs RAM, flash, and antennas; JLCPCB sourcing TBD; likely a separate module board. The 2.5G RJ45 becomes its WAN/LAN port |

### Cheap extras (rough part cost, stock not yet checked)

| Feature | Why it's useful when traveling | Rough cost | Notes |
|---|---|---|---|
| Small display (1.3–1.5" OLED/IPS) | Battery %, watts per port, time to full/empty, temperatures | $2–4 | Biggest usability win |
| Per-port power meter + cable tester | Shows each device's V/A/W and what the plugged-in USB-C cable supports (e-marker) | ~$0–1 | Mostly firmware if the PD controllers report it; otherwise one current sensor per port |
| Low-current mode | Keeps charging earbuds and watches that normally make power banks shut off | $0 | Firmware |
| Charge limit (e.g., 80%) + cycle / health stats | Longer battery life, storage mode | $0 | Firmware + fuel gauge |
| Solar input with MPPT | Recharge from a folding panel when camping | ~$1–3 (connector + protection) | The BQ25756 charger has a solar (MPPT) feature (datasheet section not yet read) |
| DC barrel output (12–24 V fixed) | Powers non-USB gear: routers, cameras, CPAP, LED strips (covers your 12/16/24 V list) | ~$1–2 | Reuses a port stage; needs a selector + overcurrent protection |
| Red night-light LED + SOS beacon | Night vision-friendly light, emergency signal | ~$0.10 | Adds a red LED next to the flashlight; SOS uses flashlight + glow |
| Personal alarm / siren | Loud alarm button, uses the speaker | $0 | Firmware |
| Lantern mode | Diffuser cap or glow ring turns it into a tent light | Mechanical | Uses the existing LEDs |
| IR blaster + receiver | Universal remote for hotel TVs and AC units via the app | ~$0.30 | IR LED + receiver on the ESP32 |
| NFC tag | Tap phone to open the app / pair Bluetooth | ~$0.30 | Passive NTAG chip + antenna, no firmware on the bank |
| Motion sensor (accelerometer) | Tap-to-wake, shake for flashlight, tamper / "bag moved" alarm | ~$0.50 | I²C |
| Temperature / humidity / pressure sensor | Room or weather readout, altitude when hiking | ~$2–3 | Mount away from the hot side or readings are skewed |
| microSD slot | Music and podcasts for the speaker offline, logs, file share (with router) | ~$0.30 | |
| Left-behind alert | Phone app warns when you walk away from the bank | $0 | BLE, firmware + app |
| Tripod thread (1/4"-20) + lanyard point | Mount as a light or speaker | Mechanical | Enclosure |
| Wireless charging pad (Qi / Qi2) | Charge a phone or earbuds on top without a cable | ~$5–10 + heat | Qi2 needs certification and magnets; adds heat on top of the metal case |

**Airline note:** print the pack's Wh rating on the case, since airlines check it.

### Slow-charge toggles (requested 2026-11-21)

Two kinds, both switchable in the app, plus one physical switch so it works without a phone.

| Toggle | What it does | How it's done |
|---|---|---|
| **Bank slow charge** (charging the bank itself) | Charges the pack gently (e.g., ~0.2C ≈ 1 A into the 5S pack) instead of the normal rate: cooler, quieter fan, longer cell life, works on weak chargers and small solar panels | Firmware lowers the BQ25756 charge-current limit over I²C. Normal rate comes from the Samsung 50S datasheet's standard charge current |
| **Port slow charge** (per USB-C port and the USB-A port) | Charges a phone or other device slowly, e.g. overnight, for battery health, less heat | USB-C: the PD controller re-advertises only low-power offers (e.g., 5 V and 9 V at a capped wattage) and renegotiates. USB-A: turns off QC/UFCS/VOOC and falls back to plain 5 V |
| **Pad slow charge** | Wireless pad at basic power instead of max | Firmware limit on the wireless transmitter |

**Physical switch:** a small side slide switch labeled **SLOW**, read by the ESP32. When on, it slow-charges both the bank and every output. Per-port overrides and the exact wattage are set in the app. Its state shows on the glow LEDs (e.g., a calm blue pulse while slow-charging).

**Defaults:** off (normal speed). Each port's setting is remembered across power cycles.

### Selected for v1 (2026-11-21)

**Hardware:**
- **Real travel-router module** (D11): Wi-Fi 6, OpenWrt.
- **Per-port power meter + USB-C cable tester:** readout in the phone app, since there's no display.
- **NFC tap-to-pair:** an NTAG I²C-type tag the ESP32 can write pairing info into.
- **Solar input with MPPT.**
- **DC 12–24 V barrel output.**
- **Red night-light LED + SOS beacon + siren.**
- **Wireless charging pad.**
- **microSD slot.**
- **Tripod mount + lantern mode.**

**Firmware-only, no hardware cost, included:** low-current mode, charge limit + health stats, left-behind alert, **slow-charge toggles** (one slide switch of hardware, see above).

**Not selected:** display, IR remote, motion sensor, temperature/humidity/pressure sensor. Status shows on the glow LEDs and in the app.

**Added later on 2026-11-21 (to stand out):** LoRa / Meshtastic off-grid messaging, swappable battery cartridge, alarm firmware, open firmware, PoE power input on the RJ45. Details in §8d.

### Design consequences of the selections

- **Router + ESP32 roles:**
  - The ESP32 stays the always-on controller: power, thermal, Bluetooth audio, the app over BLE.
  - The router module is power-gated and only boots when router mode is on. It draws several watts and boots slowly.
  - All four USB-C ports' 2.5G Ethernet chips feed the router's LAN through the internal switch, so any laptop plugged in gets the router's network over USB-C.
  - The RJ45 becomes the router's WAN port (hotel Ethernet in).
- **Router antennas:** they need the same RF window as the ESP32, or external antennas. Two radios at 2.4/5 GHz need antenna separation.
- **Wireless pad vs metal case:** a charging coil heats nearby metal and trips the pad's foreign-object detection. The pad area must be a non-metal top (plastic or glass) with a ferrite shield behind the coil, kept away from the aluminum heatsink parts. Qi2 also needs WPC certification and a magnet ring. A plain Qi pad (no certification logo) is simpler.
- **Solar input:**
  - Use a dedicated DC input jack, kept separate from the DC output so the two can't be confused.
  - Combine it with USB-C1 input through ideal-diode ORing; TI lists the LM74502H in the PMP41115 ecosystem.
  - The charger's MPPT handles the panel. The input range must cover the panel's open-circuit voltage; BQ25756 accepts 4.2–70 V.
- **DC output:**
  - Voltage is set from the app; the output defaults to **off** and is always off at power-up.
  - The glow color shows the selected voltage.
  - It has its own overcurrent protection.
  - It runs from one of the port-stage converters or a small dedicated buck-boost.
- **microSD:** on the ESP32 (offline music, logs). File sharing on the router uses the router module's own storage, or the card can move to the router; TBD.
- **Red LED:** small red LED next to the flashlight on the aluminum LED board; part TBD.
- **Power budget:** router (several W) + Ethernet switch/NICs + wireless pad (~15 W in, plus losses) + speaker + fan add continuous load on top of the USB ports.
  - On the 90 Wh pack this caps runtime, so the firmware needs a power allocator (USB ports first, then pad, router, and audio by user priority).
  - It also needs a "max runtime" mode that turns off the router, Ethernet, and pad.

---

## 8d. Standout features (selected 2026-11-21)

### LoRa / Meshtastic off-grid messaging
- **What it does:** phone-to-phone text messaging with no cell signal over the open-source Meshtastic mesh network. Phones connect to the bank over **Bluetooth** with the standard Meshtastic app.
- **Hardware:** its own small node, separate from the ESP32.
  - **MCU + BLE:** Ebyte **E73-2G4M08S1CX** (nRF52840, external-antenna version), JLCPCB **C2764963**, 713 in stock, $6.37.
  - **LoRa radio:** Ebyte **E22-900M22S** (SX1262, 850–930 MHz, 22 dBm), JLCPCB **C411293**, 1,293 in stock, $7.36.
  - nRF52840 + SX1262 is the same chip pairing as popular Meshtastic hardware.
  - The 850–930 MHz range covers both the US 915 MHz and EU 868 MHz bands; the region is set in firmware.
- **Why a separate node:** the ESP32 is already busy with Bluetooth audio and power control. The nRF52840 runs stock Meshtastic firmware (with a custom board definition), draws only milliamps, and can stay on as a mesh relay even when the rest of the bank is off.
- **Link to the ESP32:** UART (Meshtastic serial API) so the bank's app can show mesh status. The ESP32 can also power-gate the node.
- **Antennas:** the LoRa radio and the node's Bluetooth both need antennas. The metal case means external SMA (LoRa) + U.FL leads to an RF window. Keep the LoRa, Wi-Fi, and Bluetooth antennas apart.

### Swappable battery cartridge
- **What it does:** the 5S1P Samsung 50S pack (90 Wh) is a sealed, tool-less cartridge. Carry a charged spare; replace a worn pack.
- **Whole cartridge only:** never single cells, since mismatched cells in series are a safety hazard.
- **Inside each cartridge:**
  - cells (spot-welded, matched)
  - the cell protection/balancing BMS
  - a fuse
  - an NTC
  - an ID/stats chip (EEPROM or fuel-gauge memory) so the bank knows each pack's cycle count and health
- **Connector:** keyed, recessed contacts rated for full pack current (~25 A peak) with a pre-mate ground / sense pin. Pack output only enables after the bank sees the sense pin, so sparks and shorts are avoided.
- **Airline:** each cartridge is under 100 Wh and labeled with its Wh rating. Spares go in carry-on with contacts covered; the recessed connector plus a snap cap does this.
- **During a swap:** the bank shuts down unless input power is present. With USB-C1, PoE, or solar connected, pass-through keeps everything running while the pack is out.
- **Bonus:** the battery bay can hide the debug/programming pads (see open firmware).

### Alarm firmware
- **Sunrise alarm:** the glow LEDs, then the flashlight, ramp up before the alarm time.
- **Sounds:** wake-up sound and sleep sounds / white noise through the speaker, with timers.
- **Time source:** synced from the phone app or the router's network time. A small low-power RTC chip keeps time accurately between syncs (part TBD).
- **Ties in:** "be full by 7 am" charging and the slow-charge toggles.

### Open firmware
- **What's open:**
  - **ESP32 firmware:** open source; license TBD (e.g., MIT/Apache or GPL).
  - **Router:** OpenWrt (open source).
  - **LoRa node:** Meshtastic (open source).
- **Safety stays in hardware,** so custom firmware can't make the pack unsafe:
  - the cartridge BMS (over-voltage, under-voltage, over-current, temperature)
  - fuses
  - charger current ceilings set by resistors (BQ25756 ICHG/ILIM pins). This only works if the datasheet confirms the pin setting caps any register value.
  - independent over-temperature cutoff
- **Flashing:**
  - over the air via Wi-Fi from the app
  - plus programming pads in the battery bay for recovery (USB-UART bridge or pogo-pin header)
  - The USB-C ports are busy with Ethernet, so they aren't used for flashing.
- **Publish:** schematics, pinout, and a hardware API so the community can build on it.

### PoE power input on the RJ45
- **What it does:** the RJ45 accepts power from a PoE switch or injector, which charges the bank and runs pass-through. Useful in offices, vans, and permanent installs. Data still works on the same cable.
- **PoE controller:** TI **TPS2373-4RGWR** (IEEE 802.3bt PoE++ PD interface), JLCPCB **C470963**, 3,425 in stock, $4.65.
  - Alternatives are low on stock: TPS23734 (2 pcs), TPS2373-3 (4 pcs).
- **Power level:** design for **802.3bt Type 3** (about 51 W at the device); it also accepts lower-power 802.3at/af sources at reduced power. The exact class is TBD.
- **Isolation:** the bank has user-touchable metal (USB shells, aluminum case), so the PoE input needs an **isolated DC-DC converter** (flyback with a transformer) to meet Ethernet's 1500 V isolation rule. Flyback controller and transformer TBD.
- **Magnetics:** the RJ45 needs PoE-rated magnetics (center-tapped, rated for the current) that also support 2.5GBASE-T.
- **Combining inputs:** the isolated output joins USB-C1 and solar through ideal-diode ORing into the charger input.
- **Conflict:** hotel Ethernet rarely has PoE. Detection is automatic, so a non-PoE jack just works as data.

---

## 9. Key parts and JLCPCB status

| Function | Part | JLCPCB / LCSC # | Status (11/21) |
|---|---|---|---|
| Main bidirectional charger | TI BQ25756 (1–14S Li-ion, 4.2–70 V in, 20 A, reverse mode for PD EPR) | LCSC C19272232 | Stock seen on LCSC snapshots; **verify on JLCPCB** |
| EPR PD controller | TI TPS26750 (EPR 28/36/48 V + AVS, PPS, source and sink, I²C control of TI chargers) | JLCPCB search found 2 listings | **Verify stock** |
| 48 V CC/SBU port protection | TI TPD4S480 (TI requires it with TPS26750) | — | Verify |
| Per-port power-bank SoC (alt) | Injoinic IP2366 I²C (2–6S, 140 W, PD 3.1, buck-boost) | C20415848 | **0 stock**, pre-order $1.54 |
| SuperVOOC / VOOC SoC | iSmartWare SW6301V | C9900100418 | **Consign only** |
| 2.5G Ethernet (×4, one per USB-C port) | Realtek RTL8156BG-CG | C41376388 | 2,784 in stock, $3.24 |
| 2.5G switch | Realtek RTL8372N-CG | C46546780 | 1,294 in stock, $9.38 (PHY integration to verify) |
| 2.5G PHY for RJ45 | Realtek RTL8221B-VB-CG | C5155988 | 3,140 in stock, $2.61 |
| Cells (×5) | Samsung 50S 21700 | retail (18650batterystore) | $9.99 each, in stock |
| Flashlight LED | Cree XP-G3 5700 K | C17483992 | 145 in stock, $3.10 |
| Flashlight driver | Diodes AL8860QMP-13 | C2678649 | 6,082 in stock, $0.84 |
| Glow LEDs | SK6812MINI-E | C5149201 | 157,421 in stock, $0.08 |
| BMS / gauge | TBD (candidates: TI BQ76920-family AFE, BQ34Z100-G1 gauge) | — | Evaluate |
| MCU + Wi-Fi + Classic Bluetooth | Espressif ESP32-WROOM-32E-N8 (proposed, D8) | C701342 | 26,574 in stock, $4.57 |
| Speaker amp | Analog Devices MAX98357AETE+T | C910544 | 24,129 in stock, $1.25 |
| Microphone | Knowles MMICT390200012 (PDM) | C3171752 | 6,049 in stock, $1.56 |
| Travel-router module | OpenWrt-class Wi-Fi 6 (MediaTek MT7981 family) | — | Sourcing TBD (likely a separate module board) |
| Wireless charging TX | Qi transmitter IC + coil + ferrite | — | TBD |
| Solar input ORing | Ideal-diode controller (e.g., TI LM74502H) | — | Verify stock |
| NFC | NTAG I²C-type tag + PCB antenna | — | TBD |
| Red night LED | Red SMD LED | — | TBD |
| microSD | Push-push microSD socket | — | TBD (JLCPCB Basic likely) |
| SLOW slide switch | Small SPDT side-actuated slide switch | — | TBD |
| LoRa radio | Ebyte E22-900M22S (SX1262, 850–930 MHz) | C411293 | 1,293 in stock, $7.36 |
| Meshtastic MCU + BLE | Ebyte E73-2G4M08S1CX (nRF52840, U.FL) | C2764963 | 713 in stock, $6.37 |
| PoE PD interface | TI TPS2373-4RGWR (802.3bt) | C470963 | 3,425 in stock, $4.65 |
| PoE isolated DC-DC | Flyback controller + transformer | — | TBD |
| RTC | Low-power RTC chip | — | TBD |
| Cartridge connector + ID chip | Keyed high-current connector, EEPROM / gauge | — | TBD |

**Reference:** TI PMP41115 pairs TPS26750 + BQ25756 + TPD4S480 for a 240 W PD EPR charger, but for 10–12-cell packs. Per its test report, it runs at 300 kHz and reaches 97.6% full-load efficiency. Our 5S pack (15–21 V) needs a different design point (boost for 28 V+).

---

## 10. KiCad and JLCPCB build notes

- **KiCad:** install KiCad 10 (native ARM64 installer, kicad.org). Store the LCSC part number in a symbol field on every part for BOM/CPL export (e.g., with the kicad-jlcpcb-tools plugin).
- **Stackup:** 6-layer, impedance-controlled (USB 3 SuperSpeed pairs, 2.5G MDI pairs), 2 oz outer copper on the power side.
- **Board split (proposed):**
  - main power board: charger, port stages, BMS
  - Ethernet / MCU section
  - small aluminum LED board
  - fan and battery on harness connectors
- **Parts strategy:** prefer JLCPCB Basic parts for passives; each unique Extended part adds a setup fee. Consigned parts (SW6301V, RTL8157) mean buying and shipping parts to JLCPCB.
- **Repository:** the project folder sits inside the Desktop-level Git repo, on the current branch by choice.

---

## 11. Risks

1. **Sourcing:** the power-bank SoCs that handle VOOC or multi-protocol charging (SW6301V, IP2366) aren't stocked at JLCPCB.
2. **DR_Swap interop:** some phones may refuse the data-role swap that the Ethernet ports need.
3. **Pass-through charge termination:** loads on the battery node can confuse the charger.
4. **Thermal:** up to 4 ports at high power in a small enclosure, so throttling must be reliable even if the fan fails.
5. **PD 3.3 compliance:** depends on chip-vendor firmware updates.
6. **Low LED stock:** the XP-G3 has only ~100–145 units at JLCPCB.
7. **Safety:** Li-ion pack design needs proper BMS protection, fusing, and cell separation.
8. **Feature creep:** power bank + dock + 2.5G Ethernet + Wi-Fi + speakerphone + flashlight + glow + fan (+ router and the §8c extras) is a lot of firmware and enclosure work for one revision. Speaker + mic are confirmed for v1, so bring up and test each block on its own (separate sheets, solder jumpers or 0 Ω links to isolate it).
9. **RF in a metal case:** antennas need an RF window; fan noise affects the mic.
10. **Wireless pad near metal:** the coil heats nearby metal and trips foreign-object detection; needs a non-metal top and a ferrite shield.
11. **DC output at the wrong voltage** can damage gear: default off, explicit selection in the app, clear voltage indication.
12. **Router module sourcing:** probably not a JLCPCB stocked part; plan a module board or consignment.
13. **Four-port Ethernet:** up to 8 active 2.5G PHYs; the switch's PHY integration is unverified; dense high-speed routing on 4 connectors.
14. **Power vs a 90 Wh pack:** many simultaneous loads mean short runtime when everything is on; the firmware power allocator is essential.
15. **Antenna count in a metal case:** Wi-Fi 6 (router), ESP32 Wi-Fi/Bluetooth, nRF52 Bluetooth, and LoRa all need antennas and separation.
16. **PoE isolation:** a 1500 V isolated flyback adds a transformer, board area, and safety spacing.
17. **Cartridge connector:** must carry ~25 A safely through many swaps; a poor connector is a fire risk.
18. **Open firmware vs safety:** every safety limit must be enforced in hardware, independent of firmware.

---

## 12. Next steps

1. Confirm D8 (MCU: ESP32-WROOM-32E proposed). D1, D3, D10, D11, and D12 are decided.
2. Read the RTL8372N datasheet (PHY integration, SerDes modes) and pick a router module that can take a 2.5G/10G SerDes link.
3. Lock the per-port power stage (D6) after checking JLCPCB stock for BQ25756, TPS26750, and alternatives.
3. Install KiCad 10 and create the project: hierarchical sheets for power input / charger (USB-C1, solar, PoE), battery cartridge + BMS, each port stage, Ethernet + switch, router, MCU + wireless, LoRa node, audio, LEDs, and thermal/fan.
4. Draw the schematic with LCSC numbers on every part; run ERC.
5. Set the JLCPCB stackup, design rules, and BOM/CPL export.

---

## Sources

- USB-IF PD document library: https://www.usb.org/document-library/usb-power-delivery
- TI TPS26750: https://www.ti.com/product/TPS26750
- TI BQ25756: https://www.ti.com/product/BQ25756
- TI PMP41115 reference design: https://www.ti.com/tool/PMP41115 · test report https://www.ti.com/document-viewer/lit/html/TIDT407
- ChargerLAB, six 140 W PD 3.1 power-bank PMICs: https://chargerlab.com/innovating-power-exploring-six-140w-pd3-1-power-bank-pmics
- ChargerLAB, iSmartWare SW6301V: https://chargerlab.com/pd3-1-enabled-ismartware-launched-multi-protocol-buck-boost-chip-sw6301v
- CNX Software, RTL8157 5GbE adapters: https://www.cnx-software.com/2024/08/14/the-first-realtek-rtl8157-5gbps-ethernet-to-usb-3-2-adapters/
- ServeTheHome, WP-UT5 review: https://www.servethehome.com/wisdpi-wp-ut5-5gbps-usb-c-to-5gbe-adapter-review/2/
- Linux r8152 RTL8157 patch (Mar 2026): https://lkml.iu.edu/hypermail/linux/kernel/2603.2/04170.html
- TechInfoDepot, Realtek Ethernet switches: https://techinfodepot.shoutwiki.com/wiki/Realtek_Ethernet_Switch
- Android Authority, OnePlus 13 charging: https://www.androidauthority.com/flexible-fast-charging-oneplus-13-3577609
- Android Central, OnePlus 15 charging speed: https://www.androidcentral.com/phones/oneplus/oneplus-15-charging-speed
- Cell prices: https://www.18650batterystore.com/ (product feed, 2026-11-21)
- JLCPCB parts library: https://jlcpcb.com/parts
- KiCad Windows downloads: https://kicad.org/download/windows/
