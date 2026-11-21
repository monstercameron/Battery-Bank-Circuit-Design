"""Meshtastic node: Ebyte E73-2G4M08S1CX (nRF52840, BLE to phones, own U.FL antenna) + E22-900M22S (SX1262).
Pin choices follow a common nRF52840 + SX1262 Meshtastic variant; the board definition is written to match.
E22: RXEN driven by MCU, TXEN driven by DIO2 (DIO2-as-RF-switch). NRST appears on two pads in Ebyte's table - VERIFY.
"""


def build(D):
    sh = D.sheet("lora", "Meshtastic LoRa node: nRF52840 + SX1262 (850-930 MHz)", board="B")
    G, V = "GND", "V3V3_LORA"
    D.IC(sh, "E73-2G4M08S1CX", {
        "GND": G, "VCC": V, "VDH": V, "RST": "EXP_LORA_RST_N", "SWD": "LORA_SWDIO", "SWC": "LORA_SWCLK",
        "P0.06": "LORA_TXR", "P0.08": "LORA_RXR", "P0.20": "LORA_SCK", "P0.22": "LORA_MOSI", "P0.24": "LORA_MISO",
        "P1.00": "LORA_NSS", "P0.13": "LORA_BUSY", "P0.26": "LORA_DIO1", "P1.02": "LORA_NRST", "P1.04": "LORA_RXEN",
        "P0.07": "LORA_LED"},
        nc=["P1.11", "P1.10", "P0.03", "AI4", "P1.13", "AI0", "AI5", "AI7", "AI6", "XL1", "XL2", "AI3", "P1.09", "AI2",
            "P12", "DCH", "VBS", "P15", "D-", "P17", "D+", "NF1", "NF2", "P1.06"],
        fields={"Note": "Normal-voltage mode: VCC = VDDH = 3.3 V, DCCH unused (VERIFY vs nRF52840 PS). Runs stock Meshtastic."})
    D.C(sh, "C_10u_16V", V, G)
    D.C(sh, "C_100n_16V", V, G)
    D.R(sh, "10k", "EXP_LORA_RST_N", V, fields={"Note": "C-9: pull-up to the node's own gated rail"})
    D.R(sh, "1k", "LORA_TX", "LORA_TXR", fields={"Note": "C-9: series R limits back-power from the ESP32 UART when V3V3_LORA is off"})
    D.R(sh, "1k", "LORA_RX", "LORA_RXR")
    D.R(sh, "1k", "LORA_LED", "LORA_LEDA")
    D.IC(sh, "KT-0603R", {"A": V, "K": "LORA_LEDA"}, prefix="D", value="LORA LED")
    D.CONN(sh, "DEBUG_NRF52_SWD", ["GND", "3V3", "SWDIO", "SWCLK", "RESET", "TX"],
           {"GND": G, "3V3": V, "SWDIO": "LORA_SWDIO", "SWCLK": "LORA_SWCLK", "RESET": "EXP_LORA_RST_N", "TX": "LORA_TXR"},
           footprint="Connector_PinHeader_1.27mm:PinHeader_1x06_P1.27mm_Vertical", fields={"_nobom": True}, prefix="J", dnp=True)
    D.IC(sh, "E22-900M22S", {
        "GND": G, "RXEN": "LORA_RXEN", "TXEN": "LORA_DIO2", "DIO2": "LORA_DIO2", "VCC": V, "DIO1": "LORA_DIO1",
        "BUSY": "LORA_BUSY", "NRST": "LORA_NRST", "MISO": "LORA_MISO", "MOSI": "LORA_MOSI", "SCK": "LORA_SCK",
        "NSS": "LORA_NSS", "ANT": "LORA_ANT"},
        fields={"Op_I": 0.124, "Rated_I": 0.5, "Note": "22 dBm TX 124 mA max. Region set in firmware (US 915 / EU 868)."})
    D.C(sh, "C_22u_10V", V, G)
    D.C(sh, "C_100n_16V", V, G)
    D.IC(sh, "U.FL-R-SMT-1", {"GND": G, "SIN": "LORA_ANT"}, prefix="J", value="U.FL LoRa",
         fields={"Note": "50 ohm CPWG to the module ANT pad; pigtail to SMA bulkhead in the left end cap"})
    D.TP(sh, V)
    return sh
