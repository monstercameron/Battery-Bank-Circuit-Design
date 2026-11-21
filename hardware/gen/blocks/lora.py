"""Meshtastic node: Ebyte E73-2G4M08S1CX (nRF52840, BLE to phones, own U.FL antenna) + E22-900M22S (SX1262).
Pin choices follow a common nRF52840 + SX1262 Meshtastic variant; the board definition is written to match.
E22 wiring (verified against the symbol): RXEN pad 6 <- P1.04, TXEN pad 7 <- DIO2 pad 8 (DIO2-as-RF-switch),
DIO1 pad 13 -> P0.26, BUSY pad 14 -> P0.13, NRST pad 15 <- P1.02, SPI pads 16-19.

X-38 pad 12: the local E22-M series manual (docs/datasheets, (c) 2012-2026) lists pad 12 = GND; the current web pin table
(cdebyte.com/products/E22-900M22S/2) lists pad 12 = NRST ("Module reset pin, low reset") as well as pad 15.
Pad 12 is therefore isolatable: 0R to GND FITTED (safe if pad 12 is GND; if it is really NRST the radio is only held in
reset - BUSY stays high, no damage), 0R to LORA_NRST DNP (fitting it on a GND-pad module would short the nRF reset GPIO).
Check continuity pad 12 <-> pad 15 / GND on a sample of the purchased lot and swap the links if pad 12 is NRST.

X-30: V3V3_LORA is gated. ESP32 TX (IO17, idle high) -> nRF RX through SN74LVC1G125 powered from V3V3_NRF: LVC inputs and
outputs are Ioff (partial power-down) specified, so nothing is injected into the unpowered node (replaces the 1k that still
allowed ~3 mA into the clamp). nRF TX -> ESP32 RX through a second LVC1G125 on always-on V3V3, so the ESP32 RX pull-up
cannot back-feed the node. Node reset is open-drain (SN74LVC1G07 on V3V3) with the pull-up on V3V3_NRF.
"""


def build(D):
    sh = D.sheet("lora", "Meshtastic LoRa node: nRF52840 + SX1262 (850-930 MHz)", board="B")
    G = "GND"
    VN, VR = "V3V3_NRF", "V3V3_E22"
    for n_ in (VN, VR):
        D.v(n_, 3.6)
    # C-17 / X-42 isolation links: nRF and radio separately measurable
    D.JP(sh, "V3V3_LORA", VN, i_op=0.02, note="ISO nRF52840")
    D.JP(sh, "V3V3_LORA", VR, i_op=0.124, note="ISO E22 radio")
    D.TP(sh, "V3V3_LORA")
    D.TP(sh, VN, small=True)
    D.TP(sh, VR, small=True)
    D.TP(sh, "GND")
    D.IC(sh, "E73-2G4M08S1CX", {
        "GND": G, "VCC": VN, "VDH": VN, "RST": "LORA_RST_N", "SWD": "LORA_SWDIO", "SWC": "LORA_SWCLK",
        "P0.06": "LORA_TXR", "P0.08": "LORA_RXR", "P0.20": "LORA_SCK", "P0.22": "LORA_MOSI", "P0.24": "LORA_MISO",
        "P1.00": "LORA_NSS", "P0.13": "LORA_BUSY", "P0.26": "LORA_DIO1", "P1.02": "LORA_NRST", "P1.04": "LORA_RXEN",
        "P0.07": "LORA_LED"},
        nc=["P1.11", "P1.10", "P0.03", "AI4", "P1.13", "AI0", "AI5", "AI7", "AI6", "XL1", "XL2", "AI3", "P1.09", "AI2",
            "P12", "DCH", "VBS", "P15", "D-", "P17", "D+", "NF1", "NF2", "P1.06"],
        fields={"Note": "Normal-voltage mode: VCC = VDDH = 3.3 V, DCCH unused (VERIFY vs nRF52840 PS). Runs stock Meshtastic."})
    D.C(sh, "C_10u_16V", VN, G)
    D.C(sh, "C_100n_16V", VN, G)
    # reset: open-drain from the always-on side, pull-up in the node's own domain
    D.IC(sh, "SN74LVC1G07DBVR", {"A": "EXP_LORA_RST_N", "GND": G, "Y": "LORA_RST_N", "VCC": "V3V3"}, nc=["N.C."],
         fields={"Note": "X-30/C-28: open-drain (Ioff) node reset; the SWD probe can also pull LORA_RST_N low without contention"})
    D.R(sh, "100k", "EXP_LORA_RST_N", G, fields={"Note": "expander input at power-up -> node held in reset until firmware"})
    D.R(sh, "10k", "LORA_RST_N", VN, fields={"Note": "C-9: pull-up to the node's own rail"})
    D.TP(sh, "LORA_RST_N", small=True)
    # UART buffers (X-30)
    D.IC(sh, "SN74LVC1G125DBVR", {"OE": G, "A": "LORA_RX", "GND": G, "Y": "LORA_RXR", "VCC": VN},
         fields={"Note": "X-30: ESP32 TX -> nRF RX, powered by the RECEIVER domain V3V3_NRF; Ioff: no injection when the node is off"})
    D.C(sh, "C_100n_16V", VN, G)
    D.IC(sh, "SN74LVC1G125DBVR", {"OE": G, "A": "LORA_TXR", "GND": G, "Y": "LORA_TX", "VCC": "V3V3"},
         fields={"Note": "X-30: nRF TX -> ESP32 RX, powered by V3V3; the ESP32 RX pull-up sees this output, not the node"})
    D.C(sh, "C_100n_16V", "V3V3", G)
    D.R(sh, "100k", "LORA_TXR", VN, fields={"Note": "defined idle-high while the node runs, 0 V (break) while V3V3_LORA is off"})
    D.R(sh, "1k", "LORA_LED", "LORA_LEDA")
    D.IC(sh, "KT-0603R", {"A": VN, "K": "LORA_LEDA"}, prefix="D", value="LORA LED")
    D.R(sh, "100", "LORA_VTREF", VN, fields={"Note": "C-28: SWD header VTref sense only"})
    D.CONN(sh, "DEBUG_NRF52_SWD", ["GND", "VTREF", "SWDIO", "SWCLK", "RESET", "TX"],
           {"GND": G, "VTREF": "LORA_VTREF", "SWDIO": "LORA_SWDIO", "SWCLK": "LORA_SWCLK", "RESET": "LORA_RST_N", "TX": "LORA_TXR"},
           footprint="Connector_PinHeader_1.27mm:PinHeader_1x06_P1.27mm_Vertical", fields={"_nobom": True}, prefix="J", dnp=True)
    D.IC(sh, "E22-900M22S", {
        "GND": G, "12": "LORA_E22_P12", "RXEN": "LORA_RXEN", "TXEN": "LORA_DIO2", "DIO2": "LORA_DIO2", "VCC": VR, "DIO1": "LORA_DIO1",
        "BUSY": "LORA_BUSY", "NRST": "LORA_NRST", "MISO": "LORA_MISO", "MOSI": "LORA_MOSI", "SCK": "LORA_SCK",
        "NSS": "LORA_NSS", "ANT": "LORA_ANT"},
        fields={"Op_I": 0.124, "Rated_I": 0.5, "Note": "22 dBm TX 124 mA max. Region set in firmware (US 915 / EU 868). "
                                                       "Pad 12 GND-or-NRST is isolatable (X-38), see the 0R links."})
    D.R(sh, "0", "LORA_E22_P12", G, fields={"Note": "X-38: FITTED - pad 12 = GND per the E22-M series manual in docs/"})
    r12 = D.R(sh, "0", "LORA_E22_P12", "LORA_NRST",
              fields={"Note": "X-38: DNP - fit (and remove the GND link) only if pad 12 is NRST on the purchased revision"})
    r12.dnp = True
    D.R(sh, "100k", "LORA_RXEN", G, fields={"Note": "C-33: RF switch in a defined state while the nRF boots"})
    for n_ in ("LORA_NRST", "LORA_BUSY", "LORA_DIO1", "LORA_E22_P12"):
        D.TP(sh, n_, small=True)
    D.C(sh, "C_22u_10V", VR, G)
    D.C(sh, "C_100n_16V", VR, G)
    D.IC(sh, "U.FL-R-SMT-1", {"GND": G, "SIN": "LORA_ANT"}, prefix="J", value="U.FL LoRa",
         fields={"Note": "50 ohm CPWG to the module ANT pad; pigtail to SMA bulkhead in the left end cap"})
    return sh
